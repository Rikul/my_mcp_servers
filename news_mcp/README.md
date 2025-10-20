# News MCP Module

This module provides tools for fetching curated news headlines from popular RSS feeds.

## Available Tools
- **google_us_news**: Latest headlines from Google News (U.S. edition).
- **guardian_us_news**: U.S. news highlights from The Guardian.
- **tech_hacker_news**: Trending stories from Hacker News.
- **tech_verge_news**: Technology coverage from The Verge.

Each tool accepts an optional `limit` parameter (default 10, maximum 25) to control the number of articles returned.

### Feed-specific formatting
- **Google News** results highlight the primary source and list the additional outlets linked in the Google aggregation block.
- **The Guardian** entries surface the author, publication time, categories, article link, and any embedded media URLs.
- **Hacker News** stories provide both the outbound article link and the accompanying discussion thread.
- **The Verge** feed includes tags and condensed article content sourced from the Atom entry payload.

## Running the server
Install the dependencies and launch the MCP server:

```bash
pip install -e .
news-mcp
```
