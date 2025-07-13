"""
Lightweight web scraper for Render deployment (no Playwright)
"""

import requests
import time
import random
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin, urlparse
import logging

logger = logging.getLogger(__name__)

class LightweightScraper:
    """Lightweight web scraper using only requests and BeautifulSoup"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        
        # User agents for rotation
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        ]
        
        # Set default headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search DuckDuckGo using requests"""
        try:
            # First, get the search page
            search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Extract search results
            for result_div in soup.find_all('div', class_='result')[:max_results]:
                try:
                    title_elem = result_div.find('a', class_='result__a')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        url = title_elem.get('href', '')
                        
                        # Get snippet
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
            return []
    
    def search_bing(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search Bing using requests"""
        try:
            search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
            headers = {'User-Agent': random.choice(self.user_agents)}
            
            response = self.session.get(search_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Extract search results
            for result_div in soup.find_all('li', class_='b_algo')[:max_results]:
                try:
                    title_elem = result_div.find('h2')
                    if title_elem:
                        link_elem = title_elem.find('a')
                        if link_elem:
                            title = link_elem.get_text().strip()
                            url = link_elem.get('href', '')
                            
                            # Get snippet
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
            logger.error(f"Bing search failed: {e}")
            return []
    
    def scrape_content(self, url: str) -> Dict[str, Any]:
        """Scrape content from a URL"""
        try:
            headers = {'User-Agent': random.choice(self.user_agents)}
            response = self.session.get(url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title')
            title = title_elem.get_text().strip() if title_elem else ""
            
            # Extract content
            content = self._extract_text_content(soup)
            
            return {
                'title': title,
                'content': content,
                'url': url,
                'success': True,
                'scraped_successfully': len(content) > 100,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"Failed to scrape {url}: {e}")
            return {
                'title': '',
                'content': '',
                'url': url,
                'success': False,
                'scraped_successfully': False,
                'content_length': 0,
                'error': str(e)
            }
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML"""
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        # Try to find main content areas
        content_selectors = [
            "main",
            "article",
            "[role='main']",
            ".main-content",
            ".post-content",
            ".entry-content",
            ".article-content",
            ".content",
            "#main",
            "#content"
        ]
        
        main_content = ""
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                main_content = element.get_text()
                if len(main_content.strip()) > 200:
                    break
        
        # Fall back to body content
        if not main_content or len(main_content.strip()) < 200:
            body = soup.find('body')
            if body:
                main_content = body.get_text()
        
        # Clean up the text
        if main_content:
            lines = main_content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                line = line.strip()
                if len(line) > 20:  # Keep lines with substantial content
                    # Remove excessive whitespace
                    line = ' '.join(line.split())
                    cleaned_lines.append(line)
            
            return '\n'.join(cleaned_lines)
        
        return ""
    
    def search_and_scrape(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Search and scrape content from results"""
        # Try DuckDuckGo first, then Bing
        search_results = self.search_duckduckgo(query, max_results)
        
        if not search_results:
            search_results = self.search_bing(query, max_results)
        
        if not search_results:
            return []
        
        # Scrape content from each result
        enriched_results = []
        for result in search_results:
            try:
                # Add a small delay to be respectful
                time.sleep(0.5)
                
                scraped = self.scrape_content(result['url'])
                
                # Merge search result with scraped content
                enriched_result = {
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result.get('snippet', ''),
                    'search_engine': result.get('search_engine', ''),
                    'content': scraped['content'],
                    'scraped_successfully': scraped['scraped_successfully'],
                    'content_length': scraped['content_length']
                }
                
                enriched_results.append(enriched_result)
                
            except Exception as e:
                logger.error(f"Error processing result {result['url']}: {e}")
                # Add the result anyway, just without scraped content
                enriched_results.append({
                    'title': result['title'],
                    'url': result['url'],
                    'snippet': result.get('snippet', ''),
                    'search_engine': result.get('search_engine', ''),
                    'content': '',
                    'scraped_successfully': False,
                    'content_length': 0
                })
        
        return enriched_results 