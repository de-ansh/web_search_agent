#!/usr/bin/env python3
"""
Minimal server that will definitely start
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Minimal server is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/research/status")
def research_status():
    return {
        "research_service": {"service": "Minimal Test Server"},
        "api_version": "2.1.0"
    }

@app.post("/research/enhanced")
def enhanced_research(request: dict):
    return {
        "query": request.get("query", "test"),
        "success": True,
        "sources": [{"title": "Test", "url": "http://test.com", "success": True}],
        "combined_summary": f"Test summary for: {request.get('query', 'test')}",
        "individual_summaries": [],
        "processing_time": 1.0,
        "method_used": "test",
        "total_sources": 1,
        "successful_scrapes": 1
    }

@app.post("/research/quick")
def quick_research(request: dict):
    return enhanced_research(request)

if __name__ == "__main__":
    print("🚀 Starting Minimal Server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)