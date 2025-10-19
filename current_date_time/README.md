# Current Date & Time MCP Server

This is a sample MCP server that provides tools for getting the current date and time.

## Features

- Get today's date in YYYY-MM-DD format

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
