#!/usr/bin/env python3
"""
Vertex AI Image Generator

This module provides functionality to generate images using Google's Vertex AI service.
It uses the Imagen model to generate high-quality images from text descriptions.

Required Environment Variables:
    GOOGLE_APPLICATION_CREDENTIALS: Path to service account key JSON file
    GOOGLE_CLOUD_PROJECT: Your Google Cloud project ID
"""

import os
import logging
from typing import Optional, Dict, Union
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
from google.cloud import aiplatform
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VertexImageGenerator:
    """
    A class to handle image generation using Google's Vertex AI service.
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        model_name: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize the Vertex AI Image Generator.

        Args:
            project_id (str, optional): Google Cloud project ID. If not provided,
                                      will try to get from environment variable.
            location (str, optional): The location/region for Vertex AI services.
            model_name (str, optional): The model to use for image generation.
            credentials_path (str, optional): Path to service account credentials JSON.
        """
        # Load credentials from environment or parameters
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError(
                "Project ID must be provided either through constructor "
                "or GOOGLE_CLOUD_PROJECT environment variable"
            )

        # Set credentials path if provided
        if credentials_path:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

        # Check if credentials are set
        if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable must be set "
                "to the path of your service account key JSON file"
            )

        self.location = location or os.getenv("VERTEX_LOCATION", "us-central1")
        self.model_name = model_name or os.getenv("VERTEX_MODEL_NAME", "imagegeneration@002")

        logger.info(f"Initializing with project_id: {self.project_id}")
        logger.info(f"Using location: {self.location}")
        logger.info(f"Using model: {self.model_name}")

        self._init_vertex_ai()

    def _init_vertex_ai(self):
        """Initialize Vertex AI with project settings."""
        try:
            vertexai.init(
                project=self.project_id,
                location=self.location,
            )
            self.model = GenerativeModel(self.model_name)
            logger.info(f"Initialized Vertex AI with project {self.project_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {str(e)}")
            raise

    def generate_image(
        self,
        prompt: str,
        number_of_images: int = 1,
        safety_settings: Optional[Dict[str, str]] = None,
        save_path: Optional[str] = None
    ) -> Union[Image, str]:
        """
        Generate an image using the specified prompt.

        Args:
            prompt (str): Text description of the image to generate
            number_of_images (int): Number of images to generate (default: 1)
            safety_settings (dict, optional): Custom safety settings for image generation
            save_path (str, optional): Path to save the generated image

        Returns:
            Union[Image, str]: Generated image object or path to saved image
        """
        try:
            # Default safety settings if none provided
            if safety_settings is None:
                safety_settings = {
                    "hate": "block_medium",
                    "harassment": "block_medium",
                    "sexual": "block_medium",
                    "dangerous": "block_medium",
                }

            logger.info(f"Generating image with prompt: {prompt}")

            # Generate the image
            response = self.model.generate_images(
                prompt=prompt,
                number_of_images=number_of_images,
                safety_settings=safety_settings
            )

            if not response or not response.images:
                raise Exception("No image was generated")

            # Save image if path provided
            if save_path:
                # Ensure directory exists
                Path(os.path.dirname(save_path)).mkdir(parents=True, exist_ok=True)

                # Save the image
                with open(save_path, 'wb') as f:
                    f.write(response.images[0].image_bytes)
                logger.info(f"Image saved to: {save_path}")
                return save_path

            return response.images[0]

        except Exception as e:
            logger.error(f"Error generating image: {str(e)}")
            raise

def main():
    """Main function for testing the image generator."""
    try:
        # Create output directory if it doesn't exist
        output_dir = "generated_images"
        os.makedirs(output_dir, exist_ok=True)

        # Initialize generator
        generator = VertexImageGenerator()

        # Test prompt
        test_prompt = "A serene landscape with a mountain lake at sunset, digital art style"

        # Generate and save image
        output_path = os.path.join(output_dir, "test_image.png")
        result = generator.generate_image(
            prompt=test_prompt,
            save_path=output_path
        )

        print(f"Image generated and saved to: {result}")

    except Exception as e:
        print(f"Failed to generate image: {str(e)}")

if __name__ == "__main__":
    main()
