# Instagram AI Content Generator

An AI-powered tool that generates Instagram-ready content using Google's Gemini models. Generate captions, hashtags, images, and videos optimized for Instagram with just a prompt.

## Features

### Phase 1 - Content Generation & Preview

- ✨ **Text Generation**: Create engaging captions, hooks, and hashtags using Gemini 2.5 Flash
- 🖼️ **Image Generation**: Generate Instagram-quality images using Google's Imagen model
- 🎥 **Video Generation**: Create short videos using Veo 3 (placeholder implementation)
- 📱 **Instagram Optimization**: Content tailored for Instagram's algorithm and constraints
- 👀 **Live Preview**: See your generated content before downloading
- 💾 **Export Options**: Download media files and content metadata

### Phase 2 - Auto-Posting (Coming Soon)

- 🔐 **OAuth Integration**: Secure Instagram account connection
- ⏰ **Scheduling**: Schedule posts for optimal engagement times
- 📤 **Auto-Posting**: Automatically publish to Instagram via API
- 📊 **Job Management**: Track posting status and history

## Setup Instructions

### Prerequisites

- Python 3.10+
- Google AI API access (Gemini, Imagen, Veo 3)
- Google Cloud Platform account with Vertex AI enabled

### Installation

1. **Clone the repository**

```bash
git clone <repository-url>
cd test_vibe_marketer
```

2. **Install dependencies**

```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

```bash
cp env.example .env
```

Edit `.env` with your API keys:

```bash
# Google AI Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service_account.json
GCP_PROJECT=your_gcp_project_id

# Optional: Google Cloud Storage
GCS_BUCKET=your_bucket_name

# Backend Configuration
BACKEND_BASE_URL=http://localhost:8000
```

### Running the Application

#### Option 1: Manual Startup (Recommended for Development)

1. **Start the FastAPI backend**

```bash
cd /Users/timdavid/Desktop/Desktop/test_vibe_marketer
python -m uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

2. **Start the Streamlit frontend** (in a new terminal)

```bash
cd /Users/timdavid/Desktop/Desktop/test_vibe_marketer
streamlit run streamlit_app.py --server.port 8501
```

#### Option 2: Using Docker (Optional)

```bash
docker-compose up
```

## Usage

### Generating Content

1. **Open the Streamlit app** at `http://localhost:8501`
2. **Configure your content** in the sidebar:
   - Select media type (image or video)
   - Choose aspect ratio
   - Pick a style
   - Set duration (for videos)
3. **Enter your prompt** describing what you want to create
4. **Click "Generate Content"** and wait for AI to create your post
5. **Review the preview** of generated content
6. **Download** your media files and content data

### Content Structure

The generator creates Instagram-optimized content with:

- **Hook**: Eye-catching opening line
- **Captions**: Multiple variations (500-1200 characters)
- **Hashtags**: 15-25 relevant tags (mix of popular and niche)
- **Alt Text**: Accessible descriptions for images
- **Media**: High-quality image or video

## API Endpoints

The FastAPI backend provides these endpoints:

- `POST /api/generate/text` - Generate text content only
- `POST /api/generate/image` - Generate image only
- `POST /api/generate/video` - Generate video only
- `POST /api/generate/all` - Generate complete content package
- `GET /media/{filename}` - Serve generated media files
- `GET /api/jobs` - List all generation jobs
- `GET /health` - Health check

## Architecture

```
┌─────────────────┐    HTTP     ┌─────────────────┐
│   Streamlit UI  │ ────────── │   FastAPI App   │
│                 │            │                 │
│ - Prompt Input  │            │ - Gemini AI     │
│ - Preview       │            │ - Imagen        │
│ - Download      │            │ - Veo 3         │
└─────────────────┘            │ - Media Storage │
                               │ - SQLite DB     │
                               └─────────────────┘
                                        │
                               ┌─────────────────┐
                               │   Google APIs   │
                               │                 │
                               │ - Gemini 2.5    │
                               │ - Imagen       │
                               │ - Veo 3         │
                               └─────────────────┘
```

## Development Status

### ✅ Completed (Phase 1)

- [x] FastAPI backend setup
- [x] Gemini 2.5 Flash text generation
- [x] Imagen image generation
- [x] Veo 3 video generation (placeholder)
- [x] Streamlit UI
- [x] Media storage and serving
- [x] Content preview and download

### 🚧 In Progress (Phase 2)

- [ ] Meta/Facebook OAuth integration
- [ ] Instagram Graph API posting
- [ ] Job scheduling and management
- [ ] Auto-posting workflow

## Troubleshooting

### Common Issues

**"GOOGLE_API_KEY environment variable is required"**

- Make sure your `.env` file is in the project root
- Check that `GOOGLE_API_KEY` is set correctly
- Verify your API key has access to Gemini models

**"No image generated"**

- Check your Google Cloud Project setup
- Ensure Vertex AI is enabled in your GCP project
- Verify your service account has the necessary permissions

**Backend connection errors**

- Make sure the FastAPI server is running on port 8000
- Check that the backend URL in Streamlit matches your setup

**Media files not loading**

- Ensure the `data/media/` directory exists
- Check file permissions
- Verify the media files were generated successfully

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions:

- Check the troubleshooting section above
- Open an issue on GitHub
- Contact the development tam

---

**Happy posting! 📱✨**
