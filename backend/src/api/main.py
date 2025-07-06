"""
FastAPI main application for the web search agent
"""

import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio

from ..core.query_validator import QueryValidator
from ..core.similarity_detector import SimilarityDetector
from ..core.web_scraper import WebScraper
from ..ai.summarizer import ContentSummarizer

app = FastAPI(
    title="Web Search Agent API",
    description="Intelligent web browser query agent with AI-powered search and similarity detection",
    version="0.1.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    summary_type: Optional[str] = "individual"  # "individual" or "combined"

class QueryResponse(BaseModel):
    is_valid: bool
    found_similar: bool
    results: List[Dict[str, Any]]
    message: str
    combined_summary: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    message: str

# Initialize services
query_validator = QueryValidator()
similarity_detector = SimilarityDetector()

@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(status="healthy", message="Web Search Agent API is running")

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", message="API is operational")

@app.post("/search", response_model=QueryResponse)
async def search_query(request: QueryRequest):
    """
    Unified search endpoint that always returns a comprehensive AI-powered overview
    """
    try:
        query_str = request.query.strip()
        print(f"🔍 Search request for: {query_str}")
        
        if not query_str:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Validate query
        print("✅ Validating query...")
        validation = query_validator.validate_query(query_str)
        if not validation.is_valid:
            print(f"❌ Query validation failed: {validation.reason}")
            return QueryResponse(
                is_valid=False,
                found_similar=False,
                results=[],
                message=f"Invalid query: {validation.reason}"
            )
        
        # Check for similar queries
        print("🔍 Checking for similar queries...")
        similarity_result = similarity_detector.find_similar_query(query_str)
        if similarity_result.found_similar and similarity_result.best_match:
            print("✅ Found similar query in cache")
            cached_results = similarity_result.best_match["results"]
            # Generate combined summary from cached results if not present
            combined_summary = None
            if cached_results:
                combined_summary = _generate_combined_summary_from_cached_results(cached_results, query_str)
            
            return QueryResponse(
                is_valid=True,
                found_similar=True,
                results=cached_results,
                message="Found similar query in cache",
                combined_summary=combined_summary
            )
        
        # Perform optimized web search with combined summary
        print("🚀 Performing optimized web search...")
        results, combined_summary = await _perform_optimized_web_search(query_str)
        print(f"✅ Search completed with {len(results)} results")
        
        response = QueryResponse(
            is_valid=True,
            found_similar=False,
            results=results,
            message="Search completed successfully",
            combined_summary=combined_summary
        )
        
        # Store results for future similarity detection
        print("💾 Storing results for similarity detection...")
        similarity_detector.store_query_with_results(query_str, results)
        
        return response
        
    except Exception as e:
        print(f"❌ Error in search: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")



async def _perform_web_search(query_str: str) -> List[Dict[str, Any]]:
    """Perform web search and return individual summarized results"""
    # Initialize AI summarizer
    summarizer = ContentSummarizer()
    
    async with WebScraper() as scraper:
        search_results = await scraper.search_google(query_str, max_results=5)
        if not search_results:
            return []
        
        # Scrape and summarize each result
        summaries = []
        for result in search_results:
            page = await scraper.scrape_page_content(result["url"])
            
            # Use AI-powered summarization
            summary_result = summarizer.summarize_content(
                content=page["content"],
                max_length=100,  # Limit summary length
                query_context=query_str
            )
            
            summaries.append({
                "title": result["title"],
                "url": result["url"],
                "summary": summary_result.summary,
                "summary_method": summary_result.method,
                "confidence": summary_result.confidence
            })
        
        return summaries

async def _perform_fast_web_search(query_str: str) -> tuple[List[Dict[str, Any]], str]:
    """Fast web search with reduced scraping and shorter timeouts"""
    import time
    start_time = time.time()
    print(f"🚀 Starting fast web search for: '{query_str}'")
    
    # Initialize AI summarizer
    summarizer = ContentSummarizer()
    
    # Use shorter timeout for faster results
    async with WebScraper(timeout=25000) as scraper:  # Increased to 25 seconds
        print("🔍 Initializing search engines...")
        search_start = time.time()
        search_results = await scraper.search_google(query_str, max_results=3)  # Only 3 results
        search_end = time.time()
        print(f"🔍 Search engines completed in {search_end - search_start:.2f}s")
        
        if not search_results:
            return [], "No search results found."
        
        # Scrape content with limited time per page
        successful_content = []
        results = []
        successful_sources = []
        scraping_errors = []
        
        for result in search_results:
            try:
                print(f"Scraping: {result['title'][:50]}...")
                page = await scraper.scrape_page_content(result["url"])
                
                # Clean and prepare content first
                cleaned_content = _clean_scraped_content(page["content"])[:1000]
                is_fallback = _is_fallback_content(page["content"])
                
                # Determine if scraping was successful and content is usable for summary
                has_meaningful_content = len(cleaned_content) > 100 and not is_fallback
                has_basic_content = len(page["content"]) > 50 and not is_fallback
                
                # Store basic result info with accurate status
                results.append({
                    "title": result["title"],
                    "url": result["url"],
                    "content_length": len(page["content"]),
                    "scraped_successfully": has_meaningful_content,  # Only mark as successful if it contributes to summary
                    "cleaned_content_length": len(cleaned_content)
                })
                
                # Collect content for summary generation
                if has_meaningful_content:
                    successful_content.append(cleaned_content)
                    successful_sources.append(result["title"])
                    print(f"✅ Successfully scraped and added to summary: {result['title'][:50]}...")
                elif has_basic_content:
                    print(f"⚠️  Content too short for summary ({len(cleaned_content)} chars): {result['title'][:50]}...")
                else:
                    print(f"⚠️  Fallback content or scraping failed: {result['title'][:50]}...")
                    
            except Exception as e:
                error_msg = str(e)
                scraping_errors.append(f"{result['title'][:50]}...: {error_msg}")
                print(f"Error scraping page {result['url']}: {error_msg}")
                
                # Skip failed pages and continue
                results.append({
                    "title": result["title"],
                    "url": result["url"],
                    "content_length": 0,
                    "scraped_successfully": False,
                    "error": error_msg
                })
                continue
        
        # Create combined summary only from successfully scraped content
        print(f"📝 Summary generation: {len(successful_content)} sources with content, {len(successful_sources)} source names")
        
        if successful_content and len(successful_content) > 0:
            # Combine all successful content (limited for speed)
            combined_content = "\n\n".join(successful_content)
            print(f"📝 Combined content length: {len(combined_content)} characters")
            
            try:
                # Generate combined summary using AI
                summary_result = summarizer.summarize_content(
                    content=combined_content,
                    max_length=250,  # Increased for better summaries
                    query_context=query_str
                )
                
                print(f"📝 AI summary generated: {len(summary_result.summary)} characters, method: {summary_result.method}")
                
                # Format the summary with source information
                source_count = len(successful_sources)
                if source_count > 0:
                    source_info = f"Based on analysis of {source_count} source{'s' if source_count > 1 else ''}"
                    if source_count <= 3:
                        source_names = ", ".join([name[:30] + "..." if len(name) > 30 else name for name in successful_sources])
                        source_info += f" ({source_names})"
                    source_info += ":\n\n"
                    
                    combined_summary = source_info + summary_result.summary
                else:
                    combined_summary = summary_result.summary
                    
                print(f"✅ Combined summary generated successfully: {len(combined_summary)} characters")
                
            except Exception as e:
                print(f"❌ Error generating AI summary: {e}")
                # Fallback to a basic summary
                combined_summary = f"Successfully analyzed {len(successful_sources)} sources but encountered an error generating the AI summary. The individual source summaries below contain the extracted information."
        else:
            # Provide more informative error message
            print(f"❌ No content available for summary generation")
            failed_count = len(scraping_errors)
            total_results = len(search_results)
            
            if failed_count > 0:
                combined_summary = f"Unable to extract meaningful content from {total_results} search result{'s' if total_results > 1 else ''}. "
                combined_summary += "This may be due to website restrictions, content protection measures, or network timeouts. "
                combined_summary += "Common issues include: cookie consent popups, JavaScript-heavy pages, or anti-bot protection. "
                combined_summary += "Try searching for more specific terms or different sources."
            else:
                combined_summary = "Search completed but no meaningful content could be extracted from the results. The pages may have limited text content or strong content protection."
        
        # Add scraping status information
        total_results = len(search_results)
        successful_scrapes = len([r for r in results if r.get("scraped_successfully", False)])
        if successful_scrapes < total_results:
            status_msg = f" (Successfully scraped {successful_scrapes}/{total_results} pages)"
            if combined_summary and not combined_summary.endswith('.'):
                combined_summary += '.'
            combined_summary += status_msg
        
        # Log total time
        end_time = time.time()
        total_time = end_time - start_time
        print(f"✅ Fast search completed in {total_time:.2f}s total ({successful_scrapes}/{total_results} pages successful)")
        
        return results, combined_summary

async def _perform_optimized_web_search(query_str: str) -> tuple[List[Dict[str, Any]], str]:
    """
    Optimized web search with parallel processing for faster results
    """
    import time
    import asyncio
    start_time = time.time()
    print(f"🚀 Starting optimized web search for: '{query_str}'")
    
    # Initialize AI summarizer
    summarizer = ContentSummarizer()
    
    # Use shorter timeout for faster results
    async with WebScraper(timeout=12000) as scraper:  # 12 seconds per page
        print("🔍 Searching web engines...")
        search_start = time.time()
        search_results = await scraper.search_google(query_str, max_results=4)
        search_end = time.time()
        print(f"🔍 Web search completed in {search_end - search_start:.2f}s")
        
        if not search_results:
            return [], "No search results found for your query. Please try different keywords."
        
        # Process pages in parallel for much faster results
        print("📄 Processing pages in parallel...")
        
        # Create tasks for parallel processing
        tasks = []
        for i, result in enumerate(search_results):
            task = _process_single_page(scraper, result, i+1, query_str, summarizer)
            tasks.append(task)
        
        # Execute all tasks in parallel with timeout
        try:
            # Wait for all tasks to complete, with overall timeout of 20 seconds
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True), 
                timeout=20.0
            )
            
            # Process results
            successful_content = []
            successful_sources = []
            scraping_errors = []
            processed_results = []
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"❌ Task {i+1} failed: {str(result)}")
                    processed_results.append({
                        "title": search_results[i]["title"],
                        "url": search_results[i]["url"],
                        "content_length": 0,
                        "scraped_successfully": False,
                        "summary": f"Processing failed: {str(result)}",
                        "summary_method": "error",
                        "confidence": 0.0
                    })
                    scraping_errors.append(str(result))
                else:
                    # Safely unpack result tuple
                    if isinstance(result, (tuple, list)) and len(result) == 3:
                        result_info, content, source = result
                        processed_results.append(result_info)
                        if content:
                            successful_content.append(content)
                            successful_sources.append(source)
                    else:
                        scraping_errors.append("Invalid result format")
        
        except asyncio.TimeoutError:
            print("⏰ Parallel processing timed out after 20 seconds")
            # Return partial results
            processed_results = []
            successful_content = []
            successful_sources = []
            scraping_errors = ["Overall timeout after 20 seconds"]
            
            for result in search_results:
                processed_results.append({
                    "title": result["title"],
                    "url": result["url"],
                    "content_length": 0,
                    "scraped_successfully": False,
                    "summary": "Processing timed out",
                    "summary_method": "timeout",
                    "confidence": 0.0
                })
        
        # Generate comprehensive combined summary
        combined_summary = await _generate_comprehensive_summary(
            successful_content, successful_sources, query_str, len(search_results), 
            len(successful_content), summarizer, scraping_errors
        )
        
        # Log completion
        end_time = time.time()
        total_time = end_time - start_time
        successful_count = len(successful_content)
        print(f"✅ Optimized search completed in {total_time:.2f}s ({successful_count}/{len(search_results)} sources analyzed)")
        
        return processed_results, combined_summary

