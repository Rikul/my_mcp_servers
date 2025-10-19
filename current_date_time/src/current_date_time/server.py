from datetime import date
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Current Date & Time")


@mcp.tool()
def get_today_date() -> str:
    """
    Get today's date.
    
    Returns:
        Today's date in YYYY-MM-DD format
    """
    today = date.today()
    return today.strftime("%Y-%m-%d")


def main():
    mcp.run()

if __name__ == "__main__":
    main()
