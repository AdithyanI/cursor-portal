# MCP Server Template Guide

## Basic MCP Server Structure

```python
#!/usr/bin/env python3
from mcp.server.fastmcp import FastMCP
import logging

# Set up logging (recommended)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create MCP server instance
mcp = FastMCP(
    "Your Server Name",
    capabilities={
        "tools": {
            "listChanged": True  # Required by MCP spec
        }
    }
)

# Define your tools
@mcp.tool()
def your_tool_name(param1: type, param2: type) -> return_type:
    """
    Clear docstring explaining what the tool does.
    """
    logger.info(f"Processing with params: {param1}, {param2}")
    result = # Your logic here
    logger.info(f"Result: {result}")
    return result

# Main entry point
if __name__ == "__main__":
    try:
        logger.info("Starting MCP server...")
        mcp.run(transport="stdio")  # Use stdio for Cursor integration
    except Exception as e:
        logger.error(f"Error running server: {e}")
        raise
```

## Setup Requirements

1. Create a `requirements.txt` at your project root:

```
mcp[cli]==1.2.1
mcp-python-sdk>=0.1.0
```

## Implementation Steps

1. **Name Your Server**

   - Choose a descriptive name for your FastMCP instance
   - Example: `mcp = FastMCP("Calculator")`

2. **Define Tools**

   - Use `@mcp.tool()` decorator
   - Include type hints for parameters and return values
   - Write clear docstrings
   - Add logging for debugging

3. **Error Handling**
   - Wrap main execution in try-except
   - Use logging for errors
   - Return meaningful error messages

## Best Practices

1. **Documentation**

   - Add docstrings to all tools
   - Document parameter types and return values
   - Include usage examples

2. **Logging**

   - Use logging instead of print statements
   - Log input parameters and results
   - Include error details in logs

3. **Type Safety**
   - Use type hints consistently
   - Validate input parameters
   - Handle type conversion errors

## Example Implementation

```python
@mcp.tool()
def add(a: int, b: int) -> int:
    """
    Add two numbers together.

    Args:
        a (int): First number
        b (int): Second number

    Returns:
        int: Sum of the two numbers
    """
    logger.info(f"Adding {a} and {b}")
    result = a + b
    logger.info(f"Result: {result}")
    return result
```

## Testing Your Server

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the server:

```bash
python your_server.py
```

3. Test in Cursor:
   - Make sure the server is running
   - Use the tools through Cursor's interface

## Troubleshooting

1. **Server Not Starting**

   - Check if all dependencies are installed
   - Verify the Python path is correct
   - Check for syntax errors

2. **Tools Not Found**

   - Verify tool decorators are properly applied
   - Check if server capabilities are correctly set
   - Ensure tools have proper type hints

3. **Logging Issues**
   - Verify logging is configured correctly
   - Check log level settings
   - Ensure logging handler is properly set up
