#!/usr/bin/env python3
import os
import hmac
import base64
import json
import time
import hashlib
import logging
import requests
from typing import Dict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from mcp.server.fastmcp import FastMCP

# ------------------------------------------------------------------------------
# Set up logging (recommended)
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------------------
# Create FastMCP server instance
# ------------------------------------------------------------------------------
mcp = FastMCP(
    "Ghost Admin API Server",
    capabilities={
        "tools": {
            "listChanged": True  # Required by MCP spec
        }
    }
)

# ------------------------------------------------------------------------------
# Helper function to generate Ghost Admin JWT
# ------------------------------------------------------------------------------
def generate_ghost_jwt(admin_api_key: str) -> str:
    """
    Generates a short-lived JWT for authenticating with the Ghost Admin API.

    Args:
        admin_api_key (str): The admin API key in the format 'key_id:secret'.

    Returns:
        str: A JWT token string to use in the "Authorization: Ghost <token>" header.
    """
    try:
        # Split key into ID and SECRET
        key_id, secret = admin_api_key.split(":")

        # Decode the hex secret to bytes
        secret_bytes = bytes.fromhex(secret)

        # Prepare header and payload
        # iat = now, exp = now + 5 minutes
        iat = int(time.time())
        exp = iat + 5 * 60

        header = {
            "alg": "HS256",
            "kid": key_id,
            "typ": "JWT"
        }
        payload = {
            "iat": iat,
            "exp": exp,
            "aud": "/admin/"
        }

        # Base64 url-encode header and payload
        def base64_url_encode(data: bytes) -> str:
            return base64.urlsafe_b64encode(data).decode().rstrip("=")

        header_b64 = base64_url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = base64_url_encode(json.dumps(payload, separators=(",", ":")).encode())
        to_sign = f"{header_b64}.{payload_b64}".encode()

        # Sign with secret
        signature = hmac.new(secret_bytes, to_sign, hashlib.sha256).digest()
        signature_b64 = base64_url_encode(signature)

        # Final token
        token = f"{header_b64}.{payload_b64}.{signature_b64}"
        return token

    except Exception as e:
        logger.error(f"Error generating Ghost JWT: {e}")
        raise

# ------------------------------------------------------------------------------
# Tool: Create a new Ghost post
# ------------------------------------------------------------------------------
@mcp.tool()
def create_ghost_post(title: str, html_content: str, status: str = "draft") -> Dict:
    """
    Create a new post in Ghost using the Admin API.

    Args:
        title (str): Title of the post.
        html_content (str): HTML content for the post body.
        status (str, optional): Post status. Defaults to "draft".
                              Valid values: "draft", "published", "scheduled".

    Returns:
        dict: The newly created post object from Ghost Admin API.

    Example:
        >>> create_ghost_post(
        ...     title="My First Post",
        ...     html_content="<p>Hello from MCP & Ghost!</p>",
        ...     status="draft"
        ... )
    """

    logger.info("Starting to create a new Ghost post...")

    # 1) Fetch settings from environment or config
    ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")  # e.g. https://<your-ghost-domain>
    admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")        # e.g. <key_id>:<secret>

    if not ghost_admin_api_url or not admin_api_key:
        raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

    # 2) Generate a short-lived JWT for the Ghost Admin API
    token = generate_ghost_jwt(admin_api_key)

    # 3) Construct the request headers
    headers = {
        "Authorization": f"Ghost {token}",
        "Content-Type": "application/json",
        "Accept-Version": "v5.0"  # Adding API version header
    }

    # 4) Build the request body
    post_data = {
        "posts": [
            {
                "title": title,
                "html": html_content,
                "status": status
            }
        ]
    }

    # 5) Make the POST request to create a post
    try:
        # Construct the full API URL
        api_url = f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/?source=html"

        response = requests.post(
            url=api_url,
            headers=headers,
            json=post_data,
            timeout=30
        )

        # Log the request details for debugging
        logger.info(f"Request URL: {api_url}")
        logger.info(f"Request Headers: {headers}")
        logger.info(f"Response Status: {response.status_code}")
        logger.info(f"Response Content: {response.text}")

        response.raise_for_status()  # Raise an exception for 4xx/5xx errors

        # 6) Parse the response JSON
        created_post = response.json()
        logger.info(f"Ghost post created successfully: {created_post}")
        return created_post

    except requests.RequestException as re:
        logger.error(f"Request error creating Ghost post: {re}")
        logger.error(f"Response content: {getattr(re.response, 'text', 'No response content')}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

# ------------------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------------------
# if __name__ == "__main__":
#     try:
#         logger.info("Starting Ghost Admin API MCP server...")
#         mcp.run(transport="stdio")  # Using stdio for Cursor integration
#     except Exception as e:
#         logger.error(f"Error running Ghost Admin API MCP server: {e}")
#         raise

# ------------------------------------------------------------------------------
# Test section - uncomment to test post creation
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        # Sample HTML content with various formatting
        test_title = "Test Post: Getting Started with Ghost"
        test_html_content = """
        <h1>Welcome to My Ghost Blog!</h1>

        <p>This is a test post demonstrating various HTML formatting capabilities in Ghost.</p>

        <h2>Features Overview</h2>
        <ul>
            <li><strong>Bold text</strong> for emphasis</li>
            <li><em>Italic text</em> for subtle emphasis</li>
            <li>Regular paragraphs with <a href="https://ghost.org">links</a></li>
        </ul>

        <blockquote>
            <p>This is how blockquotes look in Ghost. Great for highlighting important quotes or notes.</p>
        </blockquote>

        <h3>Code Example</h3>
        <pre><code>print("Hello, Ghost!")</code></pre>

        <p>You can also add images:</p>
        <figure>
            <img src="https://aipodcast.ing/content/images/size/w600/2024/03/A_clean_minimalist_vector_logo_of_a_microphone_.png" alt="Sample image">
            <figcaption>A sample image caption</figcaption>
        </figure>
        """

        # Create the post
        logger.info("Creating test post...")
        result = create_ghost_post(
            title=test_title,
            html_content=test_html_content,
            status="published"  # Set to "published" if you want to publish immediately
        )

        logger.info(f"Post created successfully: {json.dumps(result, indent=2)}")

    except Exception as e:
        logger.error(f"Error in test: {e}")
        raise
