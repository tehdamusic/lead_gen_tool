#!/usr/bin/env python3
"""
Alternative Lead Scraper Module
-------------------------------
This module provides an alternative to the Reddit scraper by using web scraping
to collect career-related content and leads from other sources.
"""

import os
import csv
import time
import random
import logging
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/alternative_scraper.log'
)
logger = logging.getLogger('alternative_scraper')

# Ensure necessary directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('data', exist_ok=True)
os.makedirs('data/output', exist_ok=True)

class AlternativeScraper:
    """
    Scraper for collecting leads from alternative sources
    when Reddit API is unavailable.
    """
    
    def __init__(self, 
                 keywords: Optional[List[str]] = None,
                 max_leads: int = 50,
                 include_career_sites: bool = True,
                 include_forum_sites: bool = True):
        """
        Initialize the alternative scraper.
        
        Args:
            keywords: List of keywords to search for
            max_leads: Maximum number of leads to collect
            include_career_sites: Whether to include career advice sites
            include_forum_sites: Whether to include forum sites
        """
        # Default keywords related to coaching needs
        self.keywords = keywords or [
            "burnout", "career transition", "work-life balance",
            "leadership development", "professional growth",
            "job stress", "career change", "overwhelmed at work"
        ]
        
        self.max_leads = max_leads
        self.include_career_sites = include_career_sites
        self.include_forum_sites = include_forum_sites
        
        # Sources to scrape
        self.sources = []
        
        if include_career_sites:
            self.sources.extend([
                {
                    "name": "Career Builder Articles",
                    "url": "https://www.careerbuilder.com/advice/career-management",
                    "type": "career_site",
                    "selectors": {
                        "articles": "article",
                        "title": "h2",
                        "link": "a",
                        "summary": "div.article-description",
                        "author": "span.article-author"
                    }
                },
                {
                    "name": "Indeed Career Guide",
                    "url": "https://www.indeed.com/career-advice/career-development",
                    "type": "career_site",
                    "selectors": {
                        "articles": "div.css-kyg8or",
                        "title": "h2.css-1r0epbu",
                        "link": "a",
                        "summary": "p.css-58fg8c",
                        "author": None
                    }
                }
            ])
        
        if include_forum_sites:
            self.sources.extend([
                {
                    "name": "Hacker News",
                    "url": "https://news.ycombinator.com/",
                    "type": "forum",
                    "selectors": {
                        "articles": "tr.athing",
                        "title": "span.titleline a",
                        "link": "span.titleline a",
                        "points": "span.score",
                        "author": "a.hnuser"
                    }
                }
            ])
        
        logger.info(f"Alternative scraper initialized with {len(self.keywords)} keywords")
        logger.info(f"Using {len(self.sources)} alternative sources")
    
    def _get_user_agent(self) -> str:
        """
        Get a random user agent string.
        
        Returns:
            Random user agent string
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        return random.choice(user_agents)
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and parse it with BeautifulSoup.
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetching failed
        """
        headers = {
            "User-Agent": self._get_user_agent(),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            logger.info(f"Fetching URL: {url}")
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None
        
        except Exception as e:
            logger.error(f"Unexpected error processing URL {url}: {str(e)}")
            return None
    
    def extract_articles_from_source(self, source: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract articles from a source.
        
        Args:
            source: Source dictionary with URL and selectors
            
        Returns:
            List of article dictionaries
        """
        articles = []
        soup = self.fetch_page(source["url"])
        
        if not soup:
            logger.warning(f"Failed to fetch {source['name']}")
            return articles
        
        try:
            # Extract articles based on the source selectors
            article_elements = soup.select(source["selectors"]["articles"])
            logger.info(f"Found {len(article_elements)} potential articles on {source['name']}")
            
            for article_element in article_elements[:20]:  # Limit to top 20
                try:
                    # Extract title
                    title_element = article_element.select_one(source["selectors"]["title"])
                    title = title_element.text.strip() if title_element else "No title"
                    
                    # Extract link
                    link_element = article_element.select_one(source["selectors"]["link"])
                    link = link_element["href"] if link_element and "href" in link_element.attrs else ""
                    
                    # Make link absolute if it's relative
                    if link and not link.startswith(("http://", "https://")):
                        if link.startswith("/"):
                            # Extract base URL
                            base_url = "/".join(source["url"].split("/")[:3])
                            link = base_url + link
                        else:
                            # Assume it's relative to the current URL
                            link = source["url"] + "/" + link
                    
                    # Extract summary or content if available
                    summary_element = None
                    if "summary" in source["selectors"] and source["selectors"]["summary"]:
                        summary_element = article_element.select_one(source["selectors"]["summary"])
                    summary = summary_element.text.strip() if summary_element else ""
                    
                    # Extract author if available
                    author_element = None
                    if "author" in source["selectors"] and source["selectors"]["author"]:
                        author_element = article_element.select_one(source["selectors"]["author"])
                    author = author_element.text.strip() if author_element else "Unknown"
                    
                    # Create article dictionary
                    article = {
                        "title": title,
                        "url": link,
                        "summary": summary,
                        "author": author,
                        "source": source["name"],
                        "source_type": source["type"],
                        "matched_keywords": [],
                        "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Check if article matches any keywords
                    article_text = (title + " " + summary).lower()
                    for keyword in self.keywords:
                        if keyword.lower() in article_text:
                            article["matched_keywords"].append(keyword)
                    
                    # Only add article if it matches keywords
                    if article["matched_keywords"]:
                        article["matched_keywords"] = ", ".join(article["matched_keywords"])
                        articles.append(article)
                        logger.debug(f"Found matching article: {title}")
                
                except Exception as e:
                    logger.warning(f"Error processing article in {source['name']}: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(articles)} matching articles from {source['name']}")
            return articles
            
        except Exception as e:
            logger.error(f"Error extracting articles from {source['name']}: {str(e)}")
            return []
    
    def search_career_keyword(self, keyword: str) -> List[Dict[str, Any]]:
        """
        Search for career advice articles with a specific keyword.
        
        Args:
            keyword: Keyword to search for
            
        Returns:
            List of article dictionaries
        """
        articles = []
        
        try:
            # Search Indeed Career Guide
            search_url = f"https://www.indeed.com/career-advice/search?q={keyword.replace(' ', '+')}"
            soup = self.fetch_page(search_url)
            
            if soup:
                # Extract search results
                result_elements = soup.select("div.css-kyg8or")
                
                for result in result_elements[:10]:  # Limit to top 10
                    try:
                        title_element = result.select_one("h2.css-1r0epbu")
                        link_element = result.select_one("a")
                        summary_element = result.select_one("p.css-58fg8c")
                        
                        title = title_element.text.strip() if title_element else "No title"
                        link = link_element["href"] if link_element and "href" in link_element.attrs else ""
                        summary = summary_element.text.strip() if summary_element else ""
                        
                        # Make link absolute if it's relative
                        if link and not link.startswith(("http://", "https://")):
                            if link.startswith("/"):
                                link = "https://www.indeed.com" + link
                            else:
                                link = "https://www.indeed.com/" + link
                        
                        # Create article dictionary
                        article = {
                            "title": title,
                            "url": link,
                            "summary": summary,
                            "author": "Indeed Career Guide",
                            "source": "Indeed Career Search",
                            "source_type": "career_site",
                            "matched_keywords": keyword,
                            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        
                        articles.append(article)
                        
                    except Exception as e:
                        logger.warning(f"Error processing search result for '{keyword}': {str(e)}")
                        continue
            
            logger.info(f"Found {len(articles)} articles for keyword '{keyword}'")
            return articles
            
        except Exception as e:
            logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
            return []
    
    def scrape_all_sources(self) -> List[Dict[str, Any]]:
        """
        Scrape all configured sources for matching articles.
        
        Returns:
            List of all collected article data
        """
        all_articles = []
        
        # Scrape each source
        for source in self.sources:
            try:
                articles = self.extract_articles_from_source(source)
                all_articles.extend(articles)
                
                # Add a small delay between sources
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Error scraping {source['name']}: {str(e)}")
                continue
        
        # Search for each keyword
        for keyword in self.keywords[:5]:  # Limit to top 5 keywords to avoid too many requests
            try:
                keyword_articles = self.search_career_keyword(keyword)
                all_articles.extend(keyword_articles)
                
                # Add a delay between keyword searches
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                logger.error(f"Error searching for keyword '{keyword}': {str(e)}")
                continue
        
        # Remove duplicates based on URL
        unique_articles = []
        seen_urls = set()
        
        for article in all_articles:
            if article["url"] and article["url"] not in seen_urls:
                seen_urls.add(article["url"])
                unique_articles.append(article)
        
        # Limit to max_leads
        if len(unique_articles) > self.max_leads:
            unique_articles = unique_articles[:self.max_leads]
        
        logger.info(f"Collected a total of {len(unique_articles)} unique articles")
        return unique_articles
    
    def save_to_csv(self, articles: List[Dict[str, Any]], filename: str = "data/alternative_leads.csv") -> bool:
        """
        Save articles to a CSV file.
        
        Args:
            articles: List of article dictionaries
            filename: Output CSV filename
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            if not articles:
                logger.warning("No articles to save to CSV")
                return False
                
            # Convert to DataFrame
            df = pd.DataFrame(articles)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            logger.info(f"Successfully saved {len(articles)} articles to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving articles to CSV: {str(e)}")
            return False
    
    def save_to_reddit_format(self, articles: List[Dict[str, Any]], filename: str = "data/reddit_leads.csv") -> bool:
        """
        Save articles in a format compatible with the Reddit leads CSV.
        
        Args:
            articles: List of article dictionaries
            filename: Output CSV filename
            
        Returns:
            True if saving was successful, False otherwise
        """
        try:
            if not articles:
                logger.warning("No articles to save in Reddit format")
                return False
            
            # Convert to Reddit-compatible format
            reddit_format = []
            
            for article in articles:
                reddit_lead = {
                    "username": article["author"],
                    "post_title": article["title"],
                    "post_content": article["summary"][:1000] if article["summary"] else "",
                    "subreddit": article["source"],
                    "post_url": article["url"],
                    "matched_keywords": article["matched_keywords"],
                    "score": random.randint(5, 50),  # Simulated score
                    "comment_count": random.randint(1, 20),  # Simulated comment count
                    "created_utc": (datetime.now().timestamp() - random.randint(86400, 604800)),  # Random recent timestamp
                    "date_added": article["date_added"]
                }
                
                reddit_format.append(reddit_lead)
            
            # Convert to DataFrame
            df = pd.DataFrame(reddit_format)
            
            # Save to CSV
            df.to_csv(filename, index=False)
            logger.info(f"Successfully saved {len(reddit_format)} leads in Reddit format to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving leads in Reddit format: {str(e)}")
            return False
    
    def run_scraper(self, use_reddit_format: bool = True) -> List[Dict[str, Any]]:
        """
        Run the scraper and save results.
        
        Args:
            use_reddit_format: Whether to save in Reddit-compatible format
            
        Returns:
            List of scraped articles
        """
        logger.info("Starting alternative scraper")
        
        try:
            # Scrape articles
            articles = self.scrape_all_sources()
            
            # Save results in original format
            self.save_to_csv(articles)
            
            # Save in Reddit format if requested
            if use_reddit_format:
                self.save_to_reddit_format(articles)
            
            logger.info("Alternative scraper completed successfully")
            return articles
            
        except Exception as e:
            logger.error(f"Error running alternative scraper: {str(e)}")
            return []


def run_alternative_scraper(sheets_client=None, 
                           keywords: Optional[List[str]] = None,
                           max_leads: int = 50,
                           save_csv: bool = True) -> List[Dict[str, Any]]:
    """
    Run the alternative scraper as a standalone function.
    
    Args:
        sheets_client: Google Sheets client for saving results (optional)
        keywords: List of keywords to search for
        max_leads: Maximum number of leads to collect
        save_csv: Whether to save results to CSV
        
    Returns:
        List of scraped articles
    """
    # Create the scraper with provided or default parameters
    scraper = AlternativeScraper(
        keywords=keywords,
        max_leads=max_leads,
        include_career_sites=True,
        include_forum_sites=True
    )
    
    # Run the scraper
    articles = scraper.run_scraper(use_reddit_format=True)
    
    # Save to Google Sheets if provided
    if sheets_client and articles:
        try:
            logger.info("Saving results to Google Sheets")
            
            # Prepare data for sheets
            rows = []
            for article in articles:
                row = [
                    article["author"],
                    article["title"],
                    article["source"],
                    article["url"],
                    article["matched_keywords"],
                    random.randint(5, 50),  # Simulated score
                    random.randint(1, 20),  # Simulated comment count
                    article["date_added"],
                    datetime.now().strftime("%Y-%m-%d")
                ]
                rows.append(row)
            
            # Create/get sheet
            try:
                worksheet = sheets_client.open('LeadGenerationData').worksheet('RedditLeads')
            except:
                worksheet = sheets_client.open('LeadGenerationData').add_worksheet(
                    title='RedditLeads', rows=1000, cols=20
                )
                # Add header row
                worksheet.append_row([
                    "Username", "Post Title", "Subreddit", "Post URL", 
                    "Matched Keywords", "Score", "Comment Count", 
                    "Created Date", "Date Added"
                ])
            
            # Append to Google Sheet
            for row in rows:
                worksheet.append_row(row)
                time.sleep(0.5)  # Sleep to avoid API rate limits
                
            logger.info(f"Successfully saved {len(rows)} leads to Google Sheets")
            
        except Exception as e:
            logger.error(f"Error saving to Google Sheets: {str(e)}")
    
    return articles


if __name__ == "__main__":
    # Test the scraper
    keywords = [
        "burnout", "career transition", "work-life balance",
        "leadership development", "professional growth"
    ]
    
    print(f"Starting alternative scraper with keywords: {', '.join(keywords)}")
    articles = run_alternative_scraper(keywords=keywords, max_leads=30)
    print(f"Collected {len(articles)} articles")
    
    if articles:
        print("\nSample results:")
        for i, article in enumerate(articles[:5]):
            print(f"\n{i+1}. {article['title']}")
            print(f"   Source: {article['source']}")
            print(f"   Keywords: {article['matched_keywords']}")
            print(f"   URL: {article['url']}")
