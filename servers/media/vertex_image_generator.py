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
from pathlib import Path
from dotenv import load_dotenv
import vertexai
from vertexai.preview.vision_models import ImageGenerationModel

# Load environment variables from .env file
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class VertexImageGenerator:
    """
    A class to handle image generation using Google's Vertex AI service.
    """

    def __init__(self):
        """Initialize the Vertex AI image generator with project and location settings."""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = "us-central1"
        self.model_name = "imagen-3.0-generate-002"
        vertexai.init(project=self.project_id, location=self.location)
        print(f"Initialized with project ID: {self.project_id}")
        print(f"Location: {self.location}")
        print(f"Model: {self.model_name}")

    def generate_image(self, prompt: str, output_file: str) -> str:
        """
        Generate an image using Vertex AI's image generation model and save it to a file.

        Args:
            prompt (str): The text prompt describing the desired image.
            output_file (str): Path where the generated image should be saved (relative to current directory).

        Returns:
            str: Path to the saved image file.
        """
        try:
            # Ensure output directory exists
            output_dir = os.path.dirname(output_file)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)

            # Generate the image
            model = ImageGenerationModel.from_pretrained(self.model_name)
            images = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                language="en",
                aspect_ratio="1:1",
                safety_filter_level="block_some",
                person_generation="allow_adult"
            )

            if not images:
                raise Exception("No image was generated")

            # Save the image
            images[0].save(location=output_file, include_generation_parameters=False)
            print(f"Created output image at: {output_file}")
            return output_file

        except Exception as e:
            print(f"Error generating image: {str(e)}")
            raise

if __name__ == "__main__":
    # Test the image generator
    generator = VertexImageGenerator()
    prompt = "A beautiful sunset over mountains"
    try:
        output_file = os.path.join("generated_images", "test_sunset.png")
        generator.generate_image(prompt, output_file)
        print("Successfully generated and saved the image!")
    except Exception as e:
        print(f"Failed to generate image: {e}")
