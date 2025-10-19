from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Current Date & Time")


@mcp.tool()
def get_today_date(timezone: Optional[str] = None) -> str:
    """
    Get today's date.
    
    Args:
        timezone: Optional timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").
                  If not provided, uses the system's local timezone.
    
    Returns:
        Today's date in YYYY-MM-DD format
    """
    if timezone:
        try:
            tz = ZoneInfo(timezone)
            today = datetime.now(tz)
        except Exception as e:
            return f"Error: Invalid timezone '{timezone}'. {str(e)}"
    else:
        today = datetime.now()
    
    return today.strftime("%Y-%m-%d")


@mcp.tool()
def get_current_time(timezone: Optional[str] = None) -> str:
    """
    Get the current time.
    
    Args:
        timezone: Optional timezone name (e.g., "America/New_York", "Europe/London", "Asia/Tokyo").
                  If not provided, uses the system's local timezone.
    
    Returns:
        Current time in HH:MM:SS format along with the timezone
    """
    if timezone:
        try:
            tz = ZoneInfo(timezone)
            now = datetime.now(tz)
            tz_name = timezone
        except Exception as e:
            return f"Error: Invalid timezone '{timezone}'. {str(e)}"
    else:
        now = datetime.now()
        tz_name = "Local"
    
    return f"{now.strftime('%H:%M:%S')} ({tz_name})"


def main():
    mcp.run()

if __name__ == "__main__":
    main()
