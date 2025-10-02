"""Gemini 2.5 Flash text generation service."""
import google.generativeai as genai
from typing import Dict, List
import os
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TextContent(BaseModel):
    hook: str
    captions: List[str]
    hashtags: List[str]
    alt_text: str
    recommended_aspect_ratio: str

def initialize_gemini():
    """Initialize Gemini with API key."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    genai.configure(api_key=api_key)
    return genai.GenerativeModel('gemini-2.0-flash-exp')

def generate_instagram_content(prompt: str, media_type: str = "image") -> TextContent:
    """Generate Instagram-optimized content using Gemini 2.5 Flash."""
    
    model = initialize_gemini()
    
    system_prompt = f"""You are an Instagram content creator. Generate engaging, platform-optimized content.

Generate content for: {media_type.upper()} POST
Original prompt: "{prompt}"

Requirements:
1. Hook (1 sentence, eye-catching, 100-150 chars)
2. Captions (3 variations, 500-1200 chars each, engaging tone)
3. Hashtags (15-25 hashtags, mix of popular and niche)
4. Alt text (descriptive, accessible, 125 chars max)
5. Recommended aspect ratio for the {media_type}

Guidelines:
- Use Instagram-friendly language (emojis, line breaks)
- Captions should encourage engagement
- Hashtags should be relevant and mixed popularity
- Alt text should describe visual elements
- Consider Instagram's algorithm preferences

Format your response as:
HOOK: [your hook]
CAPTION 1: [variation 1]
CAPTION 2: [variation 2] 
CAPTION 3: [variation 3]
HASHTAGS: [hashtag list separated by spaces]
ALT_TEXT: [descriptive alt text]
ASPECT_RATIO: [recommended ratio, e.g., "1:1" for square, "9:16" for story]"""

    try:
        response = model.generate_content(system_prompt)
        
        if not response.text:
            raise ValueError("No response generated from Gemini")
        
        # Parse the response
        content = parse_gemini_response(response.text)
        return content
        
    except Exception as e:
        raise ValueError(f"Error generating content: {str(e)}")

def parse_gemini_response(response_text: str) -> TextContent:
    """Parse Gemini response into structured content."""
    lines = response_text.strip().split('\n')
    
    content = {
        "hook": "",
        "captions": [],
        "hashtags": [],
        "alt_text": "",
        "recommended_aspect_ratio": "1:1"
    }
    
    for line in lines:
        if line.startswith("HOOK:"):
            content["hook"] = line.replace("HOOK:", "").strip()
        elif line.startswith("CAPTION"):
            caption = line.split(":", 1)[1].strip()
            content["captions"].append(caption)
        elif line.startswith("HASHTAGS:"):
            hashtag_text = line.replace("HASHTAGS:", "").strip()
            content["hashtags"] = [tag.strip() for tag in hashtag_text.split() if tag.strip()]
        elif line.startswith("ALT_TEXT:"):
            content["alt_text"] = line.replace("ALT_TEXT:", "").strip()
        elif line.startswith("ASPECT_RATIO:"):
            content["recommended_aspect_ratio"] = line.replace("ASPECT_RATIO:", "").strip()
    
    return TextContent(**content)
