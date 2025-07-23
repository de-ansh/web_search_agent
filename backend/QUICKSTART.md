# 🚀 Quick Start Guide

Get the enhanced web scraping with Gemini AI running in under 5 minutes!

## Prerequisites

- Python 3.9+
- Internet connection

## 1. Install uv (if not already installed)

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.sh | iex"
```

## 2. One-Command Setup

```bash
cd backend
./run.sh all
```

This single command will:
- ✅ Install all dependencies
- ✅ Set up Playwright browsers  
- ✅ Configure your API keys
- ✅ Run tests
- ✅ Start the server

## 3. Get Your API Key

When prompted, get your free Gemini API key:

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with Google
3. Click "Create API Key"
4. Copy and paste when prompted

## 4. Test It Out

Once the server starts, visit:
- 🌐 **API**: http://localhost:8000
- 📚 **Docs**: http://localhost:8000/docs

Try this API call:
```bash
curl -X POST "http://localhost:8000/research/quick" \
  -H "Content-Type: application/json" \
  -d '{"query": "Python web scraping 2024", "max_sources": 3}'
```

## 🎉 That's It!

You now have:
- ✅ Enhanced web scraping with multiple fallbacks
- ✅ Gemini AI for intelligent summarization  
- ✅ FastAPI server with comprehensive endpoints
- ✅ Automatic error handling and retries

## Next Steps

- Check out the [full documentation](ENHANCED_FEATURES.md)
- Run examples: `./run.sh example`
- Explore the API docs at http://localhost:8000/docs

## Troubleshooting

**uv not found?**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
# Restart your terminal
```

**API key issues?**
```bash
./run.sh keys
```

**Need help?**
```bash
./run.sh --help
```

Happy researching! 🔍✨