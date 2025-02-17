# HeyGen Python MCP Server

This is a Python implementation of the HeyGen video generation server using the Model Context Protocol (MCP).

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your HeyGen API key:
```bash
HEYGEN_API_KEY=your_api_key_here
```

3. Run the server:
```bash
python server.py
```

## Available Tools

### 1. generate_video
Generates a video using the HeyGen API V2.

Parameters:
- `script` (required): The script/text content for the video
- `title` (optional): Title for the video
- `caption` (optional): Whether to add captions
- `callback_id` (optional): Custom ID for callback purposes
- `width` (optional, default: 720): Video width in pixels
- `height` (optional, default: 1280): Video height in pixels

### 2. download_video
Downloads a generated video from HeyGen API.

Parameters:
- `video_id` (required): ID of the video to download
- `poll_interval` (optional, default: 10000): Polling interval in milliseconds
- `max_retries` (optional, default: 30): Maximum number of polling attempts

## Usage Example

The server uses stdio transport for integration with Cursor. You can interact with it using the MCP client in Cursor or by creating a test client script. 