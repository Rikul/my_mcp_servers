# SQLite Read-Only MCP Server

A Model Context Protocol (MCP) server that provides secure, read-only access to SQLite databases.

## Features

- **Read-Only Access**: All operations are strictly read-only. Write operations (INSERT, UPDATE, DELETE, etc.) are blocked
- **Three Main Tools**:
  - `list_tables`: List all tables in a database
  - `read_rows`: Read rows from a specific table with pagination
  - `execute_select`: Execute custom SELECT queries with validation
- **Security**: Query validation prevents SQL injection and write operations
- **Error Handling**: Comprehensive error messages for debugging

## Installation

```bash
cd sqlite_read_server
pip install -e .
```

## Usage

Run the MCP server:

```bash
sqlite-read-server-mcp
```

## Available Tools

### 1. list_tables

Lists all tables in a SQLite database.

**Parameters:**
- `db_path` (string, required): Path to the SQLite database file

**Returns:**
- List of table names, or error message

**Example:**
```python
list_tables(db_path="/path/to/database.db")
# Returns: ["users", "products", "orders"]
```

### 2. read_rows

Reads rows from a specific table with pagination support.

**Parameters:**
- `db_path` (string, required): Path to the SQLite database file
- `table_name` (string, required): Name of the table to read from
- `limit` (integer, optional): Maximum number of rows to return (default: 100, max: 10000)
- `offset` (integer, optional): Number of rows to skip (default: 0)

**Returns:**
- Dictionary containing:
  - `columns`: List of column names
  - `rows`: List of row data
  - `count`: Number of rows returned
  - `offset`: Offset used
  - `limit`: Limit used

**Example:**
```python
read_rows(
    db_path="/path/to/database.db",
    table_name="users",
    limit=10,
    offset=0
)
# Returns:
# {
#   "columns": ["id", "name", "email"],
#   "rows": [[1, "Alice", "alice@example.com"], [2, "Bob", "bob@example.com"]],
#   "count": 2,
#   "offset": 0,
#   "limit": 10
# }
```

### 3. execute_select

Executes a custom SELECT query on the database.

**Parameters:**
- `db_path` (string, required): Path to the SQLite database file
- `query` (string, required): SELECT query to execute

**Security:**
- Only read-only queries (starting with SELECT or WITH) are allowed
- Queries are validated to prevent write operations
- Prohibited keywords: INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, REPLACE, ATTACH, DETACH, PRAGMA

**Returns:**
- Dictionary containing:
  - `columns`: List of column names
  - `rows`: List of row data
  - `count`: Number of rows returned

**Example:**
```python
execute_select(
    db_path="/path/to/database.db",
    query="SELECT name, email FROM users WHERE id > 10 LIMIT 5"
)
# Returns:
# {
#   "columns": ["name", "email"],
#   "rows": [["Alice", "alice@example.com"], ["Bob", "bob@example.com"]],
#   "count": 2
# }
```

## Security Features

### Read-Only Enforcement

The server implements multiple layers of protection to ensure read-only access:

1. **Query Validation**: All queries are validated before execution
2. **Keyword Blocking**: Prohibited SQL keywords are detected and blocked
3. **SELECT-Only**: Only queries starting with SELECT or WITH are allowed
4. **Comment Stripping**: SQL comments are removed before validation to prevent bypasses

### Table Name Sanitization

Table names are validated to prevent SQL injection:
- Only alphanumeric characters and underscores allowed
- Pattern matching: `^[a-zA-Z0-9_]+$`

### Database Path Validation

Database paths are validated to ensure:
- File exists
- Path points to a file (not a directory)
- Accessible for reading

## Error Handling

The server provides clear error messages for common issues:

- **Database not found**: "Database file does not exist: /path/to/db"
- **Invalid table name**: "Error: Invalid table name. Only alphanumeric characters and underscores are allowed."
- **Table doesn't exist**: "Error: Table 'table_name' does not exist"
- **Prohibited query**: "Query contains prohibited keyword 'INSERT'. Only SELECT queries are allowed."
- **Invalid query syntax**: "SQL error: near 'INVALID': syntax error"

## Limitations

- Maximum of 10,000 rows per `read_rows` request
- Only SELECT queries supported
- No write operations allowed
- SQLite databases only
