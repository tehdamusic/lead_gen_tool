#!/usr/bin/env python3
"""
Reddit Scraper Replacement Script
--------------------------------
This script replaces the existing Reddit scraper module with the new implementation
and updates all necessary project files to maintain compatibility.
"""

import os
import sys
import shutil
import re
from datetime import datetime

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_ROOT, "backup_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
REDDIT_SCRAPER_MODULE = "scrapers/reddit"

# New scraper content
NEW_SCRAPER_MODULE_CONTENT = """#!/usr/bin/env python3
\"\"\"
Reddit Lead Scraper
------------------
A standalone script to extract potential coaching leads from Reddit
based on posts related to career challenges, burnout, and personal development.
\"\"\"

import os
import sys
import praw
import time
import json
import pandas as pd
import logging
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reddit_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('reddit_scraper')

# Ensure data directory exists
os.makedirs('data', exist_ok=True)

# Load environment variables
load_dotenv()

class RedditScraper:
    \"\"\"
    Scrapes Reddit for potential coaching leads based on career challenges and personal growth topics.
    \"\"\"
    
    def __init__(self, 
                 subreddits: Optional[List[str]] = None,
                 keywords: Optional[List[str]] = None,
                 time_filter: str = "month",
                 post_limit: int = 50,
                 verbose: bool = True):
        \"\"\"
        Initialize the Reddit scraper.
        
        Args:
            subreddits: List of subreddits to scrape
            keywords: List of keywords to search for
            time_filter: Reddit time filter ('day', 'week', 'month', 'year', 'all')
            post_limit: Maximum posts to retrieve per subreddit
            verbose: Whether to print verbose output
        \"\"\"
        self.verbose = verbose
        
        # Default target subreddits focused on career and personal development
        self.subreddits = subreddits or [
            "careerguidance",
            "jobs",
            "careeradvice",
            "productivity",
            "selfimprovement",
            "DecidingToBeBetter",
            "productivity",
            "ExperiencedDevs",
            "cscareerquestions",
            "leadership",
            "ExecutiveAssistant",
            "management"
        ]
        
        # Default target keywords related to coaching opportunities
        self.keywords = keywords or [
            "burnout",
            "career transition",
            "career change", 
            "feeling lost",
            "work life balance",
            "overwhelmed",
            "stress",
            "leadership development",
            "professional development",
            "career growth",
            "stuck in career",
            "hate my job",
            "need guidance",
            "career advice",
            "mentor",
            "executive coaching", 
            "personal growth"
        ]
        
        self.time_filter = time_filter
        self.post_limit = post_limit
        self.reddit = None
        
        # Track results
        self.results = {
            "total_posts_analyzed": 0,
            "matching_posts": 0,
            "subreddit_stats": {},
            "keyword_stats": {},
            "leads": []
        }
        
        # Setup Reddit client
        self._initialize_reddit_client()
        
    def _initialize_reddit_client(self):
        \"\"\"Initialize the Reddit API client with error handling.\"\"\"
        # Get credentials from environment variables
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        username = os.getenv('REDDIT_USERNAME')
        password = os.getenv('REDDIT_PASSWORD')
        
        # Create a more specific user agent
        user_agent = os.getenv('REDDIT_USER_AGENT') or f"python:com.peaktransformation.leadgen:v1.0.0 (by /u/{username})"
        
        # Validate credentials
        if not all([client_id, client_secret, username, password]):
            logger.error("Missing Reddit API credentials. Check your .env file.")
            return
            
        # Log authentication attempt (with masked credentials)
        client_id_masked = f"{client_id[:4]}***" if client_id and len(client_id) > 4 else "***"
        logger.info(f"Initializing Reddit client (client_id={client_id_masked}, user={username})")
        
        try:
            # Create Reddit instance
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent
            )
            
            # Test connection with a simple call
            try:
                me = self.reddit.user.me()
                logger.info(f"Successfully connected to Reddit as: {me.name}")
                
                if self.verbose:
                    print(f"Connected to Reddit API as user: {me.name}")
                    print(f"Using {len(self.subreddits)} subreddits and {len(self.keywords)} keywords")
            except Exception as e:
                logger.error(f"Failed to verify Reddit user: {str(e)}")
                # Try direct API authentication as a fallback
                if not self._validate_credentials_direct():
                    logger.error("Both PRAW and direct authentication failed")
                    
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {str(e)}")
            if "401" in str(e):
                logger.error("Authentication error (401) - check your Reddit credentials")
                if self.verbose:
                    print("Authentication failed - check your Reddit credentials")
            if "429" in str(e):
                logger.error("Rate limit error (429) - Reddit is limiting requests")
                if self.verbose:
                    print("Reddit rate limit reached - try again later")
            
            # Try direct authentication
            if not self._validate_credentials_direct():
                logger.error("Both PRAW and direct authentication failed")
    
    def _validate_credentials_direct(self) -> bool:
        \"\"\"Validate Reddit credentials with a direct API request.\"\"\"
        try:
            # Get credentials
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')
            
            logger.info("Attempting direct Reddit API authentication...")
            if self.verbose:
                print("Trying direct API authentication...")
            
            # Create auth for token request
            auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
            
            # Set up data for token request
            data = {
                'grant_type': 'password',
                'username': username,
                'password': password
            }
            
            # Set up headers
            headers = {'User-Agent': f'python:com.peaktransformation.leadgen:v1.0.0 (by /u/{username})'}
            
            # Make the request
            response = requests.post(
                'https://www.reddit.com/api/v1/access_token',
                auth=auth,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info("Direct authentication successful")
                if self.verbose:
                    print("Direct authentication successful")
                return True
            else:
                logger.error(f"Direct authentication failed: {response.status_code} - {response.text}")
                if self.verbose:
                    print(f"Authentication failed: HTTP {response.status_code}")
                    print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error in direct authentication: {str(e)}")
            if self.verbose:
                print(f"Error: {str(e)}")
            return False
    
    def keyword_match(self, text: str) -> List[str]:
        \"\"\"
        Check if text contains any target keywords.
        
        Args:
            text: The text to check
            
        Returns:
            List of matching keywords
        \"\"\"
        if not text:
            return []
            
        text = text.lower()
        matches = []
        
        for keyword in self.keywords:
            if keyword.lower() in text:
                matches.append(keyword)
                
                # Update keyword stats
                if keyword in self.results["keyword_stats"]:
                    self.results["keyword_stats"][keyword] += 1
                else:
                    self.results["keyword_stats"][keyword] = 1
                
        return matches
    
    def calculate_lead_score(self, post_data: Dict[str, Any]) -> int:
        \"\"\"
        Calculate a numerical score for a lead based on various factors.
        
        Args:
            post_data: The post data dictionary
            
        Returns:
            Score from 0-100
        \"\"\"
        score = 0
        
        # Score based on number of keywords matched (max 30)
        keywords = post_data.get("matched_keywords", "").split(", ")
        keyword_count = len(keywords)
        score += min(keyword_count * 10, 30)
        
        # Score based on post engagement (max 20)
        upvotes = post_data.get("score", 0)
        comments = post_data.get("comment_count", 0)
        
        if upvotes > 100:
            score += 10
        elif upvotes > 50:
            score += 5
        
        if comments > 50:
            score += 10
        elif comments > 20:
            score += 5
        
        # Score based on post length/detail (max 20)
        content_length = len(post_data.get("post_content", ""))
        if content_length > 1000:
            score += 20
        elif content_length > 500:
            score += 15
        elif content_length > 200:
            score += 10
        elif content_length > 100:
            score += 5
        
        # Score based on high-value keywords (max 30)
        high_value_keywords = [
            "career transition", "executive", "leadership", 
            "professional development", "struggling", "mentor",
            "advice needed", "guidance", "coach"
        ]
        
        text = f"{post_data.get('post_title', '')} {post_data.get('post_content', '')}".lower()
        
        for keyword in high_value_keywords:
            if keyword in text:
                score += 5
                if score >= 100:
                    break
        
        # Cap at 100
        return min(score, 100)
    
    def scrape_subreddit(self, subreddit_name: str) -> List[Dict[str, Any]]:
        \"\"\"
        Scrape a single subreddit for relevant posts.
        
        Args:
            subreddit_name: Name of the subreddit to scrape
            
        Returns:
            List of matching post data
        \"\"\"
        matching_posts = []
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                logger.info(f"Scraping r/{subreddit_name} (attempt {retry_count+1})...")
                if self.verbose:
                    print(f"Scraping r/{subreddit_name}...")
                
                # Initialize subreddit stats if not present
                if subreddit_name not in self.results["subreddit_stats"]:
                    self.results["subreddit_stats"][subreddit_name] = {
                        "posts_analyzed": 0,
                        "matching_posts": 0
                    }
                
                # Get the subreddit
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get top posts for the time period
                for post in subreddit.top(time_filter=self.time_filter, limit=self.post_limit):
                    # Update post count
                    self.results["total_posts_analyzed"] += 1
                    self.results["subreddit_stats"][subreddit_name]["posts_analyzed"] += 1
                    
                    try:
                        # Combine title and content for matching
                        full_text = f"{post.title} {post.selftext if hasattr(post, 'selftext') else ''}"
                        matched_keywords = self.keyword_match(full_text)
                        
                        # Skip if no keywords match
                        if not matched_keywords:
                            continue
                            
                        # Extract post data
                        post_data = {
                            "username": post.author.name if post.author else "[deleted]",
                            "post_title": post.title,
                            "post_content": post.selftext[:3000] if hasattr(post, 'selftext') else "",
                            "subreddit": subreddit_name,
                            "post_url": f"https://www.reddit.com{post.permalink}",
                            "matched_keywords": ", ".join(matched_keywords),
                            "score": post.score,
                            "comment_count": post.num_comments,
                            "created_utc": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Calculate lead score
                        post_data["lead_score"] = self.calculate_lead_score(post_data)
                        
                        # Add to results
                        matching_posts.append(post_data)
                        self.results["matching_posts"] += 1
                        self.results["subreddit_stats"][subreddit_name]["matching_posts"] += 1
                        
                    except Exception as e:
                        logger.warning(f"Error processing post in r/{subreddit_name}: {str(e)}")
                        continue
                
                # If we get here without exception, break the retry loop
                break
                
            except Exception as e:
                retry_count += 1
                error_message = str(e)
                
                if "401" in error_message:
                    logger.error(f"Authentication error (401) scraping r/{subreddit_name}: {error_message}")
                    if retry_count >= max_retries:
                        break
                elif "403" in error_message:
                    logger.error(f"Access forbidden (403) for r/{subreddit_name} - subreddit may be private")
                    break  # Don't retry private subreddits
                elif "404" in error_message:
                    logger.error(f"Subreddit not found (404): r/{subreddit_name}")
                    break  # Don't retry non-existent subreddits
                elif "429" in error_message:
                    logger.error(f"Rate limited (429) while scraping r/{subreddit_name} - waiting longer")
                    time.sleep(10)  # Wait longer on rate limits
                else:
                    logger.error(f"Error scraping r/{subreddit_name}: {error_message}")
                    time.sleep(2)
                
                if retry_count >= max_retries:
                    logger.error(f"Giving up on r/{subreddit_name} after {max_retries} attempts")
                    if self.verbose:
                        print(f"  Error accessing r/{subreddit_name} - skipping")
                    break
        
        if matching_posts:
            logger.info(f"Found {len(matching_posts)} matching posts in r/{subreddit_name}")
            if self.verbose:
                print(f"  Found {len(matching_posts)} matching posts in r/{subreddit_name}")
        else:
            logger.info(f"No matching posts found in r/{subreddit_name}")
            if self.verbose:
                print(f"  No matching posts found in r/{subreddit_name}")
                
        return matching_posts
    
    def search_reddit_by_query(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        \"\"\"
        Search Reddit for a specific keyword.
        
        Args:
            query: Keyword to search for
            limit: Maximum number of results
            
        Returns:
            List of matching post data
        \"\"\"
        matching_posts = []
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                logger.info(f"Searching for keyword: '{query}' (attempt {retry_count+1})...")
                if self.verbose:
                    print(f"Searching Reddit for '{query}'...")
                
                # Search across Reddit
                for post in self.reddit.subreddit("all").search(
                    query, 
                    sort="relevance", 
                    time_filter=self.time_filter, 
                    limit=limit
                ):
                    # Update post count
                    self.results["total_posts_analyzed"] += 1
                    
                    try:
                        # Only process posts from our target subreddits
                        subreddit_name = post.subreddit.display_name
                        if subreddit_name not in self.subreddits:
                            continue
                            
                        # Initialize subreddit stats if not present
                        if subreddit_name not in self.results["subreddit_stats"]:
                            self.results["subreddit_stats"][subreddit_name] = {
                                "posts_analyzed": 0,
                                "matching_posts": 0
                            }
                        
                        self.results["subreddit_stats"][subreddit_name]["posts_analyzed"] += 1
                        
                        # Update keyword stats
                        if query in self.results["keyword_stats"]:
                            self.results["keyword_stats"][query] += 1
                        else:
                            self.results["keyword_stats"][query] = 1
                        
                        # Extract post data
                        post_data = {
                            "username": post.author.name if post.author else "[deleted]",
                            "post_title": post.title,
                            "post_content": post.selftext[:3000] if hasattr(post, 'selftext') else "",
                            "subreddit": subreddit_name,
                            "post_url": f"https://www.reddit.com{post.permalink}",
                            "matched_keywords": query,
                            "score": post.score,
                            "comment_count": post.num_comments,
                            "created_utc": datetime.fromtimestamp(post.created_utc).strftime("%Y-%m-%d %H:%M:%S"),
                            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        # Calculate lead score
                        post_data["lead_score"] = self.calculate_lead_score(post_data)
                        
                        # Add to results
                        matching_posts.append(post_data)
                        self.results["matching_posts"] += 1
                        self.results["subreddit_stats"][subreddit_name]["matching_posts"] += 1
                        
                    except Exception as e:
                        logger.warning(f"Error processing search result for '{query}': {str(e)}")
                        continue
                
                # If we get here without exception, break the retry loop
                break
                
            except Exception as e:
                retry_count += 1
                error_message = str(e)
                
                if "401" in error_message:
                    logger.error(f"Authentication error (401) searching for '{query}': {error_message}")
                    if retry_count >= max_retries:
                        break
                elif "429" in error_message:
                    logger.error(f"Rate limited (429) while searching for '{query}' - waiting longer")
                    time.sleep(10)  # Wait longer on rate limits
                else:
                    logger.error(f"Error searching for '{query}': {error_message}")
                    time.sleep(2)
                
                if retry_count >= max_retries:
                    logger.error(f"Giving up on keyword '{query}' after {max_retries} attempts")
                    if self.verbose:
                        print(f"  Error searching for '{query}' - skipping")
                    break
        
        if matching_posts:
            logger.info(f"Found {len(matching_posts)} matching posts for keyword '{query}'")
            if self.verbose:
                print(f"  Found {len(matching_posts)} matching posts for '{query}'")
        else:
            logger.info(f"No matching posts found for keyword '{query}'")
            if self.verbose:
                print(f"  No matching posts found for '{query}'")
                
        return matching_posts
    
    def search_all_keywords(self) -> List[Dict[str, Any]]:
        \"\"\"
        Search Reddit for all configured keywords.
        
        Returns:
            List of all collected lead data
        \"\"\"
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
    
    def scrape_all_subreddits(self) -> List[Dict[str, Any]]:
        \"\"\"
        Scrape all configured subreddits for relevant posts.
        
        Returns:
            List of all collected lead data
        \"\"\"
        all_leads = []
        
        for subreddit_name in self.subreddits:
            subreddit_leads = self.scrape_subreddit(subreddit_name)
            all_leads.extend(subreddit_leads)
            
        logger.info(f"Collected a total of {len(all_leads)} leads from {len(self.subreddits)} subreddits")
        return all_leads
    
    def save_leads_to_google_sheets(self, leads: List[Dict[str, Any]], sheets_client) -> bool:
        \"\"\"
        Save leads to Google Sheets.
        
        Args:
            leads: List of lead information dictionaries
            sheets_client: Google Sheets client or worksheet object
            
        Returns:
            True if saving was successful, False otherwise
        \"\"\"
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
        \"\"\"
        Save leads to a CSV file.
        
        Args:
            leads: List of lead information dictionaries
            filename: Output CSV filename
            
        Returns:
            True if saving was successful, False otherwise
        \"\"\"
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
        \"\"\"
        Run a full scraping operation and save the results.
        
        Args:
            sheets_client: Google Sheets client or worksheet (optional)
            save_csv: Whether to save results to a CSV file
            csv_filename: Filename for CSV output
            
        Returns:
            List of all collected leads
        \"\"\"
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
        
        # Sort by lead score (highest first)
        unique_leads.sort(key=lambda x: x.get("lead_score", 0), reverse=True)
        
        # Store in results
        self.results["leads"] = unique_leads
        
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
    \"\"\"
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
    \"\"\"
    # Create the scraper with provided or default parameters
    scraper = RedditScraper(
        subreddits=subreddits,
        keywords=keywords,
        time_filter=time_filter,
        post_limit=post_limit,
        verbose=False
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
"""

