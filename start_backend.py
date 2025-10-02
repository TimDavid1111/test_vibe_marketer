#!/usr/bin/env python3
"""Simple script to start the FastAPI backend."""
import uvicorn
import os
from pathlib import Path

# Set working directory to project root
os.chdir(Path(__file__).parent)

if __name__ == "__main__":
    print("🚀 Starting Instagram AI Content Generator Backend...")
    print("📡 Server will be available at: http://localhost:8000")
    print("📊 API docs will be available at: http://localhost:8000/docs")
    print("❌ Press Ctrl+C to stop the server")
    
    import subprocess
    import sys
    
    # Try to run with python3 first
    try:
        subprocess.run([sys.executable, "-m", "uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"], check=True)
    except subprocess.CalledProcessError:
        # Fallback to uvicorn.run
        uvicorn.run(
            "server.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
