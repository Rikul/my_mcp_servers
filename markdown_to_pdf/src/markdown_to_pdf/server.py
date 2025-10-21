"""
Markdown to PDF MCP Server

Provides tools to convert Markdown content to PDF files.
"""

import os
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
import markdown
from weasyprint import HTML, CSS

# Initialize the MCP server
mcp = FastMCP("Markdown to PDF")

# Get the default output directory from environment variable
DEFAULT_OUTPUT_DIR = os.getenv("MARKDOWN_PDF_OUTPUT_DIR", os.getcwd())


@mcp.tool()
def save_markdown_to_pdf(
    markdown_content: str,
    filename: str,
    output_dir: Optional[str] = None,
    css_styles: Optional[str] = None
) -> str:
    """
    Convert Markdown content to a PDF file and save it to disk.

    Args:
        markdown_content: The Markdown text to convert to PDF
        filename: Name of the output PDF file (e.g., "document.pdf")
        output_dir: Directory where the PDF should be saved. If not provided,
                   uses the MARKDOWN_PDF_OUTPUT_DIR environment variable or
                   the current working directory.
        css_styles: Optional CSS styles to apply to the PDF. If not provided,
                   uses default styling for readability.

    Returns:
        Success message with the full path to the saved PDF, or error message

    Example:
        save_markdown_to_pdf(
            markdown_content="# Hello World\\n\\nThis is a test.",
            filename="test.pdf",
            output_dir="/home/user/documents"
        )
    """
    try:
        # Determine output directory
        target_dir = output_dir if output_dir else DEFAULT_OUTPUT_DIR

        # Validate and create output directory if it doesn't exist
        output_path = Path(target_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)

        if not output_path.is_dir():
            return f"Error: Output path '{target_dir}' exists but is not a directory"

        # Ensure filename has .pdf extension
        if not filename.endswith('.pdf'):
            filename = f"{filename}.pdf"

        # Validate filename (basic sanitization)
        if any(char in filename for char in ['/', '\\', '\0']):
            return "Error: Invalid filename. Filename cannot contain path separators"

        # Full output path
        full_path = output_path / filename

        # Convert Markdown to HTML
        html_content = markdown.markdown(
            markdown_content,
            extensions=['extra', 'codehilite', 'tables', 'fenced_code']
        )

        # Default CSS for better PDF rendering
        default_css = """
        @page {
            size: A4;
            margin: 2.5cm;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            font-size: 11pt;
            line-height: 1.6;
            color: #333;
            max-width: 100%;
        }

        h1, h2, h3, h4, h5, h6 {
            margin-top: 1.5em;
            margin-bottom: 0.5em;
            font-weight: 600;
            line-height: 1.25;
        }

        h1 {
            font-size: 2em;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.3em;
        }

        h2 {
            font-size: 1.5em;
            border-bottom: 1px solid #eee;
            padding-bottom: 0.3em;
        }

        h3 { font-size: 1.25em; }
        h4 { font-size: 1em; }
        h5 { font-size: 0.875em; }
        h6 { font-size: 0.85em; color: #666; }

        p {
            margin-bottom: 1em;
        }

        code {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 0.2em 0.4em;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 85%;
        }

        pre {
            background-color: #f6f8fa;
            border-radius: 3px;
            padding: 16px;
            overflow: auto;
            line-height: 1.45;
        }

        pre code {
            background-color: transparent;
            padding: 0;
            font-size: 100%;
        }

        blockquote {
            border-left: 4px solid #ddd;
            padding-left: 1em;
            margin-left: 0;
            color: #666;
        }

        table {
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 1em;
        }

        table th,
        table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }

        table th {
            background-color: #f6f8fa;
            font-weight: 600;
        }

        table tr:nth-child(even) {
            background-color: #f9f9f9;
        }

        a {
            color: #0366d6;
            text-decoration: none;
        }

        img {
            max-width: 100%;
            height: auto;
        }

        ul, ol {
            padding-left: 2em;
            margin-bottom: 1em;
        }

        li {
            margin-bottom: 0.25em;
        }

        hr {
            border: none;
            border-top: 1px solid #eee;
            margin: 1.5em 0;
        }
        """

        # Wrap HTML content in a complete HTML document
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Markdown to PDF</title>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """

        # Use custom CSS if provided, otherwise use default
        css_to_use = css_styles if css_styles else default_css

        # Convert HTML to PDF
        HTML(string=full_html).write_pdf(
            str(full_path),
            stylesheets=[CSS(string=css_to_use)]
        )

        return f"Success: PDF saved to {full_path}"

    except PermissionError as e:
        return f"Error: Permission denied when writing to '{target_dir}': {str(e)}"
    except OSError as e:
        return f"Error: OS error occurred: {str(e)}"
    except Exception as e:
        return f"Error: Failed to convert Markdown to PDF: {str(e)}"


def main() -> None:
    """
    Main entry point for the MCP server.

    The output directory can be configured by setting the MARKDOWN_PDF_OUTPUT_DIR
    environment variable before starting the server. If not set, the current
    working directory will be used by default.

    Example:
        export MARKDOWN_PDF_OUTPUT_DIR=/home/user/pdfs
        markdown-to-pdf-mcp
    """
    mcp.run()


if __name__ == "__main__":
    main()
