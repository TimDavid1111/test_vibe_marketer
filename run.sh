#!/bin/bash

# Instagram AI Content Generator - Startup Script

echo "🚀 Starting Instagram AI Content Generator..."

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Please copy env.example to .env and add your API keys."
    echo "   cp env.example .env"
    exit 1
fi

# Install dependencies if needed
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Create data directory
mkdir -p data/media

# Start backend in background
echo "🌐 Starting FastAPI backend..."
python3 start_backend.py &
BACKEND_PID=$!

# Wait a moment for backend to start
sleep 3

# Start Streamlit frontend
echo "🎨 Starting Streamlit frontend..."
echo "📱 Streamlit will open in your browser at: http://localhost:8501"
echo "📡 Backend API docs at: http://localhost:8000/docs"
echo ""
echo "❌ Press Ctrl+C to stop both servers"

streamlit run streamlit_app.py --server.port 8501

# Cleanup when stopping
echo "🛑 Shutting down..."
kill $BACKEND_PID 2>/dev/null
echo "✅ All servers stopped"
