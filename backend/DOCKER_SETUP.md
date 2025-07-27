# 🐳 Docker Setup for RAG System with ChromaDB

## 📋 **Overview**

This Docker setup provides a complete containerized RAG (Retrieval Augmented Generation) system with:
- **ChromaDB**: Vector database for document storage and similarity search
- **RAG Agent**: FastAPI server with Gemini LLM integration
- **Redis**: Caching layer (optional)
- **Nginx**: Reverse proxy and load balancer (optional)

## 🚀 **Quick Start**

### **1. Prerequisites**
- Docker and Docker Compose installed
- Your API keys ready (Gemini, OpenAI, HuggingFace)

### **2. Setup Environment**
```bash
# Copy and configure environment file
cp .env.docker.example .env.docker

# Edit with your API keys
nano .env.docker
```

### **3. Build and Run**
```bash
# Build Docker images
./docker/build.sh

# Start all services
./docker/run.sh

# Or manually with docker-compose
docker-compose up -d
```

### **4. Access Services**
- **RAG API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ChromaDB**: http://localhost:8001
- **Health Check**: http://localhost:8000/health

## 🏗️ **Architecture**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Nginx       │    │   RAG Agent     │    │    ChromaDB     │
│  (Port 80/443)  │────│   (Port 8000)   │────│   (Port 8001)   │
│  Load Balancer  │    │   FastAPI API   │    │  Vector Database│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │     Redis       │
                       │   (Port 6379)   │
                       │   Cache Layer   │
                       └─────────────────┘
```

## 📦 **Services**

### **ChromaDB Container**
- **Image**: Custom built from `docker/Dockerfile.chromadb`
- **Port**: 8001 (external) → 8000 (internal)
- **Data**: Persistent volume `chromadb_data`
- **Health Check**: `/api/v1/heartbeat`

### **RAG Agent Container**
- **Image**: Custom built from `docker/Dockerfile.rag`
- **Port**: 8000 (external) → 8000 (internal)
- **Data**: Persistent volume `rag_data`
- **Health Check**: `/health`

### **Redis Container** (Optional)
- **Image**: `redis:7-alpine`
- **Port**: 6379
- **Data**: Persistent volume `redis_data`

### **Nginx Container** (Optional)
- **Image**: `nginx:alpine`
- **Ports**: 80, 443
- **Config**: `docker/nginx.conf`

## 🔧 **Configuration**

### **Environment Variables (.env.docker)**
```bash
# Required API Keys
GEMINI_API_KEY=your_actual_gemini_key
HUGGINGFACE_API_KEY=your_actual_hf_key

# ChromaDB Settings
CHROMA_HOST=chromadb
CHROMA_PORT=8000
VECTOR_STORE_PATH=/app/data/vector_store

# RAG Configuration
MAX_CONTEXT_DOCS=5
SIMILARITY_THRESHOLD=0.8
EMBEDDING_MODEL=all-MiniLM-L6-v2
```

### **Docker Compose Override**
Create `docker-compose.override.yml` for custom configurations:
```yaml
version: '3.8'
services:
  rag-agent:
    environment:
      - DEBUG=true
      - LOG_LEVEL=debug
    volumes:
      - ./custom_data:/app/custom_data
```

## 🛠️ **Development**

### **Local Development with Docker**
```bash
# Start only ChromaDB
docker-compose up chromadb -d

# Run RAG agent locally
export CHROMA_HOST=localhost
export CHROMA_PORT=8001
uv run python start_rag_agent.py
```

### **Debugging**
```bash
# View logs
docker-compose logs -f rag-agent
docker-compose logs -f chromadb

# Execute commands in container
docker-compose exec rag-agent bash
docker-compose exec chromadb bash

# Check container health
docker-compose ps
```

## 📊 **Monitoring**

### **Health Checks**
```bash
# RAG Agent health
curl http://localhost:8000/health

# ChromaDB health
curl http://localhost:8001/api/v1/heartbeat

# Knowledge base stats
curl http://localhost:8000/knowledge/stats
```

### **Logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f rag-agent

# Follow new logs
docker-compose logs -f --tail=100
```

## 🔒 **Security**

### **Production Considerations**
1. **API Keys**: Use Docker secrets or external key management
2. **Network**: Use custom networks and restrict access
3. **SSL/TLS**: Configure HTTPS with proper certificates
4. **Authentication**: Add API authentication
5. **Rate Limiting**: Configure Nginx rate limiting

### **Secure Environment Setup**
```bash
# Use Docker secrets
echo "your_api_key" | docker secret create gemini_api_key -

# Reference in compose file
services:
  rag-agent:
    secrets:
      - gemini_api_key
```

## 🚀 **Deployment**

### **Production Deployment**
```bash
# Build for production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy with production config
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### **Scaling**
```bash
# Scale RAG agents
docker-compose up -d --scale rag-agent=3

# Use load balancer
docker-compose up -d nginx
```

## 🧪 **Testing**

### **API Testing**
```bash
# Test basic query
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}'

# Test with web search
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "Latest AI developments", "use_web_search": true}'
```

### **Load Testing**
```bash
# Install hey (HTTP load testing tool)
go install github.com/rakyll/hey@latest

# Load test
hey -n 100 -c 10 -m POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' \
  http://localhost:8000/agent/chat
```

## 📝 **Maintenance**

### **Backup**
```bash
# Backup ChromaDB data
docker run --rm -v chromadb_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/chromadb_backup.tar.gz -C /data .

# Backup RAG data
docker run --rm -v rag_data:/data -v $(pwd):/backup alpine \
  tar czf /backup/rag_backup.tar.gz -C /data .
```

### **Updates**
```bash
# Update images
docker-compose pull

# Rebuild custom images
./docker/build.sh

# Rolling update
docker-compose up -d --no-deps rag-agent
```

### **Cleanup**
```bash
# Stop and remove containers
docker-compose down

# Remove volumes (⚠️ This deletes data!)
docker-compose down -v

# Clean up unused images
docker system prune -a
```

## 🎯 **Performance Tuning**

### **ChromaDB Optimization**
- Adjust batch sizes for bulk operations
- Configure memory limits
- Use SSD storage for better performance

### **RAG Agent Optimization**
- Tune embedding model size vs. accuracy
- Adjust context window size
- Configure caching strategies

### **Resource Limits**
```yaml
services:
  rag-agent:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

## 🆘 **Troubleshooting**

### **Common Issues**

1. **ChromaDB Connection Failed**
   ```bash
   # Check if ChromaDB is running
   docker-compose ps chromadb
   
   # Check logs
   docker-compose logs chromadb
   ```

2. **API Key Not Found**
   ```bash
   # Verify environment file
   cat .env.docker | grep GEMINI_API_KEY
   
   # Check container environment
   docker-compose exec rag-agent env | grep GEMINI
   ```

3. **Out of Memory**
   ```bash
   # Check resource usage
   docker stats
   
   # Increase memory limits
   # Edit docker-compose.yml
   ```

4. **Port Conflicts**
   ```bash
   # Check what's using the port
   lsof -i :8000
   
   # Change ports in docker-compose.yml
   ```

## 📚 **Additional Resources**

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Nginx Configuration](https://nginx.org/en/docs/)

---

**Your RAG system is now fully containerized and production-ready!** 🎉