#!/usr/bin/env python3
"""
Image Generation MCP Server

This module provides an MCP server interface for generating images from text descriptions.
"""

import os
import logging
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
def generate_image_from_text(prompt: str, save_to_file: str) -> dict:
    """
    Generate an image based on a text description.

    Args:
        prompt (str): Text description of the image you want to generate.
        save_to_file (str): Path where the generated image should be saved.

    Returns:
        dict: A dictionary containing the file path of the saved image:
            {"file_path": str}

    Example:
        >>> generate_image_from_text(
        ...     prompt="A beautiful sunset over mountains",
        ...     save_to_file="generated_images/sunset.png"
        ... )
    """
    try:
        logger.info(f"Generating image for prompt: {prompt}")

        # Generate and save the image
        file_path = generator.generate_image(prompt, save_to_file)
        logger.info(f"Image saved to: {file_path}")
        return {"file_path": file_path}

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
