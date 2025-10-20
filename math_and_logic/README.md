# Math & Logic MCP Module

This module exposes a collection of basic math and set-logic utilities via the
[Model Context Protocol](https://github.com/modelcontextprotocol/).

## Available tools

- `add(a, b)` – Returns the sum of two numbers.
- `subtract(a, b)` – Returns the difference of two numbers.
- `divide(a, b)` – Returns the quotient of two numbers, guarding against division by zero.
- `multiply(a, b)` – Returns the product of two numbers.
- `sqrt(value)` – Returns the square root of a non-negative number.
- `greater_than(a, b)` – Boolean comparison that checks if `a` is greater than `b`.
- `less_than(a, b)` – Boolean comparison that checks if `a` is less than `b`.
- `set_intercept(values_a, values_b)` – Returns the intersection of two iterables.
- `set_union(values_a, values_b)` – Returns the union of two iterables.

## Running the server

```bash
pip install -e .
math-and-logic-mcp
```

The MCP server will start and expose the tools above for use by MCP-compatible clients.
