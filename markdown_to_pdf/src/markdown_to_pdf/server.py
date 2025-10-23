"""
Markdown to PDF MCP Server

Provides tools to convert Markdown content to PDF files.
"""

import os
import re
from pathlib import Path
from typing import Optional
from mcp.server.fastmcp import FastMCP
import markdown
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Preformatted, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas

# Initialize the MCP server
mcp = FastMCP("Markdown to PDF")

# Get the default output directory from environment variable
DEFAULT_OUTPUT_DIR = os.getenv("MARKDOWN_PDF_OUTPUT_DIR", os.getcwd())


def create_styles():
    """Create custom paragraph styles for PDF."""
    styles = getSampleStyleSheet()

    # Heading styles
    styles.add(ParagraphStyle(
        name='CustomH1',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomH2',
        parent=styles['Heading2'],
        fontSize=20,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomH3',
        parent=styles['Heading3'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomH4',
        parent=styles['Heading4'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomH5',
        parent=styles['Heading4'],
        fontSize=12,
        textColor=colors.HexColor('#333333'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    ))

    styles.add(ParagraphStyle(
        name='CustomH6',
        parent=styles['Heading4'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        spaceAfter=6,
        spaceBefore=6,
        fontName='Helvetica-Bold'
    ))

    # Body text style
    styles.add(ParagraphStyle(
        name='CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        alignment=TA_LEFT,
        fontName='Helvetica'
    ))

    # Code style
    styles.add(ParagraphStyle(
        name='CustomCode',
        parent=styles['Code'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        backColor=colors.HexColor('#f6f8fa'),
        spaceAfter=12,
        spaceBefore=12,
        leftIndent=12,
        rightIndent=12,
        fontName='Courier'
    ))

    # Blockquote style
    styles.add(ParagraphStyle(
        name='CustomBlockquote',
        parent=styles['BodyText'],
        fontSize=11,
        textColor=colors.HexColor('#666666'),
        leftIndent=20,
        borderColor=colors.HexColor('#dddddd'),
        borderWidth=4,
        borderPadding=10,
        spaceAfter=12,
        fontName='Helvetica-Oblique'
    ))

    return styles


def escape_html(text):
    """Escape HTML/XML special characters for reportlab."""
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text


def markdown_to_reportlab(markdown_text):
    """Convert markdown text to reportlab elements."""
    styles = create_styles()
    story = []

    lines = markdown_text.split('\n')
    i = 0
    in_code_block = False
    code_block_lines = []
    in_list = False
    list_items = []
    list_type = None

    while i < len(lines):
        line = lines[i]

        # Handle code blocks
        if line.strip().startswith('```'):
            if in_code_block:
                # End of code block
                code_text = '\n'.join(code_block_lines)
                code_text = escape_html(code_text)
                story.append(Preformatted(code_text, styles['CustomCode']))
                code_block_lines = []
                in_code_block = False
            else:
                # Start of code block
                in_code_block = True
            i += 1
            continue

        if in_code_block:
            code_block_lines.append(line)
            i += 1
            continue

        # Handle headers
        header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if header_match:
            if in_list:
                story.append(create_list(list_items, list_type, styles))
                list_items = []
                in_list = False

            level = len(header_match.group(1))
            text = header_match.group(2)
            text = process_inline_formatting(text)
            style_name = f'CustomH{level}'
            story.append(Paragraph(text, styles[style_name]))
            i += 1
            continue

        # Handle horizontal rules
        if re.match(r'^(-{3,}|\*{3,}|_{3,})$', line.strip()):
            if in_list:
                story.append(create_list(list_items, list_type, styles))
                list_items = []
                in_list = False
            story.append(Spacer(1, 0.2*inch))
            story.append(Table([['']],  colWidths=[6*inch], style=[
                ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor('#eeeeee'))
            ]))
            story.append(Spacer(1, 0.2*inch))
            i += 1
            continue

        # Handle unordered lists
        list_match = re.match(r'^(\s*)[-*+]\s+(.+)$', line)
        if list_match:
            indent = len(list_match.group(1))
            text = list_match.group(2)
            text = process_inline_formatting(text)

            if not in_list or list_type != 'bullet':
                if in_list:
                    story.append(create_list(list_items, list_type, styles))
                    list_items = []
                list_type = 'bullet'
                in_list = True

            list_items.append(text)
            i += 1
            continue

        # Handle ordered lists
        ordered_list_match = re.match(r'^(\s*)(\d+)\.\s+(.+)$', line)
        if ordered_list_match:
            indent = len(ordered_list_match.group(1))
            text = ordered_list_match.group(3)
            text = process_inline_formatting(text)

            if not in_list or list_type != 'number':
                if in_list:
                    story.append(create_list(list_items, list_type, styles))
                    list_items = []
                list_type = 'number'
                in_list = True

            list_items.append(text)
            i += 1
            continue

        # Handle blockquotes
        blockquote_match = re.match(r'^>\s*(.*)$', line)
        if blockquote_match:
            if in_list:
                story.append(create_list(list_items, list_type, styles))
                list_items = []
                in_list = False

            text = blockquote_match.group(1)
            # Collect multi-line blockquotes
            blockquote_lines = [text]
            i += 1
            while i < len(lines) and re.match(r'^>\s*(.*)$', lines[i]):
                blockquote_lines.append(re.match(r'^>\s*(.*)$', lines[i]).group(1))
                i += 1

            blockquote_text = ' '.join(blockquote_lines)
            blockquote_text = process_inline_formatting(blockquote_text)
            story.append(Paragraph(blockquote_text, styles['CustomBlockquote']))
            continue

        # Handle tables (simple markdown tables)
        if '|' in line and line.strip().startswith('|'):
            if in_list:
                story.append(create_list(list_items, list_type, styles))
                list_items = []
                in_list = False

            table_lines = [line]
            i += 1
            while i < len(lines) and '|' in lines[i] and lines[i].strip().startswith('|'):
                table_lines.append(lines[i])
                i += 1

            table = parse_markdown_table(table_lines, styles)
            if table:
                story.append(table)
            continue

        # Handle empty lines
        if not line.strip():
            if in_list:
                story.append(create_list(list_items, list_type, styles))
                list_items = []
                in_list = False
            story.append(Spacer(1, 0.1*inch))
            i += 1
            continue

        # Handle regular paragraphs
        if line.strip():
            if in_list:
                story.append(create_list(list_items, list_type, styles))
                list_items = []
                in_list = False

            # Collect multi-line paragraphs
            para_lines = [line]
            i += 1
            while i < len(lines) and lines[i].strip() and not is_special_line(lines[i]):
                para_lines.append(lines[i])
                i += 1

            para_text = ' '.join(para_lines)
            para_text = process_inline_formatting(para_text)
            story.append(Paragraph(para_text, styles['CustomBody']))
            continue

        i += 1

    # Handle any remaining list
    if in_list:
        story.append(create_list(list_items, list_type, styles))

    return story


def is_special_line(line):
    """Check if a line is a special markdown element."""
    special_patterns = [
        r'^#{1,6}\s+',  # Headers
        r'^[-*+]\s+',   # Unordered list
        r'^\d+\.\s+',   # Ordered list
        r'^>\s*',       # Blockquote
        r'^```',        # Code block
        r'^\|',         # Table
        r'^(-{3,}|\*{3,}|_{3,})$',  # Horizontal rule
    ]
    return any(re.match(pattern, line.strip()) for pattern in special_patterns)


def create_list(items, list_type, styles):
    """Create a list flowable from list items."""
    list_items = []
    for item_text in items:
        list_items.append(ListItem(
            Paragraph(item_text, styles['CustomBody']),
            leftIndent=20
        ))

    bullet_type = 'bullet' if list_type == 'bullet' else '1'
    return ListFlowable(
        list_items,
        bulletType=bullet_type,
        start=1
    )


def process_inline_formatting(text):
    """Process inline markdown formatting (bold, italic, code, links)."""
    # Escape HTML first
    text = escape_html(text)

    # Extract inline code segments so that other formatting doesn't affect them
    code_spans: list[str] = []

    def _store_code(match: re.Match[str]) -> str:
        code_spans.append(match.group(1))
        return f"{{{{CODE_{len(code_spans) - 1}}}}}"

    text = re.sub(r'`([^`]+)`', _store_code, text)

    # Bold and italic: **text** or __text__
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)

    # Italic: *text*
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)

    # Italic: _text_ (but ignore underscores inside identifiers/URLs)
    def _italicize_underscore(match: re.Match[str]) -> str:
        start, end = match.span()
        prev_char = match.string[start - 1] if start > 0 else ''
        next_char = match.string[end] if end < len(match.string) else ''

        if prev_char and prev_char.isalnum():
            return match.group(0)
        if next_char and next_char.isalnum():
            return match.group(0)

        return f"<i>{match.group(1)}</i>"

    text = re.sub(r'_(.+?)_', _italicize_underscore, text)

    # Links: [text](url)
    text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<link href="\2" color="blue"><u>\1</u></link>', text)

    # Strikethrough: ~~text~~
    text = re.sub(r'~~(.+?)~~', r'<strike>\1</strike>', text)

    # Restore inline code segments
    for index, code in enumerate(code_spans):
        placeholder = f"{{{{CODE_{index}}}}}"
        text = text.replace(
            placeholder,
            f'<font name="Courier" backColor="#f6f8fa">{code}</font>',
        )

    return text


def parse_markdown_table(table_lines, styles):
    """Parse markdown table syntax into reportlab Table."""
    if len(table_lines) < 2:
        return None

    # Parse header
    header_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]

    # Skip separator line
    if len(table_lines) < 3:
        return None

    # Parse data rows - wrap all cells in Paragraph objects
    data = []

    # Process header row
    header_row = []
    for cell in header_cells:
        cell_text = escape_html(cell)
        header_row.append(Paragraph(cell_text, styles['CustomBody']))
    data.append(header_row)

    # Process data rows
    for line in table_lines[2:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if cells:
            row = []
            for cell in cells:
                cell_text = escape_html(cell)
                row.append(Paragraph(cell_text, styles['CustomBody']))
            data.append(row)

    if not data:
        return None

    # Create table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f6f8fa')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dddddd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))

    return table


@mcp.tool()
def save_markdown_to_pdf(
    markdown_content: str,
    filename: str,
    css_styles: Optional[str] = None
) -> str:
    """
    Convert Markdown content to a PDF file and save it to disk.

    Args:
        markdown_content: The Markdown text to convert to PDF
        filename: Name of the output PDF file (e.g., "document.pdf")
        css_styles: Optional CSS styles (Note: CSS is not fully supported with reportlab,
                   but basic styling is built-in)

    Returns:
        Success message with the full path to the saved PDF, or error message

    Example:
        save_markdown_to_pdf(
            markdown_content="# Hello World\\n\\nThis is a test.",
            filename="test.pdf"
        )
    """
    try:
        # Validate input type
        if not isinstance(markdown_content, str):
            return f"Error: markdown_content must be a string, got {type(markdown_content).__name__}"

        if not isinstance(filename, str):
            return f"Error: filename must be a string, got {type(filename).__name__}"

        # Determine output directory
        target_dir = DEFAULT_OUTPUT_DIR

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

        # Convert Markdown to reportlab elements
        try:
            story = markdown_to_reportlab(markdown_content)
        except AttributeError as e:
            if 'decode' in str(e):
                return f"Error: Type mismatch during markdown parsing. {str(e)}. Check that markdown_content is properly formatted text."
            raise

        # Create PDF
        doc = SimpleDocTemplate(
            str(full_path),
            pagesize=A4,
            rightMargin=2.5*cm,
            leftMargin=2.5*cm,
            topMargin=2.5*cm,
            bottomMargin=2.5*cm
        )

        try:
            doc.build(story)
        except AttributeError as e:
            if 'decode' in str(e):
                return f"Error: Type mismatch during PDF generation. {str(e)}. One of the story elements has an unexpected type."
            raise

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