async def _process_single_page(scraper, result, page_num, query_str, summarizer):
    """Process a single page in parallel"""
    try:
        print(f"📄 Processing page {page_num}: {result['title'][:50]}...")
        page_start = time.time()
        
        # Scrape with individual timeout
        page = await scraper.scrape_page_content(result["url"])
        
        page_end = time.time()
        print(f"📄 Page {page_num} processed in {page_end - page_start:.2f}s")
        
        # Clean and prepare content
        cleaned_content = _clean_scraped_content(page["content"])
        is_fallback = _is_fallback_content(page["content"])
        
        # Determine scraping success
        has_meaningful_content = len(cleaned_content) > 150 and not is_fallback
        has_basic_content = len(page["content"]) > 100 and not is_fallback
        
        # Store result info
        result_info = {
            "title": result["title"],
            "url": result["url"],
            "content_length": len(page["content"]),
            "scraped_successfully": has_meaningful_content or has_basic_content
        }
        
        content_for_summary = None
        source_for_summary = None
        
        # Generate individual summary if we have good content
        if has_meaningful_content:
            try:
                summary_result = summarizer.summarize_content(
                    content=cleaned_content,
                    max_length=120,
                    query_context=query_str
                )
                result_info.update({
                    "summary": summary_result.summary,
                    "summary_method": summary_result.method,
                    "confidence": summary_result.confidence
                })
                
                # Collect for combined summary
                content_for_summary = cleaned_content
                source_for_summary = result["title"]
                
            except Exception as e:
                print(f"⚠️ Failed to summarize content from {result['url']}: {str(e)}")
                result_info["scraped_successfully"] = False
        
        elif has_basic_content:
            # Still mark as successful but note limited content
            result_info["summary"] = f"Page content was detected but may be limited due to website restrictions."
            result_info["summary_method"] = "basic_extraction"
            result_info["confidence"] = 0.3
        else:
            # Failed to get meaningful content
            result_info["summary"] = "Unable to extract meaningful content from this page."
            result_info["summary_method"] = "failed_extraction"
            result_info["confidence"] = 0.0
        
        return result_info, content_for_summary, source_for_summary
        
    except Exception as e:
        print(f"❌ Error processing page {page_num} ({result['url']}): {str(e)}")
        return {
            "title": result["title"],
            "url": result["url"],
            "content_length": 0,
            "scraped_successfully": False,
            "summary": f"Failed to access this page: {str(e)}",
            "summary_method": "error",
            "confidence": 0.0
        }, None, None