NEW_SCRAPER_INIT_CONTENT = """\"\"\"
Scrapers package for the Lead Generation Tool.
Includes scrapers for LinkedIn and Reddit.
\"\"\"

from scrapers.linkedin import LinkedInScraper, run_linkedin_scraper
from scrapers.reddit.scraper import RedditScraper, run_reddit_scraper

__all__ = ['LinkedInScraper', 'run_linkedin_scraper', 'RedditScraper', 'run_reddit_scraper']
"""

def print_step(step_name, description=""):
    """Print a formatted step to the console."""
    print(f"\n{'=' * 40}")
    print(f"STEP: {step_name}")
    if description:
        print(f"{description}")
    print(f"{'=' * 40}\n")

def create_backup():
    """Create backups of necessary files."""
    print_step("Creating Backups", "Backing up files before modifications")
    
    try:
        # Create backup directory
        os.makedirs(BACKUP_DIR, exist_ok=True)
        
        # Identify files to backup
        reddit_scraper_py = os.path.join(PROJECT_ROOT, REDDIT_SCRAPER_MODULE, "scraper.py")
        reddit_init_py = os.path.join(PROJECT_ROOT, REDDIT_SCRAPER_MODULE, "__init__.py")
        
        # Backup Reddit scraper files
        if os.path.exists(reddit_scraper_py):
            shutil.copy2(reddit_scraper_py, os.path.join(BACKUP_DIR, "scraper.py.bak"))
            print(f"Backed up {reddit_scraper_py}")
        
        if os.path.exists(reddit_init_py):
            shutil.copy2(reddit_init_py, os.path.join(BACKUP_DIR, "__init__.py.bak"))
            print(f"Backed up {reddit_init_py}")
        
        # Backup scrapers/__init__.py
        scrapers_init_py = os.path.join(PROJECT_ROOT, "scrapers", "__init__.py")
        if os.path.exists(scrapers_init_py):
            shutil.copy2(scrapers_init_py, os.path.join(BACKUP_DIR, "scrapers__init__.py.bak"))
            print(f"Backed up {scrapers_init_py}")
        
        # Backup main.py to be safe
        main_py = os.path.join(PROJECT_ROOT, "main.py")
        if os.path.exists(main_py):
            shutil.copy2(main_py, os.path.join(BACKUP_DIR, "main.py.bak"))
            print(f"Backed up {main_py}")
            
        print(f"All backups created in {BACKUP_DIR}")
        return True
    except Exception as e:
        print(f"Error creating backups: {str(e)}")
        return False

