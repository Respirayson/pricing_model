"""Web scraper for fetching pricing data from various sources."""

import requests
import time
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re


class WebScraper:
    """Web scraper for collecting pricing data from various sources."""
    
    def __init__(self, delay: float = 1.0):
        """
        Initialize web scraper.
        
        Args:
            delay: Delay between requests in seconds
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_url(self, url: str) -> Optional[str]:
        """
        Fetch content from a URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            HTML content or None if failed
        """
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            time.sleep(self.delay)  # Be respectful
            return response.text
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_text_from_html(self, html: str) -> str:
        """
        Extract clean text from HTML.
        
        Args:
            html: HTML content
            
        Returns:
            Clean text content
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text
        except Exception as e:
            print(f"Error parsing HTML: {e}")
            return html
    
    def scrape_pricing_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Scrape pricing data from multiple sources.
        
        Args:
            sources: List of source configurations
            
        Returns:
            List of scraped documents
        """
        documents = []
        
        for source in sources:
            url = source.get('url')
            if not url:
                continue
            
            # Skip if it's a placeholder URL
            if 'example.com' in url:
                print(f"Skipping placeholder URL: {url}")
                continue
            
            html = self.fetch_url(url)
            if html:
                text = self.extract_text_from_html(html)
                
                doc = {
                    'source_id': source.get('id', f"web_{len(documents)}"),
                    'source_url': url,
                    'source_title': source.get('title', 'Web Scraped Content'),
                    'published_date': source.get('date'),
                    'content': text,
                    'file_type': 'html'
                }
                documents.append(doc)
                print(f"Successfully scraped: {source.get('id', url)}")
        
        return documents


def get_pricing_sources() -> List[Dict[str, Any]]:
    """
    Get list of pricing data sources to scrape.
    
    Returns:
        List of source configurations
    """
    # Import real sources
    try:
        from .real_sources import get_all_scrapable_sources
        return get_all_scrapable_sources()
    except ImportError:
        # Fallback to placeholder sources
        return [
            {
                'id': 'deepstrike_2025',
                'url': 'https://example.com/deepstrike-2025-pricing',  # Placeholder
                'title': 'DeepStrike Dark Web Data Pricing 2025',
                'date': '2025-08-13'
            },
            {
                'id': 'socradar_2024',
                'url': 'https://example.com/socradar-annual-2024',  # Placeholder
                'title': 'SOCRadar Annual Dark Web Report 2024',
                'date': '2025-01-16'
            },
            {
                'id': 'privacy_affairs_index',
                'url': 'https://example.com/privacy-affairs-index',  # Placeholder
                'title': 'Privacy Affairs Dark Web Price Index',
                'date': '2024-12-11'
            },
            {
                'id': 'wired_china_surveillance',
                'url': 'https://example.com/wired-china-surveillance',  # Placeholder
                'title': 'China Surveillance State Selling Citizen Data',
                'date': '2024-11-21'
            }
        ]


def scrape_real_sources() -> List[Dict[str, Any]]:
    """
    Scrape from real sources (when URLs are available).
    
    Returns:
        List of scraped documents
    """
    # Real sources that can be scraped
    real_sources = [
        {
            'id': 'privacy_affairs_real',
            'url': 'https://privacyaffairs.com/dark-web-price-index-2022/',
            'title': 'Privacy Affairs Dark Web Price Index 2022',
            'date': '2022-01-01'
        },
        {
            'id': 'comparitech_real',
            'url': 'https://www.comparitech.com/blog/information-security/dark-web-prices/',
            'title': 'Dark Web Prices for Stolen Data',
            'date': '2021-01-20'
        }
    ]
    
    scraper = WebScraper(delay=2.0)  # Be respectful with delays
    return scraper.scrape_pricing_sources(real_sources)
