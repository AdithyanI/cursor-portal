
# MCP Server Documentation

This document provides all essential server-related information for building Model Context Protocol (MCP) servers. It covers:

- How servers fit into the MCP architecture
- The server lifecycle (initialization and capability negotiation)
- Core “Server Features” in MCP (Prompts, Resources, Tools)
- Server-side utilities (Logging, Completion/Autocompletion, Pagination)
- Relevant request/response methods and notifications from the MCP specification

Developers creating new MCP servers can treat this as a single reference guide.

> **Note**: Some examples reference JSON-RPC methods (e.g., `resources/list`, `tools/call`) and message shapes. These are defined by the MCP schema in TypeScript and JSON Schema. Where needed, key schema excerpts are included for clarity.

---

## 1. MCP Server Overview

### 1.1 Role of Servers in MCP

In the Model Context Protocol (MCP):

- **Servers** provide modular capabilities, data, or “tools” to be used by large language models (LLMs).
- A **Host** application (such as a desktop program or a web application) spawns or connects to multiple servers via “Client” connectors.
- Each server is specialized, e.g., a server might handle local file access, database queries, or image creation.

The **server** side implements and exposes a specific set of MCP features:

- **Prompts**: Templated messages or user-facing instructions
- **Resources**: Readable data (files, database content, etc.)
- **Tools**: Executable functions (APIs, local commands, or other actions)

All communication follows [JSON-RPC 2.0](https://www.jsonrpc.org/specification) over one of the supported transports (stdio or HTTP+SSE).

---

## 2. Server Lifecycle & Capabilities

### 2.1 Initialization Sequence

1. **Server is Launched** (depending on transport):
   - **stdio**: Host spawns the server as a subprocess, connecting `stdin` and `stdout`.
   - **HTTP + SSE**: Server is already running as an independent process or service.

2. **Client → Server: `initialize` request**
   - The client sends its supported protocol version(s) and **client capabilities**.

3. **Server → Client: `initialize` response**
   - The server picks the protocol version it will use (e.g., `"2024-11-05"`)
   - Declares **server capabilities** (e.g., which features it implements)
   - Optionally returns a brief `instructions` string for how to use the server.

4. **Client → Server: `notifications/initialized`**
   - The client notifies the server that it is ready to proceed.

Below is a minimal JSON example for initialization:

```json
// Client --> Server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {}
    },
    "clientInfo": {
      "name": "ExampleClient",
      "version": "1.0.0"
    }
  }
}

// Server --> Client
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "logging": {},
      "prompts": { "listChanged": true },
      "resources": { "subscribe": true, "listChanged": true },
      "tools": { "listChanged": true }
    },
    "serverInfo": {
      "name": "ExampleServer",
      "version": "1.0.0"
    }
  }
}

// Client --> Server
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

### 2.2 Declaring Server Capabilities

During initialization, an MCP server lists which feature sets it supports inside `capabilities`. Core server-oriented capabilities are:

- `prompts` (exposing prompt templates)
- `resources` (exposing data for reading)
- `tools` (exposing callable functions)
- `logging` (emitting structured log messages)

Within each category, sub-capabilities can appear, for example:

```json
"capabilities": {
  "prompts": {
    "listChanged": true
  },
  "resources": {
    "subscribe": true,
    "listChanged": true
  },
  "tools": {
    "listChanged": true
  },
  "logging": {}
}
```

Meaning:

- **`prompts.listChanged`**: The server can notify the client when its prompt list changes.
- **`resources.subscribe`**: The server allows subscriptions for resource updates.
- **`resources.listChanged`**: The server can notify the client if available resources have changed.
- **`tools.listChanged`**: The server can similarly notify about tool list changes.
- **`logging`**: The server can emit structured log messages.

If a server does **not** offer prompts, for example, it can omit the `prompts` capability entirely.

---

## 3. Server Features

MCP servers typically provide one or more of these main “features” to the Host and its LLM.

1. **Prompts**: Templated chat instructions or “slash commands”
2. **Resources**: Arbitrary data (files, docs, database content)
3. **Tools**: Functions that can be invoked by the LLM

A single server may implement all three or just one. Each feature is optional and declared via capabilities.

### 3.1 Prompts

Prompts allow a server to publish user-facing instructions or chat templates. Clients can list these prompts and let users invoke them.

1. **List Prompts**:
   - The client calls `prompts/list` to retrieve all available prompts.
   - Server returns an array of prompt definitions (`name`, optional `description`, `arguments`).
2. **Get Prompt**:
   - The client calls `prompts/get` with a prompt `name` and (optionally) user-supplied arguments.
   - The server returns the actual message(s) that form the prompt, e.g.:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "prompts/get",
  "params": {
    "name": "code_review",
    "arguments": { "code": "def hello():\n    print('world')" }
  }
}
```

#### Prompt List Changes

If the server sets `prompts.listChanged = true`, it **should** send:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/prompts/list_changed"
}
```

whenever the set of prompts changes.

#### Prompt Data Structure

Each prompt can contain multiple messages—often with roles `"user"` or `"assistant"`. A message might be:

- Plain text (`type: "text"`)
- Image data (`type: "image"` + base64)
- Embedded resource reference (`type: "resource"`)

Example prompt definition in a `prompts/list` response:

```json
{
  "name": "code_review",
  "description": "Analyze code quality and suggest improvements",
  "arguments": [
    { "name": "code", "description": "Python code to review", "required": true }
  ]
}
```

---

### 3.2 Resources

Resources expose **readable data** to the host. Examples:

- Files in a project directory (`file:///...`)
- Database records
- Documents on external URLs

