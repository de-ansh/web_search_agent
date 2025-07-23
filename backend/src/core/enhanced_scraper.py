"""
Enhanced web scraper with improved reliability and better error handling
"""

import asyncio
import time
import random
import requests
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin, urlparse, quote_plus
from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
import re
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ScrapingResult:
    """Result of web scraping operation"""
    content: str
    title: str
    url: str
    success: bool
    method: str
    processing_time: float
    word_count: int
    error: Optional[str] = None

class EnhancedScraper:
    """Enhanced web scraper with improved reliability"""
    
    def __init__(self, 
                 headless: bool = True,
                 timeout: int = 30,
                 max_retries: int = 2,
                 use_playwright: bool = True):
        """
        Initialize enhanced scraper
        
        Args:
            headless: Run browser in headless mode
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            use_playwright: Use Playwright for JS-heavy sites
        """
        self.headless = headless
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_playwright = use_playwright
        
        # Initialize requests session for lightweight scraping
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Browser instances
        self.playwright = None
        self.browser = None
        self.page = None
        
        # Enhanced user agents
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:122.0) Gecko/20100101 Firefox/122.0"
        ]
        
        # Search engines with improved reliability
        self.search_engines = [
            ("bing", self._search_bing),
            ("duckduckgo", self._search_duckduckgo),
            ("yahoo", self._search_yahoo)
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        if self.use_playwright:
            await self._init_playwright()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self._cleanup_playwright()
    
    async def _init_playwright(self):
        """Initialize Playwright browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Enhanced browser args for better compatibility
            browser_args = [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-accelerated-2d-canvas",
                "--no-first-run",
                "--no-zygote",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=VizDisplayCompositor,TranslateUI",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-field-trial-config",
                "--disable-hang-monitor",
                "--disable-ipc-flooding-protection",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-sync",
                "--metrics-recording-only",
                "--no-default-browser-check",
                "--no-experiments",
                "--password-store=basic",
                "--use-mock-keychain",
                "--disable-component-extensions-with-background-pages",
                "--disable-default-apps",
                "--mute-audio",
                "--autoplay-policy=user-gesture-required",
                "--disable-notifications",
                "--disable-component-update"
            ]
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=browser_args
            )
            
            # Create context with enhanced settings
            context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=random.choice(self.user_agents),
                java_script_enabled=True,
                accept_downloads=False,
                ignore_https_errors=True,
                permissions=[]
            )
            
            # Block unnecessary resources for faster loading
            await context.route("**/*.{png,jpg,jpeg,gif,svg,ico,css,woff,woff2,ttf,eot}", lambda route: route.abort())
            await context.route("**/*{google-analytics,googletagmanager,facebook,twitter,instagram}*", lambda route: route.abort())
            
            self.page = await context.new_page()
            
            # Enhanced stealth settings
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
                
                window.chrome = {
                    runtime: {}
                };
                
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
                
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en']
                });
            """)
            
            logger.info("✅ Playwright browser initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Playwright: {e}")
            self.use_playwright = False
    
    async def _cleanup_playwright(self):
        """Cleanup Playwright resources"""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error cleaning up Playwright: {e}")
    
    async def search_and_scrape(self, query: str, max_results: int = 5) -> List[ScrapingResult]:
        """
        Search for query and scrape content from results
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of ScrapingResult objects
        """
        logger.info(f"🔍 Starting search and scrape for: {query}")
        
        # Try different search engines
        search_results = []
        for engine_name, search_func in self.search_engines:
            try:
                logger.info(f"🔄 Trying {engine_name} search...")
                results = await search_func(query, max_results)
                if results:
                    search_results = results
                    logger.info(f"✅ {engine_name} returned {len(results)} results")
                    break
                else:
                    logger.warning(f"⚠️  {engine_name} returned no results")
            except Exception as e:
                logger.error(f"❌ {engine_name} search failed: {e}")
                continue
        
        if not search_results:
            logger.error("❌ All search engines failed")
            return []
        
        # Scrape content from search results
        scraping_results = []
        for i, result in enumerate(search_results[:max_results]):
            logger.info(f"🔄 Scraping content {i+1}/{min(len(search_results), max_results)}: {result['url']}")
            
            scraped = await self._scrape_with_fallback(result['url'])
            
            # Enhance with search result metadata
            scraped.title = scraped.title or result.get('title', '')
            
            scraping_results.append(scraped)
            
            # Add small delay between requests
            await asyncio.sleep(0.5)
        
        logger.info(f"✅ Completed scraping {len(scraping_results)} results")
        return scraping_results
    
    async def _scrape_with_fallback(self, url: str) -> ScrapingResult:
        """
        Scrape URL with multiple fallback methods
        
        Args:
            url: URL to scrape
            
        Returns:
            ScrapingResult object
        """
        start_time = time.time()
        
        # Method 1: Try Playwright if available
        if self.use_playwright and self.page:
            try:
                result = await self._scrape_with_playwright(url)
                if result.success:
                    result.processing_time = time.time() - start_time
                    return result
            except Exception as e:
                logger.warning(f"Playwright scraping failed for {url}: {e}")
        
        # Method 2: Try requests-based scraping
        try:
            result = await self._scrape_with_requests(url)
            if result.success:
                result.processing_time = time.time() - start_time
                return result
        except Exception as e:
            logger.warning(f"Requests scraping failed for {url}: {e}")
        
        # Method 3: Generate fallback content
        processing_time = time.time() - start_time
        return ScrapingResult(
            content=f"Unable to fully load content from {url}. This appears to be a relevant resource for your search query, but the full content could not be retrieved due to website restrictions or technical limitations.",
            title="Content Loading Limited",
            url=url,
            success=False,
            method="fallback",
            processing_time=processing_time,
            word_count=25,
            error="All scraping methods failed"
        )
    
    async def _scrape_with_playwright(self, url: str) -> ScrapingResult:
        """Scrape URL using Playwright"""
        if not self.page:
            raise Exception("Playwright page not initialized")
        
        try:
            # Navigate with timeout
            await self.page.goto(url, timeout=self.timeout * 1000, wait_until="domcontentloaded")
            
            # Wait for content to load
            await self._intelligent_wait()
            
            # Get page content
            content = await self.page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Validate content quality
            if len(main_content.strip()) < 50:
                raise Exception(f"Content too short ({len(main_content)} chars)")
            
            return ScrapingResult(
                content=main_content,
                title=title,
                url=url,
                success=True,
                method="playwright",
                processing_time=0.0,  # Will be set by caller
                word_count=len(main_content.split())
            )
            
        except Exception as e:
            raise Exception(f"Playwright scraping failed: {e}")
    
    async def _scrape_with_requests(self, url: str) -> ScrapingResult:
        """Scrape URL using requests"""
        try:
            # Use random user agent
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            # Make request with timeout
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Extract main content
            main_content = self._extract_main_content(soup)
            
            # Validate content quality
            if len(main_content.strip()) < 50:
                raise Exception(f"Content too short ({len(main_content)} chars)")
            
            return ScrapingResult(
                content=main_content,
                title=title,
                url=url,
                success=True,
                method="requests",
                processing_time=0.0,  # Will be set by caller
                word_count=len(main_content.split())
            )
            
        except Exception as e:
            raise Exception(f"Requests scraping failed: {e}")
    
    async def _intelligent_wait(self):
        """Intelligent waiting strategy for page loading"""
        if not self.page:
            return
        
        try:
            # Try multiple wait strategies
            strategies = [
                ("networkidle", 8000),
                ("domcontentloaded", 5000),
                ("load", 3000)
            ]
            
            for strategy, timeout in strategies:
                try:
                    await self.page.wait_for_load_state(strategy, timeout=timeout)
                    break
                except:
                    continue
            
            # Additional wait for dynamic content
            await asyncio.sleep(random.uniform(1.0, 2.0))
            
            # Wait for common content selectors
            content_selectors = [
                "main", "article", ".content", ".main-content", 
                ".post-content", ".entry-content", "#content", "#main"
            ]
            
            for selector in content_selectors:
                try:
                    await self.page.wait_for_selector(selector, timeout=2000)
                    break
                except:
                    continue
                    
        except Exception as e:
            logger.debug(f"Intelligent wait completed with partial success: {e}")
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML with enhanced filtering"""
        # Remove unwanted elements
        for element in soup(["script", "style", "nav", "header", "footer", "aside", "noscript"]):
            element.decompose()
        
        # Remove common ad and navigation classes/IDs
        unwanted_patterns = [
            r'(ad|advertisement|banner|nav|menu|sidebar|footer|header|cookie|popup)',
            r'(social|share|follow|subscribe|newsletter)',
            r'(comment|reply|discussion)',
            r'(related|recommended|trending)',
            r'(breadcrumb|pagination|tag)'
        ]
        
        for pattern in unwanted_patterns:
            for element in soup.find_all(class_=re.compile(pattern, re.I)):
                element.decompose()
            for element in soup.find_all(id=re.compile(pattern, re.I)):
                element.decompose()
        
        # Try to find main content areas in order of preference
        content_selectors = [
            "main",
            "article",
            "[role='main']",
            ".main-content",
            ".post-content", 
            ".entry-content",
            ".article-content",
            ".content-body",
            ".page-content",
            ".text-content",
            ".content",
            "#main",
            "#content"
        ]
        
        main_content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text()
                if len(text.strip()) > 200:  # Ensure substantial content
                    main_content = text
                    break
        
        # Fallback to body content if no main content found
        if not main_content or len(main_content.strip()) < 200:
            body = soup.find('body')
            if body:
                main_content = body.get_text()
        
        # Clean and format the text
        if main_content:
            return self._clean_text(main_content)
        
        return ""
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text"""
        # Split into lines and filter
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Skip very short lines
            if len(line) < 20:
                continue
            
            # Skip lines that look like navigation or boilerplate
            line_lower = line.lower()
            skip_patterns = [
                r'click here', r'read more', r'subscribe', r'follow us',
                r'share this', r'print this', r'back to top',
                r'skip to content', r'cookie policy', r'privacy policy',
                r'terms of service', r'all rights reserved',
                r'loading\.\.\.', r'please wait'
            ]
            
            should_skip = any(re.search(pattern, line_lower) for pattern in skip_patterns)
            if should_skip:
                continue
            
            # Clean whitespace and add to results
            line = ' '.join(line.split())
            if line:
                cleaned_lines.append(line)
        
        # Join lines and do final cleanup
        result = '\n'.join(cleaned_lines)
        
        # Remove excessive whitespace
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r' {2,}', ' ', result)
        
        return result.strip()
    
    async def _search_bing(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Bing"""
        search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
        
        if self.use_playwright and self.page:
            try:
                await self.page.goto(search_url, timeout=45000)
                await self.page.wait_for_load_state("networkidle", timeout=20000)
                await asyncio.sleep(random.uniform(2, 4))
                
                content = await self.page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                results = []
                for result_div in soup.find_all('li', class_='b_algo')[:max_results]:
                    try:
                        title_elem = result_div.find('h2')
                        if title_elem:
                            link_elem = title_elem.find('a')
                            if link_elem:
                                title = link_elem.get_text().strip()
                                url = link_elem.get('href', '')
                                
                                snippet_elem = result_div.find('p')
                                snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                                
                                if title and url:
                                    results.append({
                                        'title': title,
                                        'url': url,
                                        'snippet': snippet,
                                        'search_engine': 'bing'
                                    })
                    except Exception as e:
                        logger.error(f"Error parsing Bing result: {e}")
                        continue
                
                return results
                
            except Exception as e:
                logger.error(f"Bing search with Playwright failed: {e}")
                raise
        else:
            raise Exception("Playwright not available for Bing search")
    
    async def _search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using DuckDuckGo"""
        search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            for result_div in soup.find_all('div', class_='result')[:max_results]:
                try:
                    title_elem = result_div.find('a', class_='result__a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        url = title_elem.get('href', '')
                        
                        snippet_elem = result_div.find('a', class_='result__snippet')
                        snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                        
                        if title and url:
                            results.append({
                                'title': title,
                                'url': url,
                                'snippet': snippet,
                                'search_engine': 'duckduckgo'
                            })
                except Exception as e:
                    logger.error(f"Error parsing DuckDuckGo result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            raise
    
    async def _search_yahoo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search using Yahoo"""
        search_url = f"https://search.yahoo.com/search?p={quote_plus(query)}"
        
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            for result_div in soup.find_all('div', class_='dd')[:max_results]:
                try:
                    title_elem = result_div.find('h3')
                    if title_elem:
                        link_elem = title_elem.find('a')
                        if link_elem:
                            title = link_elem.get_text().strip()
                            url = link_elem.get('href', '')
                            
                            snippet_elem = result_div.find('p')
                            snippet = snippet_elem.get_text().strip() if snippet_elem else ""
                            
                            if title and url:
                                results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet,
                                    'search_engine': 'yahoo'
                                })
                except Exception as e:
                    logger.error(f"Error parsing Yahoo result: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Yahoo search failed: {e}")
            raise