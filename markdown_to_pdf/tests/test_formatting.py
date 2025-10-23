import sys
from pathlib import Path

import pytest

# Ensure the package source is importable without installation
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from markdown_to_pdf.server import process_inline_formatting


@pytest.mark.parametrize(
    "input_text",
    [
        "snake_case_identifier",
        "multiple_snake_case_identifiers_are_common",
        "already_trailing_",
        "_leading_already",
    ],
)
def test_process_inline_formatting_preserves_snake_case(input_text):
    """Identifiers with underscores should not gain italic formatting."""
    assert process_inline_formatting(input_text) == input_text


def test_process_inline_formatting_preserves_url_underscores():
    url = "https://example.com/path_with_underscores/in_the_middle"
    assert process_inline_formatting(url) == url


@pytest.mark.parametrize(
    "markdown, expected",
    [
        (
            "Use *stars* or _underscores_ for emphasis.",
            "Use <i>stars</i> or <i>underscores</i> for emphasis.",
        ),
        (
            "Mix **bold** and __strong__ text.",
            "Mix <b>bold</b> and <b>strong</b> text.",
        ),
        (
            "Apply ~~strike~~ and `code_snippet` formatting.",
            "Apply <strike>strike</strike> and <font name=\"Courier\" backColor=\"#f6f8fa\">code_snippet</font> formatting.",
        ),
        (
            "Link to [Example](https://example.com/path_with_underscores).",
            "Link to <link href=\"https://example.com/path_with_underscores\" color=\"blue\"><u>Example</u></link>.",
        ),
    ],
)
def test_process_inline_formatting_renders_common_markdown(markdown, expected):
    """Markdown syntax is converted to reportlab-compatible tags."""
    assert process_inline_formatting(markdown) == expected


def test_process_inline_formatting_handles_italicized_phrase_with_spaces():
    text = "Surround _this phrase_ but keep context."
    expected = "Surround <i>this phrase</i> but keep context."
    assert process_inline_formatting(text) == expected