#### Listing Resources

- **`resources/list`** request → server returns an array of `Resource` objects.
- Each `Resource` includes `uri`, `name`, optional `description`, and `mimeType`.

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "resources/list"
}

// Example response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "resources": [
      {
        "uri": "file:///project/src/main.rs",
        "name": "main.rs",
        "description": "Rust entry point",
        "mimeType": "text/x-rust"
      }
    ]
  }
}
```

#### Reading Resource Contents

- **`resources/read`** → returns the actual file/data contents.
- The server can return text or binary data (base64).
- Example:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "resources/read",
  "params": {
    "uri": "file:///project/src/main.rs"
  }
}
```

**Response** might look like:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "contents": [
      {
        "uri": "file:///project/src/main.rs",
        "mimeType": "text/x-rust",
        "text": "fn main() {\n    println!(\"Hello world!\");\n}"
      }
    ]
  }
}
```

#### Subscribing to Resource Updates

If `resources.subscribe` is supported:

- The client can call `resources/subscribe` with a specific `uri`.
- The server then sends `notifications/resources/updated` whenever that resource changes.

For instance:

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "resources/subscribe",
  "params": { "uri": "file:///project/src/main.rs" }
}
```

When `main.rs` changes, the server notifies:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": { "uri": "file:///project/src/main.rs" }
}
```

#### Resource Templates

Servers can optionally define parameterized URI templates (RFC 6570) so clients can dynamically construct resource URIs. The server would expose them with `resources/templates/list`.

---

### 3.3 Tools

Tools are **callable functions** or “actions” that an LLM can invoke (with user approval).

- Each tool has a `name`, a `description`, and an `inputSchema` describing required arguments.
- The client might pass these definitions to the LLM (in a structured format).
- When the LLM decides to invoke a tool, the client issues `tools/call`.

#### Listing Tools

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/list"
}

// Example response
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "tools": [
      {
        "name": "get_weather",
        "description": "Fetch current weather by city name or zip code",
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

#### Invoking a Tool

```json
// Client -> Server
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

**Server** runs the requested action (e.g., queries an external API). Then returns:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Current weather in New York: 72°F, Partly cloudy"
      }
    ],
    "isError": false
  }
}
```

If an error occurs *inside* the tool logic, prefer returning `isError: true` in the **result** rather than a JSON-RPC-level error:

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

(That way the LLM can “see” the error.)

#### Tool List Updates

If your server’s tools can appear or disappear dynamically, set `tools.listChanged = true` and send:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/tools/list_changed"
}
```

---

## 4. Additional Server Utilities

MCP defines some optional utility features that servers *may* provide.

### 4.1 Logging

If a server declares `logging: {}`, it can push structured log messages to the client. The client might forward them to a UI or log file.

- The client can call `logging/setLevel` to control the minimum log severity.
- The server then sends `notifications/message` whenever it logs something that meets that threshold.

Example:

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "logging/setLevel",
  "params": { "level": "info" }
}

// Server -> Client (notification)
{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "error",
    "logger": "database",
    "data": {
      "error": "Connection failed",
      "details": { "host": "localhost", "port": 5432 }
    }
  }
}
```

Supported log levels (from least severe to most):
`debug, info, notice, warning, error, critical, alert, emergency`

### 4.2 Completion (Autocompletion)

Servers can optionally assist with argument autocompletion, especially for:

- Prompt arguments (e.g. auto-suggest possible “language” values)
- Resource templates (e.g. partial file paths)

If supported, the server implements `completion/complete` requests. Example:

```json
// Client -> Server
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "completion/complete",
  "params": {
    "ref": { "type": "ref/prompt", "name": "code_review" },
    "argument": {
      "name": "language",
      "value": "py"
    }
  }
}
```

The server returns an array of completions, up to 100 items:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "completion": {
      "values": ["python", "pytorch", "pyside"],
      "total": 10,
      "hasMore": true
    }
  }
}
```

### 4.3 Pagination

For any server calls that might return a large list (e.g., `resources/list`, `tools/list`, etc.), the server may provide results in **pages**:

- Return a `nextCursor` in the result if more results exist.
- The client includes `cursor` in subsequent requests to get further pages.

Example:

```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "resources": [...],
    "nextCursor": "opaque-cursor-token"
  }
}
```

---

## 5. Transport & Launching

### 5.1 stdio Transport

Most servers run as a child process launched by the Host, reading/writing JSON lines over `stdin` and `stdout`. Key notes:

