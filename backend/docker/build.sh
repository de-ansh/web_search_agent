#!/bin/bash
# Build Docker images for RAG system

set -e

echo "🐳 Building RAG System Docker Images"
echo "===================================="

# Check if .env.docker exists
if [ ! -f ".env.docker" ]; then
    echo "❌ .env.docker file not found!"
    echo "Please copy .env.docker.example to .env.docker and configure your API keys"
    exit 1
fi

# Build ChromaDB image
echo "📦 Building ChromaDB image..."
docker build -f docker/Dockerfile.chromadb -t rag-chromadb:latest .

# Build RAG Agent image
echo "🤖 Building RAG Agent image..."
docker build -f docker/Dockerfile.rag -t rag-agent:latest .

echo "✅ Docker images built successfully!"
echo ""
echo "Next steps:"
echo "1. Configure your API keys in .env.docker"
echo "2. Run: docker-compose up -d"
echo "3. Access RAG API at: http://localhost:8000"
echo "4. Access ChromaDB at: http://localhost:8001"