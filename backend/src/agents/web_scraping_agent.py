"""
Dedicated Web Scraping Agent for robust content extraction and search
"""

import asyncio
import logging
import time
import random
import re
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse, quote_plus
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup, Tag
import requests
import json
from datetime import datetime, timedelta
import hashlib
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScrapingStrategy(Enum):
    """Different scraping strategies"""
    PLAYWRIGHT = "playwright"
    REQUESTS = "requests"
    HYBRID = "hybrid"

class ContentType(Enum):
    """Types of content to extract"""
    TEXT = "text"
    STRUCTURED = "structured"
    METADATA = "metadata"
    FULL = "full"

@dataclass
class ScrapingResult:
    """Result of a scraping operation"""
    url: str
    title: str
    content: str
    success: bool
    metadata: Dict[str, Any]
    scraping_time: float
    strategy_used: str
    error: Optional[str] = None

@dataclass
class SearchResult:
    """Result of a search operation"""
    title: str
    url: str
    snippet: str
    search_engine: str
    relevance_score: float
    metadata: Dict[str, Any]

class WebScrapingAgent:
    """Advanced web scraping agent with multiple strategies and robust error handling"""
    
    def __init__(self, 
                 default_strategy: ScrapingStrategy = ScrapingStrategy.HYBRID,
                 max_concurrent_requests: int = 3,
                 request_timeout: int = 30,
                 enable_caching: bool = True,
                 cache_duration: int = 3600):
        """
        Initialize the web scraping agent
        
        Args:
            default_strategy: Default scraping strategy to use
            max_concurrent_requests: Maximum number of concurrent requests
            request_timeout: Request timeout in seconds
            enable_caching: Whether to enable result caching
            cache_duration: Cache duration in seconds
        """
        self.default_strategy = default_strategy
        self.max_concurrent_requests = max_concurrent_requests
        self.request_timeout = request_timeout
        self.enable_caching = enable_caching
        self.cache_duration = cache_duration
        
        # Initialize components
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        
        # Result caching
        self.content_cache: Dict[str, Dict[str, Any]] = {}
        self.search_cache: Dict[str, List[SearchResult]] = {}
        
        # Performance tracking
        self.strategy_performance: Dict[str, Dict[str, float]] = {
            "playwright": {"success_rate": 0.8, "avg_time": 5.0},
            "requests": {"success_rate": 0.6, "avg_time": 2.0},
            "hybrid": {"success_rate": 0.9, "avg_time": 3.5}
        }
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        
        # Search engines configuration
        self.search_engines = {
            "bing": self._search_bing,
            "duckduckgo": self._search_duckduckgo,
            "yahoo": self._search_yahoo,
            "searx": self._search_searx
        }
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self._initialize_playwright()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._cleanup()
    
    async def _initialize_playwright(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Enhanced browser configuration
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-accelerated-2d-canvas",
                    "--disable-gpu",
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--no-first-run",
                    "--no-zygote"
                ]
            )
            
            # Create context with stealth settings
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=random.choice(self.user_agents),
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=True
            )
            
            # Block unnecessary resources
            await context.route("**/*.{png,jpg,jpeg,gif,svg,ico,woff,woff2,ttf,eot}", lambda route: route.abort())
            await context.route("**/*{google-analytics,googletagmanager,facebook}*", lambda route: route.abort())
            
            self.page = await context.new_page()
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            # Continue without Playwright - will use requests-only strategy
    
    async def _cleanup(self):
        """Clean up resources"""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def search_web(self, query: str, max_results: int = 5, preferred_engines: Optional[List[str]] = None) -> List[SearchResult]:
        """
        Search the web using multiple search engines
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            preferred_engines: List of preferred search engines
            
        Returns:
            List of search results
        """
        # Check cache first
        if self.enable_caching and query in self.search_cache:
            cached_results = self.search_cache[query]
            if self._is_cache_valid(cached_results[0].metadata.get("cached_at", 0)):
                logger.info(f"Returning cached search results for: {query}")
                return cached_results[:max_results]
        
        # Determine search engines to use
        engines_to_use = preferred_engines or list(self.search_engines.keys())
        
        # Try search engines in order of preference
        for engine_name in engines_to_use:
            if engine_name in self.search_engines:
                try:
                    logger.info(f"Searching with {engine_name} for: {query}")
                    results = await self.search_engines[engine_name](query, max_results)
                    
                    if results:
                        # Cache results
                        if self.enable_caching:
                            for result in results:
                                result.metadata["cached_at"] = time.time()
                            self.search_cache[query] = results
                        
                        logger.info(f"Found {len(results)} results from {engine_name}")
                        return results
                        
                except Exception as e:
                    logger.error(f"Search failed with {engine_name}: {e}")
                    continue
        
        # If all engines fail, return empty results
        logger.warning(f"All search engines failed for query: {query}")
        return []
    
    async def scrape_content(self, url: str, content_type: ContentType = ContentType.TEXT, strategy: Optional[ScrapingStrategy] = None) -> ScrapingResult:
        """
        Scrape content from a URL using the specified strategy
        
        Args:
            url: URL to scrape
            content_type: Type of content to extract
            strategy: Scraping strategy to use
            
        Returns:
            ScrapingResult with extracted content
        """
        start_time = time.time()
        
        # Check cache first
        if self.enable_caching and url in self.content_cache:
            cached_result = self.content_cache[url]
            if self._is_cache_valid(cached_result.get("cached_at", 0)):
                logger.info(f"Returning cached content for: {url}")
                return ScrapingResult(
                    url=url,
                    title=cached_result["title"],
                    content=cached_result["content"],
                    success=True,
                    metadata=cached_result["metadata"],
                    scraping_time=cached_result["scraping_time"],
                    strategy_used=cached_result["strategy_used"]
                )
        
        # Choose strategy
        strategy_to_use = strategy or self.default_strategy
        
        # Try different strategies based on performance
        strategies_to_try = self._get_ordered_strategies(strategy_to_use)
        
        for current_strategy in strategies_to_try:
            try:
                result = await self._scrape_with_strategy(url, current_strategy, content_type)
                
                if result.success:
                    # Cache successful result
                    if self.enable_caching:
                        self.content_cache[url] = {
                            "title": result.title,
                            "content": result.content,
                            "metadata": result.metadata,
                            "scraping_time": result.scraping_time,
                            "strategy_used": result.strategy_used,
                            "cached_at": time.time()
                        }
                    
                    # Update strategy performance
                    self._update_strategy_performance(current_strategy.value, True, result.scraping_time)
                    
                    return result
                
            except Exception as e:
                logger.error(f"Scraping failed with {current_strategy.value}: {e}")
                self._update_strategy_performance(current_strategy.value, False, time.time() - start_time)
                continue
        
        # All strategies failed
        return ScrapingResult(
            url=url,
            title="",
            content="",
            success=False,
            metadata={"error": "All scraping strategies failed"},
            scraping_time=time.time() - start_time,
            strategy_used="none",
            error="All scraping strategies failed"
        )
    
    async def batch_scrape(self, urls: List[str], content_type: ContentType = ContentType.TEXT) -> List[ScrapingResult]:
        """
        Scrape multiple URLs concurrently
        
        Args:
            urls: List of URLs to scrape
            content_type: Type of content to extract
            
        Returns:
            List of scraping results
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        async def scrape_single(url: str) -> ScrapingResult:
            async with semaphore:
                return await self.scrape_content(url, content_type)
        
        tasks = [scrape_single(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch scraping error: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _scrape_with_strategy(self, url: str, strategy: ScrapingStrategy, content_type: ContentType) -> ScrapingResult:
        """Scrape content using a specific strategy"""
        start_time = time.time()
        
        if strategy == ScrapingStrategy.PLAYWRIGHT:
            return await self._scrape_with_playwright(url, content_type, start_time)
        elif strategy == ScrapingStrategy.REQUESTS:
            return await self._scrape_with_requests(url, content_type, start_time)
        elif strategy == ScrapingStrategy.HYBRID:
            # Try Playwright first, fall back to requests
            try:
                return await self._scrape_with_playwright(url, content_type, start_time)
            except Exception:
                return await self._scrape_with_requests(url, content_type, start_time)
        else:
            raise ValueError(f"Unknown scraping strategy: {strategy}")
    
    async def _scrape_with_playwright(self, url: str, content_type: ContentType, start_time: float) -> ScrapingResult:
        """Scrape content using Playwright"""
        if not self.page:
            raise RuntimeError("Playwright not initialized")
        
        try:
            # Navigate to the page with increased timeout
            await self.page.goto(url, timeout=self.request_timeout * 1000, wait_until="domcontentloaded")
            
            # Wait for additional content to load
            try:
                await self.page.wait_for_load_state("networkidle", timeout=10000)
            except:
                # If networkidle fails, wait for domcontentloaded
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                
            # Wait a bit more for dynamic content
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.warning(f"Navigation issues for {url}: {e}")
            # Continue with whatever content we have
        
        # Extract content
        content = await self.page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Extract main content based on content type
        if content_type == ContentType.TEXT:
            extracted_content = self._extract_text_content(soup)
        elif content_type == ContentType.STRUCTURED:
            extracted_content = self._extract_structured_content(soup)
        elif content_type == ContentType.METADATA:
            extracted_content = self._extract_metadata(soup)
        else:  # FULL
            extracted_content = self._extract_full_content(soup)
        
        return ScrapingResult(
            url=url,
            title=title,
            content=extracted_content,
            success=True,
            metadata={
                "word_count": len(extracted_content.split()),
                "content_type": content_type.value,
                "scraped_at": datetime.now().isoformat()
            },
            scraping_time=time.time() - start_time,
            strategy_used="playwright"
        )
    
    async def _scrape_with_requests(self, url: str, content_type: ContentType, start_time: float) -> ScrapingResult:
        """Scrape content using requests library"""
        headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        response = requests.get(url, headers=headers, timeout=self.request_timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        
        # Extract content based on content type
        if content_type == ContentType.TEXT:
            extracted_content = self._extract_text_content(soup)
        elif content_type == ContentType.STRUCTURED:
            extracted_content = self._extract_structured_content(soup)
        elif content_type == ContentType.METADATA:
            extracted_content = self._extract_metadata(soup)
        else:  # FULL
            extracted_content = self._extract_full_content(soup)
        
        return ScrapingResult(
            url=url,
            title=title,
            content=extracted_content,
            success=True,
            metadata={
                "word_count": len(extracted_content.split()),
                "content_type": content_type.value,
                "scraped_at": datetime.now().isoformat(),
                "status_code": response.status_code
            },
            scraping_time=time.time() - start_time,
            strategy_used="requests"
        )
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML with improved extraction"""
        # Remove script and style elements only (preserve nav, header, footer for now)
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Remove navigation, ads, and other non-content elements
        unwanted_elements = []
        for element in soup.find_all(True):
            if isinstance(element, Tag):
                # Check element names
                if element.name in ['nav', 'header', 'footer', 'aside', 'menu']:
                    unwanted_elements.append(element)
                    continue
                
                # Check classes and IDs
                classes = element.get('class')
                element_id = element.get('id') or ''
                
                if isinstance(classes, list):
                    class_str = ' '.join(classes).lower()
                elif classes:
                    class_str = str(classes).lower()
                else:
                    class_str = ''
                
                element_id = element_id.lower() if isinstance(element_id, str) else ''
                
                # Remove elements with unwanted classes/IDs (be more selective)
                unwanted_patterns = [
                    'advertisement', 'google-ad', 'ads-container', 'ad-banner', 'promo-box',
                    'navbar', 'nav-menu', 'sidebar', 'pagination', 'social-share',
                    'cookie-notice', 'popup', 'modal', 'overlay', 'redirect-notice',
                    'skip-link', 'back-to-top', 'search-box', 'newsletter-signup'
                ]
                
                if any(pattern in class_str or pattern in element_id for pattern in unwanted_patterns):
                    unwanted_elements.append(element)
        
        for element in unwanted_elements:
            element.decompose()
        
        # Enhanced content selectors - try multiple approaches
        main_content = ""
        
        # 1. Try semantic content containers first
        semantic_selectors = [
            "main",
            "article", 
            "[role='main']",
            ".main-content",
            ".post-content",
            ".entry-content",
            ".content-area",
            ".article-content",
            ".story-content",
            ".post-body",
            "#main-content",
            "#content",
            ".content"
        ]
        
        for selector in semantic_selectors:
            content_element = soup.select_one(selector)
            if content_element:
                main_content = content_element.get_text()
                if len(main_content.strip()) > 200:  # Prefer longer content
                    break
        
        # 2. Try looking for paragraphs and headings if semantic approach fails
        if not main_content or len(main_content.strip()) < 200:
            paragraphs = soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            paragraph_texts = []
            for p in paragraphs:
                if isinstance(p, Tag):
                    text = p.get_text().strip()
                    if len(text) > 10:  # Skip very short paragraphs
                        paragraph_texts.append(text)
            
            if paragraph_texts:
                main_content = '\n'.join(paragraph_texts)
        
        # 3. Fall back to body content if still insufficient
        if not main_content or len(main_content.strip()) < 100:
            body = soup.find('body')
            if body and isinstance(body, Tag):
                # Remove obvious navigation and footer elements
                for elem in body.find_all(True):
                    if isinstance(elem, Tag) and elem.name in ['nav', 'footer', 'header']:
                        classes = elem.get('class')
                        if isinstance(classes, list):
                            class_str = ' '.join(classes).lower()
                            if any(word in class_str for word in ['navigation', 'footer', 'header', 'menu']):
                                elem.decompose()
                
                main_content = body.get_text()
        
        # Enhanced text cleaning
        if main_content:
            # Split into lines and clean each
            lines = main_content.split('\n')
            cleaned_lines = []
            
            # Patterns to filter out common web artifacts (reduced for better content extraction)
            filter_patterns = [
                r'please if the page does not redirect automatically',
                r'click here to continue',
                r'loading\.\.\.', r'please wait',
                r'javascript must be enabled',
                r'cookies? (are|is) (required|enabled)',
                r'subscribe to our newsletter',
                r'©.*all rights reserved',
                r'error \d+', r'page not found'
            ]
            
            for line in lines:
                line = line.strip()
                # Skip empty lines and very short lines
                if len(line) > 10:  # Reduced threshold for better content extraction
                    # Remove excessive whitespace
                    line = ' '.join(line.split())
                    
                    # Filter out common web artifacts
                    line_lower = line.lower()
                    should_skip = False
                    
                    for pattern in filter_patterns:
                        if re.search(pattern, line_lower):
                            should_skip = True
                            break
                    
                    if not should_skip:
                        cleaned_lines.append(line)
            
            # Join lines and ensure readability
            text = '\n'.join(cleaned_lines)
            
            # Remove duplicate sentences
            sentences = re.split(r'[.!?]+', text)
            unique_sentences = []
            seen_sentences = set()
            
            for sentence in sentences:
                sentence = sentence.strip()
                sentence_lower = sentence.lower()
                
                # Skip very short sentences
                if len(sentence) < 15:  # Reduced minimum sentence length
                    continue
                
                # Check for duplicates (normalized)
                normalized = re.sub(r'\s+', ' ', sentence_lower)
                if normalized not in seen_sentences:
                    seen_sentences.add(normalized)
                    unique_sentences.append(sentence)
            
            # Reconstruct text from unique sentences
            text = '. '.join(unique_sentences)
            if text and not text.endswith('.'):
                text += '.'
            
            return text
        
        return ""
    
    def _extract_structured_content(self, soup: BeautifulSoup) -> str:
        """Extract structured content (headings, lists, etc.)"""
        structured_content = []
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            if isinstance(heading, Tag) and heading.name:
                structured_content.append(f"[{heading.name.upper()}] {heading.get_text().strip()}")
        
        # Extract lists
        for ul in soup.find_all('ul'):
            if isinstance(ul, Tag):
                for li in ul.find_all('li'):
                    if isinstance(li, Tag):
                        structured_content.append(f"• {li.get_text().strip()}")
        for ol in soup.find_all('ol'):
            if isinstance(ol, Tag):
                for i, li in enumerate(ol.find_all('li'), 1):
                    if isinstance(li, Tag):
                        structured_content.append(f"{i}. {li.get_text().strip()}")
        
        return '\n'.join(structured_content)
    def _extract_metadata(self, soup: BeautifulSoup) -> str:
        """Extract metadata from HTML"""
        metadata = {}
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            if isinstance(meta, Tag):
                name = meta.get('name') or meta.get('property')
                content = meta.get('content')
                if name and content:
                    metadata[name] = content
        
        # Extract structured data
        for script in soup.find_all('script', type='application/ld+json'):
            if isinstance(script, Tag) and script.string:
                try:
                    data = json.loads(script.string)
                    metadata['structured_data'] = data
                except:
                    pass
        
        return json.dumps(metadata, indent=2)
    
    def _extract_full_content(self, soup: BeautifulSoup) -> str:
        """Extract full content including text and structure"""
        text_content = self._extract_text_content(soup)
        structured_content = self._extract_structured_content(soup)
        
        return f"{text_content}\n\n--- STRUCTURE ---\n{structured_content}"
    
    async def _search_bing(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Bing"""
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        
        if self.page:
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Extract results
            results = []
            result_elements = await self.page.query_selector_all('.b_algo')
            
            for element in result_elements[:max_results]:
                try:
                    title_elem = await element.query_selector('h2 a')
                    title = await title_elem.inner_text() if title_elem else ""
                    url = await title_elem.get_attribute('href') if title_elem else ""
                    
                    snippet_elem = await element.query_selector('.b_caption p')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ""
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            search_engine="bing",
                            relevance_score=1.0 - (len(results) * 0.1),
                            metadata={"search_query": query}
                        ))
                except Exception as e:
                    logger.error(f"Error extracting Bing result: {e}")
            
            return results
        else:
            raise RuntimeError("Playwright not initialized")
    
    async def _search_duckduckgo(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using DuckDuckGo"""
        search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        
        if self.page:
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Extract results
            results = []
            result_elements = await self.page.query_selector_all('.result')
            
            for element in result_elements[:max_results]:
                try:
                    title_elem = await element.query_selector('.result__title a')
                    title = await title_elem.inner_text() if title_elem else ""
                    url = await title_elem.get_attribute('href') if title_elem else ""
                    
                    snippet_elem = await element.query_selector('.result__snippet')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ""
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            search_engine="duckduckgo",
                            relevance_score=1.0 - (len(results) * 0.1),
                            metadata={"search_query": query}
                        ))
                except Exception as e:
                    logger.error(f"Error extracting DuckDuckGo result: {e}")
            
            return results
        else:
            raise RuntimeError("Playwright not initialized")
    
    async def _search_yahoo(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using Yahoo"""
        search_url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
        
        if self.page:
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state("networkidle", timeout=15000)
            
            # Extract results
            results = []
            result_elements = await self.page.query_selector_all('[data-testid="result"]')
            
            for element in result_elements[:max_results]:
                try:
                    title_elem = await element.query_selector('h3 a')
                    title = await title_elem.inner_text() if title_elem else ""
                    url = await title_elem.get_attribute('href') if title_elem else ""
                    
                    snippet_elem = await element.query_selector('[data-testid="result-snippet"]')
                    snippet = await snippet_elem.inner_text() if snippet_elem else ""
                    
                    if title and url:
                        results.append(SearchResult(
                            title=title,
                            url=url,
                            snippet=snippet,
                            search_engine="yahoo",
                            relevance_score=1.0 - (len(results) * 0.1),
                            metadata={"search_query": query}
                        ))
                except Exception as e:
                    logger.error(f"Error extracting Yahoo result: {e}")
            
            return results
        else:
            raise RuntimeError("Playwright not initialized")
    
    async def _search_searx(self, query: str, max_results: int) -> List[SearchResult]:
        """Search using SearX"""
        searx_instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.info"
        ]
        
        for instance in searx_instances:
            try:
                search_url = f"{instance}/search?q={quote_plus(query)}"
                
                if self.page:
                    await self.page.goto(search_url, timeout=30000)
                    await self.page.wait_for_load_state("networkidle", timeout=15000)
                    
                    # Extract results
                    results = []
                    result_elements = await self.page.query_selector_all('.result')
                    
                    for element in result_elements[:max_results]:
                        try:
                            title_elem = await element.query_selector('h3 a')
                            title = await title_elem.inner_text() if title_elem else ""
                            url = await title_elem.get_attribute('href') if title_elem else ""
                            
                            snippet_elem = await element.query_selector('.content')
                            snippet = await snippet_elem.inner_text() if snippet_elem else ""
                            
                            if title and url:
                                results.append(SearchResult(
                                    title=title,
                                    url=url,
                                    snippet=snippet,
                                    search_engine="searx",
                                    relevance_score=1.0 - (len(results) * 0.1),
                                    metadata={"search_query": query, "instance": instance}
                                ))
                        except Exception as e:
                            logger.error(f"Error extracting SearX result: {e}")
                    
                    return results
                
            except Exception as e:
                logger.error(f"Error with SearX instance {instance}: {e}")
                continue
        
        raise RuntimeError("All SearX instances failed")
    
    def _get_ordered_strategies(self, preferred_strategy: ScrapingStrategy) -> List[ScrapingStrategy]:
        """Get strategies ordered by preference and performance"""
        strategies = [preferred_strategy]
        
        # Add other strategies based on performance
        other_strategies = [s for s in ScrapingStrategy if s != preferred_strategy]
        other_strategies.sort(key=lambda s: self.strategy_performance[s.value]["success_rate"], reverse=True)
        
        strategies.extend(other_strategies)
        return strategies
    
    def _update_strategy_performance(self, strategy: str, success: bool, execution_time: float):
        """Update strategy performance metrics"""
        if strategy not in self.strategy_performance:
            self.strategy_performance[strategy] = {"success_rate": 0.5, "avg_time": 5.0}
        
        current_stats = self.strategy_performance[strategy]
        
        # Update success rate (exponential moving average)
        current_stats["success_rate"] = (current_stats["success_rate"] * 0.9) + (1.0 if success else 0.0) * 0.1
        
        # Update average time
        current_stats["avg_time"] = (current_stats["avg_time"] * 0.9) + (execution_time * 0.1)
    
    def _is_cache_valid(self, cached_at: float) -> bool:
        """Check if cached result is still valid"""
        return time.time() - cached_at < self.cache_duration
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        return {
            "strategy_performance": self.strategy_performance,
            "cache_stats": {
                "content_cache_size": len(self.content_cache),
                "search_cache_size": len(self.search_cache),
                "cache_enabled": self.enable_caching
            },
            "configuration": {
                "max_concurrent_requests": self.max_concurrent_requests,
                "request_timeout": self.request_timeout,
                "default_strategy": self.default_strategy.value
            }
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self.content_cache.clear()
        self.search_cache.clear()
        logger.info("Caches cleared") 