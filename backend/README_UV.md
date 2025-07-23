# Enhanced Web Scraping with uv

This guide shows how to run the enhanced web scraping application using `uv`, a fast Python package manager.

## 🚀 Quick Start

### 1. Install uv (if not already installed)

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -c "irm https://astral.sh/uv/install.sh | iex"

# Or visit: https://docs.astral.sh/uv/getting-started/installation/
```

### 2. Complete Setup and Run

```bash
cd backend
./run.sh all
```

This will:
- Install all dependencies
- Set up Playwright browsers
- Configure API keys
- Run tests
- Start the server

## 📋 Available Commands

### Using the Shell Script (Recommended)

```bash
# Set up environment
./run.sh setup

# Configure API keys
./run.sh keys

# Run tests
./run.sh test

# Start server
./run.sh server

# Run examples
./run.sh example

# Do everything at once
./run.sh all
```

### Using Python Script

```bash
# Set up environment
uv run python run_with_uv.py setup

# Configure API keys
uv run python run_with_uv.py keys

# Run tests
uv run python run_with_uv.py test

# Start server
uv run python run_with_uv.py server

# Do everything
uv run python run_with_uv.py all
```

### Direct uv Commands

```bash
# Install dependencies
uv sync

# Start the server
uv run uvicorn src.api.main:app --reload

# Run tests
uv run python test_enhanced_research.py

# Set up API keys
uv run python setup_gemini_api.py

# Run examples
uv run python example_usage.py
```

## 🔧 Configuration

### API Keys Setup

The application supports multiple AI providers:

1. **Gemini AI** (Recommended)
   - Get your key at: https://makersuite.google.com/app/apikey
   - Free tier available

2. **OpenAI** (Fallback)
   - Get your key at: https://platform.openai.com/api-keys
   - Paid service

3. **Extractive** (No API required)
   - Rule-based summarization
   - Works offline

### Environment Variables

Create a `.env` file in the backend directory:

```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here  # Optional
```

## 🎯 Usage Examples

### 1. Start the Server

```bash
cd backend
./run.sh server
```

Server will be available at:
- 🌐 **Main API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs
- 🔍 **Enhanced Research**: http://localhost:8000/research/enhanced

### 2. Test the Enhanced Features

```bash
./run.sh test
```

### 3. Run Usage Examples

```bash
./run.sh example
```

### 4. API Requests

#### Enhanced Research
```bash
curl -X POST "http://localhost:8000/research/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence trends 2024",
    "max_sources": 5,
    "summary_length": 150,
    "use_playwright": true,
    "ai_method": "gemini"
  }'
```

#### Quick Research
```bash
curl -X POST "http://localhost:8000/research/quick" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python web scraping best practices",
    "max_sources": 3,
    "ai_method": "gemini"
  }'
```

## 🏗️ Project Structure

```
backend/
├── src/
│   ├── api/                 # FastAPI endpoints
│   ├── services/            # Enhanced research service
│   ├── ai/                  # AI summarization (Gemini, OpenAI)
│   ├── core/                # Web scraping components
│   └── agents/              # Legacy agents
├── pyproject.toml           # uv configuration
├── run.sh                   # Shell runner script
├── run_with_uv.py          # Python runner script
├── setup_gemini_api.py     # API key setup
├── test_enhanced_research.py # Test suite
└── example_usage.py        # Usage examples
```

## 🔍 API Endpoints

### Enhanced Research Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/research/enhanced` | POST | Comprehensive research with AI |
| `/research/quick` | POST | Fast research with fewer sources |
| `/research/status` | GET | Service status and capabilities |

### Legacy Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/search` | POST | Original search with validation |
| `/search/fast` | POST | Fast search mode |
| `/health` | GET | Health check |
| `/stats` | GET | System statistics |

## 🚦 Development Workflow

### 1. Initial Setup
```bash
cd backend
./run.sh setup
./run.sh keys
```

### 2. Development
```bash
# Start development server with auto-reload
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests during development
uv run python test_enhanced_research.py

# Test specific features
uv run python -c "
from src.services.enhanced_research_service import EnhancedResearchService
import asyncio

async def test():
    service = EnhancedResearchService()
    result = await service.quick_research('Python async programming')
    print(result.combined_summary)

asyncio.run(test())
"
```

### 3. Testing
```bash
# Run all tests
./run.sh test

# Test API endpoints
./run.sh example

# Manual testing
uv run python -m pytest  # If you add pytest tests
```

## 🔧 Troubleshooting

### Common Issues

#### 1. uv not found
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your terminal
```

#### 2. Playwright browsers not installed
```bash
uv run playwright install chromium
```

#### 3. API key issues
```bash
# Reconfigure API keys
./run.sh keys

# Test API keys
uv run python setup_gemini_api.py
```

#### 4. Import errors
```bash
# Reinstall dependencies
uv sync --reinstall
```

#### 5. Port already in use
```bash
# Use different port
uv run uvicorn src.api.main:app --reload --port 8001
```

### Debug Mode

```bash
# Run with debug logging
PYTHONPATH=. uv run python -c "
import logging
logging.basicConfig(level=logging.DEBUG)

from src.services.enhanced_research_service import EnhancedResearchService
import asyncio

async def debug_test():
    service = EnhancedResearchService()
    result = await service.research_query('test query')
    print(result)

asyncio.run(debug_test())
"
```

## 📊 Performance

### uv Benefits
- **Fast installs**: 10-100x faster than pip
- **Reliable resolution**: Better dependency management
- **Cross-platform**: Works on macOS, Linux, Windows
- **Lock files**: Reproducible environments

### Typical Performance
- **Setup time**: 30-60 seconds (vs 5-10 minutes with pip)
- **Server start**: 2-3 seconds
- **Enhanced research**: 8-15 seconds for 5 sources
- **Quick research**: 3-6 seconds for 3 sources

## 🎉 Next Steps

1. **Start developing**: `./run.sh server`
2. **Integrate with your app**: Use the API endpoints
3. **Customize**: Modify parameters in the service
4. **Scale**: Deploy with Docker or cloud platforms
5. **Extend**: Add new AI providers or scraping methods

## 📞 Support

- **Test installation**: `./run.sh test`
- **Check status**: `curl http://localhost:8000/research/status`
- **View logs**: Server logs show detailed information
- **API docs**: http://localhost:8000/docs

Happy researching with uv! 🚀