import re
from html import unescape
from typing import Callable, Iterable, Optional

import feedparser
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("News")

GOOGLE_US_NEWS = "https://news.google.com/rss"
GUARDIAN_US_NEWS = "https://www.theguardian.com/us/rss"
HACKER_NEWS = "https://news.ycombinator.com/rss"
VERGE_NEWS = "https://www.theverge.com/rss/index.xml"

DEFAULT_LIMIT = 10
MAX_LIMIT = 25

FeedEntry = feedparser.FeedParserDict


def _sanitize_limit(limit: Optional[int]) -> int:
    if limit is None:
        return DEFAULT_LIMIT
    try:
        value = int(limit)
    except (TypeError, ValueError):
        return DEFAULT_LIMIT
    return max(1, min(value, MAX_LIMIT))


def _strip_html(text: Optional[str]) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", cleaned).strip()


def _truncate(text: str, limit: int = 500) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


async def _fetch_feed(
    feed_url: str,
    source_name: str,
    limit: Optional[int],
    formatter: Callable[[FeedEntry, int], Iterable[str]],
) -> str:
    limited = _sanitize_limit(limit)

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(feed_url)
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            return f"Error fetching {source_name}: HTTP {error.response.status_code}"
        except httpx.RequestError as error:
            return f"Network error fetching {source_name}: {error}"

    parsed = feedparser.parse(response.text)

    if getattr(parsed, "bozo", False):
        detail = getattr(parsed, "bozo_exception", None)
        if detail:
            return f"Error parsing feed for {source_name}: {detail}"
        return f"Error parsing feed for {source_name}."

    entries = parsed.entries[:limited]

    if not entries:
        return f"No articles found for {source_name}."

    lines = [f"{source_name} - Top {len(entries)} Articles", "=" * 80, ""]

    for index, entry in enumerate(entries, 1):
        formatted_lines = list(formatter(entry, index))
        if not formatted_lines:
            continue
        lines.extend(formatted_lines)
        lines.append("")

    return "\n".join(lines).strip()


