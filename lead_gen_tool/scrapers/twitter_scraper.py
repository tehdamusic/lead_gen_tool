import time
import logging
import requests
import gspread
from pymongo import MongoClient
from oauth2client.service_account import ServiceAccountCredentials
import os

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

# Excluded keywords to remove irrelevant tweets
EXCLUDED_KEYWORDS = ["coach", "mentorship", "consulting", "trainer", "success", "achieve", "business coaching", "grow your brand", "scale your business", "free webinar", "DM me for help", "follow me for tips"]

# Function to scrape tweets via SerpAPI (Google Search)
def scrape_serpapi_for_tweets(max_tweets=50):
    logging.debug("Starting SerpAPI Google Search for Tweets")
    sheet = connect_to_google_sheets()
    if not sheet:
        logging.error("❌ Cannot proceed with Twitter scraping. Google Sheets connection failed.")
        return []

    tweets_collected = []
    total_count = 0

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
            tweet_text = result.get("title", "").lower()
            
            if "twitter.com" in tweet_url and "/status/" in tweet_url:
                if any(keyword in tweet_text for keyword in EXCLUDED_KEYWORDS):
                    logging.info(f"⏩ Skipping irrelevant tweet: {tweet_text}")
                    continue
                
                lead = {"platform": "twitter", "url": tweet_url, "text": tweet_text}
                
                if not leads_collection.find_one({"url": tweet_url}):
                    leads_collection.insert_one(lead)
                    sheet.append_row([tweet_url, tweet_text])
                    tweets_collected.append(lead)
                    total_count += 1
                    logging.info(f"✅ Saved Tweet: {tweet_url}")
                
                if total_count >= max_tweets:
                    break
            
        time.sleep(5)  # Delay to prevent hitting SerpAPI limits
    
    logging.info(f"✅ Scraped {total_count} relevant tweets via SerpAPI.")
    return tweets_collected

if __name__ == "__main__":
    logging.info("🚀 Starting Twitter Lead Generation Scraper (SerpAPI Method)")
    scrape_serpapi_for_tweets(max_tweets=50)
    logging.info("✅ Twitter Scraper Completed")
