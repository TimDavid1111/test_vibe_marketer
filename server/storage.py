"""Media storage and serving utilities."""
import os
import uuid
from pathlib import Path
from typing import Tuple, Optional
import aiofiles

DATA_DIR = Path("data")
MEDIA_DIR = DATA_DIR / "media"

async def save_media(content: bytes, filename: Optional[str] = None, extension: str = ".jpg") -> Tuple[str, str]:
    """Save media content to local storage and return the path and URL."""
    if not MEDIA_DIR.exists():
        MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    
    if filename is None:
        filename = f"{uuid.uuid4()}{extension}"
    
    filepath = MEDIA_DIR / filename
    
    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)
    
    # Return both the file path and URL
    url = f"/media/{filename}"
    return str(filepath), url