def _parse_google_related(description: Optional[str]) -> list[tuple[str, str, str]]:
    if not description:
        return []
    related: list[tuple[str, str, str]] = []
    pattern = re.compile(
        r"<li>\s*<a href=\"(?P<link>[^\"]+)\"[^>]*>(?P<title>.*?)</a>"
        r"(?:&nbsp;&nbsp;\s*<font[^>]*>(?P<source>.*?)</font>)?",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(description):
        link = unescape(match.group("link"))
        title = _strip_html(match.group("title"))
        source = _strip_html(match.group("source"))
        related.append((title, source, link))
    return related


def _format_google_entry(entry: FeedEntry, index: int) -> Iterable[str]:
    title = entry.get("title", "Untitled")
    published = entry.get("pubDate") or entry.get("published") or entry.get("updated")
    link = entry.get("link") or ""
    source_info = entry.get("source")
    source_title = ""
    if isinstance(source_info, feedparser.FeedParserDict):
        source_title = source_info.get("title", "")
    lines = [f"{index}. {title}"]
    if source_title:
        lines.append(f"   Source: {source_title}")
    if published:
        lines.append(f"   Published: {published}")
    if link:
        lines.append(f"   Primary Link: {link}")
    related = _parse_google_related(entry.get("description"))
    if related:
        lines.append("   Related Coverage:")
        for related_title, related_source, related_link in related:
            bullet = f"      - {related_title}" if related_title else "      - Related story"
            if related_source:
                bullet += f" ({related_source})"
            lines.append(bullet)
            if related_link:
                lines.append(f"        {related_link}")
    summary = _strip_html(entry.get("summary"))
    if summary and summary not in {title}:
        lines.append(f"   Summary: {_truncate(summary)}")
    return lines


def _format_guardian_entry(entry: FeedEntry, index: int) -> Iterable[str]:
    title = entry.get("title", "Untitled")
    link = entry.get("link") or ""
    published = entry.get("published") or entry.get("updated")
    author = entry.get("dc_creator") or entry.get("author")
    summary = _strip_html(entry.get("summary") or entry.get("description"))
    categories: list[str] = []
    raw_categories = []
    for field in ("tags", "categories"):
        values = entry.get(field)
        if values:
            raw_categories.extend(values)
    for category in raw_categories:
        if isinstance(category, feedparser.FeedParserDict):
            value = category.get("term") or category.get("label") or ""
        else:
            value = str(category)
        cleaned = value.strip()
        if cleaned and cleaned not in categories:
            categories.append(cleaned)

    lines = [f"{index}. {title}"]
    if author:
        lines.append(f"   By: {author}")
    if published:
        lines.append(f"   Published: {published}")
    if categories:
        lines.append(f"   Categories: {', '.join(categories)}")
    if summary:
        lines.append(f"   Summary: {_truncate(summary)}")
    if link:
        lines.append(f"   Link: {link}")
    media = entry.get("media_content") or []
    for media_item in media:
        if isinstance(media_item, feedparser.FeedParserDict):
            media_url = media_item.get("url")
            if media_url:
                lines.append(f"   Media: {media_url}")
    return lines


def _format_hacker_news_entry(entry: FeedEntry, index: int) -> Iterable[str]:
    title = entry.get("title", "Untitled")
    link = entry.get("link") or ""
    comments = entry.get("comments") or ""
    published = entry.get("published") or entry.get("updated")

    lines = [f"{index}. {title}"]
    if published:
        lines.append(f"   Published: {published}")
    if link:
        lines.append(f"   Article: {link}")
    if comments:
        lines.append(f"   Discussion: {comments}")
    summary = _strip_html(entry.get("summary"))
    if summary and summary.lower() != "comments":
        lines.append(f"   Summary: {_truncate(summary)}")
    return lines


def _format_verge_entry(entry: FeedEntry, index: int) -> Iterable[str]:
    title = entry.get("title", "Untitled")
    link = entry.get("link") or ""
    published = entry.get("published") or entry.get("updated")
    author_info = entry.get("author")
    author = ""
    if isinstance(author_info, feedparser.FeedParserDict):
        author = author_info.get("name", "")
    elif isinstance(author_info, str):
        author = author_info
    summary = _strip_html(entry.get("summary"))
    tags: list[str] = []
    for tag in entry.get("tags", []):
        if isinstance(tag, feedparser.FeedParserDict):
            term = tag.get("term") or tag.get("label")
        else:
            term = str(tag)
        term = (term or "").strip()
        if term and term not in tags:
            tags.append(term)

    lines = [f"{index}. {title}"]
    if author:
        lines.append(f"   By: {author}")
    if published:
        lines.append(f"   Published: {published}")
    if tags:
        lines.append(f"   Tags: {', '.join(tags)}")
    if summary:
        lines.append(f"   Summary: {_truncate(summary)}")
    if link:
        lines.append(f"   Link: {link}")

    content_list = entry.get("content") or []
    for content in content_list:
        if isinstance(content, feedparser.FeedParserDict):
            content_value = _strip_html(content.get("value"))
            if content_value and content_value != summary:
                lines.append(f"   Content: {_truncate(content_value)}")
                break
    return lines


@mcp.tool()
async def google_us_news(limit: Optional[int] = None) -> str:
    """Fetch top headlines from the Google News U.S. feed."""

    return await _fetch_feed(GOOGLE_US_NEWS, "Google News (US)", limit, _format_google_entry)


@mcp.tool()
async def guardian_us_news(limit: Optional[int] = None) -> str:
    """Fetch U.S. news highlights from The Guardian."""

    return await _fetch_feed(
        GUARDIAN_US_NEWS,
        "The Guardian (US)",
        limit,
        _format_guardian_entry,
    )


@mcp.tool()
async def tech_hacker_news(limit: Optional[int] = None) -> str:
    """Fetch technology headlines from Hacker News."""

    return await _fetch_feed(HACKER_NEWS, "Hacker News", limit, _format_hacker_news_entry)


@mcp.tool()
async def tech_verge_news(limit: Optional[int] = None) -> str:
    """Fetch technology stories from The Verge."""

    return await _fetch_feed(VERGE_NEWS, "The Verge", limit, _format_verge_entry)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
