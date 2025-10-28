# yfinance MCP Server

A Model Context Protocol (MCP) server that provides access to financial market data through the yfinance library. This server enables AI assistants to fetch real-time and historical stock market data including OHLCV (Open, High, Low, Close, Volume) pricing information.

## Features

- Fetch OHLCV pricing data for any ticker symbol
- Retrieve descriptive company and fundamentals data for a ticker
- Query data for specific dates (YYYY-MM-DD format)
- Retrieve the most recent N trading days
- Automatic handling of weekends and market holidays
- Returns structured JSON data with complete market information

## Installation

### Install with pip

```bash
pip install -e .
```

### Install with uv

```bash
uv pip install -e .
```

## Usage

### Running with uvx

You can run the server directly with `uvx` without installation:

```bash
uvx yfin-mcp
```

### Running with python -m

After installation, you can run the server as a Python module:

```bash
python -m yfin_mcp.server
```

Or use the installed script:

```bash
yfin-mcp
```

## Configuration

### Adding to Claude Desktop

To use this server with Claude Desktop, add the following configuration to your MCP settings file:

**macOS/Linux**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

#### Using uvx (recommended)

```json
{
  "mcpServers": {
    "yfinance": {
      "command": "uvx",
      "args": ["yfin-mcp"]
    }
  }
}
```

#### Using python -m

```json
{
  "mcpServers": {
    "yfinance": {
      "command": "python",
      "args": ["-m", "yfin_mcp.server"]
    }
  }
}
```

#### Using absolute path to Python environment

If you have the package installed in a specific virtual environment:

```json
{
  "mcpServers": {
    "yfinance": {
      "command": "/path/to/venv/bin/python",
      "args": ["-m", "yfin_mcp.server"]
    }
  }
}
```

**Windows example:**

```json
{
  "mcpServers": {
    "yfinance": {
      "command": "C:\\path\\to\\venv\\Scripts\\python.exe",
      "args": ["-m", "yfin_mcp.server"]
    }
  }
}
```

### Adding to Other MCP Clients

For other MCP-compatible clients, use the appropriate command and arguments format based on your installation method. The server uses stdio transport by default.

## Available Tools

### get_ticker_data

Fetch OHLCV pricing data for a ticker symbol.

**Parameters:**

- `ticker` (string, required): Ticker symbol to query (e.g., "AAPL", "MSFT", "GOOGL")
- `date` (string, optional): Specific date in YYYY-MM-DD format
- `last_n_days` (integer, optional): Number of most recent trading days to fetch

**Note:** You must provide either `date` or `last_n_days`, but not both.

**Returns:**

- `ticker`: The ticker symbol (uppercase)
- `candles`: Array of OHLCV data objects, each containing:
  - `date`: Trading date (YYYY-MM-DD)
  - `open`: Opening price
  - `high`: Highest price
  - `low`: Lowest price
  - `close`: Closing price
  - `volume`: Trading volume
- `requested_date` or `requested_days`: The query parameters used
- `as_json`: Complete response as a JSON string

### get_ticker_info

Fetch descriptive information and fundamental metrics for a ticker symbol.

**Parameters:**

- `ticker` (string, required): Ticker symbol to query (e.g., "AAPL", "MSFT", "GOOGL")

**Returns:**

- `ticker`: The ticker symbol (uppercase)
- `symbol`, `short_name`, `long_name`, `quote_type`, `currency`, `exchange`, `market_state`, `sector`, `industry`, `country`, `full_time_employees`: Identification and classification data when available
- `market_cap`, `enterprise_value`, `trailing_pe`, `forward_pe`, `dividend_yield`, `fifty_two_week_high`, `fifty_two_week_low`, `fifty_day_average`, `two_hundred_day_average`, `beta`, `revenue_growth`, `eps_trailing_twelve_months`, `eps_forward`, `trailing_annual_dividend_rate`, `trailing_annual_dividend_yield`, `net_income_to_common`, `profit_margins`: Selected fundamental metrics when available
- `website`, `logo_url`: Branding details when available
- `long_business_summary`: Company summary text when available
- `company_officers`: Normalized list of officer details when provided by Yahoo Finance
- `as_json`: Complete response as a JSON string

## Examples

### Fetch data for a specific date

```
Get Apple stock data for January 15, 2025
```

The assistant will call:
```json
{
  "ticker": "AAPL",
  "date": "2025-01-15"
}
```

### Fetch the last 5 trading days

```
Get Tesla stock data for the last 5 days
```

The assistant will call:
```json
{
  "ticker": "TSLA",
  "last_n_days": 5
}
```

### Fetch multiple tickers

```
Compare the last trading day for AAPL, MSFT, and GOOGL
```

The assistant will make multiple calls to get data for each ticker.

## Development

### Running Tests

```bash
pytest
```

### Project Structure

```
yfin/
├── src/
│   └── yfin_mcp/
│       ├── __init__.py
│       └── server.py       # Main server implementation
├── pyproject.toml          # Project configuration
└── README.md               # This file
```

## Dependencies

- `mcp`: Model Context Protocol SDK
- `yfinance>=0.2`: Yahoo Finance market data library
- `pandas`: Data manipulation and analysis

## License

See LICENSE file for details.

## Troubleshooting

### No data returned

- Verify the ticker symbol is correct and actively traded
- Check that the date falls on a trading day (not weekend/holiday)
- Ensure you're using the correct date format (YYYY-MM-DD)

### Installation issues

- Make sure you have Python 3.8 or higher
- Try installing in a clean virtual environment
- Check that all dependencies are properly installed

### Connection issues with Claude Desktop

- Verify the path to your Python executable is correct
- Check that the server starts without errors when run manually
- Restart Claude Desktop after modifying the configuration file
- Check Claude Desktop logs for error messages

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
