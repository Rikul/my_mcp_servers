import sys
from pathlib import Path

import pytest
from reportlab.platypus import ListFlowable, Paragraph, Preformatted, Table

# Ensure the package source is importable without installation
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from markdown_to_pdf.server import markdown_to_reportlab


def _collect_story_items(story, cls):
    """Helper to filter story elements by type."""
    return [element for element in story if isinstance(element, cls)]


def test_markdown_to_reportlab_renders_headings():
    story = markdown_to_reportlab("# Title\n## Subtitle\n### Section")

    heading_paragraphs = [
        element
        for element in _collect_story_items(story, Paragraph)
        if element.style.name.startswith("CustomH")
    ]

    assert [para.style.name for para in heading_paragraphs] == [
        "CustomH1",
        "CustomH2",
        "CustomH3",
    ]
    assert [para.text for para in heading_paragraphs] == [
        "Title",
        "Subtitle",
        "Section",
    ]


def test_markdown_to_reportlab_renders_blockquote():
    story = markdown_to_reportlab("> quoted line\n> continues")

    blockquotes = [
        element
        for element in _collect_story_items(story, Paragraph)
        if element.style.name == "CustomBlockquote"
    ]

    assert len(blockquotes) == 1
    assert blockquotes[0].text == "quoted line continues"


def test_markdown_to_reportlab_combines_paragraphs():
    story = markdown_to_reportlab(
        "First paragraph line one.\ncontinues second line.\n\nSecond paragraph."
    )

    paragraphs = [
        element
        for element in _collect_story_items(story, Paragraph)
        if element.style.name == "CustomBody"
    ]

    assert [para.text for para in paragraphs] == [
        "First paragraph line one. continues second line.",
        "Second paragraph.",
    ]


def test_markdown_to_reportlab_builds_table():
    story = markdown_to_reportlab(
        "| Name | Value |\n| ---- | ----- |\n| Alice | 42 |\n| Bob | 7 |"
    )

    tables = _collect_story_items(story, Table)
    assert len(tables) == 1

    table = tables[0]
    header_text = [cell.getPlainText() for cell in table._cellvalues[0]]
    row_text = [
        [cell.getPlainText() for cell in row]
        for row in table._cellvalues[1:]
    ]

    assert header_text == ["Name", "Value"]
    assert row_text == [["Alice", "42"], ["Bob", "7"]]


def test_markdown_to_reportlab_handles_lists():
    story = markdown_to_reportlab(
        "- item one\n- item two\n\n1. first item\n2. second item"
    )

    lists = _collect_story_items(story, ListFlowable)
    assert len(lists) == 2

    bullet_list, ordered_list = lists

    bullet_items = [
        list_item._flowables[0].text for list_item in bullet_list._flowables
    ]
    ordered_items = [
        list_item._flowables[0].text for list_item in ordered_list._flowables
    ]

    assert bullet_list._bulletType == "bullet"
    assert ordered_list._bulletType == "1"
    assert bullet_items == ["item one", "item two"]
    assert ordered_items == ["first item", "second item"]


def test_markdown_to_reportlab_renders_links():
    story = markdown_to_reportlab(
        "Visit [Example](https://example.com/path_with_underscores)."
    )

    paragraphs = [
        element
        for element in _collect_story_items(story, Paragraph)
        if element.style.name == "CustomBody"
    ]
    assert len(paragraphs) == 1

    paragraph = paragraphs[0]
    assert (
        '<link href="https://example.com/path_with_underscores" color="blue"><u>Example</u></link>'
        in paragraph.text
    )


def test_markdown_to_reportlab_renders_code_block():
    story = markdown_to_reportlab("```\nprint('hi')\nreturn 1\n```")

    code_blocks = _collect_story_items(story, Preformatted)
    assert len(code_blocks) == 1

    code_block = code_blocks[0]
    assert code_block.lines == ["print('hi')", "return 1"]
