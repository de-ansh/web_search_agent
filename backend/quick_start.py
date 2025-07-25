#!/usr/bin/env python3
"""
Quick start server for testing - minimal dependencies
"""

import sys
import os
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_dir))

# Set lightweight mode
os.environ["LIGHTWEIGHT_MODE"] = "1"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import time

app = FastAPI(
    title="Enhanced Web Search Agent API - Quick Start",
    description="Minimal version for testing",
    version="2.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Removed Pydantic models to avoid validation issues

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Enhanced Web Search Agent API - Quick Start Mode",
        "version": "2.1.0",
        "mode": "quick_start"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Quick start server is running",
        "version": "2.1.0"
    }

@app.get("/research/status")
async def research_status():
    return {
        "research_service": {
            "service": "Enhanced Research Service - Quick Start",
            "ai_method": "gemini",
            "max_sources": 5,
            "summary_length": 150
        },
        "api_version": "2.1.0",
        "enhanced_features": {
            "gemini_ai_summarization": True,
            "improved_web_scraping": True,
            "playwright_support": True,
            "fallback_scraping": True,
            "context_aware_summaries": True
        }
    }

@app.post("/research/enhanced")
async def enhanced_research(request: dict):
    """Enhanced research endpoint - simplified for quick start"""
    try:
        start_time = time.time()
        print(f"📥 Received request: {request}")
        
        # Simulate research process
        await asyncio.sleep(0.5)  # Shorter simulation time
        
        query = request.get("query", "test query")
        
        # Mock response for testing
        mock_sources = [
            {
                "title": f"Mock Result 1 for: {query}",
                "url": "https://example.com/result1",
                "success": True,
                "method": "mock",
                "word_count": 150,
                "processing_time": 1.0
            },
            {
                "title": f"Mock Result 2 for: {query}",
                "url": "https://example.com/result2", 
                "success": True,
                "method": "mock",
                "word_count": 200,
                "processing_time": 1.2
            }
        ]
        
        mock_summaries = [
            {
                "source_title": f"Mock Result 1 for: {query}",
                "source_url": "https://example.com/result1",
                "summary": f"This is a mock summary for your query about {query}. The enhanced research service is working correctly in quick start mode.",
                "method": "mock_gemini",
                "confidence": 0.9,
                "word_count": 25,
                "processing_time": 0.5,
                "scraping_method": "mock",
                "scraping_success": True
            },
            {
                "source_title": f"Mock Result 2 for: {query}",
                "source_url": "https://example.com/result2",
                "summary": f"Another mock summary providing additional context about {query}. This demonstrates the multi-source research capability.",
                "method": "mock_gemini",
                "confidence": 0.85,
                "word_count": 22,
                "processing_time": 0.6,
                "scraping_method": "mock",
                "scraping_success": True
            }
        ]
        
        combined_summary = f"Based on research about '{query}', here are the key findings: This is a comprehensive mock summary that combines insights from multiple sources. The enhanced research service with Gemini AI integration is working correctly. This demonstrates the system's ability to process queries and generate meaningful summaries."
        
        processing_time = time.time() - start_time
        
        response_data = {
            "query": query,
            "success": True,
            "sources": mock_sources,
            "combined_summary": combined_summary,
            "individual_summaries": mock_summaries,
            "processing_time": processing_time,
            "method_used": "mock_gemini",
            "total_sources": 2,
            "successful_scrapes": 2
        }
        
        print(f"📤 Sending response: {response_data}")
        return response_data
        
    except Exception as e:
        print(f"❌ Error in enhanced_research: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Enhanced research failed: {str(e)}")

@app.post("/research/quick")
async def quick_research(request: dict):
    """Quick research endpoint"""
    # Use the same logic as enhanced but with fewer sources
    print(f"📥 Quick research request: {request}")
    return await enhanced_research(request)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Quick Start Server")
    print("=" * 40)
    print("✅ Minimal dependencies")
    print("✅ Mock responses for testing")
    print("✅ All endpoints available")
    print()
    print("🌐 Server will be available at:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")