async def _generate_comprehensive_summary(
    successful_content: List[str], 
    successful_sources: List[str], 
    query_str: str,
    total_results: int,
    successful_count: int,
    summarizer,
    scraping_errors: List[str]
) -> str:
    """Generate a comprehensive summary like Perplexity or Google Search"""
    
    if successful_content:
        # Combine all successful content
        combined_content = "\n\n".join(successful_content)
        
        try:
            # Generate comprehensive summary
            summary_result = summarizer.summarize_content(
                content=combined_content,
                max_length=400,  # Longer for comprehensive coverage
                query_context=f"Provide a comprehensive, informative summary about: {query_str}"
            )
            
            # Format like Perplexity/Google with sources
            source_text = ""
            if successful_sources:
                if len(successful_sources) == 1:
                    source_text = f"Based on analysis of {successful_sources[0]}"
                elif len(successful_sources) == 2:
                    source_text = f"Based on analysis of {successful_sources[0]} and {successful_sources[1]}"
                else:
                    source_text = f"Based on analysis of {successful_sources[0]}, {successful_sources[1]}, and {len(successful_sources) - 2} other sources"
            
            # Create final summary
            final_summary = f"{summary_result.summary}\n\n{source_text}."
            
            # Add confidence note if needed
            if summary_result.confidence < 0.7:
                final_summary += f"\n\n*Note: This summary was generated with moderate confidence ({summary_result.confidence:.1f}) due to content extraction challenges.*"
            
            return final_summary
            
        except Exception as e:
            print(f"❌ Error generating combined summary: {str(e)}")
            return f"Found {total_results} results about '{query_str}' but encountered issues generating a comprehensive summary. Individual source summaries are available below."
    
    else:
        # No successful content extracted
        if scraping_errors:
            error_summary = "Unable to extract meaningful content from the search results. "
            if "timeout" in " ".join(scraping_errors).lower():
                error_summary += "This appears to be due to slow website responses or network issues."
            elif "blocked" in " ".join(scraping_errors).lower() or "403" in " ".join(scraping_errors):
                error_summary += "This may be due to websites blocking automated access or requiring authentication."
            else:
                error_summary += "This could be due to website restrictions, content protection, or technical issues."
            
            error_summary += f"\n\nTip: Try searching for '{query_str}' with more specific terms or different keywords."
            return error_summary
        else:
            return f"Found {total_results} results for '{query_str}' but the content was not accessible for analysis. The websites may have content protection or require authentication."

