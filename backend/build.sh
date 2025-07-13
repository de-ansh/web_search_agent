#!/bin/bash

# Railway Backend Build Script
set -e

echo "🚀 Starting backend build for Railway..."

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv for package management..."
    pip install uv
    uv sync --frozen || pip install -r requirements.txt
else
    echo "Using pip for package management..."
    pip install --upgrade pip
    pip install -r requirements.txt
fi

# Install Playwright and browsers
echo "🎭 Installing Playwright and browsers..."
playwright install chromium
playwright install-deps

echo "✅ Backend build completed successfully!"

# Railway deployment
cd backend
railway login
railway init
railway variables set OPENAI_API_KEY="your-key"
railway variables set PORT="8000"
railway deploy