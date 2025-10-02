"""APScheduler for Instagram posting automation."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from sqlmodel import Session, create_engine
from datetime import datetime
from typing import Optional
import asyncio
import httpx
import os

# Import our classes
from .instagram_api import InstagramAPI
from .db import GenerationJob, JobStatus

# Scheduler configuration
jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///data/scheduler.db')
}
executors = {
    'default': AsyncIOExecutor(),
}
job_defaults = {
    'coalesce': False,
    'max_instances': 3,
    'misfire_grace_time': 30
}

scheduler = AsyncIOScheduler(
    jobstores=jobstores,
    executors=executors,
    job_defaults=job_defaults
)

# Database engine
engine = create_engine("sqlite:///data/app.db")

async def execute_instagram_post(job_id: int):
    """Execute Instagram post for a scheduled job."""
    print(f"🚀 Executing Instagram post job {job_id}")
    
    try:
        with Session(engine) as session:
            # Get job from database
            job = session.query(GenerationJob).filter(GenerationJob.id == job_id).first()
            if not job:
                print(f"❌ Job {job_id} not found")
                return
            
            if job.status != JobStatus.PENDING:
                print(f"⚠️ Job {job_id} not in pending status: {job.status}")
                return
            
            # Update job status
            job.status = JobStatus.RUNNING
            session.commit()
            
            try:
                # Get user's access token
                from db import User
                user = session.query(User).filter(User.id == job.user_id).first()
                if not user:
                    raise Exception(f"User not found for job {job_id}")
                
                # Create Instagram API client
                instagram_api = InstagramAPI(user.access_token)
                
                # Get media URL (make sure it's publicly accessible)
                media_url = job.media_url
                if not media_url.startswith('http'):
                    # If it's a relative URL, make it absolute
                    backend_url = os.getenv("BACKEND_BASE_URL", "http://localhost:8000")
                    media_url = f"{backend_url}{job.media_url}"
                
                # Combine caption and hashtags
                full_caption = f"{job.caption}\n\n{job.hashtags}"
                
                # Create Instagram post
                if job.media_type.value == "image":
                    container_response = await instagram_api.create_image_container(
                        ig_user_id=user.instagram_user_id,
                        image_url=media_url,
                        caption=full_caption,
                        is_published=False
                    )
                else:  # video
                    container_response = await instagram_api.create_video_container(
                        ig_user_id=user.instagram_user_id,
                        media_type="VIDEO",
                        video_url=media_url,
                        caption=full_caption,
                        is_published=False
                    )
                
                creation_id = container_response.get("id")
                if not creation_id:
                    raise Exception("Failed to create Instagram container")
                
                # Publish the post
                publish_response = await instagram_api.publish_post(
                    ig_user_id=user.instagram_user_id,
                    creation_id=creation_id
                )
                
                instagram_post_id = publish_response.get("id")
                
                # Update job status
                job.status = JobStatus.COMPLETED
                job.instagram_post_id = instagram_post_id
                session.commit()
                
                print(f"✅ Successfully posted to Instagram: {instagram_post_id}")
                
            except Exception as e:
                # Update job status to failed
                job.status = JobStatus.FAILED
                session.commit()
                print(f"❌ Failed to post job {job_id}: {str(e)}")
                
    except Exception as e:
        print(f"💥 Critical error executing job {job_id}: {str(e)}")

async def execute_post_at_scheduled_time(job_id: int, scheduled_time: datetime):
    """Schedule a post at a specific time."""
    scheduler.add_job(
        execute_instagram_post,
        'date',
        run_date=scheduled_time,
        args=[job_id],
        id=f"ig_post_{job_id}",
        replace_existing=True
    )
    print(f"📅 Scheduled job {job_id} for {scheduled_time}")

def start_scheduler():
    """Start the scheduler."""
    if not scheduler.running:
        scheduler.start()
        print("🔧 Instagram posting scheduler started")

def stop_scheduler():
    """Stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        print("🛑 Instagram posting scheduler stopped")

async def cancel_job(job_id: int):
    """Cancel a scheduled job."""
    job_id_str = f"ig_post_{job_id}"
    try:
        scheduler.remove_job(job_id_str)
        print(f"🚫 Cancelled job {job_id}")
    except Exception as e:
        print(f"❌ Failed to cancel job {job_id}: {str(e)}")

def list_scheduled_jobs():
    """List all scheduled jobs."""
    jobs = scheduler.get_jobs()
    return [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "func": job.func.__name__ if job.func else "unknown"
        }
        for job in jobs
    ]
