# Web Search Agent Backend

Intelligent web browser query agent with AI-powered search and similarity detection.

## Features

- Query validation using AI
- Similarity detection for cached results
- Web scraping with Playwright
- Content summarization
- Caching system

## Installation

```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install
```

## Usage

```bash
# Run CLI
uv run python -m src.cli.main "your query here"

# Run API server
uv run uvicorn src.api.main:app --reload
``` 