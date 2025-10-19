# Current Date & Time MCP Server

This is a sample MCP server that provides tools for getting the current date and time.

## Features

- Get today's date in YYYY-MM-DD format (with optional timezone support)
- Get the current time in HH:MM:SS format (with optional timezone support)

## Installation

To install the server in editable mode, run the following command:

```bash
pip install -e .
```

## Usage

There are two ways to run the server:

### Using `uvx`

If you have `uvx` installed, you can run the server with the following command:

```bash
uvx current-date-time-mcp
```

### Using `python`

You can also run the server directly with `python`:

```bash
python -m current_date_time.server
```

Alternatively, you can run the `server.py` file directly:

```bash
python src/current_date_time/server.py
```

## Configuration

To use this server with Claude Code or other MCP clients, add the following entry to your `mcpServers` configuration:

```json
{
  "mcpServers": {
    "current-date-time": {
      "command": "uvx",
      "args": ["current-date-time-mcp"]
    }
  }
}
```

Alternatively, if you're running locally in development mode, specify the full path:

```json
{
  "mcpServers": {
    "current-date-time": {
      "command": "python",
      "args": [
        "-m",
        "current_date_time.server"
      ],
      "cwd": "/path/to/my_mcp_servers/current_date_time"
    }
  }
}
```

Or run the server script directly:

```json
{
  "mcpServers": {
    "current-date-time": {
      "command": "python",
      "args": [
        "/path/to/my_mcp_servers/current_date_time/src/current_date_time/server.py"
      ]
    }
  }
}
```

## Tools

### get_today_date

Get today's date with optional timezone support.

**Parameters:**
- `timezone` (optional): Timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")

**Examples:**
- `get_today_date()` - Returns date in local timezone
- `get_today_date("America/New_York")` - Returns date in New York timezone
- `get_today_date("Asia/Tokyo")` - Returns date in Tokyo timezone

### get_current_time

Get the current time with optional timezone support.

**Parameters:**
- `timezone` (optional): Timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo")

**Examples:**
- `get_current_time()` - Returns time in local timezone
- `get_current_time("America/New_York")` - Returns time in New York timezone
- `get_current_time("Europe/London")` - Returns time in London timezone
