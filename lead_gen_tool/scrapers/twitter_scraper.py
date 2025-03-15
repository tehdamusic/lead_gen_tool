import time
import logging
import requests
import gspread
from pymongo import MongoClient
from oauth2client.service_account import ServiceAccountCredentials
import os
import re
from typing import List, Dict, Any, Optional

# Configure Advanced Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Setup
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["lead_generator"]
leads_collection = db["leads"]

# Define Explicit Path for Google Sheets Credentials
GOOGLE_SHEETS_CREDENTIALS = r"D:\SCRIPTS\lead_gen_tool\config\google_sheets_credentials.json"
SHEET_NAME = "Peak Transformation Coaching Leads"

def connect_to_google_sheets():
    if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS):
        logging.error(f"❌ Missing credentials file: {GOOGLE_SHEETS_CREDENTIALS}. Twitter scraper cannot proceed.")
        return None

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(
            GOOGLE_SHEETS_CREDENTIALS, 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        )
        client = gspread.authorize(creds)
        logging.info("✅ Connected to Google Sheets.")
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        logging.error(f"⚠️ Error connecting to Google Sheets: {e}")
        return None

# SerpAPI Key
SERPAPI_KEY = "d521a421519113d62eaa50f4cb016f6719d399b535850beadeded6b79eca6363"

# Optimized Twitter Search Queries (Google Scraper)
SEARCH_QUERIES = [
    "site:twitter.com \"I hate my job\"",
    "site:twitter.com \"I feel stuck in my career\"",
    "site:twitter.com \"Should I quit my job?\"",
    "site:twitter.com \"I'm struggling at work\"",
    "site:twitter.com \"Career anxiety\""
]

# Enhanced exclusion keywords to filter out competitors and coaches
COMPETITOR_KEYWORDS = [
    # Personal coaching terms
    "coach", "coaching", "mentor", "mentoring", "consultant", "consulting",
    "trainer", "advisor", "strategist", "counselor", "therapist",
    
    # Specific coaching types
    "life coach", "career coach", "business coach", "personal coach", 
    "executive coach", "leadership coach", "mindset coach", "transformation coach",
    "wellness coach", "health coach", "success coach", "performance coach",
    
    # Marketing phrases used by coaches
    "grow your", "scale your", "transform your", "unlock your potential",
    "achieve your goals", "overcome obstacles", "mindfulness practice",
    "self-improvement", "personal growth", "life changing", "breakthrough",
    
    # Call-to-action phrases
    "free webinar", "free consultation", "book a call", "schedule a session",
    "DM me for", "link in bio", "join my", "follow for more tips", 
    "click the link", "sign up now", "limited spots", "exclusive offer"
]

def is_competitor_content(text: str) -> bool:
    """
    AI-powered function to determine if the content is from a competitor.
    Uses pattern matching and keyword detection to identify coaching-related content.
    
    Args:
        text: The text to analyze
        
    Returns:
        bool: True if the content appears to be from a competitor, False otherwise
    """
    text = text.lower()
    
    # Quick check for common coaching phrases
    for keyword in COMPETITOR_KEYWORDS:
        if keyword in text:
            return True
    
    # Check for coach in bio patterns
    coach_patterns = [
        r"(^|\s)coach(\s|$|ing|ed|es)",
        r"(^|\s)mentor(\s|$|ing|ed|s)",
        r"(career|life|business|executive)\s+(coach|mentor|consultant)",
        r"helping (people|professionals|individuals|clients) (to )?(\w+ ){1,3}(goals|dreams|potential)",
        r"transform(ing|ative)? (your|lives)",
        r"I help \w+ (to )?(\w+ )+",  # "I help professionals to achieve their goals" pattern
    ]
    
    for pattern in coach_patterns:
        if re.search(pattern, text):
            return True
    
    # Check bios that contain both offering + transformation words
    offering_terms = ["offer", "provide", "help", "guide", "teach", "support", "coach", "mentor"]
    transformation_terms = ["transform", "improve", "change", "develop", "grow", "achieve", "succeed"]
    
    if any(term in text for term in offering_terms) and any(term in text for term in transformation_terms):
        # Look for personal development context
        personal_dev_terms = ["life", "career", "personal", "professional", "mindset", "growth", "journey"]
        if any(term in text for term in personal_dev_terms):
            return True
    
    return False

