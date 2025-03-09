"""
Reddit scraper package for the Lead Generation Tool.
Uses web scraping to collect data from Reddit without requiring API credentials.
"""

from .scraper import RedditScraper, run_reddit_scraper

__all__ = ['RedditScraper', 'run_reddit_scraper']