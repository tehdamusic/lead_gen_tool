import os
import sys
import re
from dotenv import load_dotenv

# Define the paths
script_dir = os.path.dirname(os.path.abspath(__file__))
reddit_scraper_path = os.path.join(script_dir, 'scrapers', 'reddit', 'scraper.py')
backup_path = reddit_scraper_path + '.backup'

# Create a backup
def create_backup():
    if os.path.exists(reddit_scraper_path):
        with open(reddit_scraper_path, 'r') as src:
            with open(backup_path, 'w') as dest:
                dest.write(src.read())
        print(f"Created backup at {backup_path}")
    else:
        print(f"Error: {reddit_scraper_path} not found!")
        sys.exit(1)

# Fix the Reddit scraper
def fix_reddit_scraper():
    # Create backup first
    create_backup()
    
    # Read the file
    with open(reddit_scraper_path, 'r') as file:
        content = file.read()
    
    # Fix 1: Update the _init_reddit_client method to include better error handling 
    # and a more detailed user agent
    init_client_pattern = r'def _init_reddit_client\(self\)(.*?)try:(.*?)self\.reddit = praw\.Reddit\((.*?)\)(.*?)except Exception as e:'
    init_client_replacement = r'''def _init_reddit_client(self) -> None:
        """Initialize the Reddit API client using credentials from environment variables."""
        try:
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')
            
            # Create a more detailed user agent
            user_agent = f"python:com.peaktransformation.leadgen:v1.0.0 (by /u/{username})"
            
            if not all([client_id, client_secret, username, password]):
                raise ValueError("Reddit API credentials missing in environment variables")
            
            # Log the authentication attempt with masked credentials
            logger.info(f"Attempting to connect to Reddit API with client_id={client_id[:4]}***, username={username}")
            
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                username=username,
                password=password,
                user_agent=user_agent
            )
            
            # Test connection with a simple API call
            me = self.reddit.user.me()
            if me:
                logger.info(f"Successfully connected to Reddit API as user: {me.name}")
            else:
                logger.warning("Connected to Reddit API but couldn't verify user identity")
                
        except Exception as e:'''
    
    content = re.sub(init_client_pattern, init_client_replacement, content, flags=re.DOTALL)
    
    # Fix 2: Add retry logic for API calls
    scrape_subreddit_pattern = r'def scrape_subreddit\(self, subreddit_name: str\)(.*?)try:(.*?)subreddit = self\.reddit\.subreddit\(subreddit_name\)(.*?)except Exception as e:'
    scrape_subreddit_replacement = r'''def scrape_subreddit(self, subreddit_name: str) -> List[Dict[str, Any]]:
        """
        Scrape a specific subreddit for relevant posts.
        
        Args:
            subreddit_name: Name of the subreddit to scrape
            
        Returns:
            List of dictionaries containing post data
        """
        leads = []
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Scraping subreddit: r/{subreddit_name} (attempt {retry_count+1})")
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Add a small delay to prevent rate limiting
                time.sleep(1)
                
                # Get recent posts
                for submission in subreddit.top(time_filter=self.time_filter, limit=self.post_limit):
                    try:
                        # Combine title and body for keyword matching
                        full_text = f"{submission.title} {submission.selftext if hasattr(submission, 'selftext') else ''}"
                        matched_keywords = self.keyword_match(full_text)
                        
                        # Only keep posts that match our keywords
                        if matched_keywords:
                            # Extract post data safely with default values
                            post_data = {
                                "username": submission.author.name if submission.author else "[deleted]",
                                "post_title": submission.title,
                                "post_content": (submission.selftext[:5000] if hasattr(submission, 'selftext') else ""),
                                "subreddit": subreddit_name,
                                "post_url": f"https://www.reddit.com{submission.permalink}",
                                "matched_keywords": ", ".join(matched_keywords),
                                "score": submission.score if hasattr(submission, 'score') else 0,
                                "comment_count": submission.num_comments if hasattr(submission, 'num_comments') else 0,
                                "created_utc": datetime.fromtimestamp(submission.created_utc).strftime("%Y-%m-%d %H:%M:%S") if hasattr(submission, 'created_utc') else "",
                                "date_added": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            
                            leads.append(post_data)
                            logger.debug(f"Found relevant post by u/{post_data['username']} in r/{subreddit_name}")
                            
                    except Exception as e:
                        logger.warning(f"Error processing post in r/{subreddit_name}: {str(e)}")
                        continue
                
                # If we get here without exception, break the retry loop
                break
                
            except Exception as e:
                error_message = str(e)
                retry_count += 1
                
                # Log the error details
                if "401" in error_message:
                    logger.error(f"Authentication error (401) scraping r/{subreddit_name}: {error_message}")
                    if retry_count >= max_retries:
                        # Check if credentials look valid
                        self._validate_credentials()
                elif "429" in error_message:
                    logger.error(f"Rate limit exceeded (429) scraping r/{subreddit_name}: {error_message}")
                    # Wait longer on rate limit errors
                    time.sleep(10)
                else:
                    logger.error(f"Error attempt {retry_count} scraping subreddit r/{subreddit_name}: {error_message}")
                    time.sleep(2)
                
                # If we've exceeded our retries, give up on this subreddit
                if retry_count >= max_retries:
                    logger.error(f"Giving up on r/{subreddit_name} after {max_retries} failed attempts")
                    break
        
        logger.info(f"Found {len(leads)} relevant posts in r/{subreddit_name}")
        return leads'''
    
    content = re.sub(scrape_subreddit_pattern, scrape_subreddit_replacement, content, flags=re.DOTALL)
    
    # Fix 3: Add missing imports
    import_pattern = r'from dotenv import load_dotenv'
    import_replacement = r'from dotenv import load_dotenv\nimport time\nimport requests'
    content = re.sub(import_pattern, import_replacement, content)
    
    # Fix 4: Add a credential validation method
    class_def_pattern = r'class RedditScraper:(.*?)def __init__'
    class_def_replacement = r'''class RedditScraper:
    """
    A modular scraper for collecting lead data from Reddit
    based on subreddits and keywords related to stress and burnout.
    """
    
    def _validate_credentials(self):
        """Validate the Reddit API credentials by making a simple direct request."""
        try:
            # Get credentials
            client_id = os.getenv('REDDIT_CLIENT_ID')
            client_secret = os.getenv('REDDIT_CLIENT_SECRET')
            username = os.getenv('REDDIT_USERNAME')
            password = os.getenv('REDDIT_PASSWORD')
            
            if not all([client_id, client_secret, username, password]):
                logger.error("Missing Reddit API credentials in .env file")
                return False
                
            logger.info("Validating Reddit credentials with direct API request...")
            
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
                logger.info("Credentials are valid - received valid token response from Reddit API")
                return True
            else:
                logger.error(f"Credential validation failed: Status {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error validating credentials: {str(e)}")
            return False
    
    def __init__'''
    
    content = re.sub(class_def_pattern, class_def_replacement, content, flags=re.DOTALL)
    
    # Write the updated content
    with open(reddit_scraper_path, 'w') as file:
        file.write(content)
    
    print(f"Fixed Reddit scraper at {reddit_scraper_path}")
    
    # Create a .env file fix helper
    env_path = os.path.join(script_dir, '.env')
    if os.path.exists(env_path):
        print("\nHere's a template for your .env file Reddit credentials:")
        print("""
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password
""")
    else:
        print("\nWarning: .env file not found in the current directory.")

if __name__ == "__main__":
    fix_reddit_scraper()
    print("\nCompleted Reddit scraper fixes!")
    print("\nNext steps:")
    print("1. Verify your Reddit API credentials in the .env file")
    print("2. Make sure your Reddit account has verified email")
    print("3. Check that you've created a Reddit app at https://www.reddit.com/prefs/apps/")
    print("4. Run the script again to test the connection")