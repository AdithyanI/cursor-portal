Below is a **tools-only** reference for creating an MCP server. This guide omits all other MCP features (prompts, resources, logging, etc.) and focuses solely on **Tools**—so it’s ideal if your client only supports tools.

---

# MCP Server Documentation (Tools-Only)

## 1. Overview: Tools in MCP

- **Tools** are callable functions that allow an LLM to perform actions, retrieve data, or invoke external APIs.
- A client (the Host side) can discover which tools your server offers and then call them with JSON arguments.
- This approach lets LLM-driven applications use your server as a “plugin” for executing specific tasks.

## 2. Declaring Tool Capability

When responding to the client’s `initialize` request, your server’s `capabilities` **must** include `tools`. For example:

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    }
  }
}
```

- `listChanged: true` is **optional**, but recommended if your available tools can change dynamically.
- If you do not need to notify the client of changes, you can omit or set `listChanged: false`.

## 3. Listing Tools

### 3.1 tools/list Request

The Host (client) retrieves a list of all available tools via:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}
```

Your server responds with a structure like:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Get current weather information by city or zip code",
        "inputSchema": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "City name or zip code"
            }
          },
          "required": ["location"]
        }
      }
    ]
  }
}
```

Key fields for each **Tool**:

- `name`: Unique name of the tool.
- `description`: Human-readable summary (helpful for the LLM or user).
- `inputSchema`: JSON Schema describing the tool’s expected parameters.
  - Type is typically `"object"`.
  - `properties` define each parameter.
  - `required` is an array of parameter names that must be provided.

#### 3.1.1 Pagination Support

If your server has many tools, you **may** want to paginate. You can include a `nextCursor` in the response and accept a `cursor` param in the request. This is optional but follows the standard MCP [pagination approach](#).

## 4. Calling a Tool

### 4.1 tools/call Request

When the LLM (through the client) decides to invoke a tool, it sends:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "get_weather",
    "arguments": {
      "location": "New York"
    }
  }
}
```

Your server should:

1. Look up the tool by `name` (e.g. `"get_weather"`).
2. Validate input arguments against the `inputSchema`.
3. Execute the relevant action.
4. Return a response indicating success or failure.

### 4.2 Successful Tool Response

Your response might look like:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Weather in New York: 72°F, partly cloudy"
      }
    ],
    "isError": false
  }
}
```

- **`content`**: An array of items (usually text, but could also be `image`, `audio`, or an embedded `resource`).
- **`isError`**: A boolean to indicate if this call ended in an error from the **tool** itself.

### 4.3 Tool Errors vs. MCP Errors

- **Tool Execution Errors**: If something goes wrong during your tool’s logic, respond with `isError = true` in the **result**, not a JSON-RPC error. This way, the LLM can see the error output. Example:

  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "result": {
      "content": [
        {
          "type": "text",
          "text": "API request failed: rate limit exceeded"
        }
      ],
      "isError": true
    }
  }
  ```

- **Protocol-Level Errors**: If the request is invalid (e.g., unknown tool name), you should return a standard JSON-RPC error response:

  ```json
  {
    "jsonrpc": "2.0",
    "id": 2,
    "error": {
      "code": -32602,
      "message": "Unknown tool: get_weather2"
    }
  }
  ```

## 5. Handling Dynamic Tools (Optional)

If your server’s tool set can change (e.g., modules loaded/unloaded at runtime), you can notify the client. This is only needed if you set `listChanged: true` in your `tools` capability.

Whenever the list changes:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

Clients that receive this notification typically re-call `tools/list` to get the new set.

## 6. Implementation Tips

- **Tool Registration**: Maintain a simple internal map: `{ toolName => functionHandler }`.
- **JSON Schema**:
  - `type: "object"`
  - `properties: { <paramName>: { "type": "string"/"number"/... }}`
  - `required: []` (if needed).
- **Validation**: Use a JSON Schema validator (if available) to confirm arguments conform.
- **Return**:
  - A `result.content` array containing one or more text/image responses, or
  - `result.isError = true` if the tool fails.

## 7. Example Minimal Server Flow (Tools Only)

1. **Initialization**:

   - Respond with `"tools": { "listChanged": true }` inside `capabilities`.

2. **Listing Tools** (`tools/list`):

   - Return your tool definitions in the `tools` array.

3. **Calling a Tool** (`tools/call`):

   - Parse the `name` and `arguments`.
   - Execute the requested function.
   - Respond with either success or an error in `isError`.

4. **(Optional)** If your tool set changes dynamically, send `notifications/tools/list_changed`.

That’s it—no other MCP features are needed if your server is **tools-only**.

