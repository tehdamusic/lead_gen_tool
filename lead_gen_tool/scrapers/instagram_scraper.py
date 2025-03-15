import time
import json
import logging
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from pymongo import MongoClient
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# MongoDB Setup
MONGO_URI = "mongodb://localhost:27017/"
client = MongoClient(MONGO_URI)
db = client["lead_generator"]
leads_collection = db["leads"]

# Define Explicit Paths
GOOGLE_SHEETS_CREDENTIALS = r"D:\SCRIPTS\lead_gen_tool\config\google_sheets_credentials.json"
COOKIES_FILE = r"D:\SCRIPTS\lead_gen_tool\scrapers\instagram_cookies.json"
SHEET_NAME = "Peak Transformation Coaching Leads"

def connect_to_google_sheets():
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        GOOGLE_SHEETS_CREDENTIALS, 
        ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    )
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).sheet1

# Load Instagram Cookies
def load_cookies(driver, cookies_file=COOKIES_FILE):
    if not os.path.exists(cookies_file):
        logging.error(f"❌ Missing cookies file: {cookies_file}. Instagram scraper cannot proceed.")
        return False

    try:
        with open(cookies_file, "r") as f:
            cookies = json.load(f)
        for cookie in cookies:
            driver.add_cookie(cookie)
        logging.info("✅ Instagram cookies loaded successfully.")
        return True
    except Exception as e:
        logging.error(f"⚠️ Error loading cookies: {e}")
        return False

# Expanded list of influencers to target for comments
INFLUENCER_PROFILES = [
    "tonyrobbins", "garyvee", "robinsharma", "simon_sinek", "jay_shetty",
    "brendonburchard", "grantcardone", "lewishowes", "marieforleo", "melrobbins"
]

# Keywords to filter relevant comments
KEYWORDS = ["stuck", "lost", "help", "burnout", "struggling", "overwhelmed"]

# Function to scrape Instagram comments
def scrape_instagram_comments(max_comments=50):
    options = uc.ChromeOptions()
    driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    try:
        driver.get("https://www.instagram.com")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        if not load_cookies(driver):
            logging.error("❌ Instagram login required, but cookies are missing. Exiting.")
            driver.quit()
            return []
        
        driver.refresh()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        if "login" in driver.current_url.lower():
            logging.error("❌ Login failed! Check Instagram cookies.")
            driver.quit()
            return []

        sheet = connect_to_google_sheets()
        comments_collected = []
        comment_count = 0

        for profile in INFLUENCER_PROFILES:
            if comment_count >= max_comments:
                break

            driver.get(f"https://www.instagram.com/{profile}/")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            time.sleep(3)

            # Scroll to the top to ensure the most recent posts are loaded
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)

            # Refresh post list after scrolling to the top
            posts = driver.find_elements(By.CSS_SELECTOR, "a[href*='/p/']")
            post_links = [post.get_attribute("href") for post in posts[:10]]
            logging.info(f"✅ Found {len(post_links)} most recent posts for {profile}")

            for post_url in post_links:
                if comment_count >= max_comments:
                    break

                try:
                    driver.get(post_url)
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    time.sleep(3)

                    # Click "View all comments" if available
                    try:
                        view_all_buttons = driver.find_elements(By.CSS_SELECTOR, "span")
                        for button in view_all_buttons:
                            if "View all" in button.text:
                                button.click()
                                time.sleep(3)
                                break  # Click only once
                    except:
                        pass  # No "View all comments" button found

                    # Extract comments using the new selector
                    comments = driver.find_elements(By.CSS_SELECTOR, "div.xt0psk2 span")

                    for comment in comments:
                        comment_text = comment.text.strip()
                        logging.info(f"🔎 Found comment: {comment_text}")

                        if any(keyword in comment_text.lower() for keyword in KEYWORDS):
                            lead = {"platform": "instagram", "url": post_url, "comment": comment_text}

                            if not leads_collection.find_one({"comment": comment_text}):  # Prevent duplicates across posts
                                leads_collection.insert_one(lead)
                                sheet.append_row([post_url, comment_text])
                                comments_collected.append(lead)
                                comment_count += 1

                        if comment_count >= max_comments:
                            break

                except Exception as e:
                    logging.warning(f"⚠️ Error processing post: {e}")
                    continue  # Skip and move to the next post

        logging.info(f"✅ Scraped {comment_count} relevant Instagram comments.")
        return comments_collected
    
    finally:
        try:
            driver.quit()
        except Exception as e:
            logging.error(f"Error while closing WebDriver: {e}")

if __name__ == "__main__":
    scrape_instagram_comments(max_comments=50)
