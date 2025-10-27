"""Model Context Protocol server for fetching market data via yfinance."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Dict, List

import pandas as pd
import yfinance as yf
from fastmcp import FastMCP

mcp = FastMCP("yfinance MCP Server")
server = mcp  # export alias expected by clients importing `server`


@dataclass(frozen=True)
class Candle:
    """Represents OHLCV data for a single trading day."""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int


def _ensure_naive_utc(dt: datetime) -> datetime:
    """Convert an aware datetime to a naive UTC datetime for yfinance."""

    if dt.tzinfo is None:
        return dt
    return dt.astimezone(UTC).replace(tzinfo=None)


def _parse_date(date_str: str) -> datetime:
    """Parse a YYYY-MM-DD string into a timezone-aware datetime."""

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=UTC)
    except ValueError as exc:
        raise ValueError("date must be in YYYY-MM-DD format") from exc


def _serialize_candles(rows: pd.DataFrame) -> List[Candle]:
    """Convert a pandas dataframe returned by yfinance into Candle objects."""

    if rows.empty:
        return []

    if not isinstance(rows.index, pd.DatetimeIndex):
        raise ValueError("Expected yfinance data to be indexed by datetime")

    candles: List[Candle] = []
    for index, row in rows.sort_index().iterrows():
        if row[["Open", "High", "Low", "Close", "Volume"]].isna().any():
            # Skip rows with incomplete pricing data.
            continue
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

    start_naive = _ensure_naive_utc(start)
    end_naive = _ensure_naive_utc(end)

    history = yf.Ticker(ticker).history(
        start=start_naive,
        end=end_naive,
        interval="1d",
        auto_adjust=False,
    )

    if history.empty:
        return []

    # Drop dividend/split columns to simplify serialization.
    columns = ["Open", "High", "Low", "Close", "Volume"]
    missing_columns = set(columns) - set(history.columns)
    if missing_columns:
        raise ValueError(
            "yfinance response missing expected columns: " + ", ".join(sorted(missing_columns))
        )

    return _serialize_candles(history[columns])




def _validate_request(ticker: str, date: str | None, last_n_days: int | None) -> None:
    if not ticker:
        raise ValueError("ticker is required")

    if date and last_n_days:
        raise ValueError("Provide either date or last_n_days, not both")

    if not date and not last_n_days:
        raise ValueError("Either date or last_n_days must be provided")

    if last_n_days is not None:
        if int(last_n_days) < 1:
            raise ValueError("last_n_days must be positive")


def _limit_to_recent_days(candles: List[Candle], last_n_days: int | None) -> List[Candle]:
    if last_n_days is None:
        return candles
    if last_n_days >= len(candles):
        return candles
    return candles[-last_n_days:]


@mcp.tool()
def get_ticker_data(
    ticker: str,
    date: str | None = None,
    last_n_days: int | None = None,
) -> Dict[str, Any]:
    """Fetch OHLCV pricing data for a ticker symbol.

    Provide either a specific calendar date (YYYY-MM-DD) or the number of most
    recent trading days to retrieve.

    Args:
        ticker: Ticker symbol to query (e.g., AAPL)
        date: Specific date in YYYY-MM-DD format
        last_n_days: Number of most recent trading days to fetch (minimum: 1)
    """

    _validate_request(ticker, date, last_n_days)

    if date:
        start = _parse_date(date)
        end = start + timedelta(days=1)
    else:
        days = int(last_n_days or 0)
        end = datetime.now(tz=UTC)
        # Request extra days to account for weekends/holidays; yfinance will trim automatically.
        start = end - timedelta(days=max(days * 3, 7))

    candles = _fetch_history(ticker, start, end)
    candles = _limit_to_recent_days(candles, last_n_days)

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

    payload["as_json"] = json.dumps(payload, separators=(",", ":"))
    return payload


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the yfinance MCP server")
    parser.add_argument(
        "--stdio",
        action="store_true",
        help="Run the server using standard I/O transport (default)",
    )
    return parser


def main() -> None:
    """Entry point when running the module directly."""

    parser = _build_arg_parser()
    _ = parser.parse_args()
    mcp.run()


__all__ = [
    "Candle",
    "get_ticker_data",
    "main",
    "mcp",
    "server",
]


if __name__ == "__main__":
    main()