"""
Reddit scraper for extracting lead data without using the Reddit API.
Uses web scraping to collect data from Reddit.
"""

import os
import logging
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional

# Import the web scraper and parser
from .web_scraper import RedditWebScraper
from .parser import RedditHtmlParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/reddit_scraper.log'
)
logger = logging.getLogger('reddit_scraper')

# Ensure necessary directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)

class RedditScraper:
    """
    A modular scraper for collecting lead data from Reddit
    based on subreddits and keywords related to stress and burnout.
    Uses web scraping instead of the Reddit API.
    """
    
    def __init__(self, 
                 subreddits: Optional[List[str]] = None, 
                 keywords: Optional[List[str]] = None,
                 time_filter: str = "month",
                 post_limit: int = 100):
        """
        Initialize the Reddit scraper.
        
        Args:
            subreddits: List of subreddit names to search
            keywords: List of keywords to search for
            time_filter: Time filter for posts ('day', 'week', 'month', 'year', 'all')
            post_limit: Maximum number of posts to process per subreddit
        """
        # Default subreddits focusing on work-life and mental health
        self.subreddits = subreddits or [
            "Entrepreneur", 
            "Productivity", 
            "MentalHealth", 
            "GetMotivated", 
            "WorkReform",
            "careerguidance",
            "jobs",
            "careeradvice",
            "personalfinance",
            "cscareerquestions"
        ]
        
        # Default keywords related to burnout and career challenges
        self.keywords = keywords or [
            "burnout", 
            "feeling lost", 
            "overwhelmed", 
            "career transition", 
            "work-life balance",
            "stress", 
            "anxiety", 
            "depression",
            "overworked",
            "career change",
            "hate my job",
            "toxic workplace",
            "mental health",
            "exhausted",
            "quit my job",
            "working too much"
        ]
        
        self.time_filter = time_filter
        self.post_limit = post_limit
        
        # Initialize the web scraper and parser
        self.web_scraper = RedditWebScraper()
        self.html_parser = RedditHtmlParser()
        
        logger.info(f"Reddit scraper initialized with {len(self.subreddits)} subreddits and {len(self.keywords)} keywords")
    
    def keyword_match(self, text: str) -> List[str]:
        """
        Check if any keywords are found in the provided text.
        
        Args:
            text: Text to search for keywords
            
        Returns:
            List of matched keywords found in the text
        """
        if not text:
            return []
        
        text = text.lower()
        matches = []
        
        for keyword in self.keywords:
            if keyword.lower() in text:
                matches.append(keyword)
                
        return matches
    
    def scrape_subreddit(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Scrape a specific subreddit for relevant posts.
        
        Args:
            subreddit_name: Name of the subreddit to scrape
            
        Returns:
            List of dictionaries containing post data
        """
        leads = []
        
        try:
            logger.info(f"Scraping subreddit: r/{subreddit_name}")
            
            # Fetch the subreddit page
            html_content = self.web_scraper.get_subreddit_posts(
                subreddit=subreddit_name,
                time_filter=self.time_filter,
                limit=self.post_limit
            )
            
            # Parse the HTML to extract posts
            posts = self.html_parser.parse_subreddit_page(html_content, subreddit_name)
            
            # Filter posts by keywords
            for post in posts:
                # Combine title and body for keyword matching
                full_text = f"{post.get('post_title', '')} {post.get('post_content', '')}"
                matched_keywords = self.keyword_match(full_text)
                
                # Only keep posts that match our keywords
                if matched_keywords:
                    # Add matched keywords to the post data
                    post['matched_keywords'] = ", ".join(matched_keywords)
                    leads.append(post)
                    logger.debug(f"Found relevant post by u/{post.get('username', '[deleted]')} in r/{subreddit_name}")
            
            logger.info(f"Found {len(leads)} relevant posts in r/{subreddit_name}")
            return leads
            
        except Exception as e:
            logger.error(f"Error scraping subreddit r/{subreddit_name}: {str(e)}")
            return []
    
    def search_reddit_by_query(self, query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search all of Reddit for posts matching a specific query.
        
        Args:
            query: The search query
            limit: Maximum number of posts to retrieve
            
        Returns:
            List of dictionaries containing post data
        """
        leads = []
        
        try:
            logger.info(f"Searching Reddit for query: '{query}'")
            
            # Fetch the search results page
            html_content = self.web_scraper.search_reddit(
                query=query,
                time_filter=self.time_filter,
                limit=limit
            )
            
            # Parse the HTML to extract posts
            posts = self.html_parser.parse_search_results(html_content, query)
            
            # Filter results by subreddit (if configured)
            for post in posts:
                # Check if post is from a subreddit we're interested in
                if post.get('subreddit', '').lower() not in [s.lower() for s in self.subreddits]:
                    continue
                
                # Add the query as a matched keyword
                post['matched_keywords'] = query
                leads.append(post)
            
            logger.info(f"Found {len(leads)} relevant posts for query '{query}'")
            return leads
            
        except Exception as e:
            logger.error(f"Error searching Reddit for '{query}': {str(e)}")
            return []
    
    def scrape_all_subreddits(self) -> List[Dict[str, Any]]:
        """
        Scrape all configured subreddits for relevant posts.
        
        Returns:
            List of all collected lead data
        """
        all_leads = []
        
        for subreddit_name in self.subreddits:
            subreddit_leads = self.scrape_subreddit(subreddit_name)
            all_leads.extend(subreddit_leads)
            
        logger.info(f"Collected a total of {len(all_leads)} leads from {len(self.subreddits)} subreddits")
        return all_leads
    
    def search_all_keywords(self) -> List[Dict[str, Any]]:
        """
        Search Reddit for all configured keywords.
        
        Returns:
            List of all collected lead data
        """
        all_leads = []
        
        for keyword in self.keywords:
            keyword_leads = self.search_reddit_by_query(keyword, limit=50)  # Limit results per keyword
            all_leads.extend(keyword_leads)
            
        # Remove duplicates based on post URL
        unique_leads = []
        seen_urls = set()
        
        for lead in all_leads:
            if lead["post_url"] not in seen_urls:
                seen_urls.add(lead["post_url"])
                unique_leads.append(lead)
        
        logger.info(f"Collected a total of {len(unique_leads)} unique leads from {len(self.keywords)} keyword searches")
        return unique_leads
    
    def save_leads_to_google_sheets(self, leads: List[Dict[str, Any]], sheets_client) -> bool:
        """
        Save leads to Google Sheets.
        
        Args:
            leads: List of lead information dictionaries
            sheets_client: Google Sheets client or worksheet object
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            if not sheets_client:
                logger.warning("No sheets client provided, skipping saving to Google Sheets")
                return False
                
            if not leads:
                logger.warning("No leads to save to Google Sheets")
                return False
            
            logger.info(f"Saving {len(leads)} Reddit leads to Google Sheets")
            
            # Prepare data for sheets
            rows = []
            for lead in leads:
                # Create a row for each lead
                row = [
                    lead.get('username', ''),
                    lead.get('post_title', ''),
                    lead.get('subreddit', ''),
                    lead.get('post_url', ''),
                    lead.get('matched_keywords', ''),
                    lead.get('score', 0),
                    lead.get('comment_count', 0),
                    lead.get('created_utc', ''),
                    lead.get('date_added', '')
                ]
                rows.append(row)
            
            # Append to Google Sheet
            if sheets_client and rows:
                for row in rows:
                    sheets_client.append_row(row)
                logger.info(f"Successfully saved {len(rows)} Reddit leads to Google Sheets")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving Reddit leads to Google Sheets: {str(e)}")
            return False
    
    def save_leads_to_csv(self, leads: List[Dict[str, Any]], filename: str = "reddit_leads.csv") -> bool:
        """
        Save leads to a CSV file.
        
        Args:
            leads: List of lead information dictionaries
            filename: Output CSV filename
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            if not leads:
                logger.warning("No leads to save to CSV")
                return False
                
            # Convert to DataFrame
            df = pd.DataFrame(leads)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            logger.info(f"Successfully saved {len(leads)} leads to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving leads to CSV: {str(e)}")
            return False
    
    def run_full_scrape(self, sheets_client=None, save_csv: bool = True, csv_filename: str = "reddit_leads.csv") -> List[Dict[str, Any]]:
        """
        Run a full scraping operation and save the results.
        
        Args:
            sheets_client: Google Sheets client or worksheet (optional)
            save_csv: Whether to save results to a CSV file
            csv_filename: Filename for CSV output
            
        Returns:
            List of all collected leads
        """
        # Collect leads from subreddits
        subreddit_leads = self.scrape_all_subreddits()
        
        # Collect leads from keyword searches
        keyword_leads = self.search_all_keywords()
        
        # Combine and remove duplicates
        all_leads = subreddit_leads + keyword_leads
        unique_leads = []
        seen_urls = set()
        
        for lead in all_leads:
            if lead["post_url"] not in seen_urls:
                seen_urls.add(lead["post_url"])
                unique_leads.append(lead)
        
        logger.info(f"Combined results: {len(unique_leads)} unique leads")
        
        # Save to Google Sheets if client provided
        if sheets_client:
            self.save_leads_to_google_sheets(unique_leads, sheets_client)
        
        # Save to CSV if requested
        if save_csv:
            self.save_leads_to_csv(unique_leads, csv_filename)
        
        return unique_leads


def run_reddit_scraper(sheets_client=None, 
                      subreddits: Optional[List[str]] = None,
                      keywords: Optional[List[str]] = None,
                      time_filter: str = "month",
                      post_limit: int = 100,
                      save_csv: bool = True,
                      max_leads: int = 50) -> List[Dict[str, Any]]:
    """
    Run the Reddit scraper as a standalone function.
    
    Args:
        sheets_client: Google Sheets client for saving results
        subreddits: List of subreddit names to search
        keywords: List of keywords to search for
        time_filter: Time filter for posts
        post_limit: Maximum posts per subreddit
        save_csv: Whether to save results to a CSV file
        max_leads: Maximum number of leads to return (primarily for processing limits)
        
    Returns:
        List of leads collected
    """
    # Create the scraper with provided or default parameters
    scraper = RedditScraper(
        subreddits=subreddits,
        keywords=keywords,
        time_filter=time_filter,
        post_limit=post_limit
    )
    
    # Set data directory
    os.makedirs('data', exist_ok=True)
    csv_filename = "data/reddit_leads.csv"
    
    # Run the scraper
    leads = scraper.run_full_scrape(
        sheets_client=sheets_client,
        save_csv=save_csv,
        csv_filename=csv_filename
    )
    
    # Limit the number of leads if specified
    if max_leads and len(leads) > max_leads:
        logger.info(f"Limiting result to {max_leads} leads (from {len(leads)} total)")
        return leads[:max_leads]
    
    return leads


if __name__ == "__main__":
    # This allows the script to be run directly for testing
    from utils.sheets_manager import get_sheets_client
    
    # Get Google Sheets client
    try:
        sheets_client = get_sheets_client()
        worksheet = sheets_client.open('LeadGenerationData').worksheet('RedditLeads')
    except Exception as e:
        logger.error(f"Could not connect to Google Sheets: {str(e)}")
        worksheet = None
    
    # Define custom subreddits and keywords
    custom_subreddits = [
        "Entrepreneur", 
        "Productivity", 
        "MentalHealth", 
        "GetMotivated", 
        "WorkReform"
    ]
    
    custom_keywords = [
        "burnout", 
        "feeling lost", 
        "overwhelmed", 
        "career transition", 
        "work-life balance"
    ]
    
    # Run the scraper
    leads = run_reddit_scraper(
        sheets_client=worksheet,
        subreddits=custom_subreddits,
        keywords=custom_keywords,
        time_filter="month",
        post_limit=50,
        save_csv=True
    )
    
    print(f"Collected {len(leads)} leads")