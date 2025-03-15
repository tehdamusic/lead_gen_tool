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
import openai

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

# OpenAI API Key - Load from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# Coach/Competitor Exclusion Keywords (expanded list)
COACH_EXCLUSION_KEYWORDS = [
    "coach", "mentor", "consultant", "advisor", "trainer", "counselor", "therapist",
    "life coach", "business coach", "career coach", "executive coach", "personal coach",
    "leadership coach", "wellness coach", "mindset coach", "transformation coach",
    "performance coach", "success coach", "professional mentor", "life mentor",
    "business consultant", "lifestyle consultant", "career counselor", 
    "personal development", "self-help", "motivational speaker", "business advisor",
    "career strategist", "wellness consultant", "life strategist", "success strategist",
    "empowerment specialist", "transformation specialist", "mindfulness teacher",
    "DM for coaching", "coaching services", "book a session", "free consultation",
    "click link in bio", "link in bio", "sign up now", "register now", "transform your life",
    "take your life to the next level", "unlock your potential", "growth mindset guru",
    "webinar", "workshop", "masterclass", "course enrollment", "coaching program"
]

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

def is_coach_competitor(username="", bio="", comment_text=""):
    """
    AI-powered check to determine if a commenter is a coach/competitor
    Uses both keyword matching and AI analysis
    """
    # Basic keyword exclusion check
    combined_text = f"{username} {bio} {comment_text}".lower()
    if any(excluded.lower() in combined_text for excluded in COACH_EXCLUSION_KEYWORDS):
        return True, "Excluded keyword found via keyword matching"
    
    # Check for typical promotional patterns in comments
    promo_patterns = [
        "dm me", "message me", "check out my", "follow me", "visit my profile", 
        "link in bio", "book a call", "free session", "free consultation"
    ]
    
    if any(pattern in comment_text.lower() for pattern in promo_patterns):
        return True, "Promotional language detected"
    
    # Use AI for more sophisticated detection when possible
    try:
        # Combine available information for AI analysis
        profile_info = f"Username: {username}\nBio: {bio}\nComment: {comment_text}"
        
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": """Analyze if this person is likely to be a personal coach, 
                 life coach, career coach, mentor, consultant, or similar competitor in the personal/professional 
                 development space. They might be promoting services or attempting to attract clients.
                 Return 'Yes' if they appear to be a coach/competitor, or 'No' otherwise."""},
                {"role": "user", "content": profile_info}
            ],
            max_tokens=50
        )
        
        ai_decision = response.choices[0].message.content.strip().lower()
        
        if "yes" in ai_decision:
            return True, "AI detected profile as coach/competitor"
            
    except Exception as e:
        logging.warning(f"⚠️ AI filtering error: {e}. Falling back to keyword matching only.")
    
    return False, "Not detected as coach/competitor"

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
                    comment_elements = driver.find_elements(By.CSS_SELECTOR, "div._a9zr")
                    
                    for comment_element in comment_elements:
                        try:
                            # Extract username, comment text and get bio when possible
                            username_element = comment_element.find_element(By.CSS_SELECTOR, "._a9zc")
                            username = username_element.text.strip() if username_element else "Unknown"
                            
                            comment_text_element = comment_element.find_element(By.CSS_SELECTOR, "div.xt0psk2 span")
                            comment_text = comment_text_element.text.strip() if comment_text_element else ""
                            
                            # Try to get bio from profile hover if possible - simplified for this example
                            bio = ""  # In a real implementation, you might navigate to profile or use API
                            
                            logging.info(f"🔎 Found comment by {username}: {comment_text}")

                            # Check if comment matches our target keywords
                            if any(keyword in comment_text.lower() for keyword in KEYWORDS):
                                # Check if commenter is a coach/competitor
                                is_competitor, reason = is_coach_competitor(username, bio, comment_text)
                                
                                if is_competitor:
                                    logging.info(f"⏩ Skipping comment from {username} ({reason})")
                                    continue
                                
                                lead = {
                                    "platform": "instagram", 
                                    "url": post_url, 
                                    "username": username,
                                    "comment": comment_text
                                }

                                # Check for duplicates by username and comment text to avoid duplication
                                if not leads_collection.find_one({"username": username, "comment": comment_text}):
                                    leads_collection.insert_one(lead)
                                    sheet.append_row([post_url, username, comment_text])
                                    comments_collected.append(lead)
                                    comment_count += 1
                                    logging.info(f"✅ Added lead from Instagram: {username}")

                            if comment_count >= max_comments:
                                break
                                
                        except Exception as e:
                            logging.warning(f"⚠️ Error processing comment: {e}")
                            continue

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