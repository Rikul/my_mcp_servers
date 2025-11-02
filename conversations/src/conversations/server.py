"""MCP server for storing and retrieving conversation transcripts."""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.context import Context
from mcp.server.fastmcp.resources.types import TextResource

mcp = FastMCP("Conversations")


@dataclass
class Conversation:
    """A stored conversation transcript."""

    identifier: str
    slug: str
    title: str
    created_at: str
    updated_at: str
    messages: list[dict[str, str]]
    metadata: dict[str, Any]

    @property
    def message_count(self) -> int:
        return len(self.messages)


def _now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _storage_base_dir() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path.home() / ".local" / "share"
    return base / "mcp_conversations"


def _storage_dir() -> Path:
    directory = _storage_base_dir()
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def _slugify(identifier: str) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9_.-]+", "-", identifier.strip()).strip("-._")
    if not candidate:
        candidate = f"conversation-{abs(hash(identifier)) & 0xFFFFFFFF:08x}"
    return candidate[:128]


def _conversation_path(conversation_id: str) -> Path:
    slug = _slugify(conversation_id)
    return _storage_dir() / f"{slug}.json"


def _normalize_messages(messages: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for index, message in enumerate(messages):
        if not isinstance(message, dict):
            raise ValueError(f"Message at index {index} must be a mapping of role/content pairs.")
        if "content" not in message:
            raise ValueError(f"Message at index {index} must include a 'content' field.")
        role = message.get("role", "user")
        content = message["content"]
        if not isinstance(role, str):
            raise ValueError(f"Message role at index {index} must be a string.")
        if not isinstance(content, str):
            raise ValueError(f"Message content at index {index} must be a string.")
        normalized.append({"role": role, "content": content})
    if not normalized:
        raise ValueError("At least one message is required to save a conversation.")
    return normalized


def _load_conversation_from_file(path: Path) -> Conversation:
    with path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    messages = [
        {"role": str(entry.get("role", "user")), "content": str(entry.get("content", ""))}
        for entry in raw.get("messages", [])
        if isinstance(entry, dict)
    ]
    metadata = raw.get("metadata") or {}
    if not isinstance(metadata, dict):
        metadata = {"value": metadata}
    return Conversation(
        identifier=raw.get("id", raw.get("identifier", raw.get("slug", path.stem))),
        slug=raw.get("slug", path.stem),
        title=raw.get("title") or raw.get("id") or path.stem,
        created_at=raw.get("created_at") or raw.get("updated_at") or _format_timestamp(_now()),
        updated_at=raw.get("updated_at") or raw.get("created_at") or _format_timestamp(_now()),
        messages=messages,
        metadata=metadata,
    )


def _serialize_conversation(conversation: Conversation) -> dict[str, Any]:
    return {
        "id": conversation.identifier,
        "slug": conversation.slug,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "messages": conversation.messages,
        "metadata": conversation.metadata,
    }


def _format_conversation_text(conversation: Conversation) -> str:
    lines: list[str] = [conversation.title, "=" * max(len(conversation.title), 8), ""]
    for message in conversation.messages:
        role = message.get("role", "user").strip() or "user"
        content = message.get("content", "").strip()
        lines.append(f"{role}:")
        lines.append(content or "(empty message)")
        lines.append("")
    lines.append(f"Metadata: {json.dumps(conversation.metadata, ensure_ascii=False)}")
    lines.append(f"Created: {conversation.created_at}")
    lines.append(f"Updated: {conversation.updated_at}")
    return "\n".join(lines).strip()


def _write_conversation(conversation: Conversation) -> None:
    payload = _serialize_conversation(conversation)
    with _conversation_path(conversation.identifier).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def _ensure_serializable(metadata: dict[str, Any]) -> dict[str, Any]:
    try:
        json.dumps(metadata)
    except TypeError as exc:  # pragma: no cover - guard clause
        raise ValueError("Metadata must be JSON serializable.") from exc
    return metadata


def _list_conversation_files() -> Iterable[Path]:
    directory = _storage_dir()
    yield from sorted(directory.glob("*.json"))


@mcp.tool()
def save_conversation(
    conversation_id: str,
    messages: list[dict[str, Any]],
    title: str | None = None,
    metadata: dict[str, Any] | None = None,
    ctx: Context | None = None,
) -> dict[str, Any]:
    """Persist a conversation transcript on disk."""

    normalized_messages = _normalize_messages(messages)
    metadata = _ensure_serializable(metadata or {})

    path = _conversation_path(conversation_id)
    now = _format_timestamp(_now())
    if path.exists():
        existing = _load_conversation_from_file(path)
        created_at = existing.created_at
        resolved_title = title or existing.title
    else:
        created_at = now
        resolved_title = title or conversation_id

    conversation = Conversation(
        identifier=conversation_id,
        slug=_slugify(conversation_id),
        title=resolved_title,
        created_at=created_at,
        updated_at=now,
        messages=normalized_messages,
        metadata=metadata,
    )

    _write_conversation(conversation)

    if ctx is not None:
        ctx.info(f"Saved conversation '{conversation_id}' with {conversation.message_count} messages.")

    return {
        "conversation_id": conversation.identifier,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": conversation.message_count,
        "storage_path": str(path),
    }


@mcp.tool()
def load_conversation(conversation_id: str, include_resource: bool = True, ctx: Context | None = None) -> dict[str, Any]:
    """Load a saved conversation and optionally expose it as an MCP text resource."""

    path = _conversation_path(conversation_id)
    if not path.exists():
        raise ValueError(f"Conversation '{conversation_id}' was not found.")

    conversation = _load_conversation_from_file(path)

    resource_uri: str | None = None
    if include_resource:
        resource_uri = f"conversation://{conversation.slug}"
        transcript = _format_conversation_text(conversation)
        resource = TextResource(
            uri=resource_uri,
            name=f"conversation-{conversation.slug}",
            title=conversation.title,
            description="Transcript of a stored conversation.",
            text=transcript,
        )
        mcp.add_resource(resource)
        if ctx is not None:
            ctx.debug(f"Registered text resource for conversation '{conversation.identifier}'.")

    return {
        "conversation_id": conversation.identifier,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "message_count": conversation.message_count,
        "metadata": conversation.metadata,
        "messages": conversation.messages,
        "resource_uri": resource_uri,
    }


def _collect_conversations() -> list[Conversation]:
    conversations: list[Conversation] = []
    for path in _list_conversation_files():
        try:
            conversations.append(_load_conversation_from_file(path))
        except (OSError, json.JSONDecodeError):  # pragma: no cover - guard clause
            continue
    conversations.sort(key=lambda item: item.updated_at, reverse=True)
    return conversations


@mcp.tool()
def list_conversations(limit: int | None = None) -> list[dict[str, Any]]:
    """Return metadata for stored conversations ordered by most recent update."""

    conversations = _collect_conversations()
    if limit is not None and limit > 0:
        conversations = conversations[:limit]
    return [
        {
            "conversation_id": convo.identifier,
            "title": convo.title,
            "created_at": convo.created_at,
            "updated_at": convo.updated_at,
            "message_count": convo.message_count,
        }
        for convo in conversations
    ]


def _build_snippet(conversation: Conversation, query: str) -> str:
    lower_query = query.lower()
    for message in conversation.messages:
        content = message.get("content", "")
        if lower_query in content.lower():
            index = content.lower().index(lower_query)
            start = max(0, index - 80)
            end = min(len(content), index + 80)
            snippet = content[start:end]
            prefix = "…" if start > 0 else ""
            suffix = "…" if end < len(content) else ""
            return f"{prefix}{snippet}{suffix}".strip()
    metadata_blob = json.dumps(conversation.metadata, ensure_ascii=False)
    if lower_query in metadata_blob.lower():
        return "Match found in metadata."
    if lower_query in conversation.title.lower():
        return "Match found in title."
    return ""


@mcp.tool()
def search_conversations(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """Search stored conversations for a query string."""

    normalized_query = query.strip()
    if not normalized_query:
        return []

    matches: list[tuple[Conversation, str]] = []
    for conversation in _collect_conversations():
        haystacks = [conversation.title, json.dumps(conversation.metadata, ensure_ascii=False)]
        haystacks.extend(message.get("content", "") for message in conversation.messages)
        combined = "\n".join(haystacks).lower()
        if normalized_query.lower() in combined:
            snippet = _build_snippet(conversation, normalized_query)
            matches.append((conversation, snippet))

    matches.sort(key=lambda item: item[0].updated_at, reverse=True)

    if limit is not None and limit > 0:
        matches = matches[:limit]

    return [
        {
            "conversation_id": conversation.identifier,
            "title": conversation.title,
            "updated_at": conversation.updated_at,
            "message_count": conversation.message_count,
            "snippet": snippet,
        }
        for conversation, snippet in matches
    ]


def main() -> None:
    """Run the Conversations MCP server."""

    mcp.run()


if __name__ == "__main__":
    main()
