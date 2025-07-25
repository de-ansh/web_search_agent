"""
Enhanced research service combining improved web scraping with Gemini AI summarization
"""

import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import logging

try:
    from ..core.enhanced_scraper import EnhancedScraper, ScrapingResult
    from ..ai.gemini_summarizer import GeminiSummarizer, SummaryResult
except ImportError:
    # Fallback for direct execution
    from core.enhanced_scraper import EnhancedScraper, ScrapingResult
    from ai.gemini_summarizer import GeminiSummarizer, SummaryResult

logger = logging.getLogger(__name__)

@dataclass
class ResearchResult:
    """Complete research result with scraping and summarization"""
    query: str
    sources: List[Dict[str, Any]]
    combined_summary: str
    individual_summaries: List[Dict[str, Any]]
    processing_time: float
    success: bool
    method_used: str
    total_sources: int
    successful_scrapes: int
    error: Optional[str] = None

class EnhancedResearchService:
    """Enhanced research service with reliable scraping and AI summarization"""
    
    def __init__(self, 
                 use_playwright: bool = True,
                 preferred_ai_method: str = "gemini",
                 max_sources: int = 5,
                 summary_length: int = 150):
        """
        Initialize enhanced research service
        
        Args:
            use_playwright: Use Playwright for JavaScript-heavy sites
            preferred_ai_method: Preferred AI method ('gemini', 'openai', 'extractive')
            max_sources: Maximum number of sources to scrape
            summary_length: Target length for summaries in words
        """
        self.use_playwright = use_playwright
        self.preferred_ai_method = preferred_ai_method
        self.max_sources = max_sources
        self.summary_length = summary_length
        
        # Initialize components
        self.scraper = None
        try:
            self.summarizer = GeminiSummarizer(preferred_method=preferred_ai_method)
        except Exception as e:
            logger.warning(f"Failed to initialize GeminiSummarizer: {e}")
            # Fallback to a simple summarizer
            self.summarizer = None
        
        logger.info(f"✅ Enhanced Research Service initialized with {preferred_ai_method} AI")
    
    async def research_query(self, query: str) -> ResearchResult:
        """
        Perform comprehensive research on a query
        
        Args:
            query: Research query
            
        Returns:
            ResearchResult with scraped content and AI-generated summaries
        """
        start_time = time.time()
        logger.info(f"🔍 Starting enhanced research for: {query}")
        
        try:
            # Initialize scraper
            async with EnhancedScraper(
                use_playwright=self.use_playwright,
                timeout=30,
                max_retries=2
            ) as scraper:
                self.scraper = scraper
                
                # Step 1: Search and scrape content
                logger.info("📡 Searching and scraping content...")
                scraping_results = await scraper.search_and_scrape(query, self.max_sources)
                
                if not scraping_results:
                    return ResearchResult(
                        query=query,
                        sources=[],
                        combined_summary="No sources could be found or scraped for this query.",
                        individual_summaries=[],
                        processing_time=time.time() - start_time,
                        success=False,
                        method_used="none",
                        total_sources=0,
                        successful_scrapes=0,
                        error="No scraping results obtained"
                    )
                
                # Step 2: Filter successful scrapes
                successful_scrapes = [r for r in scraping_results if r.success and len(r.content.strip()) > 100]
                
                if not successful_scrapes:
                    # Use all results even if not fully successful
                    successful_scrapes = scraping_results
                
                logger.info(f"📄 Successfully scraped {len(successful_scrapes)}/{len(scraping_results)} sources")
                
                # Step 3: Generate individual summaries
                logger.info("🤖 Generating AI summaries...")
                individual_summaries = await self._generate_individual_summaries(
                    successful_scrapes, query
                )
                
                # Step 4: Generate combined summary
                combined_summary = await self._generate_combined_summary(
                    successful_scrapes, individual_summaries, query
                )
                
                # Step 5: Prepare source information
                sources = self._prepare_source_info(scraping_results)
                
                processing_time = time.time() - start_time
                
                logger.info(f"✅ Research completed in {processing_time:.2f}s")
                
                return ResearchResult(
                    query=query,
                    sources=sources,
                    combined_summary=combined_summary,
                    individual_summaries=individual_summaries,
                    processing_time=processing_time,
                    success=True,
                    method_used=self.summarizer.preferred_method,
                    total_sources=len(scraping_results),
                    successful_scrapes=len(successful_scrapes)
                )
                
        except Exception as e:
            logger.error(f"❌ Research failed: {e}")
            return ResearchResult(
                query=query,
                sources=[],
                combined_summary=f"Research failed due to technical error: {str(e)}",
                individual_summaries=[],
                processing_time=time.time() - start_time,
                success=False,
                method_used="error",
                total_sources=0,
                successful_scrapes=0,
                error=str(e)
            )
    
    async def _generate_individual_summaries(
        self, 
        scraping_results: List[ScrapingResult], 
        query: str
    ) -> List[Dict[str, Any]]:
        """Generate individual summaries for each scraped source"""
        individual_summaries = []
        
        for i, result in enumerate(scraping_results):
            try:
                logger.info(f"🤖 Summarizing source {i+1}/{len(scraping_results)}: {result.title[:50]}...")
                
                # Generate summary with query context
                if self.summarizer:
                    summary_result = self.summarizer.summarize_content(
                        content=result.content,
                        max_length=self.summary_length,
                        query_context=query
                    )
                else:
                    # Fallback to simple truncation
                    content_words = result.content.split()
                    summary_text = " ".join(content_words[:self.summary_length])
                    if len(content_words) > self.summary_length:
                        summary_text += "..."
                    
                    from ..ai.gemini_summarizer import SummaryResult
                    summary_result = SummaryResult(
                        summary=summary_text,
                        method="simple_fallback",
                        word_count=len(summary_text.split()),
                        original_length=len(content_words),
                        confidence=0.5,
                        processing_time=0.1
                    )
                
                individual_summaries.append({
                    'source_title': result.title,
                    'source_url': result.url,
                    'summary': summary_result.summary,
                    'method': summary_result.method,
                    'confidence': summary_result.confidence,
                    'word_count': summary_result.word_count,
                    'processing_time': summary_result.processing_time,
                    'scraping_method': result.method,
                    'scraping_success': result.success
                })
                
            except Exception as e:
                logger.error(f"❌ Failed to summarize source {i+1}: {e}")
                individual_summaries.append({
                    'source_title': result.title,
                    'source_url': result.url,
                    'summary': f"Summary generation failed: {str(e)}",
                    'method': 'error',
                    'confidence': 0.0,
                    'word_count': 0,
                    'processing_time': 0.0,
                    'scraping_method': result.method,
                    'scraping_success': result.success
                })
        
        return individual_summaries
    
    async def _generate_combined_summary(
        self, 
        scraping_results: List[ScrapingResult], 
        individual_summaries: List[Dict[str, Any]], 
        query: str
    ) -> str:
        """Generate a comprehensive combined summary"""
        try:
            # Combine all content for comprehensive summary
            all_content = []
            
            # Add individual summaries (they're already processed and clean)
            for summary_info in individual_summaries:
                if summary_info['summary'] and len(summary_info['summary'].strip()) > 20:
                    all_content.append(f"Source: {summary_info['source_title']}\n{summary_info['summary']}")
            
            # If no good summaries, use original content (truncated)
            if not all_content:
                for result in scraping_results:
                    if result.content and len(result.content.strip()) > 100:
                        # Take first portion of content
                        content_preview = result.content[:1000] + "..." if len(result.content) > 1000 else result.content
                        all_content.append(f"Source: {result.title}\n{content_preview}")
            
            if not all_content:
                return "Unable to generate a comprehensive summary from the available sources."
            
            # Combine all content
            combined_content = "\n\n".join(all_content)
            
            logger.info("🤖 Generating comprehensive combined summary...")
            
            # Generate comprehensive summary with longer length
            combined_summary_result = self.summarizer.summarize_content(
                content=combined_content,
                max_length=self.summary_length * 2,  # Longer for combined summary
                query_context=query
            )
            
            return combined_summary_result.summary
            
        except Exception as e:
            logger.error(f"❌ Failed to generate combined summary: {e}")
            
            # Fallback: combine individual summaries manually
            try:
                summaries = [s['summary'] for s in individual_summaries if s['summary'] and len(s['summary'].strip()) > 20]
                if summaries:
                    return f"Based on multiple sources regarding '{query}': " + " ".join(summaries[:3])  # Take first 3
                else:
                    return f"Research on '{query}' was conducted but summary generation encountered technical difficulties."
            except:
                return f"Unable to generate summary for query: {query}"
    
    def _prepare_source_info(self, scraping_results: List[ScrapingResult]) -> List[Dict[str, Any]]:
        """Prepare source information for the response"""
        sources = []
        
        for result in scraping_results:
            sources.append({
                'title': result.title,
                'url': result.url,
                'success': result.success,
                'method': result.method,
                'word_count': result.word_count,
                'processing_time': result.processing_time,
                'error': result.error
            })
        
        return sources
    
    async def quick_research(self, query: str, max_sources: int = 3) -> ResearchResult:
        """
        Perform quick research with fewer sources for faster results
        
        Args:
            query: Research query
            max_sources: Maximum number of sources (default: 3)
            
        Returns:
            ResearchResult with quick research results
        """
        # Temporarily adjust max sources
        original_max = self.max_sources
        self.max_sources = max_sources
        
        try:
            result = await self.research_query(query)
            return result
        finally:
            # Restore original max sources
            self.max_sources = original_max
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of the research service"""
        return {
            "service": "Enhanced Research Service",
            "scraper_playwright": self.use_playwright,
            "ai_method": self.preferred_ai_method,
            "max_sources": self.max_sources,
            "summary_length": self.summary_length,
            "summarizer_status": self.summarizer.get_status()
        }