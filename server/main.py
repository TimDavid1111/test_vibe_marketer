"""FastAPI main application with generation endpoints."""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import our services
from .services.text import generate_instagram_content
from .services.image import generate_instagram_image, generate_image_for_instagram_feed, generate_image_for_instagram_story
from .services.video import generate_instagram_video, generate_video_for_instagram_stories
from .storage import save_media
from .db import create_db_and_tables, GenerationJob, JobStatus, MediaType, User
from sqlmodel import Session, create_engine
from datetime import datetime, timedelta
from fastapi import Request
from .instagram_api import InstagramAPI, MetaOAuth, InstagramAPIError
from .scheduler import scheduler, execute_post_at_scheduled_time, start_scheduler, stop_scheduler

# Pydantic models for requests/responses
class GenerateTextRequest(BaseModel):
    prompt: str
    media_type: str = "image"

class GenerateImageRequest(BaseModel):
    prompt: str
    aspect_ratio: str = "1:1"
    style: str = "photographic"

class GenerateVideoRequest(BaseModel):
    prompt: str
    duration: int = 5
    aspect_ratio: str = "9:16"
    style: str = "realistic"

class GenerateAllRequest(BaseModel):
    prompt: str
    media_type: str = "image"
    aspect_ratio: str = "1:1"
    duration: Optional[int] = 5
    style: str = "photographic"

class SchedulePostRequest(BaseModel):
    prompt: str
    media_type: str
    caption: str
    hashtags: str
    media_url: str
    scheduled_at: datetime
    instagram_user_id: str

class GenerationResponse(BaseModel):
    success: bool
    content: Optional[dict] = None
    error: Optional[str] = None

# Initialize FastAPI app
app = FastAPI(title="IG AI Content Generator", version="1.0.0")

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
engine = create_engine("sqlite:///data/app.db", echo=True)

