"""
LinkedIn scraper for extracting lead data.
"""

import os
import time
import random
import logging
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    WebDriverException, 
    NoSuchElementException, 
    TimeoutException, 
    StaleElementReferenceException
)

from .utils import (
    find_chromedriver, 
    configure_chrome_options, 
    random_sleep, 
    save_profiles_to_csv
)
from .extractors import (
    extract_profiles, 
    extract_additional_info
)
from .selectors import (
    NEXT_BUTTON_SELECTORS, 
    TARGET_INDUSTRIES, 
    TARGET_ROLES, 
    TARGET_KEYWORDS
)

# Ensure directories exist
os.makedirs('logs', exist_ok=True)
os.makedirs('debug', exist_ok=True)
os.makedirs('data', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/linkedin_scraper.log'
)
logger = logging.getLogger('linkedin.scraper')

class LinkedInScraper:
    """Scraper for extracting LinkedIn lead data for life coaching."""

    def __init__(self, headless=False):
        """
        Initialize the LinkedIn scraper with a Selenium WebDriver.
        
        Args:
            headless: Whether to run browser in headless mode
        """
        self.username = os.getenv("LINKEDIN_USERNAME")
        self.password = os.getenv("LINKEDIN_PASSWORD")
        self.driver = None

        if not self.username or not self.password:
            raise ValueError("LinkedIn credentials are missing. Set LINKEDIN_USERNAME and LINKEDIN_PASSWORD in your .env file.")

        # Configure Chrome options
        options = configure_chrome_options(headless=headless)
        
        # Find the ChromeDriver
        try:
            chromedriver_path = find_chromedriver()
            logger.info(f"Using ChromeDriver at: {chromedriver_path}")
        except FileNotFoundError as e:
            logger.error(f"ChromeDriver not found: {str(e)}")
            raise

        # Start WebDriver
        try:
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply stealth mode
            self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                })
                """
            })
            
            logger.info(f"Successfully initialized WebDriver with ChromeDriver at {chromedriver_path}.")
        except WebDriverException as e:
            logger.error(f"WebDriver failed to start: {str(e)}")
            error_msg = str(e)
            if "This version of ChromeDriver only supports Chrome version" in error_msg:
                logger.error("ChromeDriver version mismatch. Please download a compatible version.")
                raise RuntimeError("ChromeDriver version doesn't match your Chrome browser version. Please download a compatible ChromeDriver from https://sites.google.com/chromium.org/driver/")
            raise RuntimeError(f"Failed to start Chrome WebDriver: {str(e)}")

    def _is_logged_in(self):
        """
        Check if the user is logged in to LinkedIn.
        
        Returns:
            True if logged in, False otherwise
        """
        current_url = self.driver.current_url
        return "feed" in current_url or "mynetwork" in current_url or "messaging" in current_url

    def _type_like_human(self, element, text):
        """
        Type text like a human would, with random delays between keystrokes.
        
        Args:
            element: Element to type into
            text: Text to type
        """
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.2))  # Random delay between keystrokes

    def _scroll_down_improved(self, scroll_count=5, wait_time=2):
        """
        Improved scroll down function that actively waits for content to load.
        
        Args:
            scroll_count: Number of scroll actions to perform
            wait_time: Base time to wait between scrolls
                
        Returns:
            Number of scrolls performed
        """
        # Get initial page height
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scrolls_performed = 0
        
        for i in range(scroll_count):
            # Scroll to bottom of page
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scrolls_performed += 1
            
            # Wait for page to load with progressive timing
            time.sleep(wait_time + (i * 0.5))  # Increase wait time for each scroll
            
            # Check if we've reached the bottom
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Try clicking "Show more results" button if it exists
            try:
                show_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, 
                                                      "button.artdeco-button--muted, button.artdeco-button--secondary")
                for btn in show_more_buttons:
                    if "show more" in btn.text.lower() or "see more" in btn.text.lower():
                        self.driver.execute_script("arguments[0].click();", btn)
                        time.sleep(wait_time + 1)  # Extra wait time after clicking button
                        break
            except:
                pass
            
            # One more check in case the button did something
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                # Try interacting with the page to trigger any lazy-loaded content
                try:
                    self.driver.execute_script("""
                        document.dispatchEvent(new MouseEvent('mousemove', {
                            'clientX': 100 + Math.random() * 100,
                            'clientY': 100 + Math.random() * 100
                        }));
                    """)
                    time.sleep(0.5)
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                except:
                    pass
                    
                if new_height == last_height:
                    break
                    
            last_height = new_height
                
        return scrolls_performed

    def handle_authentication_challenges(self):
        """Handle LinkedIn security challenges that might appear during login."""
        current_url = self.driver.current_url
        
        # Check for various challenge screens
        if "checkpoint/challenge" in current_url or "checkpoint/rm" in current_url:
            logger.warning("LinkedIn security check detected - need manual intervention")
            
            # Take a screenshot for debugging
            self.driver.save_screenshot("debug/linkedin_security_check.png")
            
            # Save the current page for analysis
            with open("debug/linkedin_security_check.html", "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
                
            # Look for common challenge elements
            try:
                # Check for CAPTCHA
                captcha_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                                                          "img[alt='CAPTCHA'], .captcha-container")
                if captcha_elements:
                    logger.warning("CAPTCHA challenge detected")
                    print("\n" + "="*50)
                    print("LinkedIn CAPTCHA challenge detected!")
                    print("Please check the browser window and complete the CAPTCHA manually.")
                    print("="*50 + "\n")
                    input("Press Enter after completing the challenge...")
                    return True
                    
                # Check for phone verification
                phone_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                                                        "input[name='phoneNumber'], .phone-verification")
                if phone_elements:
                    logger.warning("Phone verification challenge detected")
                    print("\n" + "="*50)
                    print("LinkedIn phone verification challenge detected!")
                    print("Please check the browser window and complete the verification manually.")
                    print("="*50 + "\n")
                    input("Press Enter after completing the challenge...")
                    return True
                    
                # Check for email verification
                email_elements = self.driver.find_elements(By.CSS_SELECTOR, 
                                                        "input[name='email'], .email-verification")
                if email_elements:
                    logger.warning("Email verification challenge detected")
                    print("\n" + "="*50)
                    print("LinkedIn email verification challenge detected!")
                    print("Please check the browser window and complete the verification manually.")
                    print("="*50 + "\n")
                    input("Press Enter after completing the challenge...")
                    return True
                    
                # Generic challenge handler
                logger.warning("Unknown security challenge detected")
                print("\n" + "="*50)
                print("LinkedIn security challenge detected!")
                print("Please check the browser window and complete it manually.")
                print("="*50 + "\n")
                input("Press Enter after completing the challenge...")
                return True
                
            except Exception as e:
                logger.error(f"Error handling authentication challenge: {str(e)}")
                
        return False

    def login(self):
        """
        Log into LinkedIn and handle possible CAPTCHA.
        
        Returns:
            True if login successful, False otherwise
        """
        logger.info("Logging into LinkedIn...")
        self.driver.get("https://www.linkedin.com/login")
        
        # Allow page to load with a proper wait condition
        try:
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
        except TimeoutException:
            logger.error("Login page did not load properly")
            raise RuntimeError("LinkedIn login page failed to load")

        try:
            # Find and fill the username field
            username_field = self.driver.find_element(By.ID, "username")
            username_field.clear()
            self._type_like_human(username_field, self.username)

            # Find and fill the password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            self._type_like_human(password_field, self.password)

            # Submit the form
            password_field.send_keys(Keys.RETURN)
            
            # Allow time for login to complete
            time.sleep(5)

            # Check for security challenges
            if self.handle_authentication_challenges():
                # Challenges were detected and hopefully handled by the user
                time.sleep(3)

            # Verify if login was successful
            if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
                logger.info("Successfully logged into LinkedIn.")
                return True
            else:
                # Try alternative validation
                try:
                    # Check for elements that indicate successful login
                    nav_items = self.driver.find_elements(By.CSS_SELECTOR, 
                                                        ".global-nav__nav, .feed-identity-module")
                    if nav_items:
                        logger.info("Successfully logged into LinkedIn (detected nav elements).")
                        return True
                except:
                    pass
                    
                logger.warning("Login may have failed. Check for CAPTCHA or incorrect credentials.")
                # Save page source for debugging
                with open("debug/linkedin_login_debug.html", "w", encoding="utf-8") as f:
                    f.write(self.driver.page_source)
                raise RuntimeError("LinkedIn login failed. CAPTCHA may be required.")

        except NoSuchElementException as e:
            logger.error(f"Login failed: {str(e)}")
            if self.driver:
                self.driver.quit()
            raise RuntimeError("LinkedIn login failed. CAPTCHA may be required.")

    def scrape_profiles(self, search_url, num_pages=3):
        """
        Scrapes LinkedIn profiles from a given search URL.
        
        Args:
            search_url: LinkedIn search URL to scrape
            num_pages: Number of pages to scrape
                
        Returns:
            List of dictionaries containing profile data
        """
        # Check if we need to log in first
        if not self._is_logged_in():
            logger.warning("Not logged in. Logging in first.")
            self.login()
            
        logger.info(f"Navigating to search URL: {search_url}")
        self.driver.get(search_url)
        time.sleep(5)
        
        # Add a delay between actions to avoid detection
        random_sleep(3, 5)
        
        # Save the HTML for debugging
        with open("debug/debug_linkedin.html", "w", encoding="utf-8") as f:
            f.write(self.driver.page_source)
        logger.info("Saved LinkedIn search page HTML for debugging.")
        
        # Take a screenshot as well for visual debugging
        self.driver.save_screenshot("debug/linkedin_search_page.png")
        
        profiles = []
        for page in range(num_pages):
            logger.info(f"Scraping page {page + 1} of {num_pages}")
            
            # Improved scrolling with longer wait times
            self._scroll_down_improved(scroll_count=7, wait_time=3)
            
            # Take a screenshot after scrolling
            self.driver.save_screenshot(f"debug/linkedin_search_page_{page+1}_after_scroll.png")
            
            # Use the extractors to get profile data
            extracted_profiles = extract_profiles(self.driver)
            
            if extracted_profiles:
                page_profiles = []
                for index, profile in enumerate(extracted_profiles):
                    try:
                        # Convert from the extraction format to our standard format
                        profile_data = {
                            "index": len(profiles) + index + 1,
                            "name": profile.get('name', 'Unknown'),
                            "profile_url": profile.get('url', '').split("?")[0],
                            "headline": profile.get('headline', 'No headline'),
                            "location": profile.get('location', 'Unknown location')
                        }
                        
                        # Add scoring and additional info
                        profile_data = extract_additional_info(profile_data)
                        page_profiles.append(profile_data)
                        
                    except Exception as e:
                        logger.warning(f"Error processing profile {index}: {str(e)}")
                        continue
                
                # Add profiles from this page to the main list
                profiles.extend(page_profiles)
                logger.info(f"Extracted {len(page_profiles)} profiles from page {page + 1}")
                
                # Check if we've reached the target count
                if len(profiles) >= num_pages * 10:
                    logger.info(f"Reached target profile count: {len(profiles)}")
                    break
            else:
                logger.warning(f"No profiles extracted on page {page + 1}")
            
            # Try to navigate to next page
            if page < num_pages - 1:
                next_page = False
                for selector in NEXT_BUTTON_SELECTORS:
                    try:
                        next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for next_button in next_buttons:
                            if next_button.is_enabled() and next_button.is_displayed():
                                # Using JavaScript to click can be more reliable
                                self.driver.execute_script("arguments[0].click();", next_button)
                                time.sleep(random.uniform(3, 5))
                                next_page = True
                                break
                        if next_page:
                            break
                    except NoSuchElementException:
                        continue
                    except Exception as e:
                        logger.error(f"Error clicking next button: {str(e)}")
                
                if not next_page:
                    # Try an alternative method - look for pagination links
                    try:
                        pagination_links = self.driver.find_elements(By.CSS_SELECTOR, 
                                                            "li.artdeco-pagination__indicator--number a, " + 
                                                            ".artdeco-pagination__button--next, " +
                                                            "button.artdeco-pagination__button--next")
                        
                        current_page_num = page + 1
                        next_page_num = current_page_num + 1
                        
                        for link in pagination_links:
                            link_text = link.text.strip()
                            if link_text == str(next_page_num) or "next" in link_text.lower():
                                self.driver.execute_script("arguments[0].click();", link)
                                time.sleep(random.uniform(3, 5))
                                next_page = True
                                break
                    except:
                        pass
                        
                if not next_page:
                    logger.warning("Could not navigate to next page. Ending scrape.")
                    break
        
        # Save the profiles to CSV
        filename = "data/linkedin_leads.csv"
        save_profiles_to_csv(profiles, filename)
        
        return profiles

    def scrape_by_industry_and_role(self, industry, role, num_pages=3):
        """
        Scrape LinkedIn profiles filtered by industry and role.
        
        Args:
            industry: Industry to filter on
            role: Role/title to filter on
            num_pages: Number of pages to scrape
            
        Returns:
            List of profile dictionaries
        """
        # Format search query
        search_query = f"{industry} {role}"
        search_query_url = search_query.replace(' ', '%20')
        
        # Construct search URL
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={search_query_url}&origin=GLOBAL_SEARCH_HEADER"
        
        # Perform the scraping
        profiles = self.scrape_profiles(search_url, num_pages)
        
        # Add search metadata
        for profile in profiles:
            profile['search_industry'] = industry
            profile['search_role'] = role
        
        return profiles

    def scrape_for_coaching_leads(self, num_pages=3, target_count=30):
        """
        Scrape LinkedIn specifically for coaching prospects.
        
        Args:
            num_pages: Number of pages to scrape per search
            target_count: Target number of leads to collect
            
        Returns:
            List of lead dictionaries
        """
        all_leads = []
        
        # Strategy 1: Combine industry and role
        for industry in TARGET_INDUSTRIES[:3]:  # Limit to top 3 industries
            for role in TARGET_ROLES[:3]:  # Limit to top 3 roles
                if len(all_leads) >= target_count:
                    break
                    
                logger.info(f"Searching for {role} in {industry}")
                try:
                    leads = self.scrape_by_industry_and_role(industry, role, num_pages=num_pages)
                    all_leads.extend(leads)
                    
                    # Avoid doing too many searches
                    if len(all_leads) >= target_count:
                        break
                        
                    # Add a delay between searches
                    random_sleep(5, 10)
                except Exception as e:
                    logger.error(f"Error scraping {industry} {role}: {str(e)}")
                    continue
        
        # Strategy 2: Use coaching keywords if we don't have enough leads
        if len(all_leads) < target_count:
            for keyword in TARGET_KEYWORDS[:5]:  # Limit to top 5 keywords
                if len(all_leads) >= target_count:
                    break
                    
                logger.info(f"Searching for keyword: {keyword}")
                try:
                    # Construct search URL for keyword
                    keyword_url = keyword.replace(' ', '%20')
                    search_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword_url}&origin=GLOBAL_SEARCH_HEADER"
                    
                    leads = self.scrape_profiles(search_url, num_pages=num_pages)
                    all_leads.extend(leads)
                    
                    # Add a delay between searches
                    random_sleep(5, 10)
                except Exception as e:
                    logger.error(f"Error scraping keyword {keyword}: {str(e)}")
                    continue
        
        # Remove duplicate profiles based on URL
        unique_leads = []
        seen_urls = set()
        
        for lead in all_leads:
            url = lead.get('profile_url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_leads.append(lead)
        
        logger.info(f"Collected {len(unique_leads)} unique coaching leads")
        
        # Save to a separate coaching-specific CSV
        filename = "data/life_coaching_leads.csv"
        save_profiles_to_csv(unique_leads, filename)
        
        # Save to Google Sheets
        try:
            # Import here to avoid circular imports
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from utils.sheets_manager import save_leads_to_sheet
            
            # Save to the coaching prospects worksheet
            sheets_result = save_leads_to_sheet(unique_leads, "CoachingProspects")
            
            if sheets_result:
                logger.info(f"Successfully saved {len(unique_leads)} coaching leads to Google Sheets")
            else:
                logger.warning("Failed to save coaching leads to Google Sheets")
        except Exception as e:
            logger.error(f"Error saving to Google Sheets: {str(e)}")
        
        return unique_leads

    def close(self):
        """Close the WebDriver."""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed.")


def run_linkedin_scraper(sheets_client=None, max_leads=50, headless=False):
    """
    Run the LinkedIn scraper as a standalone function.
    
    Args:
        sheets_client: Google Sheets client for saving results (optional)
        max_leads: Maximum number of leads to collect
        headless: Whether to run the browser in headless mode
        
    Returns:
        List of leads collected
    """
    from datetime import datetime
    
    try:
        # Create the scraper
        scraper = LinkedInScraper(headless=headless)
        
        # Run the scraper to find coaching leads
        leads = scraper.scrape_for_coaching_leads(
            num_pages=3,
            target_count=max_leads
        )
        
        # Save to Google Sheets if client provided
        if sheets_client:
            try:
                # Try to get existing worksheet or create new one
                try:
                    worksheet = sheets_client.open('LeadGenerationData').worksheet('LinkedInLeads')
                except:
                    # If worksheet doesn't exist, create it
                    spreadsheet = sheets_client.open('LeadGenerationData')
                    worksheet = spreadsheet.add_worksheet(title='LinkedInLeads', rows=1000, cols=20)
                    # Add header row
                    worksheet.append_row(['Name', 'Headline', 'Location', 'Profile URL', 'Coaching Fit Score', 'Coaching Notes', 'Date Added'])
                
                # Prepare data for sheets with current date
                current_date = datetime.now().strftime("%Y-%m-%d")
                rows = []
                for lead in leads:
                    row = [
                        lead.get('name', ''), 
                        lead.get('headline', ''),
                        lead.get('location', ''),
                        lead.get('profile_url', ''),
                        lead.get('coaching_fit_score', 0),
                        lead.get('coaching_notes', ''),
                        current_date
                    ]
                    rows.append(row)
                
                # Append to Google Sheet
                for row in rows:
                    worksheet.append_row(row)
                logger.info(f"Successfully saved {len(rows)} LinkedIn leads to Google Sheets")
            except Exception as e:
                logger.error(f"Error saving to Google Sheets: {str(e)}")
                # Save the detailed error for debugging
                with open("logs/sheets_error.txt", "w") as f:
                    f.write(f"Error: {str(e)}\n\n")
                    f.write(f"Traceback: {traceback.format_exc()}")
        
        # Close the scraper
        scraper.close()
        
        return leads
    except Exception as e:
        logger.error(f"Error running LinkedIn scraper: {str(e)}")
        return []
        
        return leads
    except Exception as e:
        logger.error(f"Error running LinkedIn scraper: {str(e)}")
        return []


if __name__ == "__main__":
    # Test directly
    import sys
    from datetime import datetime
    
    print("\n=== LinkedIn Scraper Test ===\n")
    
    try:
        start_time = datetime.now()
        print(f"Starting scraper test at {start_time.strftime('%H:%M:%S')}")
        
        # Run the scraper
        leads = run_linkedin_scraper(
            max_leads=20,
            headless=False
        )
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds() / 60.0
        
        print(f"\nTest completed at {end_time.strftime('%H:%M:%S')}")
        print(f"Duration: {duration:.2f} minutes")
        print(f"Leads collected: {len(leads)}")
        
        if leads:
            print("\nSample lead:")
            for k, v in sorted(leads[0].items()):
                print(f"  {k}: {v}")
        
        print("\n=== Test Finished ===\n")
    except Exception as e:
        print(f"\nTest failed: {str(e)}\n")
        import traceback
        traceback.print_exc()