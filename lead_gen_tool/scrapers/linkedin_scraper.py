import time
import logging
import random
import requests
import os
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure Advanced Logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Setup
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["lead_generator"]
leads_collection = db["leads"]

# Google Sheets Setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # Get current script directory
GOOGLE_SHEETS_CREDENTIALS = os.path.join(BASE_DIR, "../config/google_sheets_credentials.json")
SHEET_NAME = "Peak Transformation Coaching Leads"

def connect_to_google_sheets():
    """Connect to Google Sheets and return the active sheet."""
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, 
            ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"])
        client = gspread.authorize(creds)
        return client.open(SHEET_NAME).sheet1
    except Exception as e:
        logging.error(f"❌ Failed to connect to Google Sheets: {e}")
        return None

# SerpAPI Key
SERPAPI_KEY = "d521a421519113d62eaa50f4cb016f6719d399b535850beadeded6b79eca6363"

# Search terms targeting people discussing burnout or career struggles
SEARCH_TERMS = [
    "burnout site:linkedin.com/in/",
    "career change site:linkedin.com/in/",
    "stressed at work site:linkedin.com/in/",
    "overwhelmed at job site:linkedin.com/in/",
    "feeling stuck career site:linkedin.com/in/"
]

# Job titles to exclude (Coaches, Consultants, Mentors, etc.)
EXCLUDED_TITLES = ["coach", "consultant", "mentor", "trainer", "advisor", "strategist", "speaker"]

def scrape_google_for_linkedin_profiles(max_profiles=50):
    """Scrape Google for LinkedIn profiles related to career struggles."""
    logging.debug("Starting Google Search for LinkedIn Profiles")
    leads = []
    sheet = connect_to_google_sheets()

    if not sheet:
        logging.error("❌ Google Sheets connection failed. Skipping LinkedIn scraping.")
        return []

    for term in SEARCH_TERMS:
        search_url = "https://serpapi.com/search"
        params = {"engine": "google", "q": term, "api_key": SERPAPI_KEY, "timeout": 10}
        
        try:
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            results = response.json().get("organic_results", [])
        except requests.RequestException as e:
            logging.error(f"❌ SerpAPI request failed for {term}: {e}")
            continue

        logging.debug(f"Google Search found {len(results)} results for {term}")
        
        for result in results:
            profile_url = result.get("link", "")
            name = result.get("title", "").split("-")[0].strip()
            job_title = result.get("title", "").split("-")[-1].strip().lower()

            if "linkedin.com/in/" in profile_url:
                if any(excluded in job_title for excluded in EXCLUDED_TITLES):
                    logging.info(f"⏩ Skipping {name} - {job_title} (Excluded Title)")
                    continue
                
                lead = {"name": name, "job_title": job_title, "platform": "linkedin", "url": profile_url}

                if not leads_collection.find_one({"url": profile_url}):
                    leads_collection.insert_one(lead)
                    sheet.append_row([name, job_title, profile_url])
                    leads.append(lead)
                    logging.info(f"🔎 Added LinkedIn Profile: {name} - {job_title} - {profile_url}")

                if len(leads) >= max_profiles:
                    return leads
            time.sleep(random.uniform(3, 6))

    return leads

def scrape_linkedin_posts():
    """Scrape LinkedIn posts related to career struggles."""
    logging.debug("Starting LinkedIn Post Scraper")
    options = uc.ChromeOptions()
    driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.linkedin.com/feed/")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)

        if "login" in driver.current_url:
            logging.error("❌ LinkedIn requires login. Please log in manually.")
            driver.quit()
            return

        posts = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.feed-shared-update-v2")))
        logging.info(f"✅ Found {len(posts)} posts on LinkedIn Feed")

        sheet = connect_to_google_sheets()
        if not sheet:
            logging.error("❌ Google Sheets connection failed. Skipping post scraping.")
            return

        for post in posts[:10]:
            try:
                post_text = post.text[:500]  # Extract preview of post text
                post_url_element = post.find_element(By.TAG_NAME, "a")
                post_url = post_url_element.get_attribute("href") if post_url_element else ""

                if any(keyword in post_text.lower() for keyword in ["burnout", "career change", "stressed", "overwhelmed", "feeling stuck"]):
                    if "coach" in post_text.lower():
                        logging.info(f"⏩ Skipping post about coaching: {post_url}")
                        continue

                    lead = {"platform": "linkedin", "url": post_url, "post_text": post_text}

                    if not leads_collection.find_one({"url": post_url}):
                        leads_collection.insert_one(lead)
                        sheet.append_row([post_url, post_text])
                        logging.info(f"🔎 Saved LinkedIn Post: {post_url}")

            except Exception as e:
                logging.warning(f"⚠️ Error processing post: {e}")
                continue  

    finally:
        driver.quit()

if __name__ == "__main__":
    logging.info("🚀 Starting LinkedIn Lead Generation Scraper")
    scrape_google_for_linkedin_profiles(max_profiles=50)
    scrape_linkedin_posts()
    logging.info("✅ LinkedIn Scraper Completed")
