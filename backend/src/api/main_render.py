"""
Simplified FastAPI application for Render deployment (no Playwright)
"""

import time
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from ..core.query_validator import EnhancedQueryValidator
from ..core.similarity_detector import EnhancedSimilarityDetector
from ..core.lightweight_scraper import LightweightScraper
from ..ai.summarizer import ContentSummarizer

app = FastAPI(
    title="Web Search Agent API (Render)",
    description="Lightweight web search agent for Render deployment",
    version="2.0.0-render"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    summary_type: Optional[str] = "combined"
    max_results: Optional[int] = 5
    preferred_engines: Optional[List[str]] = None

class QueryResponse(BaseModel):
    is_valid: bool
    found_similar: bool
    results: List[Dict[str, Any]]
    message: str
    combined_summary: Optional[str] = None
    validation_info: Optional[Dict[str, Any]] = None
    cache_info: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    features: Dict[str, bool]

# Initialize components
query_validator = EnhancedQueryValidator()
similarity_detector = EnhancedSimilarityDetector()
summarizer = ContentSummarizer()
scraper = LightweightScraper()

@app.get("/", response_model=HealthResponse)
async def root():
    return HealthResponse(
        status="online",
        message="Web Search Agent API (Render) is running",
        version="2.0.0-render",
        features={
            "lightweight_scraper": True,
            "ai_summarization": True,
            "query_validation": True,
            "similarity_detection": True,
            "playwright": False
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        message="All systems operational (Render mode)",
        version="2.0.0-render",
        features={
            "lightweight_scraper": True,
            "ai_summarization": True,
            "query_validation": True,
            "similarity_detection": True,
            "playwright": False
        }
    )

@app.post("/search", response_model=QueryResponse)
async def search_query(request: QueryRequest):
    """
    Main search endpoint using lightweight scraper
    """
    start_time = time.time()
    
    try:
        # Validate query
        validation_result = query_validator.validate_query(request.query)
        if not validation_result.is_valid:
            return QueryResponse(
                is_valid=False,
                found_similar=False,
                results=[],
                message=validation_result.message,
                validation_info=validation_result.to_dict()
            )
        
        # Check for similar queries
        similar_query_result = similarity_detector.find_similar_query(request.query)
        
        if similar_query_result.found_similar:
            print(f"📋 Found similar query: {similar_query_result.matched_query}")
            print(f"📊 Similarity score: {similar_query_result.similarity_score:.3f}")
            
            # Generate summary from cached results
            combined_summary = _generate_combined_summary(similar_query_result.cached_results, request.query)
            
            return QueryResponse(
                is_valid=True,
                found_similar=True,
                results=similar_query_result.cached_results,
                message=f"Found similar query with {similar_query_result.similarity_score:.1%} similarity",
                combined_summary=combined_summary,
                validation_info=validation_result.to_dict(),
                cache_info=similar_query_result.to_dict()
            )
        
        # Perform new search
        results, combined_summary = await _perform_lightweight_search(
            request.query,
            request.max_results or 5
        )
        
        # Store results for future similarity matching
        similarity_detector.store_query_results(request.query, results)
        
        # Prepare response
        response = QueryResponse(
            is_valid=True,
            found_similar=False,
            results=results,
            message=f"Found {len(results)} results for your query",
            combined_summary=combined_summary,
            validation_info=validation_result.to_dict()
        )
        
        total_time = time.time() - start_time
        print(f"✅ Search completed in {total_time:.2f}s")
        
        return response
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return QueryResponse(
            is_valid=False,
            found_similar=False,
            results=[],
            message=f"Search failed: {str(e)}"
        )

@app.post("/search/fast", response_model=QueryResponse)
async def fast_search_query(request: QueryRequest):
    """
    Fast search endpoint (same as main search in Render mode)
    """
    return await search_query(request)

@app.get("/stats")
async def get_system_stats():
    """Get system performance statistics"""
    return {
        "query_validator": query_validator.get_stats(),
        "similarity_detector": similarity_detector.get_stats(),
        "deployment": "render",
        "features": {
            "lightweight_scraper": True,
            "playwright": False
        }
    }

@app.post("/cache/clear")
async def clear_cache():
    """Clear all caches"""
    similarity_detector.clear_cache()
    return {"message": "Caches cleared successfully"}

async def _perform_lightweight_search(query_str: str, max_results: int) -> tuple[List[Dict[str, Any]], str]:
    """
    Perform lightweight search using only requests
    """
    start_time = time.time()
    print(f"🚀 Starting lightweight search for: '{query_str}'")
    
    # Search and scrape using lightweight method
    enriched_results = scraper.search_and_scrape(query_str, max_results)
    
    if not enriched_results:
        return [], "No search results found for your query. Please try different keywords."
    
    # Process results
    processed_results = []
    successful_content = []
    successful_sources = []
    
    for result in enriched_results:
        result_info = {
            "title": result['title'],
            "url": result['url'],
            "content_length": result['content_length'],
            "scraped_successfully": result['scraped_successfully'],
            "search_engine": result['search_engine'],
            "relevance_score": 1.0,
            "scraping_strategy": "lightweight",
            "scraping_time": 1.0
        }
        
        # Add summary if content was successfully scraped
        if result['scraped_successfully'] and len(result['content']) > 30:
            try:
                print(f"📝 Attempting to summarize content from {result['url']} ({len(result['content'])} chars)")
                summary_result = summarizer.summarize_content(
                    content=result['content'],
                    max_length=150,
                    query_context=query_str
                )
                
                result_info.update({
                    "summary": summary_result.summary,
                    "summary_method": summary_result.method,
                    "confidence": summary_result.confidence
                })
                
                # Collect for combined summary
                successful_content.append(result['content'][:1000])
                successful_sources.append(result['title'])
                print(f"✅ Summary created using {summary_result.method} method")
                
            except Exception as e:
                print(f"❌ Summarization failed for {result['url']}: {e}")
                # Still include the raw content as a fallback
                content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                result_info["summary"] = f"Raw content preview: {content_preview}"
                result_info["summary_method"] = "raw_content"
                result_info["confidence"] = 0.3
                
                # Still collect for combined summary
                successful_content.append(result['content'][:1000])
                successful_sources.append(result['title'])
        else:
            result_info["summary"] = result.get('snippet', 'No content available')
            result_info["summary_method"] = "snippet"
            result_info["confidence"] = 0.2
        
        processed_results.append(result_info)
    
    # Generate combined summary
    combined_summary = ""
    if successful_content:
        try:
            combined_content = "\n\n".join(successful_content)
            combined_summary_result = summarizer.summarize_content(
                content=combined_content,
                max_length=350,
                query_context=query_str
            )
            combined_summary = combined_summary_result.summary
            
            # Add source attribution
            if successful_sources:
                combined_summary += f"\n\nSources: {', '.join(successful_sources[:3])}"
                if len(successful_sources) > 3:
                    combined_summary += f" and {len(successful_sources) - 3} more"
                    
        except Exception as e:
            print(f"❌ Combined summary generation failed: {e}")
            combined_summary = f"Unable to generate combined summary: {str(e)[:100]}..."
    
    total_time = time.time() - start_time
    print(f"✅ Lightweight search completed in {total_time:.2f}s total")
    
    return processed_results, combined_summary

def _generate_combined_summary(cached_results: List[Dict[str, Any]], query_str: str) -> str:
    """Generate combined summary from cached results"""
    try:
        # Extract summaries from cached results
        summaries = []
        for result in cached_results:
            if result.get('summary') and result.get('summary_method') != 'error':
                summaries.append(result['summary'])
        
        if summaries:
            # Combine summaries
            combined_text = "\n\n".join(summaries)
            
            # Generate meta-summary
            summary_result = summarizer.summarize_content(
                content=combined_text,
                max_length=300,
                query_context=query_str
            )
            
            return summary_result.summary
        else:
            return "No comprehensive summary available from cached results."
            
    except Exception as e:
        print(f"❌ Combined summary generation failed: {e}")
        return f"Unable to generate combined summary from cached results: {str(e)[:100]}..." 