#!/usr/bin/env python3
"""
Image Generation MCP Server

This module provides an MCP server interface for generating images from text descriptions.
"""

import os
import base64
import logging
from typing import Optional
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
from vertex_image_generator import VertexImageGenerator

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastMCP server instance
mcp = FastMCP(
    "Image Generation Server",
    capabilities={
        "tools": {
            "listChanged": True
        }
    }
)

# Initialize the image generator
generator = VertexImageGenerator()

@mcp.tool()
def generate_image_from_text(prompt: str, save_to_file: Optional[str] = None) -> dict:
    """
    Generate an image based on a text description.

    Args:
        prompt (str): Text description of the image you want to generate.
        save_to_file (str, optional): Path where the generated image should be saved.
                                     If not provided, returns the image data directly.

    Returns:
        dict: A dictionary containing either:
            - {"file_path": str} if save_to_file was provided
            - {"image_data": str} if save_to_file was not provided (base64 encoded)

    Example:
        >>> generate_image_from_text(
        ...     prompt="A beautiful sunset over mountains",
        ...     save_to_file="generated_images/sunset.png"
        ... )
    """
    try:
        logger.info(f"Generating image for prompt: {prompt}")

        if save_to_file:
            # Generate and save to file
            file_path = generator.generate_image(prompt, save_to_file)
            logger.info(f"Image saved to: {file_path}")
            return {"file_path": file_path}
        else:
            # Get image data and convert to base64
            image_bytes = generator.generate_image(prompt)
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            logger.info("Image generated successfully")
            return {"image_data": image_base64}

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        raise

if __name__ == "__main__":
    try:
        logger.info("Starting Image Generation server...")
        mcp.run(transport="stdio")
    except Exception as e:
        logger.error(f"Error running Image Generation server: {e}")
        raise