def update_scrapers_init():
    """Update the scrapers/__init__.py file to ensure it imports correctly."""
    print_step("Updating Scrapers Package", "Ensuring proper imports in scrapers/__init__.py")
    
    scrapers_init_py = os.path.join(PROJECT_ROOT, "scrapers", "__init__.py")
    
    try:
        # Write the updated content
        with open(scrapers_init_py, 'w') as f:
            f.write(NEW_SCRAPER_INIT_CONTENT)
        print(f"Updated {scrapers_init_py}")
        return True
    except Exception as e:
        print(f"Error updating scrapers/__init__.py: {str(e)}")
        return False

def update_reddit_module():
    """Update the Reddit scraper module with the new implementation."""
    print_step("Replacing Reddit Scraper", "Installing the new Reddit scraper implementation")
    
    # Ensure the Reddit module directory exists
    reddit_module_dir = os.path.join(PROJECT_ROOT, REDDIT_SCRAPER_MODULE)
    os.makedirs(reddit_module_dir, exist_ok=True)
    
    try:
        # Update the scraper.py file
        scraper_path = os.path.join(reddit_module_dir, "scraper.py")
        with open(scraper_path, 'w') as f:
            f.write(NEW_SCRAPER_MODULE_CONTENT)
        print(f"Updated {scraper_path}")
        
        # Create or update the __init__.py file if it doesn't exist
        init_path = os.path.join(reddit_module_dir, "__init__.py")
        
        # Simple content for the init file - can be empty, just needs to exist
        with open(init_path, 'w') as f:
            f.write('"""Reddit scraper module for the Lead Generation Tool."""\n')
        print(f"Updated {init_path}")
        
        return True
    except Exception as e:
        print(f"Error updating Reddit module: {str(e)}")
        return False

