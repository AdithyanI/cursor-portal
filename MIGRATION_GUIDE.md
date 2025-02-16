# Migration Guide: Switching from FastMCP to Standard Model Context Protocol SDK

## Introduction
This guide is designed to help you transition from using FastMCP to the standard Model Context Protocol TypeScript SDK. It provides a step-by-step plan, with detailed instructions that even a junior developer can follow.

## Step 1: Understand the Current Implementation
- Review your existing FastMCP server code.
- Identify which parts of your code rely on FastMCP's abstractions (e.g., tool registration, transport initialization).
- Take note of any configuration or dependencies that may need to be updated.

## Step 2: Install the Standard SDK
- Remove or comment out FastMCP specific dependencies if they are no longer needed.
- Install the standard SDK and its dependencies by running:

```bash
npm install @modelcontextprotocol/sdk
npm install zod
```

## Step 3: Create a New Server File
- Create a new file (for example, `server.ts` or `mcp-server.ts`).
- Use the sample code below as a starting point:

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const server = new McpServer({
  name: 'MyMCPServer',
  version: '1.0.0'
});

// Define a sample tool
const echoTool = {
  name: 'echo',
  description: 'Echoes the provided message',
  parameters: z.object({ message: z.string() }),
  execute: async (args) => ({
    content: [{ type: 'text', text: `You said: ${args.message}` }]
  })
};

server.addTool(echoTool);

// Setup the transport (using stdio for this example)
const transport = new StdioServerTransport();
await server.connect(transport);

console.log('MCP Server started!');
```

## Step 4: Register Your Existing Tools
- Convert your FastMCP tool registrations to the standard method provided by the SDK.
- For example, if you have tools like `generateVideo` or `retrieveVoiceIds`, register them using:

```typescript
server.addTool(yourToolObject);
```

- Refer to the official SDK documentation for more examples and best practices: [Model Context Protocol TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk).

## Step 5: Configure Transports
- Decide which transport suits your use case (e.g., `StdioServerTransport` for local debugging or `SSEServerTransport` for a web server).
- Adjust your server startup code to initialize the chosen transport.

## Step 6: Test Your Server Locally
- Run your new server file with Node.js:

```bash
node server.ts
```

- Use tools like curl, Postman, or simply check the logs in your terminal to ensure the server starts correctly and the tools are registered.

## Step 7: Debug and Refine
- If errors occur, use console logging to debug.
- Compare your implementation with examples from the official SDK repository.
- Verify that all tool endpoints are reachable and behaving as expected.

## Conclusion
By following these steps, you will migrate from FastMCP to the full SDK, giving you more control and flexibility in your MCP server implementation. For further reading and detailed examples, consult the official [Model Context Protocol TypeScript SDK Documentation](https://github.com/modelcontextprotocol/typescript-sdk).

Happy coding! 