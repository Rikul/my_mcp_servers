import json
import sys
import types
from datetime import datetime, timezone
from pathlib import Path

import pytest

# Provide lightweight stubs for the MCP interfaces used by the conversations server.


class _FakeTextResource:
    def __init__(self, uri: str, name: str, title: str, description: str, text: str):
        self.uri = uri
        self.name = name
        self.title = title
        self.description = description
        self.text = text


class _FakeFastMCP:
    def __init__(self, name: str):
        self.name = name
        self.resources: list[_FakeTextResource] = []

    def tool(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def add_resource(self, resource: _FakeTextResource) -> None:
        self.resources.append(resource)

    def run(self) -> None:  # pragma: no cover - not exercised in tests
        raise NotImplementedError


mcp_module = types.ModuleType("mcp")
server_module = types.ModuleType("mcp.server")
fastmcp_module = types.ModuleType("mcp.server.fastmcp")
fastmcp_module.FastMCP = _FakeFastMCP
context_module = types.ModuleType("mcp.server.fastmcp.context")
context_module.Context = object
resources_module = types.ModuleType("mcp.server.fastmcp.resources")
resources_types_module = types.ModuleType("mcp.server.fastmcp.resources.types")
resources_types_module.TextResource = _FakeTextResource

sys.modules.setdefault("mcp", mcp_module)
sys.modules.setdefault("mcp.server", server_module)
sys.modules.setdefault("mcp.server.fastmcp", fastmcp_module)
sys.modules.setdefault("mcp.server.fastmcp.context", context_module)
sys.modules.setdefault("mcp.server.fastmcp.resources", resources_module)
sys.modules.setdefault("mcp.server.fastmcp.resources.types", resources_types_module)

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PACKAGE_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from conversations import server

# Ensure the stub modules expose the attributes expected by the server after import.
setattr(mcp_module, "server", server_module)
setattr(server_module, "fastmcp", fastmcp_module)
setattr(fastmcp_module, "context", context_module)
setattr(fastmcp_module, "resources", resources_module)
setattr(resources_module, "types", resources_types_module)


@pytest.fixture(autouse=True)
def patch_storage_base_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(server, "_storage_base_dir", lambda: tmp_path)
    return tmp_path


@pytest.fixture
def fake_resources(monkeypatch):
    resources = []

    def record_resource(resource):
        resources.append(resource)

    monkeypatch.setattr(server.mcp, "add_resource", record_resource)
    return resources


def test_normalize_messages_validates_structure():
    with pytest.raises(ValueError):
        server._normalize_messages([])
    with pytest.raises(ValueError):
        server._normalize_messages(["not-a-dict"])
    with pytest.raises(ValueError):
        server._normalize_messages([{ "role": "user" }])
    with pytest.raises(ValueError):
        server._normalize_messages([{ "content": 42 }])

    normalized = server._normalize_messages([
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ])
    assert normalized == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]


def test_save_and_load_roundtrip(monkeypatch, fake_resources):
    timestamps = iter(
        [
            datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 13, tzinfo=timezone.utc),
        ]
    )
    monkeypatch.setattr(server, "_now", lambda: next(timestamps))

    messages = [
        {"role": "user", "content": "How are you?"},
        {"role": "assistant", "content": "Doing well!"},
    ]
    metadata = {"topic": "status"}

    save_result = server.save_conversation("chat-123", messages, title="Greeting", metadata=metadata)

    path = server._conversation_path("chat-123")
    assert path.exists()
    stored = json.loads(path.read_text())
    assert stored["messages"] == messages
    assert stored["metadata"] == metadata

    load_result = server.load_conversation("chat-123")

    assert save_result["conversation_id"] == "chat-123"
    assert load_result["messages"] == messages
    assert load_result["metadata"] == metadata
    assert fake_resources  # resource registered
    assert fake_resources[0].uri == "conversation://chat-123"


def test_list_conversations_orders_by_recent(monkeypatch):
    timestamps = iter(
        [
            datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 12, 5, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 12, 10, tzinfo=timezone.utc),
        ]
    )
    monkeypatch.setattr(server, "_now", lambda: next(timestamps))

    server.save_conversation("chat-a", [{"content": "First"}])
    server.save_conversation("chat-b", [{"content": "Second"}])
    # Update chat-a to bump timestamp
    server.save_conversation("chat-a", [{"content": "First updated"}])

    listings = server.list_conversations()
    assert [item["conversation_id"] for item in listings] == ["chat-a", "chat-b"]
    assert listings[0]["message_count"] == 1


def test_search_conversations_returns_snippet(monkeypatch):
    timestamps = iter(
        [
            datetime(2024, 1, 1, 12, tzinfo=timezone.utc),
            datetime(2024, 1, 1, 12, 1, tzinfo=timezone.utc),
        ]
    )
    monkeypatch.setattr(server, "_now", lambda: next(timestamps))

    server.save_conversation(
        "chat-snippet",
        [
            {"role": "user", "content": "Discussing project Alpha requirements."},
            {"role": "assistant", "content": "Project Alpha is on schedule."},
        ],
        metadata={"tags": ["alpha", "project"]},
    )

    results = server.search_conversations("alpha")
    assert results
    assert results[0]["conversation_id"] == "chat-snippet"
    assert "alpha" in results[0]["snippet"].lower()

    empty = server.search_conversations("   ")
    assert empty == []