@app.on_event("startup")
async def startup_event():
    """Initialize database and scheduler on startup."""
    Path("data").mkdir(exist_ok=True)
    create_db_and_tables()
    start_scheduler()
    print("🚀 Instagram AI Content Generator backend started")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown."""
    stop_scheduler()
    print("👋 Instagram AI Content Generator backend stopped")

# Utility route to serve generated media
@app.get("/media/{filename}")
async def serve_media(filename: str):
    """Serve generated media files."""
    media_path = Path("data") / "media" / filename
    if media_path.exists():
        return FileResponse(media_path)
    raise HTTPException(status_code=404, detail="File not found")

# Generation endpoints
@app.post("/api/generate/text", response_model=GenerationResponse)
async def generate_text(request: GenerateTextRequest):
    """Generate Instagram text content using Gemini 2.5 Flash."""
    try:
        content = generate_instagram_content(request.prompt, request.media_type)
        
        return GenerationResponse(
            success=True,
            content={
                "hook": content.hook,
                "captions": content.captions,
                "hashtags": content.hashtags,
                "alt_text": content.alt_text,
                "recommended_aspect_ratio": content.recommended_aspect_ratio
            }
        )
    except Exception as e:
        return GenerationResponse(success=False, error=str(e))

@app.post("/api/generate/image", response_model=GenerationResponse)
async def generate_image(request: GenerateImageRequest):
    """Generate Instagram image using Imagen."""
    try:
        result = generate_instagram_image(
            request.prompt,
            request.aspect_ratio,
            request.style
        )
        
        # Save image to storage
        _, media_url = await save_media(
            result.image_data,
            extension=".jpg"
        )
        
        return GenerationResponse(
            success=True,
            content={
                "image_url": media_url,
                "prompt_used": result.prompt_used,
                "parameters": result.parameters
            }
        )
    except Exception as e:
        return GenerationResponse(success=False, error=str(e))

@app.post("/api/generate/video", response_model=GenerationResponse)
async def generate_video(request: GenerateVideoRequest):
    """Generate Instagram video using Veo 3."""
    try:
        result = generate_instagram_video(
            request.prompt,
            request.duration,
            request.aspect_ratio,
            request.style
        )
        
        # Save video to storage
        _, media_url = await save_media(
            result.video_data,
            extension=".mp4"
        )
        
        return GenerationResponse(
            success=True,
            content={
                "video_url": media_url,
                "prompt_used": result.prompt_used,
                "parameters": result.parameters
            }
        )
    except Exception as e:
        return GenerationResponse(success=False, error=str(e))

@app.post("/api/generate/all", response_model=GenerationResponse)
async def generate_all(request: GenerateAllRequest):
    """Generate complete Instagram content (text + media)."""
    try:
        # Generate text content
        text_content = generate_instagram_content(request.prompt, request.media_type)
        
        # Generate media based on type
        media_url = None
        media_metadata = None
        
        if request.media_type == "image":
            result = generate_instagram_image(
                request.prompt,
                request.aspect_ratio,
                request.style
            )
            _, media_url = await save_media(result.image_data, extension=".jpg")
            media_metadata = {
                "type": "image",
                "prompt_used": result.prompt_used,
                "parameters": result.parameters
            }
        elif request.media_type == "video":
            duration = request.duration or 5
            result = generate_instagram_video(
                request.prompt,
                duration,
                request.aspect_ratio,
                request.style
            )
            _, media_url = await save_media(result.video_data, extension=".mp4")
            media_metadata = {
                "type": "video",
                "prompt_used": result.prompt_used,
                "parameters": result.parameters
            }
        
        # Store in database
        with Session(engine) as session:
            # Get caption safely
            caption = text_content.captions[0] if text_content.captions else text_content.hook
            hashtags_text = " ".join(text_content.hashtags) if text_content.hashtags else ""
            
            job = GenerationJob(
                prompt=request.prompt,
                media_type=MediaType(request.media_type),
                caption=caption,
                hashtags=hashtags_text,
                media_url=media_url,
                status=JobStatus.COMPLETED
            )
            session.add(job)
            session.commit()
        
        return GenerationResponse(
            success=True,
            content={
                "text": {
                    "hook": text_content.hook,
                    "captions": text_content.captions,
                    "hashtags": text_content.hashtags,
                    "alt_text": text_content.alt_text,
                    "recommended_aspect_ratio": text_content.recommended_aspect_ratio
                },
                "media": {
                    "url": media_url,
                    "metadata": media_metadata
                }
            }
        )
    except Exception as e:
        return GenerationResponse(success=False, error=str(e))

@app.get("/api/jobs")
async def list_jobs():
    """List all generation jobs."""
    try:
        with Session(engine) as session:
            jobs = session.query(GenerationJob).all()
            return {"jobs": [
                {
                    "id": job.id,
                    "prompt": job.prompt,
                    "media_type": job.media_type,
                    "caption": job.caption,
                    "hashtags": job.hashtags,
                    "media_url": job.media_url,
                    "status": job.status,
                    "created_at": job.created_at.isoformat(),
                    "instagram_post_id": job.instagram_post_id
                }
                for job in jobs
            ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# OAuth and Instagram posting endpoints
@app.get("/oauth/meta/login")
async def start_meta_oauth():
    """Start Meta OAuth flow."""
    app_id = os.getenv("META_APP_ID")
    app_secret = os.getenv("META_APP_SECRET")
    redirect_uri = os.getenv("META_REDIRECT_URI", "http://localhost:8000/oauth/meta/callback")
    
    if not app_id or not app_secret:
        raise HTTPException(status_code=500, detail="Meta app credentials not configured")
    
    oauth = MetaOAuth(app_id, app_secret, redirect_uri)
    auth_url = oauth.get_auth_url()
    
    return {"auth_url": auth_url}

@app.get("/oauth/meta/callback")
async def handle_meta_callback(request: Request):
    """Handle Meta OAuth callback."""
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")
    
    try:
        app_id = os.getenv("META_APP_ID")
        app_secret = os.getenv("META_APP_SECRET")
        redirect_uri = os.getenv("META_REDIRECT_URI", "http://localhost:8000/oauth/meta/callback")
        
        oauth = MetaOAuth(app_id, app_secret, redirect_uri)
        
        # Exchange code for token
        token_response = await oauth.exchange_code_for_token(code)
        access_token = token_response.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get long-lived token
        long_token_response = await oauth.get_long_lived_token(access_token)
        long_lived_token = long_token_response.get("access_token")
        
        # Get Instagram user info
        instagram_api = InstagramAPI(long_lived_token)
        user_info = await instagram_api.get_user_info()
        instagram_user_id = user_info.get("id")
        
        if not instagram_user_id:
            raise HTTPException(status_code=400, detail="Could not retrieve Instagram user ID")
        
        # Store user info in database
        with Session(engine) as session:
            existing_user = session.query(User).filter(User.instagram_user_id == instagram_user_id).first()
            
            if existing_user:
                existing_user.access_token = long_lived_token
                existing_user.token_expires_at = datetime.utcnow() + timedelta(days=60)
            else:
                user = User(
                    instagram_user_id=instagram_user_id,
                    access_token=long_lived_token,
                    token_expires_at=datetime.utcnow() + timedelta(days=60)
                )
                session.add(user)
            
            session.commit()
        
        return {"status": "success", "instagram_user_id": instagram_user_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/schedule-post")
async def schedule_post(request: SchedulePostRequest):
    """Schedule a post to Instagram."""
    try:
        with Session(engine) as session:
            # Find user
            user = session.query(User).filter(User.instagram_user_id == request.instagram_user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="Instagram user not found")
            
            # Create job
            job = GenerationJob(
                user_id=user.id,
                prompt=request.prompt,
                media_type=MediaType(request.media_type),
                caption=request.caption,
                hashtags=request.hashtags,
                media_url=request.media_url,
                scheduled_at=request.scheduled_at,
                status=JobStatus.PENDING
            )
            session.add(job)
            session.commit()
            
            # Add to scheduler
            await execute_post_at_scheduled_time(job.id, request.scheduled_at)
            
            return {"status": "success", "job_id": job.id}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/publish-now")
async def publish_now(request: SchedulePostRequest):
    """Publish post immediately to Instagram."""
    try:
        # Set scheduled_at to now
        request.scheduled_at = datetime.utcnow()
        
        # Schedule the post
        result = await schedule_post(request)
        
        # TODO: Execute immediately or add to queue
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
