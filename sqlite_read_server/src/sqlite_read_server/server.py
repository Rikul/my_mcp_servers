"""SQLite Read-Only MCP Server - Provides read-only access to SQLite databases."""

from __future__ import annotations

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

# Global variable to store the configured database path
_database_path: str | None = None

mcp = FastMCP("SQLite Read-Only Server")


def _validate_database_path() -> str:
    """Validate that the database path exists and is accessible."""
    global _database_path

    if not _database_path:
        raise ValueError(
            "No database path configured. Please configure database path at startup."
        )

    path = Path(_database_path)
    if not path.exists():
        raise ValueError(f"Database file does not exist:{_database_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file:{_database_path}")
    return str(_database_path)


def _strip_string_literals(query: str) -> str:
    """Return the query with contents of quoted string literals removed."""

    result: list[str] = []
    i = 0
    in_single = False
    in_double = False
    length = len(query)

    while i < length:
        char = query[i]

        if in_single:
            if char == "'":
                # SQLite escapes single quotes with a doubled quote.
                if i + 1 < length and query[i + 1] == "'":
                    i += 2
                    continue
                in_single = False
            i += 1
            continue

        if in_double:
            if char == '"':
                if i + 1 < length and query[i + 1] == '"':
                    i += 2
                    continue
                in_double = False
            i += 1
            continue

        if char == "'":
            in_single = True
            i += 1
            continue

        if char == '"':
            in_double = True
            i += 1
            continue

        result.append(char)
        i += 1

    return "".join(result)


def _is_read_only_query(query: str) -> bool:
    """
    Validate that a SQL query is read-only (SELECT only).

    Returns True if the query appears to be a SELECT statement.
    Raises ValueError if the query contains prohibited operations.
    """
    # Remove SQL comments
    query_clean = re.sub(r"--.*$", "", query, flags=re.MULTILINE)
    query_clean = re.sub(r"/\*.*?\*/", "", query_clean, flags=re.DOTALL)

    # Remove string literals to avoid false positives when scanning for keywords
    query_no_literals = _strip_string_literals(query_clean)

    # Convert to uppercase for checking
    query_upper = query_no_literals.upper().strip()

    # Check for prohibited keywords
    prohibited_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "REPLACE",
        "ATTACH",
        "DETACH",
        "PRAGMA",
    ]

    for keyword in prohibited_keywords:
        # Use word boundaries to avoid false positives
        if re.search(rf"\b{keyword}\b", query_upper):
            raise ValueError(
                f"Query contains prohibited keyword '{keyword}'. "
                f"Only SELECT queries are allowed."
            )

    # Must start with SELECT (after whitespace)
    if not (query_upper.startswith("SELECT") or query_upper.startswith("WITH")):
        raise ValueError(
            "Query must start with SELECT or WITH. Only read-only queries are allowed."
        )

    return True


@mcp.tool()
def list_tables() -> list[str] | str:
    """
    List all tables in a SQLite database.

    Returns:
        List of table names in the database, or error message
    """
    try:
        validated_path = _validate_database_path()

        conn = sqlite3.connect(validated_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]
            return tables
        finally:
            conn.close()

    except Exception as e:
        return f"Error listing tables: {str(e)}"


@mcp.tool()
def read_rows(
    table_name: str, limit: int = 100, offset: int = 0
) -> dict[str, Any] | str:
    """
    Read rows from a specific table in a SQLite database.

    Args:
        table_name: Name of the table to read from
        limit: Maximum number of rows to return (default: 100, max: 10000)
        offset: Number of rows to skip (default: 0)

    Returns:
        Dictionary containing column names and row data, or error message
    """
    try:
        validated_path = _validate_database_path()

        # Validate limit
        if limit <= 0:
            return "Error: limit must be greater than 0"
        if limit > 10000:
            return "Error: limit cannot exceed 10000"

        # Validate offset
        if offset < 0:
            return "Error: offset cannot be negative"

        # Sanitize table name to prevent SQL injection
        # Only allow alphanumeric, underscore, and basic characters
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            return "Error: Invalid table name. Only alphanumeric characters and underscores are allowed."

        conn = sqlite3.connect(validated_path)
        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                return f"Error: Table '{table_name}' does not exist"

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            # Read rows
            cursor.execute(
                f"SELECT * FROM {table_name} LIMIT ? OFFSET ?", (limit, offset)
            )
            rows = cursor.fetchall()

            return {
                "columns": columns,
                "rows": rows,
                "count": len(rows),
                "offset": offset,
                "limit": limit,
            }
        finally:
            conn.close()

    except Exception as e:
        return f"Error reading rows: {str(e)}"


