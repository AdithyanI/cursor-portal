# MCP Tools (Python SDK)

Tools in MCP are **callable functions** your server exposes for the AI model. When the model (or user) decides to invoke a tool, the client packages a JSON request and sends it to your server. The Python SDK can automatically parse the incoming arguments, call your Python function, and return the results in a standard format.

## 1. High-Level “FastMCP” Approach

The simplest way to build an MCP server in Python is with `FastMCP`. It provides:

- A decorator-based API for registering tools
- Automatic JSON argument parsing for function parameters
- (Optionally) injection of a `Context` object for logging, progress, and resource access

### 1.1 Creating a FastMCP Server

```python
from mcp.server.fastmcp import FastMCP

# Create a server
app = FastMCP("MyToolsServer")
```

### 1.2 Defining Tools with the `@tool` Decorator

You can register a tool by decorating a function with `@app.tool()`. The function’s signature (parameter names & types) is automatically converted into a JSON schema for the tool’s arguments.

```python
from mcp.server.fastmcp import Context

@app.tool()
def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

@app.tool()
async def fetch_data(url: str, ctx: Context) -> str:
    """Fetch data from a URL. Demonstrates using the optional Context."""
    ctx.info(f"Fetching {url}...")
    # do an async HTTP request here
    result = "..."
    return result
```

Key points:

- **Function’s docstring** → used as the tool description (unless you override).
- **Parameters** → automatically validated from JSON.
- **Optional**: If your function has a `Context` parameter, it’s injected automatically at runtime (for logging, progress, etc.).
- Return values can be `str`, `bytes`, or complex objects. They become JSON or text content in the final tool result.

### 1.3 Tool Calls at Runtime

**How it works under the hood**:

1. The LLM (through the Host client) sends a `tools/call` request with `{ "name": "<toolName>", "arguments": { ... } }`.
2. FastMCP inspects the tool’s function signature, parses and validates arguments, and calls your Python function.
3. The result is wrapped as `TextContent` or `ImageContent` (or other structured responses).

If your function raises an exception, FastMCP automatically flags the tool response as an error with `isError: true`.

### 1.4 Running the Server

You can run your server in `stdio` mode (common for local child-process usage) or SSE:

```python
if __name__ == "__main__":
    app.run(transport="stdio")  # or transport="sse"
```

**Example**: Stdio is typical for a child process launched by Claude Desktop or an MCP client.

---

## 2. Detailed Internals of Tools

Below is a breakdown of how tools actually work under the hood within the **`fastmcp.tools`** subpackage.

### 2.1 `Tool` Class

When you do `@server.tool()`, it internally creates a `Tool` object with:

- `fn` (the original Python function)
- `name` (defaults to `fn.__name__`)
- `description` (from docstring or an override)
- `parameters` (a JSON schema describing the function’s parameters)
- `is_async` (whether function is async)
- `context_kwarg` (which param receives a `Context`)

**We** do _not_ manually create `Tool` objects—this is done automatically by the decorator.

### 2.2 `ToolManager`

A `ToolManager`:

- Keeps a dictionary of **tool name** → **Tool**
- Provides a `call_tool(name, arguments, context)` method that:
  1. Looks up the `Tool`
  2. Validates the arguments
  3. Calls the Python function
  4. Returns or raises

In `FastMCP`, each server instance has a single `ToolManager` that all tool definitions get registered into.

### 2.3 How Arguments Are Validated

Internally, the decorator runs a small type-inspection routine (`func_metadata`). That does:

- Extract your function’s signature (each param name & type)
- Build a small Pydantic model to parse JSON arguments
- If the user passes a parameter that’s typed `Context`, it’s not in the JSON schema (the server injects it at call time)

### 2.4 Return Values & The Final Tool “result”

When your function returns (for example) a string, FastMCP wraps it as `TextContent(type="text", text=...)`. If you return a specialized object like `Image` (from `mcp.server.fastmcp.utilities.types`), it’s automatically encoded as base64 image content. You can also return a list of multiple items, each of which is turned into a separate content item.

**In JSON**:

```json
{
  "id": 42,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Hello, world!"
      }
    ],
    "isError": false
  },
  "jsonrpc": "2.0"
}
```

If your code raises an exception or you want to forcibly set `isError = true`, the final result might look like:

```json
{
  "id": 42,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Something went wrong: KeyError('whatever')"
      }
    ],
    "isError": true
  },
  "jsonrpc": "2.0"
}
```

---

## 3. Low-Level “Server” Approach

If you’re not using `FastMCP`, you can still handle Tools with the “low-level” server class in `mcp.server.lowlevel.Server`. That means manually adding handlers:

```python
from mcp.server.lowlevel import Server

server = Server(name="Example")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="my_tool",
            description="My custom tool",
            inputSchema={
                "type": "object",
                "required": ["x"],
                "properties": {
                    "x": {
                        "type": "number",
                        "description": "Number to be processed"
                    }
                }
            },
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) \
        -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "my_tool":
        x = arguments["x"]
        result = f"The number is {x}"
        return [types.TextContent(type="text", text=result)]
    else:
        raise ValueError(f"Unknown tool: {name}")
```

Then run your server:

```python
async def main():
    async with stdio_server() as (read, write):
        await server.run(
            read, write,
            server.create_initialization_options()
        )

anyio.run(main)
```

**Here** you must handle input schemas, argument parsing, etc. yourself. That’s why `FastMCP` is usually simpler for real usage.

---

## 4. Using Tools in the MCP Client

_(Optional, purely for testing your server)_

A Python-based MCP **client** can discover and call your tools. You might do:

```python
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

async def main():
    # Suppose your server.py has a "main" that runs the server in stdio
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"],
        env={}
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 1) List Tools
            tool_list_result = await session.list_tools()
            print("Available tools:", tool_list_result.tools)

            # 2) Call a tool
            call_res = await session.call_tool("greet", {"name": "Alice"})
            print("Tool result:", call_res.content, "Error?", call_res.isError)

```

---

## 5. Summary & Best Practices

**Step-by-step** for building a Tools-only Python server with `FastMCP`:

1. **Create** a `FastMCP("NameOfServer")`
2. **Decorate** each function with `@server.tool()`
   - Add docstrings that become the tool’s description
   - Carefully type your parameters & return
3. (Optional) Use a `Context` parameter for logging or progress
4. **Run** via `server.run("stdio")` or `server.run("sse")`
5. **Test** by listing tools from the client and calling them with arguments

**That’s it!** Your server will automatically expose standard “list tools” and “call tool” MCP endpoints, with typed argument parsing and error handling included.

---

### Reference

**Relevant Source Files** (within the Python SDK repo):

- `src/mcp/server/fastmcp/tools/`: Implementation of `Tool` and `ToolManager`
- `src/mcp/server/fastmcp/server.py`: The `FastMCP` class that ties everything together
- `src/mcp/shared/session.py`: Underlying request/response logic

**Core Methods**:

- `@server.tool()`: Decorator to register a Python function as a tool
- `await session.call_tool("name", {...})`: Used by a client to invoke it
- `ToolManager.add_tool(...)`: Internally used by `@tool()`

**Return Value Handling**:

- Plain text → `TextContent(type="text", text=...)`
- Binary images → `ImageContent(type="image", data=..., mimeType=...)`
- Arbitrary objects → JSON-serialized text content or an error on parse failure
