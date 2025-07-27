# 🤖 RAG AI Agent Setup with uv

## 🚀 **Quick Start with uv**

### 1. **Install Dependencies**
```bash
cd backend
uv sync
```

### 2. **Install Additional Tools**
```bash
# Install Playwright browsers for web scraping
uv run playwright install chromium

# Download spaCy language model (optional)
uv run python -m spacy download en_core_web_sm
```

### 3. **Set Up Environment**
```bash
# Configure API keys
uv run python setup_gemini_api.py

# OR manually create .env file
echo "GEMINI_API_KEY=your_gemini_api_key_here" >> .env
```

### 4. **Start RAG Agent**
```bash
# Option 1: Direct start
uv run python start_rag_agent.py

# Option 2: Using run script
./run.sh rag

# Option 3: Using server command
./run.sh server
```

## 🧪 **Testing the RAG System**

### Test New RAG Endpoints
```bash
# Test RAG chat endpoint
curl -X POST "http://localhost:8000/agent/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is artificial intelligence?",
    "use_web_search": true
  }'

# Test streaming chat
curl -X POST "http://localhost:8000/agent/stream" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Explain machine learning",
    "use_web_search": false
  }'
```

### Test Legacy Compatibility
```bash
# Test legacy enhanced research (works with existing frontend)
curl -X POST "http://localhost:8000/research/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is deep learning?",
    "max_sources": 3
  }'
```

### Test Knowledge Management
```bash
# Add documents to knowledge base
curl -X POST "http://localhost:8000/knowledge/add" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {
        "title": "AI Overview",
        "content": "Artificial Intelligence is...",
        "url": "https://example.com/ai"
      }
    ],
    "source": "manual"
  }'

# Get knowledge base stats
curl "http://localhost:8000/knowledge/stats"
```

## 🔧 **Development Commands with uv**

### Run Tests
```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_rag_agent.py

# Run with coverage
uv run pytest --cov=src
```

### Development Tools
```bash
# Format code
uv run black src/
uv run isort src/

# Type checking
uv run mypy src/

# Linting
uv run flake8 src/
```

### Database Management
```bash
# Reset vector database (use with caution!)
uv run python -c "
from src.infrastructure.vector_database.chroma_client import ChromaVectorStore
store = ChromaVectorStore()
store.reset_collection()
print('Vector database reset!')
"

# Check database stats
uv run python -c "
from src.infrastructure.vector_database.chroma_client import ChromaVectorStore
store = ChromaVectorStore()
stats = store.get_collection_stats()
print(f'Documents: {stats.get(\"document_count\", 0)}')
"
```

### Populate Knowledge Base
```bash
# Create a script to populate knowledge base
uv run python tools/populate_knowledge_base.py

# Add web content to knowledge base
uv run python -c "
import asyncio
from src.agent.rag_agent import RAGAgent

async def add_web_content():
    agent = RAGAgent()
    docs = [
        {
            'title': 'Python Documentation',
            'content': 'Python is a programming language...',
            'url': 'https://docs.python.org'
        }
    ]
    await agent.add_knowledge(docs, source='web')
    print('Added web content to knowledge base!')

asyncio.run(add_web_content())
"
```

## 🐳 **Docker with uv**

### Build Docker Image
```bash
# Create Dockerfile that uses uv
cat > Dockerfile.rag << 'EOF'
FROM python:3.11-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies with uv
RUN uv sync --frozen

# Install Playwright browsers
RUN uv run playwright install chromium

# Expose port
EXPOSE 8000

# Start RAG agent
CMD ["uv", "run", "python", "start_rag_agent.py"]
EOF

# Build image
docker build -f Dockerfile.rag -t rag-agent .

# Run container
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key rag-agent
```

## 📊 **Monitoring with uv**

### Performance Monitoring
```bash
# Monitor memory usage
uv run python -c "
import psutil
import time
from src.agent.rag_agent import RAGAgent

agent = RAGAgent()
process = psutil.Process()

print(f'Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB')
print(f'Vector DB stats: {agent.vector_store.get_collection_stats()}')
"

# Benchmark RAG performance
uv run python tools/benchmark_rag.py
```

### Health Checks
```bash
# Check all components
uv run python -c "
import asyncio
from src.agent.rag_agent import RAGAgent

async def health_check():
    try:
        agent = RAGAgent()
        status = agent.get_agent_status()
        print('🤖 RAG Agent Status:')
        for key, value in status.items():
            print(f'   {key}: {value}')
    except Exception as e:
        print(f'❌ Health check failed: {e}')

asyncio.run(health_check())
"
```

## 🔄 **Migration from Old System**

### Migrate Existing Data
```bash
# Export data from old system (if needed)
uv run python tools/export_old_data.py

# Import into new RAG system
uv run python tools/import_to_rag.py
```

### Update Frontend Integration
The RAG system maintains backward compatibility with existing frontend through legacy endpoints:
- `/research/enhanced` → Maps to RAG agent
- `/research/quick` → Maps to RAG agent (fast mode)
- `/research/status` → Returns RAG agent status

## 🎯 **Production Deployment with uv**

### Environment Setup
```bash
# Production environment
export ENVIRONMENT=production
export GEMINI_API_KEY=your_production_key
export REDIS_URL=redis://localhost:6379
export VECTOR_DB_PATH=/data/vector_store

# Start with production settings
uv run python start_rag_agent.py
```

### Process Management
```bash
# Using systemd service
sudo tee /etc/systemd/system/rag-agent.service << 'EOF'
[Unit]
Description=RAG AI Agent
After=network.target

[Service]
Type=simple
User=raguser
WorkingDirectory=/opt/rag-agent/backend
ExecStart=/usr/local/bin/uv run python start_rag_agent.py
Restart=always
Environment=GEMINI_API_KEY=your_key

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable rag-agent
sudo systemctl start rag-agent
```

## 🎉 **All uv Commands Summary**

```bash
# Setup
uv sync                                    # Install dependencies
uv run playwright install chromium        # Install browsers
uv run python setup_gemini_api.py        # Setup API keys

# Development
uv run python start_rag_agent.py         # Start RAG agent
uv run pytest                            # Run tests
uv run black src/                        # Format code

# Database
uv run python tools/populate_kb.py       # Populate knowledge base
uv run python tools/backup_data.py       # Backup data

# Monitoring
uv run python tools/benchmark_rag.py     # Performance tests
uv run python tools/health_check.py      # Health monitoring
```

The RAG system is now fully integrated with `uv` for fast, reliable dependency management and execution! 🚀