@mcp.tool()
def execute_select(query: str) -> dict[str, Any] | str:
    """
    Execute a SELECT query on a SQLite database.

    Only SELECT queries are allowed for security. Queries containing
    INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or other write operations
    will be rejected.

    Args:
        query: SELECT query to execute

    Returns:
        Dictionary containing column names and query results, or error message
    """
    try:
        validated_path = _validate_database_path()

        # Validate that query is read-only
        _is_read_only_query(query)

        conn = sqlite3.connect(validated_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query)

            # Get column names from cursor description
            columns = (
                [desc[0] for desc in cursor.description] if cursor.description else []
            )

            rows = cursor.fetchall()

            return {"columns": columns, "rows": rows, "count": len(rows)}
        finally:
            conn.close()

    except ValueError as e:
        # Validation errors (prohibited keywords, etc.)
        return f"Query validation error: {str(e)}"
    except sqlite3.Error as e:
        # SQL errors
        return f"SQL error: {str(e)}"
    except Exception as e:
        # Other errors
        return f"Error executing query: {str(e)}"


@mcp.tool()
def get_table_info(table_name: str) -> dict[str, Any] | str:
    """
    Get detailed information about a table's structure using PRAGMA table_info.

    Args:
        table_name: Name of the table to get information for

    Returns:
        Dictionary containing table structure information, or error message
    """
    try:
        validated_path = _validate_database_path()

        # Sanitize table name to prevent SQL injection
        # Only allow alphanumeric, underscore, and basic characters
        if not re.match(r"^[a-zA-Z0-9_]+$", table_name):
            return "Error: Invalid table name. Only alphanumeric characters and underscores are allowed."

        conn = sqlite3.connect(validated_path)
        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,),
            )
            if not cursor.fetchone():
                return f"Error: Table '{table_name}' does not exist"

            # Get table info using PRAGMA table_info
            cursor.execute(f"PRAGMA table_info({table_name})")
            table_info = cursor.fetchall()

            # Format the results into a more readable structure
            columns = []
            for row in table_info:
                column_info = {
                    "cid": row[0],  # Column ID (position)
                    "name": row[1],  # Column name
                    "type": row[2],  # Data type
                    "notnull": bool(row[3]),  # NOT NULL constraint
                    "default_value": row[4],  # Default value
                    "pk": bool(row[5]),  # Primary key
                }
                columns.append(column_info)

            return {
                "table_name": table_name,
                "columns": columns,
                "column_count": len(columns),
            }
        finally:
            conn.close()

    except Exception as e:
        return f"Error getting table info: {str(e)}"


def main() -> None:
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="SQLite Read-Only MCP Server")
    parser.add_argument(
        "--database", "-d", type=str, help="Path to the SQLite database file"
    )
    parser.add_argument(
        "--env-var",
        type=str,
        default="SQLITE_DATABASE_PATH",
        help="Environment variable name for database path (default: SQLITE_DATABASE_PATH)",
    )

    args = parser.parse_args()

    # Determine database path from command line, environment variable, or prompt for it
    database_path = None

    if args.database:
        database_path = args.database
    elif args.env_var and os.getenv(args.env_var):
        database_path = os.getenv(args.env_var)

    # Database path is now required
    if not database_path:
        print(
            "Error: Database path is required. Provide it via --database argument or environment variable.",
            file=sys.stderr,
        )
        sys.exit(1)

    global _database_path
    _database_path = database_path.strip()
    _validate_database_path()

    mcp.run()


if __name__ == "__main__":
    main()
