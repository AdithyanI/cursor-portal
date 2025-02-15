# Cursor Calculator MCP Server

A simple calculator server that integrates with Cursor using the Model Context Protocol (MCP).

## Installation

1. Install dependencies:

```bash
uv pip install mcp[cli]
```

2. Install the server in Cursor:

```bash
mcp install simple_mcp_server.py
```

## Available Tools

The server provides a single versatile calculator tool:

### calculate

Performs basic calculations on a list of numbers.

Example usage:

```json
{
  "operation": "add",
  "numbers": [1, 2, 3, 4, 5]
}
```

Supported operations:

- `add`: Sum all numbers
- `multiply`: Multiply all numbers
- `average`: Calculate the average

## Development

To test the server locally:

```bash
mcp dev simple_mcp_server.py
```

This will start the MCP Inspector at http://localhost:5173 where you can test the tools interactively.
