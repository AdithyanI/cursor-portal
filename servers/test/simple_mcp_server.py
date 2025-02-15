#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP(
    "Calculator",
    capabilities={
        "tools": {
            "listChanged": True
        }
    }
)

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers together"""
    logger.info(f"Adding {a} and {b}")
    result = a + b
    logger.info(f"Result: {result}")
    return result

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers together"""
    logger.info(f"Multiplying {a} and {b}")
    result = a * b
    logger.info(f"Result: {result}")
    return result

if __name__ == "__main__":
    try:
        logger.info("Starting Calculator MCP server...")
        # Run the server in stdio mode
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise
