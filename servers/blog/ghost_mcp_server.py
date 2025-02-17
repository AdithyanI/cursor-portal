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

@mcp.tool()
def list_recent_posts(limit: int = 10) -> Dict:
    """
    List the most recent Ghost posts.

    Args:
        limit (int, optional): Number of posts to retrieve. Defaults to 10.

    Returns:
        Dict: List of recent posts with their IDs, titles, and status.
    """
    try:
        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        if not ghost_admin_api_url or not admin_api_key:
            raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

        # Generate JWT token
        token = generate_ghost_jwt(admin_api_key)
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0"
        }

        # Get recent posts
        logger.info(f"Fetching {limit} most recent posts...")
        posts_response = requests.get(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/?limit={limit}&order=created_at%20desc",
            headers=headers
        )
        posts_response.raise_for_status()
        posts_data = posts_response.json()

        if not posts_data.get("posts"):
            return {
                "content": [{
                    "type": "text",
                    "text": "No posts found"
                }]
            }

        # Format posts for display
        posts_list = []
        for post in posts_data["posts"]:
            posts_list.append({
                "id": post["id"],
                "title": post["title"],
                "status": post["status"],
                "created_at": post["created_at"],
                "url": post["url"]
            })

        # Create a nicely formatted response
        response_text = "Recent Ghost Posts:\n\n"
        for i, post in enumerate(posts_list, 1):
            response_text += f"{i}. Title: {post['title']}\n"
            response_text += f"   ID: {post['id']}\n"
            response_text += f"   Status: {post['status']}\n"
            response_text += f"   Created: {post['created_at']}\n"
            response_text += f"   URL: {post['url']}\n\n"

        return {
            "content": [{
                "type": "text",
                "text": response_text
            }],
            "posts": posts_list  # Include raw data for potential programmatic use
        }

    except Exception as e:
        logger.error(f"Error listing recent posts: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "isError": True
        }

@mcp.tool()
def edit_ghost_post(
    post_id: str, 
    title: str = None, 
    html_content: str = None, 
    status: str = None,
    video_id: str = None,
    video_position: str = "top"  # 'top' or 'bottom'
) -> Dict:
    """
    Edit an existing Ghost post and optionally add a video.

    Args:
        post_id (str): The ID of the post to edit.
        title (str, optional): New title for the post. If None, keeps existing title.
        html_content (str, optional): New HTML content for the post. If None, keeps existing content.
        status (str, optional): New status for the post. If None, keeps existing status.
                              Valid values: "draft", "published", "scheduled".
        video_id (str, optional): HeyGen video ID to embed in the post.
        video_position (str, optional): Where to add the video - 'top' or 'bottom'. Defaults to 'top'.

    Returns:
        Dict: The updated post object from Ghost Admin API.

    Example of working video embed HTML:
    ```html
    <!-- kg-card-begin: html -->
    <div class="kg-card kg-video-card" style="max-width: 400px; margin: 2em auto;">
        <video 
            src="https://your-ghost-domain/content/media/your-video.mp4"
            controls
            preload="metadata"
            playsinline
            style="width: 100%; height: auto;">
            Your browser does not support the video tag.
        </video>
    </div>
    <!-- kg-card-end: html -->
    ```

    Notes on video embedding:
    1. Use HTML card type instead of video card for better compatibility
    2. Include proper video attributes: controls, preload="metadata", playsinline
    3. Set container max-width and margin for centered, responsive layout
    4. Use width: 100% on video element for proper scaling
    5. Always upload video to Ghost media library first using upload_video_to_ghost()
    """
    try:
        logger.info(f"Starting to edit Ghost post {post_id}...")

        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        if not ghost_admin_api_url or not admin_api_key:
            raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

        # Generate JWT token
        token = generate_ghost_jwt(admin_api_key)
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0",
            "Content-Type": "application/json"
        }

        # First, get the current post data
        logger.info("Fetching current post data...")
        post_response = requests.get(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/{post_id}/",
            headers=headers
        )
        post_response.raise_for_status()
        current_post = post_response.json()["posts"][0]
        
        # If we have a video_id, upload it first
        video_ghost_url = None
        if video_id:
            logger.info(f"Processing video {video_id}...")
            
            # Use the new upload_video_to_ghost tool
            upload_result = upload_video_to_ghost(video_id)
            if "isError" in upload_result and upload_result["isError"]:
                raise ValueError(f"Failed to upload video: {upload_result['content'][0]['text']}")
            
            video_ghost_url = upload_result["video_url"]

            # Create a valid Lexical video card
            video_card = {
                "type": "video",
                "version": 1,
                "src": video_ghost_url,
                "width": "wide",
                "caption": None,
                "thumbnailSrc": None,
                "duration": None,
                "loop": False,
                "autoplay": False,
                "muted": False
            }

            # Get current lexical content
            current_lexical_str = current_post.get("lexical", "{}")
            try:
                current_lexical = json.loads(current_lexical_str)
            except Exception as e:
                logger.warning("Failed to parse existing lexical content, creating a new structure.")
                current_lexical = {}

            if not current_lexical.get("root"):
                current_lexical["root"] = {
                    "children": [],
                    "direction": None,
                    "format": "",
                    "indent": 0,
                    "type": "root",
                    "version": 1
                }

            existing_children = current_lexical["root"].get("children", [])
            if video_position.lower() == "top":
                new_children = [video_card] + existing_children
            else:
                new_children = existing_children + [video_card]

            current_lexical["root"]["children"] = new_children
            updated_content = current_lexical
            
            # Also update html_content if not provided
            if html_content is None:
                html_content = current_post.get("html", "")
            # Add a simple marker for the video in HTML
            video_marker = f'<figure class="kg-card kg-video-card kg-width-wide"><div class="kg-video-container"><video src="{video_ghost_url}" playsinline="true" controls="true"></video></div></figure>'
            if video_position.lower() == "top":
                html_content = video_marker + html_content
            else:
                html_content = html_content + video_marker
        else:
            # If no video, use existing lexical content
            updated_content = json.loads(current_post.get("lexical", "{}"))

        # Prepare update data, keeping existing values if not provided
        update_data = {
            "posts": [{
                "id": post_id,
                "title": title if title is not None else current_post["title"],
                "html": html_content if html_content is not None else current_post.get("html", ""),
                "status": status if status is not None else current_post["status"],
                "updated_at": current_post["updated_at"],
                "mobiledoc": None,  # Use lexical instead
                "lexical": json.dumps(updated_content)
            }]
        }

        # Log what we're updating
        changes = []
        if title is not None:
            changes.append(f"title: '{current_post['title']}' -> '{title}'")
        if html_content is not None:
            changes.append("html content updated")
        if status is not None:
            changes.append(f"status: '{current_post['status']}' -> '{status}'")
        if video_id is not None:
            changes.append(f"added video at {video_position}")
        logger.info(f"Updating post with changes: {', '.join(changes)}")

        # Make the update request
        update_response = requests.put(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/{post_id}/?source=html",
            headers=headers,
            json=update_data
        )
        update_response.raise_for_status()
        updated_post = update_response.json()

        # Create a summary of what was updated
        summary = f"Post {post_id} updated successfully:\n"
        if title is not None:
            summary += f"- Title changed to: {title}\n"
        if html_content is not None:
            summary += "- Content updated\n"
        if status is not None:
            summary += f"- Status changed to: {status}\n"
        if video_id is not None:
            summary += f"- Video added at {video_position}\n"
            summary += f"- Video URL: {video_ghost_url}\n"

        return {
            "content": [{
                "type": "text",
                "text": summary
            }],
            "post": updated_post["posts"][0]
        }

    except requests.exceptions.HTTPError as e:
        error_msg = (
            f"HTTP error occurred while editing post:\n"
            f"Status code: {e.response.status_code}\n"
            f"Response: {e.response.text}"
        )
        logger.error(error_msg)
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {error_msg}"
            }],
            "isError": True
        }
    except Exception as e:
        error_msg = f"Error editing Ghost post: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {error_msg}"
            }],
            "isError": True
        }

@mcp.tool()
def upload_base64_image(base64_image: str, image_name: str = "uploaded_image.jpg") -> Dict:
    """
    Upload a base64 encoded image to Ghost.

    Args:
        base64_image (str): Base64 encoded image data
        image_name (str, optional): Name for the uploaded image. Defaults to "uploaded_image.jpg"

    Returns:
        Dict: Response containing the uploaded image URL
    """
    try:
        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        if not ghost_admin_api_url or not admin_api_key:
            raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

        # Generate JWT token
        token = generate_ghost_jwt(admin_api_key)
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0"
        }

        # Define supported image types and their MIME types
        MIME_TYPES = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'svg': 'image/svg+xml',
            'tiff': 'image/tiff',
            'bmp': 'image/bmp',
            'ico': 'image/x-icon',
            'avif': 'image/avif'
        }

        # Prepare the image data
        if not base64_image.startswith('data:image/'):
            # Get file extension and convert to lowercase
            image_ext = image_name.split('.')[-1].lower() if '.' in image_name else 'jpg'
            
            # Get the appropriate MIME type
            mime_type = MIME_TYPES.get(image_ext, 'image/jpeg')  # Default to jpeg if unknown extension
            
            # Add the correct data URI prefix
            base64_image = f"data:{mime_type};base64,{base64_image}"
        else:
            # If it already has a data URI, validate the MIME type
            mime_type = base64_image.split(';')[0].split(':')[1]
            if mime_type not in MIME_TYPES.values():
                logger.warning(f"Unsupported MIME type: {mime_type}. Proceeding anyway as Ghost may support it.")

        # Upload image to Ghost
        upload_data = {
            "images": [{
                "file": base64_image,
                "ref": image_name
            }]
        }

        upload_response = requests.post(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/images/upload/",
            headers={**headers, "Content-Type": "application/json"},
            json=upload_data
        )
        upload_response.raise_for_status()
        
        result = upload_response.json()
        if 'images' in result and len(result['images']) > 0:
            return {
                "url": result['images'][0]['url'],
                "ref": image_name,
                "mime_type": mime_type
            }
        else:
            raise ValueError("No image URL in upload response")

    except Exception as e:
        logger.error(f"Error uploading base64 image: {e}")
        raise

@mcp.tool()
def upload_image_from_url(image_url: str, image_name: str = None) -> Dict:
    """
    Upload an image to Ghost from a URL.

    Args:
        image_url (str): URL of the image to upload
        image_name (str, optional): Name for the uploaded image. If None, extracted from URL.

    Returns:
        Dict: Response containing the uploaded image URL
    """
    try:
        # Download the image
        response = requests.get(image_url)
        response.raise_for_status()

        # Get image name from URL if not provided
        if not image_name:
            image_name = image_url.split('/')[-1]
            # If no extension in name, try to detect from content type
            if '.' not in image_name:
                content_type = response.headers.get('content-type', '').lower()
                if 'image/' in content_type:
                    ext = content_type.split('/')[-1]
                    if ext == 'jpeg':
                        ext = 'jpg'
                    image_name = f"downloaded_image.{ext}"
                else:
                    image_name = "downloaded_image.jpg"

        # Convert to base64
        base64_image = base64.b64encode(response.content).decode('utf-8')
        
        # Upload using the base64 upload function
        return upload_base64_image(base64_image, image_name)

    except Exception as e:
        logger.error(f"Error uploading image from URL: {e}")
        raise

@mcp.tool()
def upload_local_image(file_path: str, image_name: str = None) -> Dict:
    """
    Upload a local image file to Ghost.

    Args:
        file_path (str): Path to the local image file
        image_name (str, optional): Name for the uploaded image. If None, uses the original filename.

    Returns:
        Dict: Response containing the uploaded image URL
    """
    try:
        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        if not ghost_admin_api_url or not admin_api_key:
            raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

        # Generate JWT token
        token = generate_ghost_jwt(admin_api_key)
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0"
        }

        # Use original filename if image_name not provided
        if not image_name:
            image_name = os.path.basename(file_path)

        # Upload image using multipart form data
        with open(file_path, 'rb') as image_file:
            files = {
                'file': (image_name, image_file, 'image/png'),
                'purpose': (None, 'image')
            }
            
            upload_response = requests.post(
                f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/images/upload/",
                headers=headers,
                files=files
            )
            
            # Log response for debugging
            logger.info(f"Upload response status: {upload_response.status_code}")
            logger.info(f"Upload response headers: {dict(upload_response.headers)}")
            logger.info(f"Upload response content: {upload_response.text}")
            
            upload_response.raise_for_status()
            
            result = upload_response.json()
            if 'images' in result and len(result['images']) > 0:
                return {
                    "url": result['images'][0]['url'],
                    "ref": image_name
                }
            else:
                raise ValueError("No image URL in upload response")

    except Exception as e:
        logger.error(f"Error uploading local image: {e}")
        raise

@mcp.tool()
def add_image_to_post(
    post_id: str,
    image_url: str = None,
    base64_image: str = None,
    image_name: str = "blog_image.jpg",
    image_position: str = "top",
    image_caption: str = None
) -> Dict:
    """
    Add an image to an existing Ghost post. Can accept either a URL or base64 image data.
    Preserves all existing content while adding the new image.

    Args:
        post_id (str): ID of the post to add the image to
        image_url (str, optional): URL of the image to add
        base64_image (str, optional): Base64 encoded image data
        image_name (str, optional): Name for the image file. Defaults to "blog_image.jpg"
        image_position (str, optional): Where to add the image - 'top' or 'bottom'. Defaults to 'top'
        image_caption (str, optional): Caption to display under the image

    Returns:
        Dict: Response containing the updated post data
    """
    try:
        # Validate inputs
        if not image_url and not base64_image:
            raise ValueError("Either image_url or base64_image must be provided")
        if image_url and base64_image:
            raise ValueError("Only one of image_url or base64_image should be provided")

        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        if not ghost_admin_api_url or not admin_api_key:
            raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

        # Generate JWT token
        token = generate_ghost_jwt(admin_api_key)
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0",
            "Content-Type": "application/json"
        }

        # Get current post data
        post_response = requests.get(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/{post_id}/",
            headers=headers
        )
        post_response.raise_for_status()
        current_post = post_response.json()["posts"][0]

        # Upload the image
        if image_url:
            if image_url.startswith(('http://', 'https://')):
                upload_result = upload_image_from_url(image_url, image_name)
            else:
                # If it's a local file path
                upload_result = upload_local_image(image_url, image_name)
        else:
            upload_result = upload_base64_image(base64_image, image_name)

        image_ghost_url = upload_result['url']

        # Create image card
        image_card = {
            "type": "image",
            "version": 1,
            "src": image_ghost_url,
            "width": "wide",
            "caption": image_caption
        }

        # Get current content in Lexical format
        current_content = current_post.get("lexical", "{}")
        if isinstance(current_content, str):
            current_content = json.loads(current_content)
        
        # Ensure we have a valid root structure
        if not current_content.get("root"):
            current_content = {
                "root": {
                    "children": [],
                    "direction": None,
                    "format": "",
                    "indent": 0,
                    "type": "root",
                    "version": 1
                }
            }

        # Get existing children or initialize empty list
        existing_children = current_content.get("root", {}).get("children", [])

        # Create new content with image while preserving existing content
        if image_position.lower() == "top":
            new_children = [image_card] + existing_children
        else:  # bottom
            new_children = existing_children + [image_card]

        # Update the lexical content while preserving structure
        updated_content = {
            "root": {
                "children": new_children,
                "direction": current_content.get("root", {}).get("direction"),
                "format": current_content.get("root", {}).get("format", ""),
                "indent": current_content.get("root", {}).get("indent", 0),
                "type": "root",
                "version": 1
            }
        }

        # Update the post
        update_data = {
            "posts": [{
                "id": post_id,
                "updated_at": current_post["updated_at"],
                "title": current_post.get("title"),  # Preserve title
                "status": current_post.get("status"),  # Preserve status
                "mobiledoc": None,  # Use lexical instead
                "lexical": json.dumps(updated_content)
            }]
        }

        # Make the update request
        update_response = requests.put(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/{post_id}/?source=html",
            headers=headers,
            json=update_data
        )
        update_response.raise_for_status()
        updated_post = update_response.json()

        return {
            "content": [{
                "type": "text",
                "text": f"Image successfully added to post at {image_position}. Image URL: {image_ghost_url}"
            }],
            "post": updated_post["posts"][0]
        }

    except Exception as e:
        logger.error(f"Error adding image to post: {e}")
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "isError": True
        }

@mcp.tool()
def delete_ghost_post(post_id: str) -> Dict:
    """
    Delete a post from Ghost using the Admin API.

    Args:
        post_id (str): The ID of the post to delete.

    Returns:
        Dict: Response indicating success or failure of the deletion.
    """
    try:
        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        if not ghost_admin_api_url or not admin_api_key:
            raise ValueError("Missing GHOST_ADMIN_API_URL or GHOST_ADMIN_API_KEY environment variables.")

        # Generate JWT token
        token = generate_ghost_jwt(admin_api_key)
        headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0"
        }

        # First, verify the post exists and get its details
        logger.info(f"Verifying post {post_id} exists...")
        verify_response = requests.get(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/{post_id}/",
            headers=headers
        )
        verify_response.raise_for_status()
        post_details = verify_response.json()["posts"][0]

        # Delete the post
        logger.info(f"Deleting post {post_id}...")
        delete_response = requests.delete(
            f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/posts/{post_id}/",
            headers=headers
        )
        delete_response.raise_for_status()

        return {
            "content": [{
                "type": "text",
                "text": f"Successfully deleted post:\nTitle: {post_details['title']}\nID: {post_id}\nStatus: {post_details['status']}\nCreated: {post_details['created_at']}"
            }],
            "deleted_post": post_details
        }

    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP error occurred while deleting post:\nStatus code: {e.response.status_code}\nResponse: {e.response.text}"
        logger.error(error_msg)
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {error_msg}"
            }],
            "isError": True
        }
    except Exception as e:
        error_msg = f"Error deleting Ghost post: {str(e)}"
        logger.error(error_msg)
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {error_msg}"
            }],
            "isError": True
        }

@mcp.tool()
def upload_video_to_ghost(video_id: str) -> Dict:
    """
    Upload a HeyGen video to Ghost's media library.

    Args:
        video_id (str): The HeyGen video ID to upload.

    Returns:
        Dict: Response containing the uploaded video URL and details.
    """
    try:
        # Get Ghost credentials
        ghost_admin_api_url = os.environ.get("GHOST_ADMIN_API_URL")
        admin_api_key = os.environ.get("GHOST_ADMIN_API_KEY")
        heygen_api_key = os.environ.get("HEYGEN_API_KEY")
        
        if not all([ghost_admin_api_url, admin_api_key, heygen_api_key]):
            raise ValueError("Missing required environment variables")

        # Generate Ghost JWT token
        token = generate_ghost_jwt(admin_api_key)
        ghost_headers = {
            "Authorization": f"Ghost {token}",
            "Accept-Version": "v5.0"
        }

        # First get the video URL from HeyGen
        status_response = requests.get(
            f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
            headers={
                "X-Api-Key": heygen_api_key,
                "Accept": "application/json"
            }
        )
        status_response.raise_for_status()
        video_data = status_response.json()

        if video_data["data"]["status"] != "completed":
            raise ValueError(f"Video is not ready. Current status: {video_data['data']['status']}")

        video_url = video_data["data"]["video_url"]
        if not video_url:
            raise ValueError("Video URL not found in response")

        # Download the video
        logger.info("Downloading video from HeyGen...")
        video_response = requests.get(video_url)
        video_response.raise_for_status()

        # Create a temporary directory for video storage
        temp_dir = os.path.join(os.path.dirname(__file__), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_video_path = os.path.join(temp_dir, f"video_{video_id}.mp4")

        # Save video temporarily
        with open(temp_video_path, "wb") as f:
            f.write(video_response.content)

        # Upload to Ghost
        logger.info("Uploading video to Ghost...")
        with open(temp_video_path, "rb") as video_file:
            files = {
                "file": (f"video_{video_id}.mp4", video_file, "video/mp4"),
                "purpose": (None, "video")
            }
            upload_response = requests.post(
                f"{ghost_admin_api_url.rstrip('/')}/ghost/api/admin/media/upload/",
                headers=ghost_headers,
                files=files
            )
            upload_response.raise_for_status()
            upload_data = upload_response.json()

        # Clean up temporary file
        os.remove(temp_video_path)

        if 'media' in upload_data and len(upload_data['media']) > 0:
            ghost_video_url = upload_data['media'][0]['url']
            return {
                "content": [{
                    "type": "text",
                    "text": f"Video uploaded successfully to Ghost. URL: {ghost_video_url}"
                }],
                "video_url": ghost_video_url,
                "video_id": video_id
            }
        else:
            raise ValueError(f"No URL in upload response. Response data: {json.dumps(upload_data, indent=2)}")

    except Exception as e:
        logger.error(f"Error uploading video to Ghost: {str(e)}")
        return {
            "content": [{
                "type": "text",
                "text": f"Error: {str(e)}"
            }],
            "isError": True
        }

# ------------------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    try:
        logger.info("Starting Ghost Admin API MCP server...")
        mcp.run(transport="stdio")  # Using stdio for Cursor integration
    except Exception as e:
        logger.error(f"Error running Ghost Admin API MCP server: {e}")
        raise
