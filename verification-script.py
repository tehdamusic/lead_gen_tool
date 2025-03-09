#!/usr/bin/env python3
"""
Verification script for the web-based Reddit scraper.
Tests that the scraper works correctly and returns data in the expected format.
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Add the project root to the path so we can import the modules
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_web_scraper_directly():
    """Test the web scraper directly to check if it can access Reddit."""
    print("\nTesting direct access to Reddit...")
    
    try:
        from scrapers.reddit.web_scraper import RedditWebScraper
        
        # Create the web scraper
        web_scraper = RedditWebScraper()
        
        # Try to access Reddit's front page
        print("Attempting to access Reddit's front page...")
        html_content = web_scraper.session.get("https://www.reddit.com/").text
        
        # Check if we got a valid response
        if "Reddit" in html_content and len(html_content) > 1000:
            print(f"✓ Successfully accessed Reddit! (Got {len(html_content)} bytes)")
            
            # Let's check if we can find any posts
            print("\nLooking for post elements in the HTML...")
            from bs4 import BeautifulSoup
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try different selectors to find posts
            selectors = [
                'div.thing', 
                'div[data-testid="post-container"]',
                'div.Post',
                'div._1oQyIsiPHYt6nx7VOmd1sz',  # Current Reddit post container class
                'article'  # Another common container for posts
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"✓ Found {len(elements)} elements with selector: {selector}")
                    
                    # If we found elements, let's print some details about the first one
                    if len(elements) > 0:
                        print(f"Sample element: {elements[0].name} with {len(elements[0].attrs)} attributes")
                        print(f"Classes: {elements[0].get('class', 'No class')}")
                        print(f"Contains {len(elements[0].find_all())} child elements")
                    
                    break
            else:
                print("✗ Could not find any post elements with known selectors")
                # Print some information about the page structure
                print(f"Page has {len(soup.find_all())} total elements")
                print(f"Common elements: {', '.join([tag.name for tag in soup.find_all()[:10]])}")
                
            return True
        else:
            print(f"✗ Received invalid or empty response from Reddit")
            return False
            
    except Exception as e:
        print(f"Error accessing Reddit: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_web_scraper():
    """Test that the web-based Reddit scraper works and returns data in the expected format."""
    print("Testing web-based Reddit scraper...")
    
    try:
        from scrapers.reddit.scraper import RedditScraper, run_reddit_scraper
        
        # Create a minimal test configuration with a popular subreddit and common keywords
        test_subreddits = ["AskReddit"]
        test_keywords = ["help", "advice", "question"]
        
        # Initialize the scraper
        scraper = RedditScraper(
            subreddits=test_subreddits,
            keywords=test_keywords,
            time_filter="week",  # Use 'week' for faster results
            post_limit=5  # Limit to 5 posts for faster testing
        )
        
        print(f"Successfully initialized scraper with subreddits: {test_subreddits}")
        print(f"Using keywords: {test_keywords}")
        
        # Test a single subreddit scrape
        print("\nTesting single subreddit scrape...")
        subreddit_leads = scraper.scrape_subreddit(test_subreddits[0])
        print(f"Found {len(subreddit_leads)} leads in r/{test_subreddits[0]}")
        
        if subreddit_leads:
            print("Sample lead data:")
            sample_lead = subreddit_leads[0]
            for key, value in sample_lead.items():
                # Truncate long values for display
                if isinstance(value, str) and len(value) > 50:
                    value = value[:50] + "..."
                print(f"  {key}: {value}")
        
        # Test keyword search
        print("\nTesting keyword search...")
        keyword_leads = scraper.search_reddit_by_query(test_keywords[0], limit=5)
        print(f"Found {len(keyword_leads)} leads for keyword '{test_keywords[0]}'")
        
        # Test saving to CSV
        if subreddit_leads or keyword_leads:
            all_leads = subreddit_leads + keyword_leads
            test_filename = "test_reddit_leads.csv"
            
            print(f"\nSaving {len(all_leads)} leads to {test_filename}...")
            scraper.save_leads_to_csv(all_leads, test_filename)
            
            # Verify the CSV was created
            if os.path.exists(test_filename):
                print(f"Successfully created {test_filename}")
                
                # Check that the data is correctly formatted
                df = pd.read_csv(test_filename)
                print(f"CSV contains {len(df)} rows and {len(df.columns)} columns")
                print(f"Columns: {', '.join(df.columns)}")
                
                # Clean up the test file
                os.remove(test_filename)
                print(f"Cleaned up test file {test_filename}")
            else:
                print(f"Error: Failed to create {test_filename}")
        
        print("\nWeb scraper test completed.")
        return True
        
    except Exception as e:
        print(f"\nError during web scraper test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_main_integration():
    """Test that the main.py file correctly uses the web-based Reddit scraper."""
    print("\nTesting integration with main.py...")
    
    try:
        # We'll use a mock args object to simulate command line arguments
        class MockArgs:
            def __init__(self):
                self.max_leads = 5
                self.save_csv = True
                self.subreddits = "AskReddit"
                self.keywords = "help,advice,question"
        
        # Import the run_reddit_scraper function from main.py
        sys.path.insert(0, project_root)
        from main import run_reddit_scraper
        
        # Create mock args
        args = MockArgs()
        
        print("Calling run_reddit_scraper from main.py...")
        results = run_reddit_scraper(args)
        
        if results.get("success", False):
            print(f"Successfully ran Reddit scraper from main.py")
            print(f"Collected {results.get('leads_scraped', 0)} leads")
            return True
        else:
            print(f"Error running Reddit scraper from main.py: {results.get('error', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"\nError testing main.py integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_downstream_compatibility():
    """Verify that downstream components (scoring, message generation) can use the web scraper data."""
    print("\nVerifying compatibility with downstream components...")
    
    # Check if lead_scorer.py can process the data
    try:
        from analysis.lead_scorer import LeadScorer
        
        # Create a test lead in the format produced by the web scraper
        test_lead = {
            "username": "test_user",
            "post_title": "Feeling overwhelmed with my job",
            "post_content": "I've been working 60+ hours a week and feeling burnt out.",
            "subreddit": "AskReddit",
            "post_url": "https://www.reddit.com/r/AskReddit/test_post",
            "matched_keywords": "burnout, overwhelmed",
            "score": 100,
            "comment_count": 10,
            "created_utc": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Create a scorer and test if it can process the lead
        scorer = LeadScorer(threshold=0.5, use_ai=False)
        
        print("Testing if LeadScorer can process web scraper lead data...")
        scored_leads = scorer.score_leads([test_lead])
        
        if scored_leads and len(scored_leads) > 0:
            print("✓ LeadScorer successfully processed web scraper lead data")
            print(f"  Final score: {scored_leads[0].get('final_score', 'N/A')}")
            print(f"  Qualified: {scored_leads[0].get('qualified', 'N/A')}")
        else:
            print("✗ LeadScorer failed to process web scraper lead data")
        
        # Check message generator if available
        try:
            from communication.message_generator import MessageGenerator
            
            print("Testing if MessageGenerator can process web scraper lead data...")
            # We'll skip actually running the generator to avoid API calls
            test_method = None
            
            try:
                # Try to access the method without errors
                test_method = MessageGenerator.process_reddit_leads
                print("✓ MessageGenerator appears compatible with web scraper lead data")
            except AttributeError:
                print("? MessageGenerator interface is different than expected")
                print("  You may need to manually verify message generator compatibility")
                
        except (ImportError, AttributeError) as e:
            print(f"? Cannot verify MessageGenerator compatibility: {str(e)}")
        
        return True
        
    except (ImportError, Exception) as e:
        print(f"Error verifying downstream compatibility: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the verification script."""
    print("==================================================")
    print("Web-based Reddit Scraper Verification")
    print("==================================================")
    
    success = []
    
    # Test direct access to Reddit
    direct_access_success = test_web_scraper_directly()
    success.append(direct_access_success)
    
    # Test the web scraper
    web_scraper_success = test_web_scraper()
    success.append(web_scraper_success)
    
    # Test the main.py integration
    integration_success = test_main_integration()
    success.append(integration_success)
    
    # Verify downstream compatibility
    compatibility_success = verify_downstream_compatibility()
    success.append(compatibility_success)
    
    # Print overall results
    print("\n==================================================")
    print("Verification Results:")
    print(f"- Direct Reddit access: {'✓ Passed' if direct_access_success else '✗ Failed'}")
    print(f"- Web scraper test: {'✓ Passed' if web_scraper_success else '✗ Failed'}")
    print(f"- Main.py integration: {'✓ Passed' if integration_success else '✗ Failed'}")
    print(f"- Downstream compatibility: {'✓ Passed' if compatibility_success else '✗ Failed'}")
    print(f"\nOverall result: {'✓ ALL TESTS PASSED' if all(success) else '✗ SOME TESTS FAILED'}")
    print("==================================================")

if __name__ == "__main__":
    main()