#!/bin/bash
# Run RAG system with Docker Compose

set -e

echo "🚀 Starting RAG System with Docker"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if .env.docker exists
if [ ! -f ".env.docker" ]; then
    echo "❌ .env.docker file not found!"
    echo "Please copy .env.docker and configure your API keys"
    exit 1
fi

# Check if API keys are configured
if grep -q "your_gemini_api_key_here" .env.docker; then
    echo "⚠️ Please configure your API keys in .env.docker before running"
    echo "Edit .env.docker and replace 'your_gemini_api_key_here' with your actual API key"
    exit 1
fi

# Start services
echo "🐳 Starting Docker containers..."
docker-compose up -d

echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check ChromaDB
if curl -f http://localhost:8001/api/v1/heartbeat > /dev/null 2>&1; then
    echo "✅ ChromaDB is healthy"
else
    echo "⚠️ ChromaDB is not responding yet"
fi

# Check RAG Agent
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ RAG Agent is healthy"
else
    echo "⚠️ RAG Agent is not responding yet"
fi

echo ""
echo "🎉 RAG System is starting up!"
echo "================================"
echo "📊 Service URLs:"
echo "   RAG API:    http://localhost:8000"
echo "   RAG Docs:   http://localhost:8000/docs"
echo "   ChromaDB:   http://localhost:8001"
echo "   Health:     http://localhost:8000/health"
echo ""
echo "📝 Useful commands:"
echo "   View logs:     docker-compose logs -f"
echo "   Stop services: docker-compose down"
echo "   Restart:       docker-compose restart"
echo ""
echo "🧪 Test the API:"
echo "curl -X POST http://localhost:8000/agent/chat \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"query\": \"What is machine learning?\"}'"