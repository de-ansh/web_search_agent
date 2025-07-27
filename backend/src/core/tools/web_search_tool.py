"""
Enhanced Web Search Tool for RAG Agent with Intelligence
"""

import asyncio
import time
import re
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import logging

# Import existing enhanced scraper
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

try:
    from src.core.enhanced_scraper import EnhancedScraper
except ImportError:
    # Fallback if import fails
    EnhancedScraper = None

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Enhanced search result with intelligence metrics"""
    title: str
    url: str
    content: str
    score: float
    source: str
    method: str
    word_count: int
    relevance_score: float = 0.0
    freshness_score: float = 0.0
    authority_score: float = 0.0
    content_quality_score: float = 0.0
    key_topics: List[str] = None
    sentiment: str = "neutral"
    language: str = "en"

class EnhancedWebSearchTool:
    """Enhanced web search tool with intelligent content processing"""
    
    def __init__(
        self, 
        max_results: int = 5, 
        timeout: int = 30,
        enable_content_analysis: bool = True,
        enable_deduplication: bool = True
    ):
        """
        Initialize enhanced web search tool
        
        Args:
            max_results: Maximum search results
            timeout: Request timeout
            enable_content_analysis: Enable content quality analysis
            enable_deduplication: Enable duplicate content removal
        """
        self.max_results = max_results
        self.timeout = timeout
        self.enable_content_analysis = enable_content_analysis
        self.enable_deduplication = enable_deduplication
        
        # Authority domains (higher trust score)
        self.authority_domains = {
            'wikipedia.org': 0.9,
            'github.com': 0.8,
            'stackoverflow.com': 0.8,
            'medium.com': 0.7,
            'arxiv.org': 0.9,
            'nature.com': 0.9,
            'sciencedirect.com': 0.8,
            'ieee.org': 0.8,
            'acm.org': 0.8,
            'edu': 0.8,  # Educational domains
            'gov': 0.9,  # Government domains
        }
        
        # Content quality indicators
        self.quality_indicators = {
            'positive': ['detailed', 'comprehensive', 'analysis', 'research', 'study', 'evidence', 'data'],
            'negative': ['click here', 'buy now', 'advertisement', 'sponsored', 'popup', 'subscribe']
        }
        
        if EnhancedScraper:
            logger.info("✅ Enhanced web search tool initialized with intelligent processing")
        else:
            logger.warning("⚠️ Enhanced scraper not available, using fallback")
    
    async def search_and_process(
        self,
        query: str,
        max_results: Optional[int] = None,
        query_context: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced search with intelligent processing
        
        Args:
            query: Search query
            max_results: Maximum results to return
            query_context: Additional context for relevance scoring
            
        Returns:
            List of intelligently processed search results
        """
        max_results = max_results or self.max_results
        start_time = time.time()
        
        try:
            if EnhancedScraper:
                # Use enhanced scraper with more results for filtering
                search_limit = min(max_results * 2, 10)  # Get more results for filtering
                
                async with EnhancedScraper(
                    use_playwright=False,  # Use requests for speed
                    timeout=self.timeout,
                    max_retries=1
                ) as scraper:
                    raw_results = await scraper.search_and_scrape(query, search_limit)
                    
                    # Process and enhance results
                    enhanced_results = []
                    for result in raw_results:
                        if result.success and result.content:
                            enhanced_result = await self._enhance_result(
                                result, query, query_context
                            )
                            enhanced_results.append(enhanced_result)
                    
                    # Apply intelligent filtering and ranking
                    filtered_results = await self._intelligent_filter_and_rank(
                        enhanced_results, query, max_results
                    )
                    
                    processing_time = time.time() - start_time
                    logger.info(f"✅ Enhanced web search returned {len(filtered_results)} results in {processing_time:.2f}s")
                    
                    return [self._result_to_dict(result) for result in filtered_results]
            else:
                # Fallback implementation
                return await self._fallback_search(query, max_results)
                
        except Exception as e:
            logger.error(f"❌ Enhanced web search failed: {e}")
            return []
    
    async def _enhance_result(
        self, 
        raw_result: Any, 
        query: str, 
        query_context: Optional[str]
    ) -> SearchResult:
        """Enhance a single search result with intelligence metrics"""
        
        # Calculate relevance score
        relevance_score = self._calculate_relevance_score(
            raw_result.content, raw_result.title, query, query_context
        )
        
        # Calculate authority score
        authority_score = self._calculate_authority_score(raw_result.url)
        
        # Calculate content quality score
        content_quality_score = self._calculate_content_quality_score(raw_result.content)
        
        # Calculate freshness score (placeholder - would need date extraction)
        freshness_score = 0.5  # Default neutral freshness
        
        # Extract key topics
        key_topics = self._extract_key_topics(raw_result.content, query)
        
        # Analyze sentiment (simple implementation)
        sentiment = self._analyze_sentiment(raw_result.content)
        
        # Calculate overall score
        overall_score = (
            relevance_score * 0.4 +
            authority_score * 0.2 +
            content_quality_score * 0.2 +
            freshness_score * 0.2
        )
        
        return SearchResult(
            title=raw_result.title,
            url=raw_result.url,
            content=raw_result.content,
            score=overall_score,
            source='web_search_enhanced',
            method=raw_result.method,
            word_count=raw_result.word_count,
            relevance_score=relevance_score,
            freshness_score=freshness_score,
            authority_score=authority_score,
            content_quality_score=content_quality_score,
            key_topics=key_topics,
            sentiment=sentiment,
            language='en'  # Default, could be detected
        )
    
    async def _intelligent_filter_and_rank(
        self,
        results: List[SearchResult],
        query: str,
        max_results: int
    ) -> List[SearchResult]:
        """Apply intelligent filtering and ranking"""
        
        if not results:
            return []
        
        # Remove duplicates if enabled
        if self.enable_deduplication:
            results = self._remove_duplicates(results)
        
        # Filter low-quality results
        filtered_results = [
            result for result in results
            if result.content_quality_score > 0.3 and result.relevance_score > 0.2
        ]
        
        # Sort by overall score
        filtered_results.sort(key=lambda x: x.score, reverse=True)
        
        # Ensure diversity in sources (avoid too many from same domain)
        diverse_results = self._ensure_source_diversity(filtered_results)
        
        return diverse_results[:max_results]
    
    def _calculate_relevance_score(
        self, 
        content: str, 
        title: str, 
        query: str, 
        context: Optional[str]
    ) -> float:
        """Calculate relevance score based on content and query"""
        
        query_terms = query.lower().split()
        content_lower = content.lower()
        title_lower = title.lower()
        
        # Count query term matches
        title_matches = sum(1 for term in query_terms if term in title_lower)
        content_matches = sum(1 for term in query_terms if term in content_lower)
        
        # Calculate scores
        title_score = title_matches / len(query_terms) if query_terms else 0
        content_score = min(content_matches / len(query_terms), 1.0) if query_terms else 0
        
        # Boost for exact phrase matches
        exact_phrase_bonus = 0.2 if query.lower() in content_lower else 0
        
        # Context relevance (if provided)
        context_score = 0
        if context:
            context_terms = context.lower().split()
            context_matches = sum(1 for term in context_terms if term in content_lower)
            context_score = min(context_matches / len(context_terms), 0.3) if context_terms else 0
        
        # Combine scores
        relevance_score = (
            title_score * 0.4 +
            content_score * 0.4 +
            exact_phrase_bonus +
            context_score
        )
        
        return min(relevance_score, 1.0)
    
    def _calculate_authority_score(self, url: str) -> float:
        """Calculate authority score based on domain"""
        
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc.lower()
            
            # Check exact domain matches
            for auth_domain, score in self.authority_domains.items():
                if auth_domain in domain:
                    return score
            
            # Check for educational/government domains
            if domain.endswith('.edu'):
                return 0.8
            elif domain.endswith('.gov'):
                return 0.9
            elif domain.endswith('.org'):
                return 0.6
            else:
                return 0.5  # Default score
                
        except Exception:
            return 0.5
    
    def _calculate_content_quality_score(self, content: str) -> float:
        """Calculate content quality score"""
        
        content_lower = content.lower()
        
        # Count positive and negative indicators
        positive_count = sum(1 for indicator in self.quality_indicators['positive'] 
                           if indicator in content_lower)
        negative_count = sum(1 for indicator in self.quality_indicators['negative'] 
                           if indicator in content_lower)
        
        # Length factor (not too short, not too long)
        length_score = min(len(content) / 1000, 1.0) if len(content) > 100 else 0.2
        
        # Sentence structure (simple check for periods)
        sentence_count = content.count('.')
        structure_score = min(sentence_count / 10, 0.3) if sentence_count > 0 else 0
        
        # Calculate quality score
        quality_score = (
            length_score * 0.4 +
            structure_score * 0.2 +
            min(positive_count * 0.1, 0.3) -
            min(negative_count * 0.1, 0.2)
        )
        
        return max(min(quality_score, 1.0), 0.0)
    
    def _extract_key_topics(self, content: str, query: str) -> List[str]:
        """Extract key topics from content"""
        
        # Simple keyword extraction (in production, use NLP)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Filter common words and get unique terms
        common_words = {'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been', 'said', 'each', 'which', 'their', 'time', 'more', 'very', 'what', 'know', 'just', 'first', 'into', 'over', 'think', 'also', 'your', 'work', 'life', 'only', 'can', 'still', 'should', 'after', 'being', 'now', 'made', 'before', 'here', 'through', 'when', 'where', 'much', 'some', 'these', 'many', 'would', 'there'}
        
        filtered_words = [word for word in words if word not in common_words and len(word) > 4]
        
        # Count frequency and get top terms
        word_freq = {}
        for word in filtered_words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency and return top 10
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in top_words[:10]]
    
    def _analyze_sentiment(self, content: str) -> str:
        """Simple sentiment analysis"""
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'best', 'love', 'perfect', 'awesome', 'fantastic']
        negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'horrible', 'disgusting', 'disappointing', 'failed', 'broken']
        
        content_lower = content.lower()
        
        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _remove_duplicates(self, results: List[SearchResult]) -> List[SearchResult]:
        """Remove duplicate content"""
        
        seen_content: Set[str] = set()
        unique_results = []
        
        for result in results:
            # Create content hash for comparison
            content_hash = hash(result.content[:500])  # Use first 500 chars
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_results.append(result)
        
        return unique_results
    
    def _ensure_source_diversity(self, results: List[SearchResult]) -> List[SearchResult]:
        """Ensure diversity in sources"""
        
        domain_count = {}
        diverse_results = []
        
        for result in results:
            try:
                from urllib.parse import urlparse
                domain = urlparse(result.url).netloc
                
                # Limit results per domain
                if domain_count.get(domain, 0) < 2:  # Max 2 results per domain
                    diverse_results.append(result)
                    domain_count[domain] = domain_count.get(domain, 0) + 1
                    
            except Exception:
                diverse_results.append(result)  # Include if parsing fails
        
        return diverse_results
    
    def _result_to_dict(self, result: SearchResult) -> Dict[str, Any]:
        """Convert SearchResult to dictionary"""
        return {
            'title': result.title,
            'url': result.url,
            'content': result.content,
            'score': result.score,
            'source': result.source,
            'method': result.method,
            'word_count': result.word_count,
            'relevance_score': result.relevance_score,
            'freshness_score': result.freshness_score,
            'authority_score': result.authority_score,
            'content_quality_score': result.content_quality_score,
            'key_topics': result.key_topics,
            'sentiment': result.sentiment,
            'language': result.language
        }
    
    async def _fallback_search(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        """Enhanced fallback search implementation"""
        
        logger.warning("⚠️ Using enhanced fallback search (returns intelligent mock data)")
        
        # Generate more realistic mock results with intelligence metrics
        mock_results = []
        
        for i in range(min(max_results, 3)):
            result = {
                'title': f"Enhanced Result {i+1}: {query}",
                'url': f"https://example{i+1}.com/article?q={query.replace(' ', '-')}",
                'content': f"This is an enhanced mock search result for '{query}'. It demonstrates intelligent content processing with relevance scoring, authority metrics, and content quality analysis. The system can handle complex queries and provide contextually relevant information.",
                'score': 0.8 - (i * 0.1),  # Decreasing scores
                'source': 'web_search_enhanced_fallback',
                'method': 'mock_enhanced',
                'word_count': 45 + (i * 5),
                'relevance_score': 0.9 - (i * 0.1),
                'freshness_score': 0.7,
                'authority_score': 0.6 + (i * 0.1),
                'content_quality_score': 0.8 - (i * 0.05),
                'key_topics': [query.split()[0] if query.split() else 'topic', 'information', 'analysis'],
                'sentiment': 'neutral',
                'language': 'en'
            }
            mock_results.append(result)
        
        return mock_results

# Backward compatibility alias
WebSearchTool = EnhancedWebSearchTool