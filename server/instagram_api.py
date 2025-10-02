"""Instagram Graph API client for posting content."""
import httpx
import os
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio

class InstagramAPIError(Exception):
    """Custom exception for Instagram API errors."""
    pass

class InstagramAPI:
    """Client for Instagram Graph API operations."""
    
    BASE_URL = "https://graph.facebook.com/v21.0"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_params = {"access_token": access_token}
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to Instagram Graph API."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        request_params = {**self.base_params}
        if params:
            request_params.update(params)
        
        async with httpx.AsyncClient() as client:
            if method.upper() == "GET":
                response = await client.get(url, params=request_params)
            elif method.upper() == "POST":
                response = await client.post(url, params=request_params, data=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code != 200:
                raise InstagramAPIError(f"API request failed: {response.text}")
            
            return response.json()
    
    async def get_user_info(self) -> Dict[str, Any]:
        """Get Instagram user information."""
        return await self._make_request("GET", "me")
    
    async def get_accounts(self) -> Dict[str, Any]:
        """Get Instagram accounts."""
        return await self._make_request("GET", "me/accounts")
    
    async def create_image_container(
        self,
        ig_user_id: str,
        image_url: str,
        caption: str,
        is_published: bool = False
    ) -> Dict[str, Any]:
        """Create Instagram image post container."""
        data = {
            "image_url": image_url,
            "caption": caption,
            "access_token": self.access_token,
            "published": is_published
        }
        
        return await self._make_request("POST", f"{ig_user_id}/media", data=data)
    
    async def create_video_container(
        self,
        ig_user_id: str,
        media_type: str,
        video_url: Optional[str] = None,
        caption: Optional[str] = None,
        is_published: bool = False
    ) -> Dict[str, Any]:
        """Create Instagram video post container."""
        data = {
            "media_type": media_type,
            "access_token": self.access_token,
            "published": is_published
        }
        
        if video_url:
            data["video_url"] = video_url
        if caption:
            data["caption"] = caption
            
        return await self._make_request("POST", f"{ig_user_id}/media", data=data)
    
    async def publish_post(self, ig_user_id: str, creation_id: str) -> Dict[str, Any]:
        """Publish Instagram post."""
        data = {
            "creation_id": creation_id,
            "access_token": self.access_token
        }
        
        return await self._make_request("POST", f"{ig_user_id}/media_publish", data=data)
    
    async def check_status(self, og_container_id: str) -> Dict[str, Any]:
        """Check status of uploaded video."""
        return await self._make_request("GET", og_container_id)
    
    async def upload_video_resumable(
        self,
        video_file_path: str,
        ig_user_id: str,
        caption: str
    ) -> Dict[str, Any]:
        """Upload video using resumable upload (simplified version)."""
        # This is a simplified implementation
        # In production, you'd implement the full resumable upload protocol
        
        # Step 1: Initialize upload session
        init_data = {
            "file_size": os.path.getsize(video_file_path),
            "access_token": self.access_token
        }
        
        init_response = await self._make_request(
            "POST", 
            f"{ig_user_id}/media",
            data=init_data
        )
        
        upload_session_id = init_response.get("upload_session_id")
        if not upload_session_id:
            raise InstagramAPIError("Failed to initialize upload session")
        
        # Step 2: Upload chunks (simplified - in reality you'd implement proper chunking)
        chunk_data = {
            "upload_session_id": upload_session_id,
            "start_offset": 0,
            "access_token": self.access_token
        }
        
        # In a real implementation, you'd upload the file in chunks
        # For now, we'll create a container with video_url instead
        video_data = {
            "media_type": "VIDEO",
            "caption": caption,
            "is_carousel_item": False,
            "access_token": self.access_token
        }
        
        return await self._make_request("POST", f"{ig_user_id}/media", data=video_data)

class MetaOAuth:
    """Facebook/Meta OAuth implementation."""
    
    BASE_URL = "https://www.facebook.com/v21.0/dialog/oauth"
    TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"
    
    def __init__(self, app_id: str, app_secret: str, redirect_uri: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
    
    def get_auth_url(self, state: Optional[str] = None) -> str:
        """Generate Facebook OAuth authorization URL."""
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": "instagram_basic,pages_show_list,pages_read_engagement,instagram_content_publish",
            "response_type": "code"
        }
        
        if state:
            params["state"] = state
            
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.BASE_URL}?{param_string}"
    
    async def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """Exchange authorization code for access token."""
        data = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(self.TOKEN_URL, data=data)
            
            if response.status_code != 200:
                raise InstagramAPIError(f"Token exchange failed: {response.text}")
            
            return response.json()
    
    async def get_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Exchange short-lived token for long-lived token."""
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(self.TOKEN_URL, params=params)
            
            if response.status_code != 200:
                raise InstagramAPIError(f"Long-lived token request failed: {response.text}")
            
            return response.json()