def scrape_serpapi_for_tweets(max_tweets: int = 50) -> List[Dict[str, Any]]:
    """
    Scrape tweets via SerpAPI (Google Search) and filter out competitor content.
    
    Args:
        max_tweets: Maximum number of tweets to collect
        
    Returns:
        List of collected tweet data
    """
    logging.debug("Starting SerpAPI Google Search for Tweets with Competitor Filtering")
    sheet = connect_to_google_sheets()
    if not sheet:
        logging.error("❌ Cannot proceed with Twitter scraping. Google Sheets connection failed.")
        return []

    tweets_collected = []
    total_count = 0
    filtered_count = 0

    for query in SEARCH_QUERIES:
        if total_count >= max_tweets:
            break
        
        logging.info(f"🔍 Searching Google for tweets via SerpAPI: {query}")
        search_url = "https://serpapi.com/search"
        params = {"engine": "google", "q": query, "api_key": SERPAPI_KEY, "num": 20}
        
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"❌ SerpAPI request failed: {e}")
            continue
        
        results = response.json().get("organic_results", [])
        logging.debug(f"SerpAPI returned {len(results)} results for {query}")
        
        for result in results:
            tweet_url = result.get("link")
            tweet_text = result.get("title", "")
            tweet_snippet = result.get("snippet", "")
            
            # Combine title and snippet for better context
            full_content = f"{tweet_text} {tweet_snippet}"
            
            if "twitter.com" in tweet_url and "/status/" in tweet_url:
                # Apply AI-powered competitor filtering
                if is_competitor_content(full_content):
                    logging.info(f"🚫 Filtered competitor content: {tweet_text[:50]}...")
                    filtered_count += 1
                    continue
                
                lead = {
                    "platform": "twitter", 
                    "url": tweet_url, 
                    "text": tweet_text,
                    "content": full_content,
                    "filtered_date": time.strftime("%Y-%m-%d")
                }
                
                if not leads_collection.find_one({"url": tweet_url}):
                    leads_collection.insert_one(lead)
                    sheet.append_row([tweet_url, tweet_text])
                    tweets_collected.append(lead)
                    total_count += 1
                    logging.info(f"✅ Saved Tweet: {tweet_url}")
                
                if total_count >= max_tweets:
                    break
            
        time.sleep(5)  # Delay to prevent hitting SerpAPI limits
    
    logging.info(f"✅ Scraped {total_count} relevant tweets via SerpAPI. Filtered out {filtered_count} competitor tweets.")
    return tweets_collected

def analyze_profile_bio(profile_url: str) -> Optional[str]:
    """
    Fetch and analyze Twitter profile bio to determine if it's a competitor.
    This uses the Twitter API if available, otherwise attempts to extract from Google snippets.
    
    Args:
        profile_url: Twitter profile URL
        
    Returns:
        Optional[str]: Bio text if found, None otherwise
    """
    # Extract username from URL
    username_match = re.search(r'twitter\.com/([^/]+)', profile_url)
    if not username_match:
        return None
    
    username = username_match.group(1)
    
    # Try to get profile bio via Google search
    search_url = "https://serpapi.com/search"
    params = {"engine": "google", "q": f"site:twitter.com {username} bio", "api_key": SERPAPI_KEY}
    
    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        results = response.json().get("organic_results", [])
        
        if results:
            # Look for bio in the snippet
            snippet = results[0].get("snippet", "")
            return snippet
            
    except Exception as e:
        logging.warning(f"⚠️ Error fetching profile bio for {username}: {e}")
    
    return None

if __name__ == "__main__":
    logging.info("🚀 Starting Twitter Lead Generation Scraper with AI-powered Competitor Filtering")
    scrape_serpapi_for_tweets(max_tweets=50)
    logging.info("✅ Twitter Scraper Completed")