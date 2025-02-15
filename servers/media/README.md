# Vertex AI Image Generator

This service provides image generation capabilities using Google's Vertex AI platform.

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set up Google Cloud credentials:
   - Create a service account in your Google Cloud project
   - Download the JSON key file
   - Set environment variables:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

3. Enable required Google Cloud APIs:
   - Vertex AI API
   - Cloud Storage API

## Usage

### Basic Usage

```python
from vertex_image_generator import VertexImageGenerator

# Initialize the generator
generator = VertexImageGenerator()

# Generate an image
result = generator.generate_image(
    prompt="Your image description here",
    save_path="output/image.png"
)
```

### Test the Generator

Run the script directly to test:

```bash
python vertex_image_generator.py
```

This will generate a test image and save it in the `generated_images` directory.

## Features

- Text-to-image generation using Vertex AI
- Customizable safety settings
- Multiple image generation
- Automatic file saving
- Environment variable configuration
- Detailed logging

## Directory Structure

```
media/
├── vertex_image_generator.py  # Main image generation module
├── requirements.txt          # Python dependencies
├── README.md                # This file
└── generated_images/        # Default output directory
```

## Error Handling

The service includes comprehensive error handling and logging:

- Initialization errors
- API errors
- File system errors
- Configuration errors

## Safety Settings

Default safety settings are set to "block_medium" for:

- Hate content
- Harassment
- Sexual content
- Dangerous content

These can be customized when calling `generate_image()`.