def _generate_combined_summary_from_cached_results(cached_results: List[Dict[str, Any]], query_str: str) -> str:
    """Generate a combined summary from cached results"""
    if not cached_results:
        return f"No cached summary available for '{query_str}'."
    
    # Extract individual summaries from cached results
    individual_summaries = []
    sources = []
    
    for result in cached_results:
        if result.get("summary") and result.get("scraped_successfully", False):
            individual_summaries.append(result["summary"])
            sources.append(result.get("title", "Unknown source"))
    
    if individual_summaries:
        # Combine individual summaries
        combined_text = " ".join(individual_summaries)
        
        # Create a cohesive summary
        if sources:
            source_text = f"Based on {len(sources)} previously analyzed sources"
            if len(sources) <= 3:
                source_text += f" ({', '.join(sources)})"
        else:
            source_text = "Based on previously analyzed sources"
        
        return f"{combined_text}\n\n{source_text}."
    
    return f"Cached results found for '{query_str}' but no comprehensive summary is available."

def _is_fallback_content(content: str) -> bool:
    """Check if content is from fallback generation rather than actual scraping"""
    fallback_indicators = [
        "could not be fully loaded due to website restrictions",
        "This page from",
        "appears to be a relevant resource",
        "This is a comprehensive resource about",
        "ConsentDetailsIABV2SETTINGS",
        "website restrictions or network issues"
    ]
    
    return any(indicator in content for indicator in fallback_indicators)

