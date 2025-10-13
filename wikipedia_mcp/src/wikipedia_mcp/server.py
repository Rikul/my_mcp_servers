import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Wikipedia")

WIKIPEDIA_API_BASE = "https://en.wikipedia.org/api/rest_v1"
MEDIAWIKI_API_BASE = "https://en.wikipedia.org/w/api.php"


@mcp.tool()
async def get_page_summary(title: str) -> str:
    """
    Get a summary of a Wikipedia page.
    
    Args:
        title: The title of the Wikipedia page (e.g., "Python (programming language)")
    
    Returns:
        A summary of the page including title, description, and extract
    """
    headers = {
        "User-Agent": "WikipediaMCP/1.0 (Educational/Research Purpose)"
    }
    async with httpx.AsyncClient(headers=headers) as client:
        try:
            # Use REST API for page summary
            url = f"{WIKIPEDIA_API_BASE}/page/summary/{title}"
            response = await client.get(url)
            response.raise_for_status()
            
            data = response.json()
            
            result = f"Title: {data.get('title', 'N/A')}\n"
            result += f"Description: {data.get('description', 'N/A')}\n\n"
            result += f"Summary:\n{data.get('extract', 'No summary available')}\n\n"
            
            if 'content_urls' in data:
                result += f"Read more: {data['content_urls']['desktop']['page']}"
            
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return f"Page not found: {title}"
            return f"Error fetching page: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


@mcp.tool()
async def get_page_content(title: str) -> str:
    """
    Get the full content of a Wikipedia page in plain text.
    
    Args:
        title: The title of the Wikipedia page (e.g., "Artificial intelligence")
    
    Returns:
        The full text content of the page
    """
    async with httpx.AsyncClient() as client:
        try:
            # Use MediaWiki API for full content
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "extracts",
                "explaintext": True,
                "exsectionformat": "plain"
            }
            
            response = await client.get(MEDIAWIKI_API_BASE, params=params)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get('query', {}).get('pages', {})
            
            # Get the first (and should be only) page
            page = next(iter(pages.values()))
            
            if 'missing' in page:
                return f"Page not found: {title}"
            
            content = page.get('extract', 'No content available')
            page_title = page.get('title', title)
            
            return f"Title: {page_title}\n\n{content}"
            
        except Exception as e:
            return f"Error fetching page content: {str(e)}"


@mcp.tool()
async def search_articles(query: str, limit: int = 10) -> str:
    """
    Search for Wikipedia articles.
    
    Args:
        query: The search query
        limit: Maximum number of results to return (default: 10, max: 50)
    
    Returns:
        A list of matching articles with titles and snippets
    """
    async with httpx.AsyncClient() as client:
        try:
            # Limit the results to a reasonable maximum
            limit = min(limit, 50)
            
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": limit,
                "srprop": "snippet|titlesnippet"
            }
            
            response = await client.get(MEDIAWIKI_API_BASE, params=params)
            response.raise_for_status()
            
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            if not search_results:
                return f"No results found for: {query}"
            
            result = f"Search results for '{query}' ({len(search_results)} results):\n\n"
            
            for i, item in enumerate(search_results, 1):
                title = item.get('title', 'N/A')
                # Remove HTML tags from snippet
                snippet = item.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', '')
                result += f"{i}. {title}\n   {snippet}\n\n"
            
            return result.strip()
            
        except Exception as e:
            return f"Error searching articles: {str(e)}"


def main():
    mcp.run()

if __name__ == "__main__":
    main()