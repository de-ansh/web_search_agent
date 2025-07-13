#!/bin/bash

# 🚀 Render Deployment Script
# This script helps deploy the Web Search Agent to Render

echo "🌟 Render Deployment for Web Search Agent"
echo "========================================="

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Not in a git repository. Please run this from the project root."
    exit 1
fi

# Check if required files exist
echo "🔍 Checking required files..."

required_files=(
    "render.yaml"
    "backend/requirements-render.txt"
    "backend/src/api/main_render.py"
    "backend/src/core/lightweight_scraper.py"
    "frontend/package.json"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Required file missing: $file"
        exit 1
    fi
done

echo "✅ All required files found"

# Stage all changes
echo "📦 Staging changes for deployment..."
git add .

# Check if there are any changes to commit
if git diff --cached --exit-code > /dev/null; then
    echo "ℹ️  No changes to commit"
else
    echo "📝 Committing changes..."
    git commit -m "feat: Add Render deployment configuration with lightweight scraper

- Add requirements-render.txt with lightweight dependencies
- Add main_render.py for Render-specific API
- Add lightweight_scraper.py for requests-only scraping
- Update render.yaml with optimized configuration
- Add comprehensive troubleshooting guide"
fi

# Push to origin
echo "🚀 Pushing to GitHub..."
git push origin main

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub"
else
    echo "❌ Failed to push to GitHub"
    exit 1
fi

echo ""
echo "🎉 Deployment Preparation Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Go to https://render.com"
echo "2. Connect your GitHub repository"
echo "3. Render will automatically detect render.yaml"
echo "4. Both backend and frontend will be deployed"
echo ""
echo "🔧 If deployment fails, check RENDER_TROUBLESHOOTING.md"
echo ""
echo "Manual deployment option:"
echo "- Backend: Python web service"
echo "- Frontend: Node.js web service"
echo "- Use the configuration from render.yaml"
echo ""
echo "🔑 Don't forget to set your OpenAI API key in Render dashboard!"
echo "   Environment → Add OPENAI_API_KEY → Deploy"
echo ""
echo "🌐 Once deployed, your app will be available at:"
echo "   - Backend: https://your-backend-name.onrender.com"
echo "   - Frontend: https://your-frontend-name.onrender.com"
echo ""
echo "🎯 Happy deploying! 🚀" 