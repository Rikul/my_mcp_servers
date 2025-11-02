# Conversations MCP Server

This MCP server provides utilities for storing and retrieving chat conversations. It lets you:

- Save conversations with an identifier, title, messages, and optional metadata.
- Load previously saved conversations back into the MCP context as structured data and text resources.
- Search across saved conversations by keyword to locate relevant transcripts.

Conversations are stored on disk inside the user's application data directory (for example
`~/.local/share/mcp_conversations`). Each conversation is written as a JSON document that
contains the transcript and metadata.

## Available tools

- `save_conversation` – Store or update a conversation transcript.
- `load_conversation` – Retrieve a saved conversation and expose it as an MCP text resource.
- `list_conversations` – List saved conversations with summary metadata.
- `search_conversations` – Find conversations whose titles, metadata, or messages match a query string.

## Running the server

```bash
uv run conversations
```

The server exposes the MCP tools described above.
