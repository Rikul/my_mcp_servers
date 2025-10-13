# Wikipedia MCP Server

This is a sample MCP server that provides tools for interacting with Wikipedia.

## Features

- Get a summary of a Wikipedia page.
- Get the full content of a Wikipedia page.
- Search for Wikipedia articles.

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
uvx mcp.server wikipedia-mcp
```

### Using `python`

You can also run the server directly with `python`:

```bash
python -m wikipedia_mcp.server
```

Alternatively, you can run the `server.py` file directly:

```bash
python src/wikipedia_mcp/server.py
```

## Configuration

To use this server with Claude Code or other MCP clients, add the following entry to your `mcpServers` configuration:

```json
{
  "mcpServers": {
    "wikipedia": {
      "command": "uvx",
      "args": ["wikipedia-mcp"]
    }
  }
}
```

Alternatively, if you're running locally in development mode, specify the full path:

```json
{
  "mcpServers": {
    "wikipedia": {
      "command": "python",
      "args": [
        "-m",
        "wikipedia_mcp.server"
      ],
      "cwd": "D:/Documents/src/mcp/my_mcp_servers/wikipedia_mcp"
    }
  }
}
```

Or run the server script directly:

```json
{
  "mcpServers": {
    "wikipedia": {
      "command": "python",
      "args": [
        "D:/Documents/src/mcp/my_mcp_servers/wikipedia_mcp/src/wikipedia_mcp/server.py"
      ]
    }
  }
}
```
