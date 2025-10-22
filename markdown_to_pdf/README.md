# Markdown to PDF MCP Server

An MCP (Model Context Protocol) server that provides tools to convert Markdown content to beautifully formatted PDF files.

## Features

- Convert Markdown text to PDF with a single function call
- Configurable output directory via environment variable or function parameter
- Support for extended Markdown features (tables, code blocks, syntax highlighting)
- Customizable CSS styling for PDF output
- Clean, professional default styling
- Automatic directory creation if output path doesn't exist
- Comprehensive error handling

## Installation

```bash
cd markdown_to_pdf
pip install -e .
```

This will install the server and its dependencies:
- `mcp` - Model Context Protocol framework
- `markdown` - Markdown parser with extensions support
- `reportlab` - Pure Python PDF generation library (no external dependencies required)
- `Pygments` - Syntax highlighting support

## Usage

### Starting the Server

You can configure the default output directory using an environment variable:

```bash
# Set the default output directory
export MARKDOWN_PDF_OUTPUT_DIR=/path/to/your/pdf/folder

# Start the server
markdown-to-pdf-mcp
```

If you don't set `MARKDOWN_PDF_OUTPUT_DIR`, the server will use the current working directory as the default.

## MCP Client Configuration

To use this server with an MCP client (like Claude Desktop), add the following configuration:

### Claude Desktop Configuration

Add this entry to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json` on Windows or `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

#### Basic Configuration

```json
{
  "mcpServers": {
    "markdown-to-pdf": {
      "command": "markdown-to-pdf-mcp",
      "args": []
    }
  }
}
```

#### With Custom Output Directory

```json
{
  "mcpServers": {
    "markdown-to-pdf": {
      "command": "markdown-to-pdf-mcp",
      "args": [],
      "env": {
        "MARKDOWN_PDF_OUTPUT_DIR": "C:\\Users\\YourName\\Documents\\PDFs"
      }
    }
  }
}
```

#### Using Python Module (Alternative)

If you prefer to run the server as a Python module:

```json
{
  "mcpServers": {
    "markdown-to-pdf": {
      "command": "python",
      "args": ["-m", "markdown_to_pdf.server"]
    }
  }
}
```

#### With Virtual Environment

If you installed the package in a virtual environment:

```json
{
  "mcpServers": {
    "markdown-to-pdf": {
      "command": "path/to/your/venv/Scripts/markdown-to-pdf-mcp.exe",
      "args": [],
      "env": {
        "MARKDOWN_PDF_OUTPUT_DIR": "C:\\Users\\YourName\\Documents\\PDFs"
      }
    }
  }
}
```

#### Linux/macOS Configuration

```json
{
  "mcpServers": {
    "markdown-to-pdf": {
      "command": "markdown-to-pdf-mcp",
      "args": [],
      "env": {
        "MARKDOWN_PDF_OUTPUT_DIR": "/home/username/Documents/PDFs"
      }
    }
  }
}
```

Once configured, restart your MCP client to load the server. The server will be available with the `save_markdown_to_pdf` tool.

### Using the Tool in MCP Clients

Once the server is configured and running, you can use the `save_markdown_to_pdf` tool in your MCP client. Here are some example use cases:

#### Basic Usage
```
Convert this markdown to PDF:

# My Report
This is a test document with **bold** text.

Save it as "report.pdf"
```

#### With Custom Output Directory
```
Convert this markdown to PDF and save it to my Documents folder:

# Meeting Notes
- Point 1
- Point 2

Save as "meeting_notes.pdf" in "C:\Users\YourName\Documents"
```

#### With Custom Styling
```
Convert this markdown to PDF with custom styling:

# Styled Document
This document should have a serif font.

Save as "styled.pdf" with CSS that uses Georgia font family.
```

### Available Tools

#### `save_markdown_to_pdf`

Convert Markdown content to a PDF file and save it to disk.

**Parameters:**

- `markdown_content` (string, required): The Markdown text to convert to PDF
- `filename` (string, required): Name of the output PDF file (e.g., "document.pdf")
- `output_dir` (string, optional): Directory where the PDF should be saved. If not provided, uses the `MARKDOWN_PDF_OUTPUT_DIR` environment variable or current working directory
- `css_styles` (string, optional): Custom CSS styles to apply to the PDF. If not provided, uses clean default styling

**Returns:**

Success message with the full path to the saved PDF, or an error message if conversion fails.

**Example:**

```python
save_markdown_to_pdf(
    markdown_content="""
# My Document

This is a **sample** document with:

- Bullet points
- **Bold** and *italic* text
- Code blocks

## Code Example

```python
def hello():
    print("Hello, World!")
```

## Table

| Feature | Status |
|---------|--------|
| Tables  | ✓      |
| Code    | ✓      |
| Images  | ✓      |
""",
    filename="my_document.pdf",
    output_dir="/home/user/documents"
)
```

### Supported Markdown Features

The server supports extended Markdown syntax including:

- **Headers** (H1-H6)
- **Text formatting** (bold, italic, strikethrough)
- **Lists** (ordered and unordered)
- **Code blocks** with syntax highlighting
- **Inline code**
- **Tables**
- **Blockquotes**
- **Horizontal rules**
- **Links**
- **Images** (with proper sizing)

### Default Styling

The PDF output includes professional default styling with:

- A4 page size with 2.5cm margins
- Clean, readable typography
- Syntax-highlighted code blocks
- Styled tables with alternating row colors
- Proper spacing and hierarchy for headers
- GitHub-inspired color scheme

### Custom Styling

The server uses reportlab's built-in styling system with professional defaults. While the `css_styles` parameter is available for compatibility, the styling is handled internally through reportlab's ParagraphStyle system, which provides clean and consistent PDF output without requiring external dependencies.

## Configuration

### Environment Variables

- `MARKDOWN_PDF_OUTPUT_DIR`: Default directory for saving PDF files

### Parameter Priority

The output directory is determined in this order:

1. `output_dir` parameter (if provided to the function)
2. `MARKDOWN_PDF_OUTPUT_DIR` environment variable (if set)
3. Current working directory (fallback)

## Error Handling

The server provides clear error messages for common issues:

- **Permission errors**: When the server doesn't have write access to the output directory
- **Invalid paths**: When the output path exists but is not a directory
- **Invalid filenames**: When the filename contains path separators or invalid characters
- **Conversion errors**: When Markdown parsing or PDF generation fails

## Dependencies

- **Python 3.8+**
- **mcp**: MCP server framework
- **markdown**: Markdown parser with extensions support
- **weasyprint**: Powerful PDF rendering engine