- **No extra text** should be printed to stdout, only valid JSON-RPC lines.
- Stderr can be used for debug logs or crash traces if desired.

The server typically waits for the client’s `initialize` request, responds, and then processes further requests.

### 5.2 HTTP + SSE Transport

Alternately, your server can run independently with an HTTP interface:

- **SSE** endpoint: for pushing JSON-RPC messages to the client.
- **HTTP POST** endpoint: for receiving requests from the client.

This transport is more complex but allows a single server process to handle multiple client connections, or run as a remote service.

---

## 6. Security and Trust

Because servers can do things like read files, call APIs, or run code, be mindful of:

- **User consent**: Expose only safe capabilities, require explicit user approval for sensitive operations.
- **Access controls**: Validate resource URIs, tool inputs, etc.
- **Data leakage**: Filter logs or messages to avoid revealing secrets.
- **Malicious input**: Tools or resource queries may come from prompts generated by an LLM. Implement safe checks and handle untrusted inputs properly.

---

## 7. Putting It All Together

**A typical server** will:

1. **Advertise** which features it offers: prompts, resources, tools, logging, etc.
2. Implement the required JSON-RPC methods:
   - `initialize` / respond with its capabilities.
   - `prompts/list`, `prompts/get` if it offers prompts.
   - `resources/list`, `resources/read`, etc., if it offers resources.
   - `tools/list`, `tools/call` if it provides tools.
   - `logging/setLevel` (optional).
3. Respect optional additions like subscription, pagination, or completion.
4. Send notifications for changes in prompt/tool/resource lists, log messages, etc.

---

## 8. Reference: Key Methods for Servers

Below is a quick index of server “handler” methods—i.e., requests that the client will make if the server declares the corresponding capability.

| Method                      | Description                                         |
|----------------------------|-----------------------------------------------------|
| **initialize**             | Handle initial handshake (required)                |
| **logging/setLevel**       | Set the minimum log level if `logging` is supported |
| **prompts/list**           | List available prompts (if `prompts` is supported) |
| **prompts/get**            | Retrieve a specific prompt                         |
| **tools/list**             | List available tools (if `tools` is supported)     |
| **tools/call**             | Invoke a tool function                             |
| **resources/list**         | List known resources (if `resources` is supported) |
| **resources/read**         | Retrieve resource contents                         |
| **resources/subscribe**    | Subscribe to updates for a particular resource     |
| **resources/unsubscribe**  | Cancel a previous resource subscription            |
| **roots/list**             | (Less common) If server wants to request “roots” from the client, though typically it’s a client feature |
| **completion/complete**    | Provide autocompletion suggestions (optional)      |

Notifications the server **can** send:

| Notification                            | Purpose                               |
|----------------------------------------|---------------------------------------|
| **notifications/message**               | Logging output (if `logging` enabled) |
| **notifications/resources/list_changed**| Resource list changed                 |
| **notifications/resources/updated**     | A subscribed resource was updated     |
| **notifications/prompts/list_changed**  | Prompt set changed                    |
| **notifications/tools/list_changed**    | Tool set changed                      |

---

## 9. Schema & Further Details

- The full schema that defines these JSON-RPC messages is in the repository:
  - [`schema/2024-11-05/schema.ts`](schema/2024-11-05/schema.ts)
  - [`schema/2024-11-05/schema.json`](schema/2024-11-05/schema.json)
- For additional examples and advanced usage, consult the official MCP documentation site:
  <https://modelcontextprotocol.io>

---

## 10. Example Implementation Hints

While exact implementations vary by language, here are general tips:

1. **Parse JSON lines** from stdin (for stdio) or from HTTP POST bodies.
2. Route requests by `method`:
   - `initialize` → send your server’s capabilities.
   - `prompts/list` → return your prompt definitions, etc.
3. Use your language’s JSON library to build structured responses.
4. For advanced servers:
   - Support concurrency or asynchronous requests.
   - Cache resource data or handle resource watchers for `subscribe` updates.
   - Carefully handle tool invocation with robust error checking.

---

### (Optional) Directory Structure

Because every MCP server is different, there is **no fixed** directory layout. Many implementers choose a structure like:

```
servers/
  blog/
    main.go (or .py, .js, etc.)
    ...
  social/
    main.go
    ...
  creative/
    main.go
    ...
```

Where each subdirectory is a separate MCP server addressing a specific integration or function. However, **this is not specified by MCP**; it is purely a project decision.

---

## 11. Conclusion

By implementing these protocols (Prompts, Resources, Tools, and optionally Logging, Subscriptions, Pagination, etc.), you can build an MCP server that seamlessly plugs into hosts and LLM-driven workflows. Remember to:

- **Advertise capabilities** and handle only the features you actually implement.
- **Validate** all inputs carefully (LLM text is untrusted).
- Provide **helpful** responses, notifications, and (when relevant) a good log or debugging experience.

With these guidelines, you should have all necessary details to create robust MCP servers that power dynamic AI-driven applications.
