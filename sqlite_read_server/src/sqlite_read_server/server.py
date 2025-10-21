"""SQLite Read-Only MCP Server - Provides read-only access to SQLite databases."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("SQLite Read-Only Server")


def _validate_database_path(db_path: str) -> str:
    """Validate that the database path exists and is accessible."""
    path = Path(db_path)
    if not path.exists():
        raise ValueError(f"Database file does not exist: {db_path}")
    if not path.is_file():
        raise ValueError(f"Path is not a file: {db_path}")
    return db_path


def _is_read_only_query(query: str) -> bool:
    """
    Validate that a SQL query is read-only (SELECT only).

    Returns True if the query appears to be a SELECT statement.
    Raises ValueError if the query contains prohibited operations.
    """
    # Remove SQL comments
    query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)

    # Convert to uppercase for checking
    query_upper = query_clean.upper().strip()

    # Check for prohibited keywords
    prohibited_keywords = [
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'ATTACH', 'DETACH', 'PRAGMA'
    ]

    for keyword in prohibited_keywords:
        # Use word boundaries to avoid false positives
        if re.search(rf'\b{keyword}\b', query_upper):
            raise ValueError(
                f"Query contains prohibited keyword '{keyword}'. "
                f"Only SELECT queries are allowed."
            )

    # Must start with SELECT (after whitespace)
    if not query_upper.startswith('SELECT'):
        raise ValueError(
            "Query must start with SELECT. Only SELECT queries are allowed."
        )

    return True


@mcp.tool()
def list_tables(db_path: str) -> list[str] | str:
    """
    List all tables in a SQLite database.

    Args:
        db_path: Path to the SQLite database file

    Returns:
        List of table names in the database, or error message
    """
    try:
        _validate_database_path(db_path)

        conn = sqlite3.connect(db_path)
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
    db_path: str,
    table_name: str,
    limit: int = 100,
    offset: int = 0
) -> dict[str, Any] | str:
    """
    Read rows from a specific table in a SQLite database.

    Args:
        db_path: Path to the SQLite database file
        table_name: Name of the table to read from
        limit: Maximum number of rows to return (default: 100, max: 10000)
        offset: Number of rows to skip (default: 0)

    Returns:
        Dictionary containing column names and row data, or error message
    """
    try:
        _validate_database_path(db_path)

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
        if not re.match(r'^[a-zA-Z0-9_]+$', table_name):
            return "Error: Invalid table name. Only alphanumeric characters and underscores are allowed."

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()

            # Check if table exists
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
                (table_name,)
            )
            if not cursor.fetchone():
                return f"Error: Table '{table_name}' does not exist"

            # Get column names
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]

            # Read rows
            cursor.execute(
                f"SELECT * FROM {table_name} LIMIT ? OFFSET ?",
                (limit, offset)
            )
            rows = cursor.fetchall()

            return {
                "columns": columns,
                "rows": rows,
                "count": len(rows),
                "offset": offset,
                "limit": limit
            }
        finally:
            conn.close()

    except Exception as e:
        return f"Error reading rows: {str(e)}"


@mcp.tool()
def execute_select(db_path: str, query: str) -> dict[str, Any] | str:
    """
    Execute a SELECT query on a SQLite database.

    Only SELECT queries are allowed for security. Queries containing
    INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, or other write operations
    will be rejected.

    Args:
        db_path: Path to the SQLite database file
        query: SELECT query to execute

    Returns:
        Dictionary containing column names and query results, or error message
    """
    try:
        _validate_database_path(db_path)

        # Validate that query is read-only
        _is_read_only_query(query)

        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(query)

            # Get column names from cursor description
            columns = [desc[0] for desc in cursor.description] if cursor.description else []

            rows = cursor.fetchall()

            return {
                "columns": columns,
                "rows": rows,
                "count": len(rows)
            }
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


def main() -> None:
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
