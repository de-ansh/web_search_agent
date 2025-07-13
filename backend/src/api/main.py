"""
Enhanced FastAPI application with improved query validation, similarity matching, and web scraping
"""

import time
import asyncio
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import traceback

from ..core.query_validator import EnhancedQueryValidator
from ..core.similarity_detector import EnhancedSimilarityDetector
from ..ai.summarizer import ContentSummarizer

# Try to import the full web scraping agent first, fallback to lightweight
try:
    from ..agents.web_scraping_agent import WebScrapingAgent, ContentType, ScrapingStrategy
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    WebScrapingAgent = None
    ContentType = None
    ScrapingStrategy = None

# Always import the lightweight scraper as fallback
from ..core.lightweight_scraper import LightweightScraper

app = FastAPI(
    title="Enhanced Web Search Agent API",
    description="Intelligent web search agent with enhanced LLM-based validation, similarity matching, and robust scraping",
    version="2.0.0"
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
    summary_type: Optional[str] = "combined"  # "individual" or "combined"
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

# Initialize enhanced services
query_validator = EnhancedQueryValidator()
similarity_detector = EnhancedSimilarityDetector(
    similarity_threshold=0.8,
    llm_validation_threshold=0.7,
    enable_llm_validation=True
)

@app.get("/", response_model=HealthResponse)
async def root():
    """Enhanced health check endpoint"""
    return HealthResponse(
        status="healthy", 
        message="Enhanced Web Search Agent API is running",
        version="2.0.0",
        features={
            "llm_query_validation": True,
            "llm_similarity_validation": True,
            "knn_similarity_search": True,
            "ttl_cache_policy": True,
            "dedicated_scraping_agent": True
        }
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return await root()

@app.post("/search", response_model=QueryResponse)
async def enhanced_search_query(request: QueryRequest):
    """
    Enhanced search endpoint with LLM-based validation, similarity matching, and TTL policies
    """
    try:
        query_str = request.query.strip()
        max_results = request.max_results or 5
        preferred_engines = request.preferred_engines
        
        print(f"🔍 Enhanced search request for: {query_str}")
        
        if not query_str:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Enhanced query validation
        print("✅ Validating query with enhanced LLM classifier...")
        validation = query_validator.validate_query(query_str)
        
        if not validation.is_valid:
            print(f"❌ Query validation failed: {validation.reason}")
            return QueryResponse(
                is_valid=False,
                found_similar=False,
                results=[],
                message=f"Invalid query: {validation.reason}",
                validation_info={
                    "validation_method": validation.validation_method,
                    "confidence": validation.confidence,
                    "category": validation.category
                }
            )
        
        # Enhanced similarity detection with LLM validation
        print("🔍 Checking for similar queries with enhanced matching...")
        similarity_result = similarity_detector.find_similar_query(query_str)
        
        if similarity_result.found_similar and similarity_result.best_match:
            print(f"✅ Found similar query in cache (method: {similarity_result.validation_method})")
            cached_results = similarity_result.best_match["results"]
            
            # Generate combined summary from cached results if not present
            combined_summary = None
            if cached_results:
                combined_summary = _generate_combined_summary_from_cached_results(cached_results, query_str)
            
            return QueryResponse(
                is_valid=True,
                found_similar=True,
                results=cached_results,
                message=f"Found similar query in cache: {similarity_result.cache_hit_reason}",
                combined_summary=combined_summary,
                validation_info={
                    "validation_method": validation.validation_method,
                    "confidence": validation.confidence,
                    "category": validation.category
                },
                cache_info={
                    "cache_hit": True,
                    "similarity_method": similarity_result.validation_method,
                    "llm_validated": similarity_result.llm_validated,
                    "similarity_score": similarity_result.best_similarity
                }
            )
        
        # Perform enhanced web search with dedicated scraping agent
        print("🚀 Performing enhanced web search with dedicated scraping agent...")
        try:
            results, combined_summary = await _perform_enhanced_web_search(
                query_str, max_results, preferred_engines
            )
            print(f"✅ Enhanced search completed with {len(results)} results")
        except Exception as search_error:
            print(f"❌ Enhanced search failed: {search_error}")
            results = []
            combined_summary = f"Search failed: {str(search_error)[:100]}..."
        
        response = QueryResponse(
            is_valid=True,
            found_similar=False,
            results=results,
            message="Enhanced search completed successfully",
            combined_summary=combined_summary,
            validation_info={
                "validation_method": validation.validation_method,
                "confidence": validation.confidence,
                "category": validation.category
            },
            cache_info={
                "cache_hit": False,
                "similarity_method": similarity_result.validation_method,
                "llm_validated": False
            }
        )
        
        # Store results with TTL for future similarity detection
        print("💾 Storing results with TTL policy...")
        similarity_detector.store_query_with_results(
            query_str, 
            results, 
            metadata={
                "search_timestamp": time.time(),
                "validation_method": validation.validation_method,
                "max_results": max_results
            }
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Error in enhanced search: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/search/fast", response_model=QueryResponse)
async def fast_search_query(request: QueryRequest):
    """
    Fast search endpoint with reduced processing time
    """
    try:
        query_str = request.query.strip()
        max_results = min(request.max_results or 3, 3)  # Limit to 3 for fast search
        
        print(f"🚀 Fast search request for: {query_str}")
        
        if not query_str:
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Quick validation (heuristic only)
        validation = query_validator.validate_query(query_str)
        if not validation.is_valid:
            return QueryResponse(
                is_valid=False,
                found_similar=False,
                results=[],
                message=f"Invalid query: {validation.reason}",
                validation_info={
                    "validation_method": validation.validation_method,
                    "confidence": validation.confidence
                }
            )
        
        # Check cache (embedding similarity only)
        similarity_result = similarity_detector.find_similar_query(query_str)
        if similarity_result.found_similar and similarity_result.best_match:
            cached_results = similarity_result.best_match["results"]
            combined_summary = _generate_combined_summary_from_cached_results(cached_results, query_str)
            
            return QueryResponse(
                is_valid=True,
                found_similar=True,
                results=cached_results[:max_results],
                message="Found similar query in cache (fast mode)",
                combined_summary=combined_summary,
                validation_info={
                    "validation_method": validation.validation_method,
                    "confidence": validation.confidence
                },
                cache_info={
                    "cache_hit": True,
                    "similarity_method": "embedding_only",
                    "llm_validated": False
                }
            )
        
        # Perform fast web search
        results, combined_summary = await _perform_fast_web_search(query_str, max_results)
        
        response = QueryResponse(
            is_valid=True,
            found_similar=False,
            results=results,
            message="Fast search completed successfully",
            combined_summary=combined_summary,
            validation_info={
                "validation_method": validation.validation_method,
                "confidence": validation.confidence
            },
            cache_info={
                "cache_hit": False,
                "similarity_method": "embedding_only",
                "llm_validated": False
            }
        )
        
        # Store results with shorter TTL for fast searches
        similarity_detector.store_query_with_results(
            query_str, 
            results,
            metadata={
                "search_mode": "fast",
                "search_timestamp": time.time()
            }
        )
        
        return response
        
    except Exception as e:
        print(f"❌ Error in fast search: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Fast search failed: {str(e)}")

@app.get("/stats")
async def get_system_stats():
    """Get system statistics"""
    try:
        cache_stats = similarity_detector.get_cache_stats()
        
        return {
            "cache_statistics": cache_stats,
            "api_version": "2.0.0",
            "features": {
                "enhanced_query_validation": True,
                "llm_similarity_validation": True,
                "knn_search": cache_stats.get("knn_enabled", False),
                "ttl_policies": True,
                "dedicated_scraping_agent": True
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")

@app.post("/cache/clear")
async def clear_cache():
    """Clear expired cache entries"""
    try:
        removed_count = similarity_detector.clear_expired_queries()
        return {
            "message": f"Cache cleared successfully. Removed {removed_count} expired entries.",
            "removed_count": removed_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

async def _perform_enhanced_web_search(query_str: str, max_results: int, preferred_engines: Optional[List[str]] = None) -> tuple[List[Dict[str, Any]], str]:
    """
    Enhanced web search using available scraping methods
    """
    start_time = time.time()
    print(f"🚀 Starting enhanced web search for: '{query_str}'")
    
    # Enhance financial queries for better specificity
    enhanced_query = _enhance_financial_query(query_str)
    if enhanced_query != query_str:
        print(f"🔍 Enhanced financial query: '{query_str}' → '{enhanced_query}'")
        search_query = enhanced_query
    else:
        search_query = query_str
    
    summarizer = ContentSummarizer()
    
    if PLAYWRIGHT_AVAILABLE:
        # Use full WebScrapingAgent when available
        async with WebScrapingAgent(
            default_strategy=ScrapingStrategy.HYBRID,
            max_concurrent_requests=3,
            request_timeout=30,
            enable_caching=True
        ) as scraping_agent:
            
            # Search for results
            print("🔍 Searching with enhanced agent...")
            search_start = time.time()
            search_results = await scraping_agent.search_web(
                search_query,
                max_results=max_results,
                preferred_engines=preferred_engines or ["bing", "duckduckgo"]
            )
            search_end = time.time()
            print(f"🔍 Search completed in {search_end - search_start:.2f}s")
            
            if not search_results:
                return [], "No search results found for your query. Please try different keywords."
            
            # Convert search results to URLs for scraping
            urls_to_scrape = [result.url for result in search_results]
            
            # Scrape content in parallel
            print("📄 Scraping content with enhanced agent...")
            scraping_start = time.time()
            scraping_results = await scraping_agent.batch_scrape(
                urls_to_scrape,
                content_type=ContentType.TEXT
            )
            scraping_end = time.time()
            print(f"📄 Scraping completed in {scraping_end - scraping_start:.2f}s")
            
            # Process results
            processed_results = []
            successful_content = []
            successful_sources = []
            
            for i, (search_result, scraping_result) in enumerate(zip(search_results, scraping_results)):
                # Create result info
                result_info = {
                    "title": search_result.title,
                    "url": search_result.url,
                    "content_length": len(scraping_result.content),
                    "scraped_successfully": scraping_result.success,
                    "search_engine": search_result.search_engine,
                    "relevance_score": search_result.relevance_score,
                    "scraping_strategy": scraping_result.strategy_used,
                    "scraping_time": scraping_result.scraping_time
                }
                
                # Add summary if content was successfully scraped
                if scraping_result.success and len(scraping_result.content) > 30:
                    try:
                        print(f"📝 Attempting to summarize content from {search_result.url} ({len(scraping_result.content)} chars)")
                        summary_result = summarizer.summarize_content(
                            content=scraping_result.content,
                            max_length=150,
                            query_context=query_str
                        )
                        
                        result_info.update({
                            "summary": summary_result.summary,
                            "summary_method": summary_result.method,
                            "confidence": summary_result.confidence
                        })
                        
                        # Collect for combined summary
                        successful_content.append(scraping_result.content[:1000])
                        successful_sources.append(search_result.title)
                        print(f"✅ Summary created using {summary_result.method} method")
                        
                    except Exception as e:
                        print(f"❌ Summarization failed for {search_result.url}: {e}")
                        # Still include the raw content as a fallback
                        content_preview = scraping_result.content[:300] + "..." if len(scraping_result.content) > 300 else scraping_result.content
                        result_info["summary"] = f"Raw content preview: {content_preview}"
                        result_info["summary_method"] = "raw_content"
                        result_info["confidence"] = 0.3
                        
                        # Still collect for combined summary
                        successful_content.append(scraping_result.content[:1000])
                        successful_sources.append(search_result.title)
                else:
                    # More detailed error information
                    error_reason = "Content extraction failed"
                    if scraping_result.error:
                        error_reason += f": {scraping_result.error}"
                    elif len(scraping_result.content) <= 30:
                        error_reason += f" (only {len(scraping_result.content)} characters extracted)"
                    
                    result_info["summary"] = error_reason
                    result_info["summary_method"] = "error"
                    result_info["confidence"] = 0.0
                
                processed_results.append(result_info)
    
    else:
        # Use lightweight scraper for Render deployment
        print("🔍 Using lightweight scraper (Render mode)...")
        scraper = LightweightScraper()
        
        # Search and scrape using lightweight method
        enriched_results = scraper.search_and_scrape(search_query, max_results)
        
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
                "relevance_score": 1.0,  # Default score
                "scraping_strategy": "lightweight",
                "scraping_time": 1.0  # Default time
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
    print(f"✅ Enhanced search completed in {total_time:.2f}s total")
    
    return processed_results, combined_summary

async def _perform_fast_web_search(query_str: str, max_results: int) -> tuple[List[Dict[str, Any]], str]:
    """
    Fast web search with reduced processing
    """
    start_time = time.time()
    print(f"🚀 Starting fast web search for: '{query_str}'")
    
    async with WebScrapingAgent(
        default_strategy=ScrapingStrategy.REQUESTS,  # Faster strategy
        max_concurrent_requests=2,
        request_timeout=15,  # Shorter timeout
        enable_caching=True
    ) as scraping_agent:
        
        # Search for results
        search_results = await scraping_agent.search_web(
            query_str, 
            max_results=max_results,
            preferred_engines=["bing"]  # Use only one engine for speed
        )
        
        if not search_results:
            return [], "No search results found."
        
        # Quick scraping with shorter content
        results = []
        for search_result in search_results:
            scraping_result = await scraping_agent.scrape_content(
                search_result.url,
                content_type=ContentType.TEXT,
                strategy=ScrapingStrategy.REQUESTS
            )
            
            result_info = {
                "title": search_result.title,
                "url": search_result.url,
                "content_length": len(scraping_result.content),
                "scraped_successfully": scraping_result.success,
                "search_engine": search_result.search_engine,
                "scraping_strategy": scraping_result.strategy_used,
                "summary": scraping_result.content[:200] + "..." if scraping_result.content else "No content",
                "summary_method": "truncated",
                "confidence": 0.8 if scraping_result.success else 0.0
            }
            
            results.append(result_info)
        
        # Simple combined summary
        combined_summary = f"Found {len(results)} results for '{query_str}'. Fast search mode provides basic content extraction."
        
        total_time = time.time() - start_time
        print(f"✅ Fast search completed in {total_time:.2f}s total")
        
        return results, combined_summary

def _generate_combined_summary_from_cached_results(cached_results: List[Dict[str, Any]], query_str: str) -> str:
    """Generate combined summary from cached results"""
    try:
        summarizer = ContentSummarizer()
        
        # Extract summaries from cached results
        summaries = []
        for result in cached_results:
            if "summary" in result and result["summary"]:
                summaries.append(result["summary"])
        
        if not summaries:
            return "No summaries available from cached results."
        
        # Combine and re-summarize
        combined_content = "\n\n".join(summaries)
        combined_summary_result = summarizer.summarize_content(
            content=combined_content,
            max_length=250,
            query_context=query_str
        )
        
        return combined_summary_result.summary
        
    except Exception as e:
        print(f"❌ Error generating combined summary from cache: {e}")
        return "Unable to generate combined summary from cached results."

def _clean_scraped_content(content: str) -> str:
    """Clean scraped content"""
    if not content:
        return ""
    
    # Remove extra whitespace
    lines = content.split('\n')
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    return '\n'.join(cleaned_lines)

def _enhance_financial_query(query: str) -> str:
    """Enhance financial queries for better specificity and accuracy"""
    query_lower = query.lower().strip()
    
    # Specific company disambiguation patterns (most specific first)
    specific_company_patterns = {
        # Tata Group companies
        r'\btata\s+steel\b.*(?:share|stock|price)': 'Tata Steel Limited NSE:TATASTEEL stock price (steel manufacturing company)',
        r'\btata\s+motors?\b.*(?:share|stock|price)': 'Tata Motors Limited NSE:TATAMOTORS stock price (automobile company)',
        r'\btata\s+consultancy\b.*(?:share|stock|price)': 'Tata Consultancy Services NSE:TCS stock price',
        r'\btata\s+power\b.*(?:share|stock|price)': 'Tata Power NSE:TATAPOWER stock price',
        
        # ITC specific disambiguation  
        r'\bitc\s+ltd?\b.*(?:share|stock|price)': 'ITC Limited NSE:ITC stock price (tobacco FMCG company, not ITC Hotels)',
        r'\bitc\s+limited\b.*(?:share|stock|price)': 'ITC Limited NSE:ITC stock price',
        r'\bitc\s+(?:share|stock|price)': 'ITC Limited NSE:ITC stock price (not ITC Hotels)',
        
        # Reliance companies
        r'\breliance\s+industries\b.*(?:share|stock|price)': 'Reliance Industries NSE:RELIANCE stock price',
        r'\breliance\s+(?:share|stock|price)': 'Reliance Industries NSE:RELIANCE stock price',
        
        # Infosys variations
        r'\binfosys\b.*(?:share|stock|price)': 'Infosys Limited NSE:INFY stock price',
        
        # HDFC companies
        r'\bhdfc\s+bank\b.*(?:share|stock|price)': 'HDFC Bank NSE:HDFCBANK stock price',
        r'\bhdfc\b.*(?:share|stock|price)': 'HDFC Limited NSE:HDFC stock price',
    }
    
    # Apply specific company patterns first
    for pattern, replacement in specific_company_patterns.items():
        if re.search(pattern, query_lower):
            enhanced = re.sub(pattern, replacement, query_lower, flags=re.IGNORECASE)
            print(f"Enhanced query: '{query}' → '{enhanced}'")
            return enhanced
    
    # General patterns (only apply if no specific pattern matched)
    general_patterns = {
        # Multi-word company names (preserve full names)
        r'([a-zA-Z\s]+?)\s+ltd\s+(?:share|stock|price)': r'\1 Limited NSE stock price',
        r'([a-zA-Z\s]+?)\s+limited\s+(?:share|stock|price)': r'\1 Limited NSE stock price',
        r'([a-zA-Z\s]+?)\s+inc\s+(?:share|stock|price)': r'\1 Inc stock price',
        r'([a-zA-Z\s]+?)\s+corp\s+(?:share|stock|price)': r'\1 Corporation stock price',
        
        # Add market context for better search results
        r'(?:share|stock)\s+price\s+(?:of\s+)?([a-zA-Z\s]+)': r'\1 stock price NSE BSE live current',
        r'current\s+(?:share|stock)\s+price\s+([a-zA-Z\s]+)': r'\1 live stock price today NSE BSE',
    }
    
    # Apply general patterns
    for pattern, replacement in general_patterns.items():
        if re.search(pattern, query_lower):
            enhanced = re.sub(pattern, replacement, query_lower, flags=re.IGNORECASE)
            print(f"Enhanced query: '{query}' → '{enhanced}'")
            return enhanced
    
    return query

def _validate_financial_content(content: str, original_query: str) -> bool:
    """Validate that financial content matches the intended company with enhanced specificity"""
    query_lower = original_query.lower().strip()
    content_lower = content.lower()
    
    print(f"🔍 Validating content for query: '{original_query}'")
    
    # Skip validation for very short content (likely errors)
    if len(content.strip()) < 50:
        print("❌ Content too short for validation")
        return False
    
    # Specific company validation rules
    company_validations = {
        # Tata Group companies
        'tata steel': {
            'required_in_content': ['tata steel', 'tatasteel'],
            'stock_symbols': ['nse:tatasteel', 'bse:500470', 'tatasteel'],
            'industry_keywords': ['steel', 'iron', 'mining', 'metal', 'sponge iron', 'steel production'],
            'exclude_keywords': ['tata motors', 'tatamotors', 'automobile', 'car', 'vehicle', 'passenger vehicle', 'commercial vehicle'],
            'business_description': 'steel manufacturing'
        },
        'tata motors': {
            'required_in_content': ['tata motors', 'tatamotors'],
            'stock_symbols': ['nse:tatamotors', 'bse:500570', 'tatamotors'],
            'industry_keywords': ['automobile', 'car', 'vehicle', 'passenger vehicle', 'commercial vehicle', 'automotive', 'truck', 'bus'],
            'exclude_keywords': ['tata steel', 'tatasteel', 'steel', 'iron', 'mining', 'metal'],
            'business_description': 'automobile manufacturing'
        },
        'tata consultancy': {
            'required_in_content': ['tata consultancy', 'tcs'],
            'stock_symbols': ['nse:tcs', 'bse:532540'],
            'industry_keywords': ['software', 'it services', 'consulting', 'technology', 'digital'],
            'exclude_keywords': ['tata motors', 'tata steel'],
            'business_description': 'IT services'
        },
        'tata power': {
            'required_in_content': ['tata power', 'tatapower'],
            'stock_symbols': ['nse:tatapower', 'bse:500400'],
            'industry_keywords': ['power', 'electricity', 'energy', 'utility', 'generation', 'transmission'],
            'exclude_keywords': ['tata motors', 'tata steel'],
            'business_description': 'power generation'
        },
        
        # ITC companies
        'itc ltd': {
            'required_in_content': ['itc ltd', 'itc limited', 'itc'],
            'stock_symbols': ['nse:itc', 'bse:500875'],
            'industry_keywords': ['tobacco', 'cigarette', 'fmcg', 'consumer goods', 'food products', 'personal care'],
            'exclude_keywords': ['itc hotels', 'itchotels', 'hotel', 'hospitality', 'resort'],
            'business_description': 'tobacco and FMCG'
        },
        
        # Reliance companies
        'reliance industries': {
            'required_in_content': ['reliance industries', 'reliance'],
            'stock_symbols': ['nse:reliance', 'bse:500325'],
            'industry_keywords': ['petrochemical', 'oil', 'gas', 'refining', 'chemicals', 'retail', 'telecom'],
            'exclude_keywords': [],
            'business_description': 'conglomerate'
        },
        
        # Infosys
        'infosys': {
            'required_in_content': ['infosys'],
            'stock_symbols': ['nse:infy', 'bse:500209'],
            'industry_keywords': ['software', 'it services', 'consulting', 'technology', 'digital'],
            'exclude_keywords': [],
            'business_description': 'IT services'
        }
    }
    
    # Find which company is being queried
    matched_company = None
    for company_key in company_validations.keys():
        if company_key in query_lower:
            matched_company = company_key
            break
    
    if matched_company:
        validation_rules = company_validations[matched_company]
        print(f"🏢 Detected company: {matched_company}")
        
        # Check 1: Company name must be present
        company_name_found = any(name in content_lower for name in validation_rules['required_in_content'])
        if not company_name_found:
            print(f"❌ Company name not found in content. Expected: {validation_rules['required_in_content']}")
            return False
        print(f"✅ Company name found in content")
        
        # Check 2: Exclude wrong companies
        if validation_rules['exclude_keywords']:
            wrong_company_found = any(keyword in content_lower for keyword in validation_rules['exclude_keywords'])
            if wrong_company_found:
                print(f"❌ Wrong company detected in content: {validation_rules['exclude_keywords']}")
                return False
            print(f"✅ No conflicting companies found")
        
        # Check 3: Industry/business validation (at least one should match)
        industry_match = any(keyword in content_lower for keyword in validation_rules['industry_keywords'])
        stock_symbol_match = any(symbol in content_lower for symbol in validation_rules['stock_symbols'])
        
        if industry_match or stock_symbol_match:
            print(f"✅ Industry context or stock symbol validated")
            return True
        else:
            print(f"⚠️ No industry keywords or stock symbols found. Expected: {validation_rules['industry_keywords']} or {validation_rules['stock_symbols']}")
            # Be more lenient - if company name is found and no wrong company is detected, consider it valid
            return True
    
    # General validation for unspecified companies
    if any(term in query_lower for term in ['stock', 'share', 'price']):
        print("🔍 General financial query validation")
        
        # Extract company names from query (multi-word support)
        company_patterns = [
            r'([a-zA-Z\s]+?)\s+ltd',
            r'([a-zA-Z\s]+?)\s+limited',
            r'([a-zA-Z\s]+?)\s+inc',
            r'([a-zA-Z\s]+?)\s+corp',
            r'([a-zA-Z]+)\s+(?:share|stock|price)'
        ]
        
        query_company_names = []
        for pattern in company_patterns:
            matches = re.findall(pattern, query_lower)
            query_company_names.extend([name.strip() for name in matches if len(name.strip()) > 2])
        
        if query_company_names:
            print(f"🏢 Extracted company names from query: {query_company_names}")
            
            # Check if any of the extracted company names appear in content
            for company_name in query_company_names:
                if company_name in content_lower:
                    print(f"✅ Found company name '{company_name}' in content")
                    return True
            
            print(f"❌ None of the company names found in content: {query_company_names}")
            return False
    
    print("✅ No specific validation rules apply - considering valid")
    return True

def _is_fallback_content(content: str) -> bool:
    """Check if content is fallback/generated content"""
    fallback_indicators = [
        "generated content",
        "fallback content",
        "enhanced_fallback",
        "no content available"
    ]
    content_lower = content.lower()
    return any(indicator in content_lower for indicator in fallback_indicators) 