#!/usr/bin/env python3
import os
import logging
import requests
import time
import json
from typing import Dict, Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Set up logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastMCP server
mcp = FastMCP(
    "HeyGen Video Generation Server",
    capabilities={
        "tools": {
            "listChanged": True
        }
    }
)

# Get API key from environment
HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY")
if not HEYGEN_API_KEY:
    raise ValueError("HEYGEN_API_KEY environment variable is required")

# Create output directory if it doesn't exist
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def pretty_print_request(req):
    """
    Helper function to format request details for logging
    """
    return '{}\n{}\n{}\n\n{}'.format(
        '-----------REQUEST-----------',
        req.method + ' ' + req.url,
        '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
        req.body if req.body else "No body"
    )

def pretty_print_response(res):
    """
    Helper function to format response details for logging
    """
    return '{}\n{}\n{}\n\n{}'.format(
        '-----------RESPONSE-----------',
        'Status: ' + str(res.status_code),
        '\n'.join('{}: {}'.format(k, v) for k, v in res.headers.items()),
        res.text if res.text else "No body"
    )

@mcp.tool()
def generate_video(script: str) -> Dict:
    """
    Generate a video using the HeyGen API V2.
    
    Args:
        script (str): The script/text content for the video.
    
    Returns:
        Dict: Response containing the video generation status
    """
    logger.info("generate_video called with script: %s", script)
    try:
        # Use exact same request body as our working test
        request_body = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": "Abigail_expressive_2024112501"
                },
                "voice": {
                    "type": "text",
                    "voice_id": "26b2064088674c80b1e5fc5ab1a068eb",
                    "input_text": script
                }
            }],
            "dimension": {"width": 720, "height": 1280}
        }

        # Log what we're about to send
        print("\nRequest Body:")
        print(json.dumps(request_body, indent=2))
        
        # Make request exactly as in test
        response = requests.post(
            "https://api.heygen.com/v2/video/generate",
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": HEYGEN_API_KEY,
                "Accept": "application/json"
            },
            json=request_body
        )
        
        # Log response details
        print("\nResponse Status:", response.status_code)
        print("Response Headers:")
        print(json.dumps(dict(response.headers), indent=2))
        print("\nResponse Body:")
        print(json.dumps(response.json() if response.text else {}, indent=2))

        response.raise_for_status()
        data = response.json()

        return {
            "content": [{
                "type": "text",
                "text": f"Video generation initiated. Video ID: {data['data']['video_id']}"
            }]
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "isError": True
        }

@mcp.tool()
def download_video(
    video_id: str,
    poll_interval: int = 10000,
    max_retries: int = 30
) -> Dict:
    """
    Download a generated video from HeyGen API.

    Args:
        video_id (str): ID of the video to download
        poll_interval (int): Polling interval in milliseconds (default: 10000)
        max_retries (int): Maximum number of polling attempts (default: 30)

    Returns:
        Dict: Response containing the download status and file path
    """
    logger.info("download_video called with video_id: %s, poll_interval: %s ms, max_retries: %s", video_id, poll_interval, max_retries)
    try:
        interval = poll_interval / 1000  # Convert to seconds
        retries = 0

        while retries < max_retries:
            logger.info(f"Checking video status (attempt {retries + 1}/{max_retries})")

            status_response = requests.get(
                f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
                headers={
                    "X-Api-Key": HEYGEN_API_KEY,
                    "Accept": "application/json"
                }
            )

            status_data = status_response.json()

            if status_data["data"]["status"] == "completed":
                video_url = status_data["data"]["video_url"]
                if not video_url:
                    raise ValueError("Video URL not found in the response")

                video_response = requests.get(video_url)
                video_response.raise_for_status()

                file_path = os.path.join(OUTPUT_DIR, f"video_{video_id}.mp4")
                with open(file_path, "wb") as f:
                    f.write(video_response.content)

                return {
                    "content": [{
                        "type": "text",
                        "text": f"Video downloaded successfully and saved to {file_path}"
                    }]
                }

            elif status_data["data"]["status"] == "failed":
                raise ValueError("Video processing failed")

            time.sleep(interval)
            retries += 1

        raise TimeoutError("Video processing timeout")

    except Exception as e:
        logger.error(f"Error in download_video tool: {e}")
        raise

@mcp.tool()
def retrieve_voices() -> Dict:
    """
    Retrieve available voice IDs from HeyGen API.

    Returns:
        Dict: Response containing the available voices
    """
    logger.info("retrieve_voices called")
    try:
        response = requests.get(
            "https://api.heygen.com/v2/voices",
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": HEYGEN_API_KEY,
                "Accept": "application/json"
            }
        )

        response.raise_for_status()
        data = response.json()

        return {
            "content": [{
                "type": "text",
                "text": "Successfully retrieved available voices",
                "details": data
            }]
        }

    except Exception as e:
        logger.error(f"Error in retrieve_voices tool: {e}")
        raise

@mcp.tool()
def retrieve_avatars() -> Dict:
    """
    Retrieve available avatars from HeyGen API.

    Returns:
        Dict: Response containing the available avatars
    """
    logger.info("retrieve_avatars called")
    try:
        response = requests.get(
            "https://api.heygen.com/v2/avatars",
            headers={
                "Content-Type": "application/json",
                "X-Api-Key": HEYGEN_API_KEY,
                "Accept": "application/json"
            }
        )

        response.raise_for_status()
        data = response.json()

        return {
            "content": [{
                "type": "text",
                "text": "Successfully retrieved available avatars",
                "details": data
            }]
        }

    except Exception as e:
        logger.error(f"Error in retrieve_avatars tool: {e}")
        raise

@mcp.tool()
def retrieve_video_list(limit: int = None, token: str = None) -> Dict:
    """
    Retrieve a list of videos from the HeyGen API (https://docs.heygen.com/reference/video-list).

    Args:
        limit (int, optional): Number of videos to retrieve (range: 0-100).
        token (str, optional): Pagination token for next page.

    Returns:
        Dict: API response containing 'code', 'message', and 'data' (which includes 'token' and the list of videos).
    """
    logger.info("retrieve_video_list called with limit: %s, token: %s", limit, token)
    try:
        if not HEYGEN_API_KEY:
            raise ValueError("HEYGEN_API_KEY environment variable is required")
        
        url = "https://api.heygen.com/v1/video.list"
        headers = {
            "X-Api-Key": HEYGEN_API_KEY,
            "Accept": "application/json"
        }
        params = {}
        if limit is not None:
            params['limit'] = limit
        if token:
            params['token'] = token
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()  # Expected to have 'code', 'data', and 'message'
        
        videos = data.get("data", {}).get("videos", [])
        formatted_videos = []
        for video in videos:
            formatted_videos.append({
                "video_id": video.get("video_id"),
                "status": video.get("status"),
                "created_at": video.get("created_at"),
                "type": video.get("type")
            })
        
        return {
            "code": data.get("code", 100),
            "message": data.get("message"),
            "data": {
                "token": data.get("data", {}).get("token"),
                "videos": formatted_videos
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving video list: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    try:
        logger.info("Starting HeyGen Video Generation MCP server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error running HeyGen Video Generation MCP server: {e}")
        raise 