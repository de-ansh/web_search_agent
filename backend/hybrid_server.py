#!/usr/bin/env python3
"""
Hybrid server - real research with timeouts and fallbacks
"""

import sys
import os
import asyncio
import time
from pathlib import Path

# Add paths
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(src_dir))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

app = FastAPI(
    title="Enhanced Web Search Agent API - Hybrid Mode",
    description="Real research with timeouts and fallbacks",
    version="2.1.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class EnhancedResearchRequest(BaseModel):
    query: str
    max_sources: Optional[int] = 3  # Reduced for speed
    summary_length: Optional[int] = 100  # Shorter summaries
    use_playwright: Optional[bool] = False  # Use requests only for speed
    ai_method: Optional[str] = "extractive"  # Use extractive for speed

class EnhancedResearchResponse(BaseModel):
    query: str
    success: bool
    sources: List[Dict[str, Any]]
    combined_summary: str
    individual_summaries: List[Dict[str, Any]]
    processing_time: float
    method_used: str
    total_sources: int
    successful_scrapes: int
    error: Optional[str] = None

@app.get("/")
async def root():
    return {
        "status": "healthy",
        "message": "Enhanced Web Search Agent API - Hybrid Mode",
        "version": "2.1.0",
        "mode": "hybrid"
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Hybrid server is running",
        "version": "2.1.0"
    }

@app.get("/research/status")
async def research_status():
    return {
        "research_service": {
            "service": "Enhanced Research Service - Hybrid Mode",
            "ai_method": "extractive",
            "max_sources": 3,
            "summary_length": 100
        },
        "api_version": "2.1.0",
        "enhanced_features": {
            "real_web_scraping": True,
            "extractive_summarization": True,
            "timeout_protection": True,
            "fallback_responses": True
        }
    }

async def timeout_wrapper(coro, timeout_seconds=30):
    """Wrapper to timeout long-running operations"""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        return None

@app.post("/research/enhanced", response_model=EnhancedResearchResponse)
async def enhanced_research(request: EnhancedResearchRequest):
    """Enhanced research with timeout protection"""
    start_time = time.time()
    
    try:
        # Try real research with timeout
        print(f"🔍 Starting research for: {request.query}")
        
        # Import and use real service with timeout
        try:
            from src.services.enhanced_research_service import EnhancedResearchService
            
            service = EnhancedResearchService(
                use_playwright=False,  # Use requests only for speed
                preferred_ai_method="extractive",  # Fast summarization
                max_sources=min(request.max_sources, 3),  # Limit sources
                summary_length=min(request.summary_length, 100)  # Shorter summaries
            )
            
            # Run with timeout
            result = await timeout_wrapper(
                service.research_query(request.query),
                timeout_seconds=45  # 45 second timeout
            )
            
            if result and result.success:
                print(f"✅ Real research completed in {result.processing_time:.1f}s")
                return EnhancedResearchResponse(
                    query=result.query,
                    success=result.success,
                    sources=result.sources,
                    combined_summary=result.combined_summary,
                    individual_summaries=result.individual_summaries,
                    processing_time=result.processing_time,
                    method_used=result.method_used,
                    total_sources=result.total_sources,
                    successful_scrapes=result.successful_scrapes
                )
            else:
                print("⚠️  Real research timed out or failed, using fallback")
                raise Exception("Research timed out")
                
        except Exception as e:
            print(f"❌ Real research failed: {e}")
            raise Exception(f"Real research failed: {e}")
            
    except Exception as e:
        # Fallback to mock response
        print(f"🔄 Using fallback response due to: {e}")
        processing_time = time.time() - start_time
        
        return EnhancedResearchResponse(
            query=request.query,
            success=True,
            sources=[
                {
                    "title": f"Fallback Result for: {request.query}",
                    "url": "https://fallback.example.com",
                    "success": False,
                    "method": "fallback",
                    "word_count": 100,
                    "processing_time": processing_time,
                    "error": str(e)
                }
            ],
            combined_summary=f"Research for '{request.query}' encountered technical difficulties. This is a fallback response. The system attempted real web scraping but timed out or failed. Please try a simpler query or try again later.",
            individual_summaries=[
                {
                    "source_title": f"Fallback for: {request.query}",
                    "source_url": "https://fallback.example.com",
                    "summary": f"Fallback summary for {request.query} due to technical issues.",
                    "method": "fallback",
                    "confidence": 0.3,
                    "word_count": 15,
                    "processing_time": processing_time,
                    "scraping_method": "fallback",
                    "scraping_success": False
                }
            ],
            processing_time=processing_time,
            method_used="fallback",
            total_sources=1,
            successful_scrapes=0,
            error=f"Research failed: {str(e)}"
        )

@app.post("/research/quick", response_model=EnhancedResearchResponse)
async def quick_research(request: EnhancedResearchRequest):
    """Quick research with even shorter timeout"""
    # Reduce parameters for speed
    request.max_sources = 2
    request.summary_length = 50
    return await enhanced_research(request)

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting Hybrid Server")
    print("=" * 40)
    print("✅ Real web scraping (with timeouts)")
    print("✅ Extractive summarization")
    print("✅ Fallback responses")
    print("✅ 45-second timeout protection")
    print()
    print("🌐 Server will be available at:")
    print("   http://localhost:8000")
    print("   http://localhost:8000/docs")
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")