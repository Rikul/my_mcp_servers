# SQLite Read-Only MCP Server

A Model Context Protocol (MCP) server that provides secure, read-only access to SQLite databases.

## Features

- **Read-Only Access**: All operations are strictly read-only. Write operations (INSERT, UPDATE, DELETE, etc.) are blocked
- **Four Main Tools**:
  - `list_tables`: List all tables in a database
  - `read_rows`: Read rows from a specific table with pagination
  - `execute_select`: Execute custom SELECT queries with validation
  - `get_table_info`: Get detailed information about a table's structure
- **Security**: Query validation prevents SQL injection and write operations
- **Error Handling**: Comprehensive error messages for debugging
- **Database Configuration**: Database path must be configured at server startup

## Installation

```bash
cd sqlite_read_server
pip install -e .
```

## Usage

### Command Line Options

The database path is **required** and can be specified in two ways:

1. **Command line argument**:
```bash
sqlite-read-server-mcp --database /path/to/your/database.db
# or short form:
sqlite-read-server-mcp -d /path/to/your/database.db
```

2. **Environment variable**:
```bash
# Set environment variable
set SQLITE_DATABASE_PATH=C:\path\to\your\database.db
sqlite-read-server-mcp

# Or use custom environment variable name
set MY_DB_PATH=C:\path\to\your\database.db
sqlite-read-server-mcp --env-var MY_DB_PATH
```

**Note**: A database path must be provided at startup. The server will not start without a valid database configuration.

## MCP Client Configuration

To use this server with an MCP client (like Claude Desktop), add the following configuration. **Note**: The database path must be configured at server startup.

### Claude Desktop Configuration with Database Path

Add this entry to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "sqlite-read-server": {
      "command": "sqlite-read-server-mcp",
      "args": ["--database", "C:\\path\\to\\your\\database.db"]
    }
  }
}
```

### Using Environment Variable

```json
{
  "mcpServers": {
    "sqlite-read-server": {
      "command": "sqlite-read-server-mcp",
      "args": [],
      "env": {
        "SQLITE_DATABASE_PATH": "C:\\path\\to\\your\\database.db"
      }
    }
  }
}
```

### Alternative: Using Python Module

If you prefer to run the server as a Python module:

```json
{
  "mcpServers": {
    "sqlite-read-server": {
      "command": "python",
      "args": ["-m", "sqlite_read_server.server", "--database", "C:\\path\\to\\your\\database.db"]
    }
  }
}
```

### With Custom Environment

If you installed the package in a virtual environment:

```json
{
  "mcpServers": {
    "sqlite-read-server": {
      "command": "path/to/your/venv/Scripts/sqlite-read-server-mcp.exe",
      "args": ["--database", "C:\\path\\to\\your\\database.db"]
    }
  }
}
```

Once configured, restart your MCP client to load the server. The server will be available with four tools: `list_tables`, `read_rows`, `execute_select`, and `get_table_info`.

## Available Tools

### 1. list_tables

Lists all tables in a SQLite database.

**Parameters:**
- None (uses database configured at startup)

**Returns:**
- List of table names, or error message

**Example:**
```python
list_tables()
# Returns: ["users", "products", "orders"]
```

### 2. read_rows

Reads rows from a specific table with pagination support.

**Parameters:**
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
    query="SELECT name, email FROM users WHERE id > 10 LIMIT 5"
)
# Returns:
# {
#   "columns": ["name", "email"],
#   "rows": [["Alice", "alice@example.com"], ["Bob", "bob@example.com"]],
#   "count": 2
# }
```

### 4. get_table_info

Get detailed information about a table's structure using PRAGMA table_info.

**Parameters:**
- `table_name` (string, required): Name of the table to get information for

**Returns:**
- Dictionary containing:
  - `table_name`: Name of the table
  - `columns`: List of column information dictionaries
  - `column_count`: Number of columns in the table

Each column information dictionary contains:
- `cid`: Column ID (position)
- `name`: Column name
- `type`: Data type
- `notnull`: Whether the column has NOT NULL constraint
- `default_value`: Default value for the column
- `pk`: Whether the column is part of the primary key

**Example:**
```python
get_table_info(table_name="users")
# Returns:
# {
#   "table_name": "users",
#   "columns": [
#     {
#       "cid": 0,
#       "name": "id",
#       "type": "INTEGER",
#       "notnull": true,
#       "default_value": null,
#       "pk": true
#     },
#     {
#       "cid": 1,
#       "name": "name",
#       "type": "TEXT",
#       "notnull": false,
#       "default_value": null,
#       "pk": false
#     }
#   ],
#   "column_count": 2
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

- **Database not configured**: "No database path configured. Please configure database path at startup."
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


# Example System Prompt to use with the tool

You are a world-class, helpful, and highly knowledgeable Database Administrator (DBA). Your expertise covers all major SQL dialects.

Your core mission is to provide technical, detailed, and actionable advice. All recommendations must adhere to industry best practices for data integrity, security, performance, and scalability.

When responding:

Be Pragmatic: Focus on solutions that can be implemented effectively in a production environment.

Tone: Maintain a professional, technical, and solution-oriented tone.

You can use DB tools to get a list of tables, get information about any table, get all rows in a table or send a SELECT query.

---

Before starting the conversation:

	- Get the list of tables.
	- If no database is connected, ask the user for database path.
	- When the database is connected, get the list of tables and for each table, get the table information.

You should display results to the user and ask for furture instructions.