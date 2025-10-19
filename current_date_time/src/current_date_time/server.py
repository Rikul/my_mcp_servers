from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Optional
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Current Date & Time")


def _get_datetime_with_timezone(timezone: Optional[str] = None) -> tuple[datetime, str]:
    """
    Helper function to get datetime with timezone.
    
    Args:
        timezone: Optional timezone name
        
    Returns:
        Tuple of (datetime object, timezone name)
        
    Raises:
        ZoneInfoNotFoundError: If the timezone parameter is provided but invalid
    """
    if timezone:
        tz = ZoneInfo(timezone)
        dt = datetime.now(tz)
        tz_name = timezone
    else:
        dt = datetime.now()
        tz_name = "Local"
    
    return dt, tz_name


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
    try:
        today, _ = _get_datetime_with_timezone(timezone)
        return today.strftime("%Y-%m-%d")
    except ZoneInfoNotFoundError:
        return f"Error: Invalid timezone '{timezone}'. Please use a valid IANA timezone identifier."


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
    try:
        now, tz_name = _get_datetime_with_timezone(timezone)
        return f"{now.strftime('%H:%M:%S')} ({tz_name})"
    except ZoneInfoNotFoundError:
        return f"Error: Invalid timezone '{timezone}'. Please use a valid IANA timezone identifier."


def main():
    mcp.run()

if __name__ == "__main__":
    main()
