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


def _normalize_info_value(value: Any) -> Any:
    """Normalize values returned by yfinance for safe JSON serialization."""

    if value is None:
        return None

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()

    if pd.isna(value):  # type: ignore[arg-type]
        return None

    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return value

    return value


def _fetch_ticker_info(ticker: str) -> Dict[str, Any]:
    """Retrieve summary information about a ticker symbol."""

    info = yf.Ticker(ticker).get_info()

    if not info:
        raise ValueError(f"No ticker information available for {ticker}")

    field_map = {
        "symbol": "symbol",
        "shortName": "short_name",
        "longName": "long_name",
        "quoteType": "quote_type",
        "currency": "currency",
        "exchange": "exchange",
        "marketState": "market_state",
        "sector": "sector",
        "industry": "industry",
        "country": "country",
        "fullTimeEmployees": "full_time_employees",
        "marketCap": "market_cap",
        "enterpriseValue": "enterprise_value",
        "trailingPE": "trailing_pe",
        "forwardPE": "forward_pe",
        "dividendYield": "dividend_yield",
        "fiftyTwoWeekHigh": "fifty_two_week_high",
        "fiftyTwoWeekLow": "fifty_two_week_low",
        "fiftyDayAverage": "fifty_day_average",
        "twoHundredDayAverage": "two_hundred_day_average",
        "beta": "beta",
        "revenueGrowth": "revenue_growth",
        "epsTrailingTwelveMonths": "eps_trailing_twelve_months",
        "epsForward": "eps_forward",
        "trailingAnnualDividendRate": "trailing_annual_dividend_rate",
        "trailingAnnualDividendYield": "trailing_annual_dividend_yield",
        "netIncomeToCommon": "net_income_to_common",
        "profitMargins": "profit_margins",
        "website": "website",
        "logo_url": "logo_url",
    }

    payload: Dict[str, Any] = {"ticker": ticker.upper()}

    for source_key, target_key in field_map.items():
        value = _normalize_info_value(info.get(source_key))
        if value is not None:
            payload[target_key] = value

    summary_fields = [
        "longBusinessSummary",
        "companyOfficers",
    ]

    for key in summary_fields:
        value = info.get(key)
        if key == "companyOfficers" and isinstance(value, list):
            normalized_officers = []
            for officer in value:
                if not isinstance(officer, dict):
                    continue
                normalized_officer: Dict[str, Any] = {}
                for officer_key, officer_value in officer.items():
                    normalized_value = _normalize_info_value(officer_value)
                    if normalized_value is not None:
                        normalized_officer[officer_key] = normalized_value
                if normalized_officer:
                    normalized_officers.append(normalized_officer)
            if normalized_officers:
                payload["company_officers"] = normalized_officers
            continue

        normalized_value = _normalize_info_value(value)
        if normalized_value is not None:
            payload["long_business_summary" if key == "longBusinessSummary" else key] = (
                normalized_value
            )

    payload["as_json"] = json.dumps(payload, separators=(",", ":"))
    return payload


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


@mcp.tool()
def get_ticker_info(ticker: str) -> Dict[str, Any]:
    """Fetch descriptive information and fundamentals for a ticker symbol."""

    if not ticker:
        raise ValueError("ticker is required")

    return _fetch_ticker_info(ticker)


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
    "get_ticker_info",
    "main",
    "mcp",
    "server",
]


if __name__ == "__main__":
    main()