"""
Parser for Reddit HTML content.
Extracts structured data from Reddit pages without using the API.
"""

import re
import logging
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from bs4 import BeautifulSoup

# Configure logging
logger = logging.getLogger('reddit.parser')

class RedditHtmlParser:
    """
    Parser for Reddit HTML content to extract post information.
    """
    
    def __init__(self):
        """Initialize the Reddit HTML parser."""
        logger.info("Reddit HTML parser initialized")
    
    def parse_subreddit_page(self, html_content: str, subreddit: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content from a subreddit page and extract post information.
        
        Args:
            html_content: HTML content of the subreddit page
            subreddit: Name of the subreddit
            
        Returns:
            List of dictionaries containing post data
        """
        if not html_content:
            logger.warning(f"Empty HTML content for r/{subreddit}")
            return []
        
        try:
            # First try to extract data from JSON embedded in the page (modern Reddit)
            posts = self._extract_from_json(html_content)
            if posts:
                logger.info(f"Extracted {len(posts)} posts from JSON data for r/{subreddit}")
                return posts
            
            # Fall back to HTML parsing if JSON extraction fails
            posts = self._parse_html_posts(html_content, subreddit)
            logger.info(f"Extracted {len(posts)} posts from HTML for r/{subreddit}")
            return posts
            
        except Exception as e:
            logger.error(f"Error parsing HTML content for r/{subreddit}: {str(e)}")
            return []
    
    def parse_search_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """
        Parse HTML content from a search results page and extract post information.
        
        Args:
            html_content: HTML content of the search results page
            query: The search query
            
        Returns:
            List of dictionaries containing post data
        """
        if not html_content:
            logger.warning(f"Empty HTML content for search query: '{query}'")
            return []
        
        try:
            # First try to extract data from JSON embedded in the page (modern Reddit)
            posts = self._extract_from_json(html_content)
            if posts:
                logger.info(f"Extracted {len(posts)} posts from JSON data for search: '{query}'")
                return posts
            
            # Fall back to HTML parsing if JSON extraction fails
            posts = self._parse_html_search_results(html_content, query)
            logger.info(f"Extracted {len(posts)} posts from HTML for search: '{query}'")
            return posts
            
        except Exception as e:
            logger.error(f"Error parsing HTML content for search query '{query}': {str(e)}")
            return []
    
    def _extract_from_json(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Extract post data from JSON embedded in the Reddit page (modern Reddit approach).
        
        Args:
            html_content: HTML content of the Reddit page
            
        Returns:
            List of dictionaries containing post data
        """
        posts = []
        try:
            # Find the data embedded as JSON in the page
            # Reddit often includes the post data in a script tag as JSON
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for the script that contains the post data
            # The exact pattern may change, so we'll try a few approaches
            
            # Method 1: Look for the JSON data in specific script tags
            for script in soup.find_all('script', id=re.compile(r'data|__NEXT_DATA__|__INITIAL_DATA__')):
                try:
                    if script.string:
                        data = json.loads(script.string)
                        posts = self._extract_posts_from_json(data)
                        if posts:
                            return posts
                except (json.JSONDecodeError, ValueError):
                    continue
            
            # Method 2: Look for JSON data in any script tag
            pattern = re.compile(r'window\.___r = ({.*?});', re.DOTALL)
            for script in soup.find_all('script'):
                if script.string:
                    match = pattern.search(script.string)
                    if match:
                        try:
                            data = json.loads(match.group(1))
                            posts = self._extract_posts_from_json(data)
                            if posts:
                                return posts
                        except (json.JSONDecodeError, ValueError):
                            continue
            
            return posts
            
        except Exception as e:
            logger.warning(f"Failed to extract posts from JSON: {str(e)}")
            return []
    
    def _extract_posts_from_json(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract post data from the JSON structure.
        This is a complex function as Reddit's JSON structure can vary.
        
        Args:
            data: JSON data from the Reddit page
            
        Returns:
            List of dictionaries containing post data
        """
        posts = []
        
        # This is a simplified version - the actual implementation would need to
        # handle the complex and possibly changing structure of Reddit's JSON data
        
        # For now, we'll return an empty list and rely on HTML parsing
        # A full implementation would traverse the JSON structure looking for posts
        
        return posts
    
    def _parse_html_posts(self, html_content: str, subreddit: str) -> List[Dict[str, Any]]:
        """
        Parse post information from HTML content (old Reddit fallback).
        
        Args:
            html_content: HTML content of the subreddit page
            subreddit: Name of the subreddit
            
        Returns:
            List of dictionaries containing post data
        """
        posts = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find post containers - different selectors for different Reddit layouts
        post_elements = soup.select('div.thing, div[data-testid="post-container"]')
        
        for post_element in post_elements:
            try:
                # Extract post data with fallbacks for different layouts
                post_data = self._extract_post_data(post_element, subreddit)
                if post_data:
                    posts.append(post_data)
            except Exception as e:
                logger.warning(f"Error extracting post data: {str(e)}")
                continue
        
        return posts
    
    def _parse_html_search_results(self, html_content: str, query: str) -> List[Dict[str, Any]]:
        """
        Parse post information from search results HTML content.
        
        Args:
            html_content: HTML content of the search results page
            query: The search query
            
        Returns:
            List of dictionaries containing post data
        """
        # Search results have a similar structure to subreddit posts
        # but we might need to extract the subreddit as well
        posts = []
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find post containers - different selectors for different Reddit layouts
        post_elements = soup.select('div.thing, div[data-testid="post-container"]')
        
        for post_element in post_elements:
            try:
                # For search results, we need to extract the subreddit too
                subreddit_element = post_element.select_one('a[href^="/r/"]')
                subreddit = subreddit_element.text.strip() if subreddit_element else "Unknown"
                
                # Remove the 'r/' prefix if present
                if subreddit.startswith('r/'):
                    subreddit = subreddit[2:]
                
                post_data = self._extract_post_data(post_element, subreddit)
                if post_data:
                    # Add the search query to the post data
                    post_data['matched_keywords'] = query
                    posts.append(post_data)
            except Exception as e:
                logger.warning(f"Error extracting search result data: {str(e)}")
                continue
        
        return posts
    
    def _extract_post_data(self, post_element, subreddit: str) -> Dict[str, Any]:
        """
        Extract data from an individual post element.
        
        Args:
            post_element: BeautifulSoup element representing a post
            subreddit: Name of the subreddit
            
        Returns:
            Dictionary containing post data
        """
        # This is a complex function that needs to handle different Reddit layouts
        # We'll use a series of selectors with fallbacks
        
        # Extract post title
        title_element = post_element.select_one('a.title, h1, h3, [data-testid="post-title"]')
        title = title_element.text.strip() if title_element else "No title"
        
        # Extract username/author
        author_element = post_element.select_one('a.author, [data-testid="post-author"]')
        username = author_element.text.strip() if author_element else "[deleted]"
        
        # Extract post URL
        url_element = post_element.select_one('a.title, a[data-testid="post-url"]')
        post_url = url_element['href'] if url_element and 'href' in url_element.attrs else ""
        
        # Ensure it's a full URL
        if post_url.startswith('/'):
            post_url = f"https://www.reddit.com{post_url}"
        
        # Extract post content/body
        content_element = post_element.select_one('div.md, [data-testid="post-content"]')
        post_content = content_element.text.strip() if content_element else ""
        
        # Extract score
        score_element = post_element.select_one('div.score, [data-testid="post-score"]')
        try:
            score = int(score_element.text.strip()) if score_element else 0
        except ValueError:
            # Handle text like "1.2k" or "Vote"
            score_text = score_element.text.strip() if score_element else "0"
            if 'k' in score_text.lower():
                try:
                    score = int(float(score_text.lower().replace('k', '')) * 1000)
                except ValueError:
                    score = 0
            else:
                score = 0
        
        # Extract comment count
        comment_element = post_element.select_one('a.comments, [data-testid="comment-count"]')
        try:
            comment_text = comment_element.text.strip() if comment_element else "0"
            # Extract numbers from text like "123 comments"
            comment_count = int(re.search(r'\d+', comment_text).group())
        except (ValueError, AttributeError):
            comment_count = 0
        
        # Extract timestamp (this is complex as Reddit formats dates in various ways)
        timestamp_element = post_element.select_one('time, [data-testid="post-timestamp"]')
        if timestamp_element and 'datetime' in timestamp_element.attrs:
            created_utc = timestamp_element['datetime']
        else:
            # Fallback to current time
            created_utc = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create post data dictionary in the same format as the API-based scraper
        post_data = {
            "username": username,
            "post_title": title,
            "post_content": post_content,
            "subreddit": subreddit,
            "post_url": post_url,
            "matched_keywords": "",  # This will be filled in later by the main scraper
            "score": score,
            "comment_count": comment_count,
            "created_utc": created_utc,
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return post_data