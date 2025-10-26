"""Model Context Protocol server for fetching market data via yfinance."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

import yfinance as yf
from modelcontextprotocol.server import Server

SERVER_NAME = "yfinance"


def _parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string into a timezone-aware datetime."""

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError("date must be in YYYY-MM-DD format") from exc


@dataclass
class Candle:
    """Represents OHLCV data for a single trading day."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


def _serialize_candles(rows: Any) -> List[Candle]:
    """Convert a pandas dataframe returned by yfinance into Candle objects."""

    candles: List[Candle] = []
    for index, row in rows.iterrows():
        candles.append(
            Candle(
                date=index.strftime("%Y-%m-%d"),
                open=float(row["Open"]),
                high=float(row["High"]),
                low=float(row["Low"]),
                close=float(row["Close"]),
                volume=int(row["Volume"]),
            )
        )
    return candles


def _fetch_history(ticker: str, start: datetime, end: datetime) -> List[Candle]:
    """Fetch OHLCV data for the provided date range."""

    history = yf.Ticker(ticker).history(start=start, end=end, auto_adjust=False)
    if history.empty:
        return []
    return _serialize_candles(history)


server = Server(SERVER_NAME)


@server.tool(
    name="get_ticker_data",
    description=(
        "Fetch OHLCV pricing data for a ticker symbol. Provide either a specific "
        "calendar date (YYYY-MM-DD) or the number of most recent trading days to "
        "retrieve."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "Ticker symbol to query (e.g., AAPL)",
            },
            "date": {
                "type": ["string", "null"],
                "description": "Specific date in YYYY-MM-DD format",
            },
            "last_n_days": {
                "type": ["integer", "null"],
                "minimum": 1,
                "description": "Number of most recent trading days to fetch",
            },
        },
        "required": ["ticker"],
    },
)
def get_ticker_data(
    ticker: str,
    date: str | None = None,
    last_n_days: int | None = None,
) -> Dict[str, Any]:
    """Retrieve yfinance data for a ticker."""

    if not ticker:
        raise ValueError("ticker is required")

    if date and last_n_days:
        raise ValueError("Provide either date or last_n_days, not both")

    if not date and not last_n_days:
        raise ValueError("Either date or last_n_days must be provided")

    if date:
        start = _parse_date(date)
        end = start + timedelta(days=1)
    else:
        days = int(last_n_days)
        if days < 1:
            raise ValueError("last_n_days must be positive")
        end = datetime.now(tz=UTC)
        # Request extra days to account for weekends/holidays; yfinance will trim automatically.
        start = end - timedelta(days=days * 2)

    candles = _fetch_history(ticker, start, end)

    if not candles:
        message = f"No market data available for {ticker}"
        if date:
            message += f" on {date}"
        else:
            message += " in the requested time range"
        raise ValueError(message)

    payload: Dict[str, Any] = {
        "ticker": ticker.upper(),
        "candles": [asdict(candle) for candle in candles],
    }

    if last_n_days:
        payload["requested_days"] = last_n_days
    if date:
        payload["requested_date"] = date

    payload["as_json"] = json.dumps(payload)
    return payload


def main() -> None:
    """Entry point when running the module directly."""

    parser = argparse.ArgumentParser(description="Run the yfinance MCP server")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run the server using standard I/O transport (default)",
    )
    _ = parser.parse_args()
    server.run()


if __name__ == "__main__":
    main()