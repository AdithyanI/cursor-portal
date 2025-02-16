# Video Generation MCP Server

This is a Model Context Protocol (MCP) server that integrates with the HeyGen API to generate AI-powered videos. The server provides a simple interface for creating videos with customizable text, avatars, and voices.

## Features

- Generate AI videos using HeyGen's API
- Customizable parameters:
  - Script/text content
  - Avatar selection (optional)
  - Voice selection (optional)
- Error handling and logging
- TypeScript support
- Environment variable configuration for API keys

## Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- HeyGen API key (get one from [HeyGen's website](https://www.heygen.com/))

## Installation

1. Clone the repository and navigate to the server directory:
   ```bash
   cd servers/creative/video-gen
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Configure your environment variables by creating a `.env` file:
   ```bash
   HEYGEN_API_KEY=your_api_key_here
   ```

## Running the Server

You can run the server in two ways:

1. Using npm scripts:
   ```bash
   npm run dev    # Run in development mode with auto-reload
   # or
   npm start      # Run in production mode
   ```

2. Using FastMCP CLI directly:
   ```bash
   npx fastmcp dev server.ts
   ```

## Using the Server

The server exposes a single tool called `generateVideo` with the following parameters:

```typescript
{
  script: string;       // Required: The text content for the video
  avatar?: string;      // Optional: HeyGen avatar ID
  voice?: string;       // Optional: HeyGen voice ID
}
```

### Example Usage

1. Start the server
2. Connect to the server using an MCP client
3. Call the `generateVideo` tool with your parameters:

```json
{
  "script": "Hello! This is a test video using HeyGen API.",
  "avatar": "TH01",    // Optional
  "voice": "en_us_001" // Optional
}
```

### Response Format

The tool returns a response in the following format:

```json
{
  "success": true,
  "video_id": "generated_video_id",
  "status": "processing",
  "message": "Video generation started successfully"
}
```

## Error Handling

The server includes comprehensive error handling:
- API key validation
- Request validation
- HeyGen API error responses
- Network errors

All errors are logged and returned with appropriate error messages.

## Development

The server is built with TypeScript and uses:
- `fastmcp` for MCP server implementation
- `zod` for parameter validation
- `node-fetch` for API requests
- `dotenv` for environment variable management

To modify the server:
1. Edit `server.ts` for core functionality
2. Update parameter schemas in the `videoParameters` object
3. Modify error handling in the `execute` function

## Troubleshooting

1. If the server fails to start, check:
   - Your HeyGen API key is correctly set in `.env`
   - All dependencies are installed
   - You're in the correct directory

2. If video generation fails:
   - Check the API response in the logs
   - Verify your parameters match HeyGen's requirements
   - Ensure your API key has sufficient permissions

## License

ISC
