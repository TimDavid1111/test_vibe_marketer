"""Streamlit UI for Instagram AI Content Generator."""
import streamlit as st
import requests
import json
from datetime import datetime, timedelta
import base64

# Configuration
BACKEND_URL = "http://localhost:8000"

st.set_page_config(
    page_title="Instagram AI Content Generator",
    page_icon="📱",
    layout="wide"
)

st.title("📱 Instagram AI Content Generator")
st.markdown("Generate Instagram-ready content with AI using Gemini models")

# Sidebar configuration
st.sidebar.header("Configuration")
media_type = st.sidebar.selectbox(
    "Media Type",
    ["image", "video"],
    index=0,
    help="Choose whether to generate an image or video"
)

if media_type == "image":
    aspect_ratio = st.sidebar.selectbox(
        "Aspect Ratio",
        ["1:1", "4:5", "9:16"],
        index=0,
        help="Choose aspect ratio for the image"
    )
    duration = None
elif media_type == "video":
    aspect_ratio = st.sidebar.selectbox(
        "Aspect Ratio",
        ["9:16", "16:9", "1:1"],
        index=0,
        help="Choose aspect ratio for the video"
    )
    duration = st.sidebar.slider(
        "Duration (seconds)",
        min_value=5,
        max_value=60,
        value=15,
        help="Video duration in seconds"
    )

style = st.sidebar.selectbox(
    "Style",
    ["photographic", "artistic", "minimalist", "vibrant"],
    index=0,
    help="Choose the visual style"
)

# Main content area
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Input")
    
    # Prompt input
    prompt = st.text_area(
        "Describe your Instagram content:",
        placeholder="e.g., 'A beautiful sunset over the mountains, peaceful and inspiring'",
        height=100,
        help="Describe what you want to create for your Instagram post"
    )
    
    # Generate button
    if st.button("🚀 Generate Content", type="primary", use_container_width=True):
        if not prompt.strip():
            st.error("Please enter a prompt!")
        else:
            # Show loading spinner
            with st.spinner("Generating your Instagram content..."):
                try:
                    # Prepare request payload
                    payload = {
                        "prompt": prompt,
                        "media_type": media_type,
                        "aspect_ratio": aspect_ratio,
                        "style": style
                    }
                    
                    if duration:
                        payload["duration"] = duration
                    
                    # Call backend API
                    response = requests.post(
                        f"{BACKEND_URL}/api/generate/all",
                        json=payload,
                        timeout=60
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data["success"]:
                            st.success("Content generated successfully!")
                            st.session_state.content = data["content"]
                        else:
                            st.error(f"Error: {data['error']}")
                    else:
                        st.error(f"Request failed with status {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to connect to backend: {str(e)}")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

with col2:
    st.header("👀 Preview")
    
    # Display generated content
    if "content" in st.session_state:
        content = st.session_state.content
        
        # Display media (image or video)
        if content["media"]["url"]:
            media_url = f"{BACKEND_URL}{content['media']['url']}"
            
            if media_type == "image":
                st.image(media_url, caption="Generated Image")
            else:
                st.video(media_url)
            
            # Download button for media
            st.download_button(
                label=f"Download {media_type.title()}",
                data=requests.get(media_url).content,
                file_name=f"ig_{media_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{'jpg' if media_type == 'image' else 'mp4'}",
                mime=f"image/jpeg" if media_type == "image" else "video/mp4"
            )
        
        # Display text content
        st.subheader("📝 Caption Options")
        
        captions = content["text"]["captions"]
        selected_caption_idx = st.selectbox(
            "Choose caption variant:",
            range(len(captions)),
            format_func=lambda i: f"Caption {i+1} ({len(captions[i])} chars)"
        )
        
        selected_caption = captions[selected_caption_idx]
        
        # Show selected caption in a nice format
        st.info(selected_caption)
        
        # Copy caption to clipboard (requires JavaScript)
        st.button("📋 Copy Caption to Clipboard")
        
        # Display hashtags
        st.subheader("#️⃣ Hashtags")
        hashtags_text = " ".join(content["text"]["hashtags"])
        st.text(hashtags_text)
        
        # Copy hashtags
        st.button("📋 Copy Hashtags to Clipboard")
        
        # Display hook
        st.subheader("🎯 Hook")
        st.success(content["text"]["hook"])
        
        # Display alt text
        st.subheader("♿ Alt Text")
        st.text(content["text"]["alt_text"])
        
        # Schedule and Posting section
        st.subheader("📱 Instagram Posting")
        
        # OAuth connection (Phase 2)
        col_auth1, col_auth2 = st.columns([1, 1])
        
        with col_auth1:
            if st.button("🔗 Connect Instagram Account", disabled=True):
                try:
                    response = requests.get(f"{BACKEND_URL}/oauth/meta/login")
                    if response.status_code == 200:
                        auth_url = response.json()["auth_url"]
                        st.info(f"Redirect to: {auth_url}")
                        st.markdown(f"🔐 **[Click here to connect your Instagram account]({auth_url})**")
                    else:
                        st.error("Failed to initiate OAuth")
                except:
                    st.error("Could not connect to backend")
        
        with col_auth2:
            st.info("📋 Meta app credentials needed in .env")
        
        # Scheduling interface (placeholder for now)
        st.subheader("⏰ Schedule Post")
        
        col_schedule1, col_schedule2 = st.columns([1, 1])
        
        with col_schedule1:
            schedule_enabled = st.checkbox("Enable scheduling", value=False)
            
            if schedule_enabled:
                scheduled_time = st.datetime_input(
                    "Schedule post for:",
                    value=datetime.now() + timedelta(hours=1),
                    min_value=datetime.now()
                )
        
        with col_schedule2:
            if schedule_enabled:
                if st.button("📅 Schedule Post", disabled=True):
                    st.info("📌 Instagram scheduling will be available after Meta app migration (Phase 2)")
        
        # Auto-post controls
        st.subheader("🚀 Instant Post")
        
        col_post1, col_post2 = st.columns([1, 1])
        
        with col_post1:
            if st.button("📤 Post Now", disabled=True):
                st.info("📌 Auto-posting will be available after Meta app migration (Phase 2)")
        
        with col_post2:
            st.info("🔐 Instagram API access required")
        
        # Save to file
        content_to_save = {
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "media_type": media_type,
            "caption": selected_caption,
            "hashtags": hashtags_text,
            "hook": content["text"]["hook"],
            "alt_text": content["text"]["alt_text"],
            "media_url": content["media"]["url"]
        }
        
        st.download_button(
            label="💾 Download Content JSON",
            data=json.dumps(content_to_save, indent=2),
            file_name=f"ig_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )

    else:
        st.info("👆 Enter a prompt and click 'Generate Content' to see your Instagram post!")

# Footer
st.markdown("---")
st.markdown("💡 This tool uses Google's Gemini models to generate Instagram-optimized content")

# Debug information
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.write("Backend URL:", BACKEND_URL)
    if "content" in st.session_state:
        st.sidebar.json(st.session_state.content)
