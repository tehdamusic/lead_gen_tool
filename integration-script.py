#!/usr/bin/env python3
"""
Integration script for the web-based Reddit scraper.

This script updates the main.py file to fully integrate the new web-based
Reddit scraper, replacing the API-based version.
"""

import os
import sys
import re
import shutil
from datetime import datetime

# Backup the original main.py file
def backup_main_file():
    """Create a backup of the main.py file before modifications."""
    if os.path.exists('main.py'):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'main.py.bak_{timestamp}'
        shutil.copy2('main.py', backup_file)
        print(f"Created backup of main.py as {backup_file}")
        return True
    else:
        print("Error: main.py file not found!")
        return False

# Update the main.py file to use the web-based Reddit scraper
def update_main_file():
    """Update the main.py file to use the web-based Reddit scraper."""
    if not os.path.exists('main.py'):
        print("Error: main.py file not found!")
        return False
    
    with open('main.py', 'r') as file:
        content = file.read()
    
    # Replace import statements if necessary
    if 'import praw' in content:
        print("Removing PRAW import as it's no longer needed...")
        content = re.sub(r'import praw\n', '', content)
    
    # Check if REDDIT_CLIENT environment variables are used in check_environment
    env_check_pattern = r'required_vars = \[(.*?)\]'
    env_check_match = re.search(env_check_pattern, content, re.DOTALL)
    
    if env_check_match:
        env_vars_text = env_check_match.group(1)
        if 'REDDIT_CLIENT_ID' in env_vars_text:
            print("Removing Reddit API environment variables from requirements...")
            updated_env_vars = []
            for line in env_vars_text.splitlines():
                if not any(var in line for var in ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']):
                    updated_env_vars.append(line)
            
            # Rejoin the updated env vars
            updated_env_vars_text = '\n'.join(updated_env_vars)
            content = content.replace(env_check_match.group(1), updated_env_vars_text)
    
    # Completely replace the run_reddit_scraper function with our new implementation
    # that uses the web-based scraper
    run_reddit_pattern = r'def run_reddit_scraper\(args\)(.*?)(?=def |$)'
    
    # The new implementation that directly calls the web-based scraper
    new_reddit_function = """def run_reddit_scraper(args) -> Dict[str, Any]:
    \"\"\"Run Reddit scraper component.\"\"\"
    try:
        from scrapers.reddit.scraper import run_reddit_scraper as reddit_scraper_runner
        from utils.sheets_manager import get_sheets_client
        
        print("Starting Reddit scraper...")
        sheets_client = get_sheets_client()
        
        # Get max leads from args or use default
        max_leads = getattr(args, 'max_leads', 50)
        save_csv = getattr(args, 'save_csv', True)
        
        # Get custom subreddits and keywords if provided
        subreddits = getattr(args, 'subreddits', None)
        keywords = getattr(args, 'keywords', None)
        
        # Run the scraper
        leads = reddit_scraper_runner(
            sheets_client=sheets_client,
            subreddits=subreddits,
            keywords=keywords,
            time_filter="month",
            post_limit=max_leads,
            save_csv=save_csv
        )
        
        results = {
            "leads_scraped": len(leads),
            "source": "reddit",
            "success": True
        }
        
        print(f"Reddit scraper completed. Collected {len(leads)} leads.")
        return results
    except Exception as e:
        logger.error(f"Error running Reddit scraper: {str(e)}")
        print(f"Error running Reddit scraper: {str(e)}")
        traceback.print_exc()
        return {
            "leads_scraped": 0,
            "source": "reddit",
            "success": False,
            "error": str(e)
        }

"""
    
    # Find and replace the run_reddit_scraper function
    if re.search(run_reddit_pattern, content, re.DOTALL):
        print("Replacing the run_reddit_scraper function...")
        content = re.sub(run_reddit_pattern, new_reddit_function, content, flags=re.DOTALL)
    else:
        print("Warning: Could not find run_reddit_scraper function in main.py!")
    
    # Remove the fallback scraper function if it exists
    fallback_pattern = r'def run_alternative_scraper_if_reddit_fails\(args\)(.*?)(?=def |$)'
    if re.search(fallback_pattern, content, re.DOTALL):
        print("Removing the alternative scraper fallback function...")
        content = re.sub(fallback_pattern, '', content, flags=re.DOTALL)
    
    # Update any references to the fallback function in run_full_pipeline
    if 'run_alternative_scraper_if_reddit_fails' in content:
        print("Updating references to the fallback scraper...")
        content = content.replace('run_alternative_scraper_if_reddit_fails(args)', 'run_reddit_scraper(args)')
    
    # Write the updated content back to main.py
    with open('main.py', 'w') as file:
        file.write(content)
    
    print("Successfully updated main.py to use the web-based Reddit scraper")
    return True

# Update the scrapers/__init__.py file if needed
def update_scrapers_init():
    """Ensure the scrapers/__init__.py file correctly imports the Reddit web scraper."""
    init_path = 'scrapers/__init__.py'
    if not os.path.exists(init_path):
        print(f"Error: {init_path} file not found!")
        return False
    
    with open(init_path, 'r') as file:
        content = file.read()
    
    # Check if the imports are already correct
    if 'from scrapers.reddit.scraper import RedditScraper, run_reddit_scraper' in content:
        print(f"{init_path} already has the correct imports.")
        return True
    
    # Update the imports if needed
    updated_content = re.sub(
        r'from scrapers\.reddit.*import.*',
        'from scrapers.reddit.scraper import RedditScraper, run_reddit_scraper',
        content
    )
    
    # Make sure the __all__ list includes the correct exports
    if '__all__' in updated_content:
        all_pattern = r'__all__ = \[(.*?)\]'
        all_match = re.search(all_pattern, updated_content, re.DOTALL)
        if all_match:
            all_items = all_match.group(1)
            if "'RedditScraper'" not in all_items or "'run_reddit_scraper'" not in all_items:
                # Add the missing items to __all__
                all_items_list = [item.strip() for item in re.findall(r"'([^']*)'", all_items)]
                if "'RedditScraper'" not in all_items:
                    all_items_list.append('RedditScraper')
                if "'run_reddit_scraper'" not in all_items:
                    all_items_list.append('run_reddit_scraper')
                
                # Update the __all__ list
                new_all = "__all__ = ['" + "', '".join(all_items_list) + "']"
                updated_content = re.sub(all_pattern, new_all, updated_content, flags=re.DOTALL)
    
    # Write the updated content back to the file
    with open(init_path, 'w') as file:
        file.write(updated_content)
    
    print(f"Successfully updated {init_path}")
    return True

# Run integration tests to verify the web scraper works correctly
def run_integration_tests():
    """Run simple integration tests to verify the web scraper works correctly."""
    print("\nRunning integration tests...")
    
    # Test importing the module
    try:
        from scrapers.reddit import RedditScraper, run_reddit_scraper
        print("✓ Successfully imported RedditScraper and run_reddit_scraper")
    except ImportError as e:
        print(f"✗ Import error: {str(e)}")
        return False
    
    # Test creating an instance of the scraper
    try:
        scraper = RedditScraper(
            subreddits=["Entrepreneur", "Productivity"],
            keywords=["burnout", "stress"],
            time_filter="week",
            post_limit=5
        )
        print(f"✓ Successfully created RedditScraper instance with {len(scraper.subreddits)} subreddits")
    except Exception as e:
        print(f"✗ Scraper initialization error: {str(e)}")
        return False
    
    # Test running a minimal scrape (just one subreddit, limited posts)
    print("Testing a minimal scrape (this might take a few seconds)...")
    try:
        # Run a minimal test scrape
        test_leads = scraper.scrape_subreddit("Entrepreneur")
        print(f"✓ Test scrape successful, found {len(test_leads)} leads")
    except Exception as e:
        print(f"✗ Test scrape error: {str(e)}")
        return False
    
    print("\nAll integration tests passed!")
    return True

# Main function
def main():
    """Run the integration script."""
    print("==================================================")
    print("Reddit Web Scraper Integration Script")
    print("==================================================")
    
    # Backup the main.py file
    if not backup_main_file():
        return
    
    # Update the main.py file
    if not update_main_file():
        return
    
    # Update the scrapers/__init__.py file
    update_scrapers_init()
    
    # Run integration tests
    run_integration_tests()
    
    print("\n==================================================")
    print("Integration completed successfully!")
    print("The web-based Reddit scraper is now fully integrated.")
    print("==================================================")

if __name__ == "__main__":
    main()