def _clean_scraped_content(content: str) -> str:
    """Clean and prepare scraped content for summarization"""
    import re
    
    if not content:
        return ""
    
    # Remove common website elements (but be more conservative)
    content = re.sub(r'Cookie\s+.*?Accept\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Privacy\s+Policy\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Terms\s+of\s+Service\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'Subscribe\s+to\s+Newsletter\s*', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\bSign\s+up\b', '', content, flags=re.IGNORECASE)
    content = re.sub(r'\bLog\s+in\b', '', content, flags=re.IGNORECASE)
    
    # Remove excessive whitespace and normalize
    content = re.sub(r'\s+', ' ', content)
    content = content.strip()
    
    # Split into sentences but be less aggressive about filtering
    sentences = content.split('.')
    # Keep sentences with at least 15 characters (reduced from 20)
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 15]
    
    # Rejoin sentences
    cleaned_content = '. '.join(meaningful_sentences)
    
    # If we don't have much content, try a different approach
    if len(cleaned_content) < 100:
        # Try splitting by newlines and keeping longer paragraphs
        paragraphs = content.split('\n')
        long_paragraphs = [p.strip() for p in paragraphs if len(p.strip()) > 50]
        if long_paragraphs:
            cleaned_content = ' '.join(long_paragraphs)
    
    # Final cleanup
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content).strip()
    
    # Limit length to prevent overwhelming the summarizer
    if len(cleaned_content) > 2000:
        cleaned_content = cleaned_content[:2000] + "..."
    
    print(f"🧹 Content cleaning: {len(content)} -> {len(cleaned_content)} characters")
    return cleaned_content

@app.get("/debug/last-search")
async def get_last_search_debug():
    """Get debug information about the last search performed"""
    # This would be expanded to store actual debug info in a real implementation
    return {
        "message": "Debug endpoint - check server logs for detailed search information",
        "tip": "Enable verbose logging to see detailed scraping and summarization steps"
    }

@app.get("/stats")
async def get_stats():
    """Get statistics about the search agent"""
    try:
        stats = similarity_detector.get_similarity_stats()
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.get("/history")
async def get_history(limit: int = 10):
    """Get recent query history"""
    try:
        history = similarity_detector.get_query_history(limit=limit)
        return {
            "status": "success",
            "data": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting history: {str(e)}")

def start_server():
    """Entry point for UV script"""
    import uvicorn
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    start_server() 