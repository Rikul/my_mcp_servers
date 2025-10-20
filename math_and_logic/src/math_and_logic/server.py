"""Math and logic tools implemented as an MCP server."""

from __future__ import annotations

from math import sqrt as math_sqrt
from typing import Any, Iterable

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Math & Logic")


def _ensure_iterable_hashable(values: Iterable[Any]) -> set[Any]:
    """Convert an iterable to a set, ensuring the values are hashable."""
    try:
        return set(values)
    except TypeError as exc:  # pragma: no cover - guard clause
        raise ValueError("All elements must be hashable to form a set operation.") from exc


@mcp.tool()
def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""

    return a + b


@mcp.tool()
def subtract(a: float, b: float) -> float:
    """Return the difference of two numbers (a - b)."""

    return a - b


@mcp.tool()
def divide(a: float, b: float) -> float | str:
    """Return the quotient of two numbers."""

    if b == 0:
        return "Error: Division by zero is undefined."
    return a / b


@mcp.tool()
def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""

    return a * b


@mcp.tool()
def sqrt(value: float) -> float | str:
    """Return the square root of a non-negative number."""

    if value < 0:
        return "Error: Square root of a negative number is not defined for real numbers."
    return math_sqrt(value)


@mcp.tool()
def greater_than(a: float, b: float) -> bool:
    """Return True if *a* is greater than *b*."""

    return a > b


@mcp.tool()
def less_than(a: float, b: float) -> bool:
    """Return True if *a* is less than *b*."""

    return a < b


@mcp.tool()
def set_intercept(values_a: Iterable[Any], values_b: Iterable[Any]) -> list[Any] | str:
    """Return the intersection of two iterables as a list without duplicates."""

    try:
        intersection = _ensure_iterable_hashable(values_a) & _ensure_iterable_hashable(values_b)
    except ValueError as exc:
        return str(exc)
    return list(intersection)


@mcp.tool()
def set_union(values_a: Iterable[Any], values_b: Iterable[Any]) -> list[Any] | str:
    """Return the union of two iterables as a list without duplicates."""

    try:
        union = _ensure_iterable_hashable(values_a) | _ensure_iterable_hashable(values_b)
    except ValueError as exc:
        return str(exc)
    return list(union)


def main() -> None:
    """Run the MCP server."""

    mcp.run()


if __name__ == "__main__":
    main()