def update_main_py():
    """Update main.py to use the new Reddit scraper if needed."""
    print_step("Checking Main Script", "Verifying main.py works with the new scraper")
    
    main_py_path = os.path.join(PROJECT_ROOT, "main.py")
    
    if not os.path.exists(main_py_path):
        print(f"Warning: main.py not found at {main_py_path}, skipping")
        return True
        
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
            
        # Check if the Reddit scraper import is correct
        if "from scrapers.reddit.scraper import run_reddit_scraper" in content:
            print("main.py is already using the correct import path")
            return True
            
        # Only update if we need to fix the import
        updated_content = re.sub(
            r'from scrapers(?:\.\w+)* import .*?run_reddit_scraper',
            'from scrapers.reddit.scraper import run_reddit_scraper',
            content
        )
        
        # Only write to file if we made changes
        if updated_content != content:
            with open(main_py_path, 'w') as f:
                f.write(updated_content)
            print(f"Updated import in {main_py_path}")
            
        return True
    except Exception as e:
        print(f"Error updating main.py: {str(e)}")
        return False

def run_installation():
    """Execute the full installation process."""
    print("\n" + "=" * 80)
    print(" REDDIT SCRAPER REPLACEMENT SCRIPT ".center(80, "="))
    print("=" * 80 + "\n")
    
    print("This script will replace the current Reddit scraper with")
    print("the new implementation that includes better error handling")
    print("and more robust lead collection capabilities.\n")
    
    print("Before continuing, make sure:")
    print("1. Your lead generation tool is not currently running")
    print("2. You have your Reddit API credentials in your .env file")
    print("\nBackups will be created before any changes are made.")
    
    proceed = input("\nDo you want to proceed? (y/n): ").strip().lower()
    if proceed != 'y':
        print("Installation cancelled.")
        return
    
    # Step 1: Create backups
    if not create_backup():
        print("Failed to create backups. Aborting installation.")
        return
    
    # Step 2: Update the scrapers/__init__.py file
    if not update_scrapers_init():
        print("Failed to update scrapers/__init__.py. Aborting installation.")
        return
    
    # Step 3: Replace the Reddit scraper module
    if not update_reddit_module():
        print("Failed to update Reddit scraper module. Aborting installation.")
        return
    
    # Step 4: Update main.py if needed
    if not update_main_py():
        print("Warning: Could not update main.py, but continuing installation.")
    
    # Final step: Verify installation
    print_step("Installation Complete", "The new Reddit scraper has been installed successfully")
    print("The new Reddit scraper has been installed with the following improvements:")
    print("- Better error handling and retry logic")
    print("- More robust authentication methods")
    print("- Lead scoring to prioritize the most promising prospects")
    print("- Comprehensive logging for better troubleshooting")
    
    print("\nTo test the new scraper, you can run:")
    print("  python -m scrapers.reddit.scraper")
    
    print("\nOr use your lead generation tool normally with:")
    print("  python main.py reddit")
    
    print("\nIf you encounter any issues, backups of your original files")
    print(f"can be found in the {BACKUP_DIR} directory.")

if __name__ == "__main__":
    run_installation()