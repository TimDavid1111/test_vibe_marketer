"""Imagen image generation service using Gemini API."""
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    # Fallback if the new google.genai is not available
    GENAI_AVAILABLE = False
    
from typing import Optional, Dict
import os
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ImageResult:
    def __init__(self, image_data: bytes, prompt_used: str, parameters: Dict):
        self.image_data = image_data
        self.prompt_used = prompt_used
        self.parameters = parameters

def initialize_gemini():
    """Initialize Gemini."""
    if not GENAI_AVAILABLE:
        raise ValueError("Imagen API not available - requires google.genai package")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    client = genai.Client(api_key=api_key)
    return client

def generate_instagram_image(
    prompt: str, 
    aspect_ratio: str = "1:1",
    style: str = "photographic"
) -> ImageResult:
    """Generate Instagram-optimized image using Imagen via Gemini API."""
    
    client = initialize_gemini()
    
    # Enhance prompt for Instagram (480 token limit)
    enhanced_prompt = f"{prompt}, Instagram style, {style} photography, high quality, professional lighting, social media optimized"
    
    try:
        # Configure generation parameters
        generation_config = types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=aspect_ratio,
            person_generation="allow_adult"
        )
        
        # Generate image using Imagen 4.0
        response = client.models.generate_images(
            model='imagen-4.0-generate-001',
            prompt=enhanced_prompt,
            config=generation_config
        )
        
        if not response.generated_images:
            raise ValueError("No image generated")
        
        # Get the first generated image
        generated_image = response.generated_images[0]
        
        # Convert to bytes - the image might already be in bytes format
        if hasattr(generated_image.image, 'image_bytes'):
            # If it has image_bytes attribute, use it directly
            img_bytes_raw = generated_image.image.image_bytes
        else:
            # Otherwise try PIL operations
            img_pil = generated_image.image
            img_bytes = io.BytesIO()
            img_pil.save(img_bytes)
            img_bytes_raw = img_bytes.getvalue()
        
        parameters = {
            "model": "imagen-4.0-generate-001",
            "aspect_ratio": aspect_ratio,
            "number_of_images": 1,
            "person_generation": "allow_adult"
        }
        
        return ImageResult(
            image_data=img_bytes_raw,
            prompt_used=enhanced_prompt,
            parameters=parameters
        )
        
    except Exception as e:
        raise ValueError(f"Error generating image: {str(e)}")

def generate_image_for_instagram_story(prompt: str) -> ImageResult:
    """Generate image optimized for Instagram Stories (9:16 aspect ratio)."""
    return generate_instagram_image(prompt, aspect_ratio="9:16", style="photographic")

def generate_image_for_instagram_feed(prompt: str) -> ImageResult:
    """Generate image optimized for Instagram Feed (1:1 //aspect ratio)."""
    return generate_instagram_image(prompt, aspect_ratio="1:1", style="photographic")