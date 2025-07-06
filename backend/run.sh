#!/bin/bash

# Web Search Agent Backend Startup Script
echo "🚀 Starting Web Search Agent Backend..."

# Set the working directory to the backend folder
cd "$(dirname "$0")"

# Set PYTHONPATH to current directory
export PYTHONPATH="$(pwd)"

echo "📁 Working directory: $(pwd)"
echo "🐍 Python path: $PYTHONPATH"
echo "🌐 Server will be available at: http://localhost:8000"
echo "=" * 50

# Start the server
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload 