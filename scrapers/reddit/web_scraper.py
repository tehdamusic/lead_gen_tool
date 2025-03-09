"""
Web scraper for Reddit without using the API.
Uses direct HTTP requests and HTML parsing.
"""

import os
import time
import random
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import quote_plus

# Configure logging
logger = logging.getLogger('reddit.web_scraper')

class RedditWebScraper:
    """
    A web scraper that fetches data from Reddit without using the API.
    """
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.57"
    ]
    
    def __init__(self, timeout: int = 10, max_retries: int = 3):
        """
        Initialize the Reddit web scraper.
        
        Args:
            timeout: HTTP request timeout in seconds
            max_retries: Maximum number of retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self._get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
        
        logger.info("Reddit web scraper initialized")
    
    def _get_random_user_agent(self) -> str:
        """Get a random user agent to avoid detection."""
        return random.choice(self.USER_AGENTS)
    
    def _random_delay(self, min_seconds: float = 1.0, max_seconds: float = 3.0) -> None:
        """
        Implement a random delay between requests to avoid rate limiting.
        
        Args:
            min_seconds: Minimum delay in seconds
            max_seconds: Maximum delay in seconds
        """
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def get_subreddit_posts(self, subreddit: str, time_filter: str = 'month', limit: int = 25) -> str:
        """
        Fetch posts from a specific subreddit.
        
        Args:
            subreddit: Name of the subreddit
            time_filter: Time filter ('day', 'week', 'month', 'year', 'all')
            limit: Maximum number of posts to fetch
            
        Returns:
            HTML content of the subreddit page
        """
        url = f"https://www.reddit.com/r/{subreddit}/top/?t={time_filter}&limit={limit}"
        logger.info(f"Fetching subreddit: r/{subreddit} (time: {time_filter}, limit: {limit})")
        
        for attempt in range(self.max_retries):
            try:
                # Rotate user agent occasionally
                if random.random() < 0.3:
                    self.session.headers.update({'User-Agent': self._get_random_user_agent()})
                
                # Add a random delay between requests
                if attempt > 0:
                    self._random_delay(2.0, 5.0)
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                # Log successful response
                logger.info(f"Successfully fetched r/{subreddit} (status: {response.status_code})")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                # Increase delay after failures
                self._random_delay(3.0, 7.0)
        
        logger.error(f"Failed to fetch r/{subreddit} after {self.max_retries} attempts")
        return ""
    
    def search_reddit(self, query: str, time_filter: str = 'month', limit: int = 25) -> str:
        """
        Search Reddit for a specific query.
        
        Args:
            query: Search query
            time_filter: Time filter ('day', 'week', 'month', 'year', 'all')
            limit: Maximum number of results to fetch
            
        Returns:
            HTML content of the search results page
        """
        encoded_query = quote_plus(query)
        url = f"https://www.reddit.com/search/?q={encoded_query}&t={time_filter}&limit={limit}"
        logger.info(f"Searching Reddit for: '{query}' (time: {time_filter}, limit: {limit})")
        
        for attempt in range(self.max_retries):
            try:
                # Rotate user agent occasionally
                if random.random() < 0.3:
                    self.session.headers.update({'User-Agent': self._get_random_user_agent()})
                
                # Add a random delay between requests
                if attempt > 0:
                    self._random_delay(2.0, 5.0)
                
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()  # Raise exception for HTTP errors
                
                # Log successful response
                logger.info(f"Successfully searched for '{query}' (status: {response.status_code})")
                return response.text
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Search request failed (attempt {attempt+1}/{self.max_retries}): {str(e)}")
                # Increase delay after failures
                self._random_delay(3.0, 7.0)
        
        logger.error(f"Failed to search for '{query}' after {self.max_retries} attempts")
        return ""