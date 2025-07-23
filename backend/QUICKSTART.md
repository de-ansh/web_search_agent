# 🚀 Quick Start Guide

Get the enhanced web scraping with Gemini AI running in 5 minutes!

## Prerequisites

- Python 3.9+
- `uv` package manager

## Install uv (if needed)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## One-Command Setup

```bash
cd backend
./run.sh all
```

That's it! This will:
1. ✅ Install all dependencies
2. ✅ Set up Playwright browsers  
3. ✅ Help you configure API keys
4. ✅ Run tests to verify everything works
5. ✅ Start the server

## Manual Setup (if you prefer step-by-step)

### 1. Install Dependencies
```bash
cd backend
uv sync
uv run playwright install chromium
```

### 2. Set Up API Keys
```bash
uv run python setup_gemini_api.py
```

Get your API keys:
- **Gemini**: https://makersuite.google.com/app/apikey
- **OpenAI** (optional): https://platform.openai.com/api-keys

### 3. Test Everything
```bash
uv run python test_runner.py
```

### 4. Start the Server
```bash
uv run uvicorn src.api.main:app --reload
```

## 🎯 Try It Out

Once running, visit:
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Test with curl:
```bash
curl -X POST "http://localhost:8000/research/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "latest AI developments 2024",
    "max_sources": 3,
    "ai_method": "gemini"
  }'
```

## 🛠️ Common Commands

```bash
# Start server
./run.sh server

# Run tests  
./run.sh test

# Set up API keys
./run.sh keys

# Run examples
./run.sh example
```

## 🆘 Need Help?

- Check [README_UV.md](README_UV.md) for detailed instructions
- See [ENHANCED_FEATURES.md](ENHANCED_FEATURES.md) for feature documentation
- Run `./run.sh` without arguments to see all options

## 🎉 You're Ready!

The enhanced web scraping service is now running with:
- ✅ Reliable web scraping (Playwright + requests fallback)
- ✅ AI-powered summarization (Gemini + OpenAI fallback)
- ✅ Context-aware summaries
- ✅ Multiple search engines
- ✅ Robust error handling

Happy researching! 🔍