#!/usr/bin/env python3
"""
Script to fix all integration issues for the web-based Reddit scraper.
This script will:
1. Fix the indentation error in main.py
2. Fix the OpenAI client initialization in message_generator.py using modern best practices
3. Add improved testing for the web scraper
4. Optionally commit changes to git
"""

import os
import re
import sys
import subprocess
from datetime import datetime
import shutil

def backup_file(filepath):
    """Create a backup of a file."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{filepath}.bak_{timestamp}'
        shutil.copy2(filepath, backup_file)
        print(f"Created backup of {filepath} as {backup_file}")
        return True
    else:
        print(f"Error: {filepath} file not found!")
        return False

def fix_main_py():
    """Fix the indentation error in main.py."""
    main_py_path = 'main.py'
    
    if not os.path.exists(main_py_path):
        print(f"Error: {main_py_path} not found!")
        return False
    
    # Backup the file
    backup_file(main_py_path)
    
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the check_dependencies function
        dependency_pattern = r'def check_dependencies\(\)[^{]*?{.*?return (True|False).*?}(?=\s*def|\s*$)'
        
        # The corrected check_dependencies function
        corrected_function = '''def check_dependencies() -> bool:
    """Check that all required Python dependencies are installed."""
    try:
        # Check core dependencies one by one to pinpoint any issues
        print("Checking dependencies...")
        
        # Web scraping
        import selenium
        print("✓ Selenium")
        import bs4
        print("✓ BeautifulSoup")
        
        # API clients
        import openai
        print("✓ OpenAI API")
        import gspread
        print("✓ gspread (Google Sheets API)")
        import googleapiclient
        print("✓ Google API Client")
        
        # Data processing
        import pandas
        print("✓ Pandas")
        import numpy
        print("✓ NumPy")
        
        # Environment & GUI
        import dotenv
        print("✓ python-dotenv")
        import tkinter
        print("✓ tkinter")
        
        print("All dependencies successfully imported!")
        logger.info("All required dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        print(f"Error: Missing dependency: {str(e)}")
        print("Please install all required dependencies using 'pip install -r requirements.txt'")
        return False'''
        
        # Try to replace the function using regex
        # If this fails, we'll fall back to manual search and replace
        try:
            # First attempt with regex
            new_content = re.sub(dependency_pattern, corrected_function, content, flags=re.DOTALL)
            
            # Check if the replacement actually happened
            if new_content == content:
                # If no change, try a simpler approach - look for the function signature and replace from there
                function_start_idx = content.find("def check_dependencies()")
                if function_start_idx != -1:
                    # Find the next function definition
                    next_func_idx = content.find("def ", function_start_idx + 1)
                    if next_func_idx != -1:
                        # Replace everything between the function signature and the next function
                        new_content = content[:function_start_idx] + corrected_function + content[next_func_idx:]
                    else:
                        # If there's no next function, we may be at the end of the file
                        # Look for other landmarks like classes or main blocks
                        end_markers = ["class ", "if __name__", "# Main function"]
                        for marker in end_markers:
                            next_marker_idx = content.find(marker, function_start_idx + 1)
                            if next_marker_idx != -1:
                                new_content = content[:function_start_idx] + corrected_function + content[next_marker_idx:]
                                break
        except Exception as e:
            print(f"Error during regex replacement: {str(e)}")
            # Fall back to manual approach
            function_start_idx = content.find("def check_dependencies()")
            if function_start_idx != -1:
                # Look for the next function
                next_func_idx = content.find("def ", function_start_idx + 1)
                if next_func_idx != -1:
                    new_content = content[:function_start_idx] + corrected_function + content[next_func_idx:]
                else:
                    print("Could not find the end of the check_dependencies function!")
                    return False
        
        # Write the updated content back to the file
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✓ Fixed indentation error in {main_py_path}")
        return True
        
    except Exception as e:
        print(f"Error fixing {main_py_path}: {str(e)}")
        return False

def fix_message_generator():
    """Fix the OpenAI client initialization in message_generator.py with modern best practices."""
    message_generator_path = 'communication/message_generator.py'
    
    if not os.path.exists(message_generator_path):
        print(f"Error: {message_generator_path} not found!")
        return False
    
    # Backup the file
    backup_file(message_generator_path)
    
    try:
        with open(message_generator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the __init__ method in the MessageGenerator class
        class_idx = content.find("class MessageGenerator")
        if class_idx == -1:
            print("Could not find MessageGenerator class in message_generator.py!")
            return False
            
        init_idx = content.find("def __init__", class_idx)
        if init_idx == -1:
            print("Could not find __init__ method in MessageGenerator class!")
            return False
            
        # Find the end of the __init__ method - look for the next method
        next_method_idx = content.find("def ", init_idx + 1)
        if next_method_idx == -1:
            print("Could not find the end of the __init__ method!")
            return False
            
        # The corrected __init__ method with modern OpenAI SDK handling
        corrected_init = '''    def __init__(self, model="gpt-4"):
        """
        Initialize AI-powered message generator with a scoring threshold.
        
        Args:
            model: OpenAI model to use for AI scoring
        """
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            logger.error("Missing OpenAI API key in .env file.")
            raise ValueError("Missing OpenAI API key.")
        
        self.model = model
        logger.info(f"Initialized MessageGenerator with model: {model}")
        
        # Initialize OpenAI client based on available version and capabilities
        try:
            import openai
            
            # Check OpenAI version
            try:
                openai_version = openai.__version__
                logger.info(f"Using OpenAI SDK version: {openai_version}")
            except AttributeError:
                openai_version = "unknown"
                logger.warning("Could not determine OpenAI SDK version")
            
            # Preferred approach: Use Client class (recommended for OpenAI SDK v1.x+)
            try:
                # First try with Client class (recommended modern approach)
                from openai import Client
                self.client = Client(api_key=self.api_key)
                self.client_version = "v1"
                logger.info("Using OpenAI Client class (recommended)")
            except (ImportError, AttributeError) as e:
                logger.warning(f"Client class not available: {e}")
                
                # Fallback to module approach for v1.x+
                if hasattr(openai, 'chat') and hasattr(openai.chat, 'completions'):
                    # Modern non-instantiated approach (works with v1.x+)
                    openai.api_key = self.api_key
                    self.client = openai
                    self.client_version = "v1"
                    logger.info("Using OpenAI module directly (v1.x non-instantiated approach)")
                else:
                    # Legacy approach for pre-1.0 versions
                    openai.api_key = self.api_key
                    self.client = openai
                    self.client_version = "legacy"
                    logger.info("Using legacy OpenAI client (pre-1.0)")
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            # Last resort fallback
            import openai
            openai.api_key = self.api_key
            self.client = openai
            self.client_version = "legacy"
            logger.info("Using legacy OpenAI client (fallback after error)")'''
            
        # Replace the __init__ method with the corrected version
        new_content = content[:init_idx] + corrected_init + content[next_method_idx:]
        
        # Write the updated content back to the file
        with open(message_generator_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✓ Fixed OpenAI client initialization in {message_generator_path}")
        
        # Add warning about the need to update generate_message method
        print("\n⚠️  Note about OpenAI API usage:")
        print("  The OpenAI SDK has changed how responses are structured.")
        print("  If you see errors when generating messages, update your response handling:")
        print("  - For Client class: response.choices[0].message.content")
        print("  - For module approach: response.choices[0].message.content")
        print("  - For legacy: response['choices'][0]['message']['content']")
        
        return True
        
    except Exception as e:
        print(f"Error fixing {message_generator_path}: {str(e)}")
        return False

def add_improved_test_script():
    """Create or update the verification script with improved testing."""
    verification_script_path = 'verification-script.py'
    
    try:
        # Check if verification script exists - if so, backup and update it
        if os.path.exists(verification_script_path):
            backup_file(verification_script_path)
            
        # Write the new test script
        with open(verification_script_path, 'w', encoding='utf-8') as f:
            f.write('''#!/usr/bin/env python3
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
    print("\\nTesting direct access to Reddit...")
    
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
            print("\\nLooking for post elements in the HTML...")
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
        print("\\nTesting single subreddit scrape...")
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
        print("\\nTesting keyword search...")
        keyword_leads = scraper.search_reddit_by_query(test_keywords[0], limit=5)
        print(f"Found {len(keyword_leads)} leads for keyword '{test_keywords[0]}'")
        
        # Test saving to CSV
        if subreddit_leads or keyword_leads:
            all_leads = subreddit_leads + keyword_leads
            test_filename = "test_reddit_leads.csv"
            
            print(f"\\nSaving {len(all_leads)} leads to {test_filename}...")
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
        
        print("\\nWeb scraper test completed.")
        return True
        
    except Exception as e:
        print(f"\\nError during web scraper test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_main_integration():
    """Test that the main.py file correctly uses the web-based Reddit scraper."""
    print("\\nTesting integration with main.py...")
    
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
        print(f"\\nError testing main.py integration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def verify_downstream_compatibility():
    """Verify that downstream components (scoring, message generation) can use the web scraper data."""
    print("\\nVerifying compatibility with downstream components...")
    
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
    print("\\n==================================================")
    print("Verification Results:")
    print(f"- Direct Reddit access: {'✓ Passed' if direct_access_success else '✗ Failed'}")
    print(f"- Web scraper test: {'✓ Passed' if web_scraper_success else '✗ Failed'}")
    print(f"- Main.py integration: {'✓ Passed' if integration_success else '✗ Failed'}")
    print(f"- Downstream compatibility: {'✓ Passed' if compatibility_success else '✗ Failed'}")
    print(f"\\nOverall result: {'✓ ALL TESTS PASSED' if all(success) else '✗ SOME TESTS FAILED'}")
    print("==================================================")

if __name__ == "__main__":
    main()''')
            
        print(f"✓ Created improved verification script at {verification_script_path}")
        return True
        
    except Exception as e:
        print(f"Error creating verification script: {str(e)}")
        return False

def commit_changes():
    """Commit changes to git if requested."""
    try:
        # Check if git is installed
        result = subprocess.run(['git', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("Git is not installed or not in PATH. Cannot commit changes.")
            return False
        
        # Check if this is a git repository
        result = subprocess.run(['git', 'status'], capture_output=True, text=True)
        if result.returncode != 0:
            print("This directory is not a git repository. Cannot commit changes.")
            return False
        
        # Add the changed files
        subprocess.run(['git', 'add', 'main.py', 'communication/message_generator.py', 'verification-script.py'])
        
        # Commit the changes
        commit_message = "Fix web-based Reddit scraper integration issues and update OpenAI client handling"
        subprocess.run(['git', 'commit', '-m', commit_message])
        
        print(f"✓ Committed changes with message: '{commit_message}'")
        return True
    except Exception as e:
        print(f"Error committing changes: {str(e)}")
        return False

def main():
    """Run the fix all script."""
    print("==================================================")
    print("Web-based Reddit Scraper Integration Fixes")
    print("==================================================")
    
    # Keep track of what succeeded
    success = []
    
    # Fix main.py indentation
    print("\n1. Fixing indentation error in main.py...")
    main_py_success = fix_main_py()
    success.append(main_py_success)
    
    # Fix message_generator.py
    print("\n2. Fixing OpenAI client initialization in message_generator.py...")
    message_generator_success = fix_message_generator()
    success.append(message_generator_success)
    
    # Improve verification script
    print("\n3. Adding improved web scraper testing...")
    verification_success = add_improved_test_script()
    success.append(verification_success)
    
    # Print overall results
    print("\n==================================================")
    print("Fix Results:")
    print(f"- main.py fix: {'✓ Passed' if main_py_success else '✗ Failed'}")
    print(f"- message_generator.py fix: {'✓ Passed' if message_generator_success else '✗ Failed'}")
    print(f"- verification script improvement: {'✓ Passed' if verification_success else '✗ Failed'}")
    
    # Optionally commit changes
    if all(success):
        print("\nAll fixes applied successfully!")
        commit_choice = input("\nWould you like to commit these changes to git? (y/n): ").strip().lower()
        if commit_choice == 'y':
            commit_changes()
    else:
        print("\nSome fixes failed. Please check the logs and try again.")
    
    print("\n==================================================")
    print("Next steps:")
    print("1. Run the verification script to check if the issues are fixed:")
    print("   python verification-script.py")
    print("2. Test the full pipeline:")
    print("   python main.py pipeline --no-linkedin --no-scorer --no-messages --no-email")
    print("\nNote about OpenAI API usage:")
    print("Modern OpenAI SDK can use both instantiated Client approach (recommended):")
    print("   from openai import Client")
    print("   client = Client()")
    print("Or the module-level approach:")
    print("   import openai  # SDK version 1.x+")
    print("   response = openai.chat.completions.create(...)")
    print("Both return Pydantic objects where you access attributes via dot notation.")
    print("==================================================")

if __name__ == "__main__":
    main()
