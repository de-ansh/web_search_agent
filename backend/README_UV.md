# Enhanced Web Scraping with uv

This guide shows how to run the enhanced web scraping project using `uv`, a fast Python package manager.

## 🚀 Quick Start

### 1. Install uv
```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or on macOS with Homebrew
brew install uv
```

### 2. Setup Everything at Once
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

## 📋 Step-by-Step Setup

### 1. Install Dependencies
```bash
cd backend
uv sync
```

### 2. Install Playwright Browsers
```bash
uv run playwright install chromium
```

### 3. Set Up API Keys
```bash
uv run python setup_gemini_api.py
```

### 4. Test the Installation
```bash
uv run python test_runner.py
```

### 5. Start the Server
```bash
uv run uvicorn src.api.main:app --reload
```

## 🛠️ Available Commands

### Using the Shell Script (Recommended)
```bash
./run.sh setup     # Set up environment and dependencies
./run.sh keys      # Set up API keys
./run.sh test      # Run tests
./run.sh server    # Start the server
./run.sh example   # Run usage examples
./run.sh all       # Do everything
```

### Using the Python Runner
```bash
python run_with_uv.py setup    # Set up environment
python run_with_uv.py keys     # Set up API keys
python run_with_uv.py test     # Run tests
python run_with_uv.py server   # Start server
python run_with_uv.py all      # Do everything
```

### Direct uv Commands
```bash
# Start the server
uv run uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
uv run python test_runner.py

# Set up API keys
uv run python setup_gemini_api.py

# Run examples
uv run python example_usage.py

# Install new dependencies
uv add package-name

# Update dependencies
uv sync
```

## 🔧 Configuration

### API Keys Setup
The setup script will help you configure:

1. **Gemini API Key** (Primary)
   - Get from: https://makersuite.google.com/app/apikey
   - Used for high-quality AI summarization

2. **OpenAI API Key** (Fallback)
   - Get from: https://platform.openai.com/api-keys
   - Used as backup when Gemini is unavailable

### Environment Variables
Create a `.env` file in the backend directory:
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

## 🧪 Testing

### Run All Tests
```bash
uv run python test_runner.py
```

### Test Specific Features
```bash
# Test API key configuration
uv run python setup_gemini_api.py

# Test with examples
uv run python example_usage.py
```

## 🌐 API Endpoints

Once the server is running, you can access:

- **Health Check**: http://localhost:8000/health
- **API Documentation**: http://localhost:8000/docs
- **Enhanced Research**: http://localhost:8000/research/enhanced
- **Quick Research**: http://localhost:8000/research/quick
- **Service Status**: http://localhost:8000/research/status

### Example API Usage
```bash
# Enhanced research
curl -X POST "http://localhost:8000/research/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "artificial intelligence trends 2024",
    "max_sources": 5,
    "ai_method": "gemini"
  }'

# Quick research
curl -X POST "http://localhost:8000/research/quick" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python web scraping",
    "max_sources": 3
  }'
```

## 📦 Project Structure

```
backend/
├── src/
│   ├── api/           # FastAPI endpoints
│   ├── core/          # Core scraping logic
│   ├── ai/            # AI summarization
│   └── services/      # Enhanced research service
├── pyproject.toml     # uv configuration
├── run.sh            # Shell runner script
├── run_with_uv.py    # Python runner script
├── test_runner.py    # Test runner
└── setup_gemini_api.py # API key setup
```

## 🔍 Troubleshooting

### Import Errors
If you get import errors, make sure you're running from the backend directory:
```bash
cd backend
uv run python test_runner.py
```

### API Key Issues
Test your API keys:
```bash
uv run python setup_gemini_api.py
# Choose option to test keys
```

### Playwright Issues
Reinstall Playwright browsers:
```bash
uv run playwright install chromium
```

### Port Already in Use
Change the port:
```bash
uv run uvicorn src.api.main:app --reload --port 8001
```

## 🚀 Performance Tips

### For Development
```bash
# Use quick research for faster testing
uv run python -c "
import asyncio
from src.services.enhanced_research_service import EnhancedResearchService

async def quick_test():
    service = EnhancedResearchService(use_playwright=False, max_sources=2)
    result = await service.quick_research('Python tips')
    print(result.combined_summary)

asyncio.run(quick_test())
"
```

### For Production
- Set `use_playwright=True` for better scraping
- Configure both Gemini and OpenAI for redundancy
- Use appropriate `max_sources` based on your needs

## 📈 Monitoring

### Check Service Status
```bash
curl http://localhost:8000/research/status
```

### View Logs
The server will show detailed logs including:
- Scraping progress
- AI summarization method used
- Processing times
- Error details

## 🔮 Advanced Usage

### Custom Configuration
```python
from src.services.enhanced_research_service import EnhancedResearchService

# Custom service configuration
service = EnhancedResearchService(
    use_playwright=True,
    preferred_ai_method="gemini",
    max_sources=8,
    summary_length=200
)

# Perform research
result = await service.research_query("your query here")
```

### Batch Processing
```python
queries = [
    "AI trends 2024",
    "Climate solutions",
    "Tech innovations"
]

for query in queries:
    result = await service.quick_research(query, max_sources=3)
    print(f"{query}: {result.combined_summary[:100]}...")
```

## 🎯 Next Steps

1. **Start with setup**: `./run.sh setup`
2. **Configure API keys**: `./run.sh keys`
3. **Test everything**: `./run.sh test`
4. **Start developing**: `./run.sh server`
5. **Integrate into your app**: Use the API endpoints

For more detailed information, see [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md).