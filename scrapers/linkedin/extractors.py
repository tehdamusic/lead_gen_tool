"""
Profile extraction methods for LinkedIn.
"""

import logging
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import time

from .selectors import (
    NAME_SELECTORS, 
    HEADLINE_SELECTORS, 
    LOCATION_SELECTORS,
    ROLE_KEYWORD_SCORES,
    COACHING_KEYWORDS,
    TARGET_LOCATIONS,
    PROFILE_CONTAINER_SELECTORS
)

# Configure logging
logger = logging.getLogger('linkedin.extractors')

def extract_profiles_js(driver):
    """
    Extract profile information using JavaScript for better reliability.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of profile dictionaries
    """
    # Updated JavaScript to handle LinkedIn's current DOM structure
    js_script = """
    var profiles = []; 
    
    // Try different container selectors
    var containers = document.querySelectorAll('.reusable-search__result-container');
    
    if (!containers || containers.length === 0) {
        containers = document.querySelectorAll('li.reusable-search__result-container');
    }
    
    if (!containers || containers.length === 0) {
        containers = document.querySelectorAll('li.search-result');
    }
    
    if (!containers || containers.length === 0) {
        containers = document.querySelectorAll('.entity-result');
    }

    if (!containers || containers.length === 0) {
        containers = document.querySelectorAll('.artdeco-entity-lockup');
    }
    
    if (!containers || containers.length === 0) {
        containers = document.querySelectorAll('ul.reusable-search__entity-result-list > li');
    }
    
    // Log to console for debugging
    console.log("Found " + containers.length + " potential profile containers");
    
    containers.forEach(function(profile) { 
        // Try multiple selector patterns for each field
        
        // For the name field
        var nameElement = null;
        var nameSelectors = [
            '.entity-result__title-text a span[aria-hidden="true"]',
            '.entity-result__title-text span[aria-hidden="true"]',
            '.entity-result__title-line a span span',
            '.search-result__info .actor-name',
            '.app-aware-link span[aria-hidden="true"]',
            '.artdeco-entity-lockup__title span'
        ];
        
        for (var i = 0; i < nameSelectors.length; i++) {
            nameElement = profile.querySelector(nameSelectors[i]);
            if (nameElement) break;
        }
        
        // For the link
        var linkElement = null;
        var linkSelectors = [
            '.app-aware-link[href*="/in/"]',
            'a[href*="/in/"]',
            '.entity-result__title-text a[href*="/in/"]',
            '.search-result__info a[href*="/in/"]'
        ];
        
        for (var i = 0; i < linkSelectors.length; i++) {
            linkElement = profile.querySelector(linkSelectors[i]);
            if (linkElement) break;
        }
        
        // For the headline
        var headlineElement = null;
        var headlineSelectors = [
            '.entity-result__primary-subtitle',
            '.search-result__info .subline-level-1',
            '.entity-result__summary span',
            '.entity-result__primary-subtitle span',
            '.artdeco-entity-lockup__subtitle'
        ];
        
        for (var i = 0; i < headlineSelectors.length; i++) {
            headlineElement = profile.querySelector(headlineSelectors[i]);
            if (headlineElement) break;
        }
        
        // For the location
        var locationElement = null;
        var locationSelectors = [
            '.entity-result__secondary-subtitle',
            '.search-result__info .subline-level-2',
            '.entity-result__secondary-subtitle span',
            '.artdeco-entity-lockup__caption'
        ];
        
        for (var i = 0; i < locationSelectors.length; i++) {
            locationElement = profile.querySelector(locationSelectors[i]);
            if (locationElement) break;
        }
        
        if (linkElement) {
            profiles.push({ 
                url: linkElement.href.trim(), 
                name: nameElement ? nameElement.innerText.trim() : "Unknown", 
                headline: headlineElement ? headlineElement.innerText.trim() : "No headline", 
                location: locationElement ? locationElement.innerText.trim() : "Unknown location" 
            }); 
        }
    });
    
    return profiles;
    """
    
    try:
        profiles_data = driver.execute_script(js_script)
        if not profiles_data:
            logger.warning("No profiles found on the page using JavaScript extraction")
            return []
            
        logger.info(f"Successfully extracted {len(profiles_data)} profiles via JavaScript")
        return profiles_data
    except Exception as e:
        logger.error(f"JavaScript extraction failed: {str(e)}")
        return []

def extract_profiles_selenium(driver):
    """
    Extract profile information using Selenium as a fallback method.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of profile dictionaries
    """
    profiles = []
    
    try:
        # Try multiple container selectors for better compatibility
        profile_containers = []
        
        for selector in PROFILE_CONTAINER_SELECTORS:
            profile_containers = driver.find_elements(By.CSS_SELECTOR, selector)
            if profile_containers:
                logger.info(f"Found {len(profile_containers)} profile containers using selector: {selector}")
                break
                
        if not profile_containers:
            logger.warning("Could not find any profile containers with any selector")
            # Take a screenshot for debugging
            driver.save_screenshot("debug/no_profiles_found.png")
            # Save the page source for analysis
            with open("debug/debug_linkedin_failed.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            return []
            
        for profile in profile_containers:
            try:
                # Try multiple approaches to find the profile link
                profile_url = None
                
                # First approach: direct link to profile
                try:
                    link_elements = profile.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
                    for link in link_elements:
                        href = link.get_attribute('href')
                        if href and '/in/' in href:
                            profile_url = href
                            break
                except:
                    pass
                    
                if not profile_url:
                    logger.warning("Could not find profile URL, skipping profile")
                    continue
                
                # Try to find name with multiple selectors
                profile_name = "Unknown"
                for selector in NAME_SELECTORS:
                    try:
                        name_elements = profile.find_elements(By.CSS_SELECTOR, selector)
                        if name_elements and name_elements[0].text.strip():
                            profile_name = name_elements[0].text.strip()
                            break
                    except:
                        continue
                
                # Try to find headline with multiple selectors
                headline = "No headline"
                for selector in HEADLINE_SELECTORS:
                    try:
                        headline_elements = profile.find_elements(By.CSS_SELECTOR, selector)
                        if headline_elements and headline_elements[0].text.strip():
                            headline = headline_elements[0].text.strip()
                            break
                    except:
                        continue
                
                # Try to find location with multiple selectors
                location = "Unknown location"
                for selector in LOCATION_SELECTORS:
                    try:
                        location_elements = profile.find_elements(By.CSS_SELECTOR, selector)
                        if location_elements and location_elements[0].text.strip():
                            location = location_elements[0].text.strip()
                            break
                    except:
                        continue
                
                # Create profile dict and add to list
                profile_data = {
                    'url': profile_url,
                    'name': profile_name,
                    'headline': headline,
                    'location': location
                }
                
                profiles.append(profile_data)
                logger.debug(f"Added profile: {profile_name}")
                
            except Exception as e:
                logger.warning(f"Error processing profile: {str(e)}")
                continue
                
        logger.info(f"Successfully extracted {len(profiles)} profiles via Selenium")
        return profiles
        
    except Exception as e:
        logger.error(f"Selenium extraction failed: {str(e)}")
        return []

def extract_profiles(driver):
    """
    Extract profiles using both methods and combine results.
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        List of profile dictionaries
    """
    # Try JavaScript method first (faster and more reliable)
    profiles = extract_profiles_js(driver)
    
    # If JavaScript method failed or found no profiles, try Selenium method
    if not profiles:
        logger.info("JavaScript extraction returned no results, trying Selenium extraction")
        profiles = extract_profiles_selenium(driver)
    
    # Log the results
    if profiles:
        logger.info(f"Successfully extracted {len(profiles)} profiles in total")
    else:
        logger.warning("No profiles extracted using either method")
        
        # As a last resort, try a different approach with direct DOM observation
        try:
            logger.info("Attempting emergency profile extraction method")
            # Save the page source for analysis
            with open("debug/linkedin_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
                
            # Look for any potential profile links directly
            all_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="/in/"]')
            logger.info(f"Found {len(all_links)} potential profile links")
            
            emergency_profiles = []
            for link in all_links[:10]:  # Limit to first 10 to avoid duplicates
                try:
                    href = link.get_attribute('href')
                    if href and '/in/' in href and 'linkedin.com' in href:
                        # Try to get parent elements that might contain name/headline
                        parent = link
                        for _ in range(5):  # Try up to 5 levels up
                            try:
                                parent = parent.find_element(By.XPATH, '..')
                                # Look for text that might be a name
                                potential_texts = parent.find_elements(By.CSS_SELECTOR, 'span, div')
                                texts = [t.text for t in potential_texts if t.text and len(t.text) > 2]
                                
                                if texts:
                                    emergency_profiles.append({
                                        'url': href,
                                        'name': texts[0] if len(texts) > 0 else "Unknown",
                                        'headline': texts[1] if len(texts) > 1 else "No headline",
                                        'location': texts[2] if len(texts) > 2 else "Unknown location"
                                    })
                                    break
                            except:
                                continue
                except:
                    continue
                    
            if emergency_profiles:
                logger.info(f"Emergency extraction found {len(emergency_profiles)} profiles")
                # Remove duplicates based on URL
                seen_urls = set()
                unique_profiles = []
                for p in emergency_profiles:
                    if p['url'] not in seen_urls:
                        seen_urls.add(p['url'])
                        unique_profiles.append(p)
                return unique_profiles
    
    return profiles

def extract_additional_info(profile_data):
    """
    Extract additional information from profile data and calculate coaching fit score.
    
    Args:
        profile_data: Dictionary containing basic profile information
        
    Returns:
        Enhanced profile data with coaching fit score
    """
    # Initialize score and notes
    score = 0
    notes = []
    
    # Get profile data
    headline = profile_data.get('headline', '').lower()
    location = profile_data.get('location', '').lower()
    name = profile_data.get('name', '')
    
    # Score based on role keywords in headline
    for role, role_score in ROLE_KEYWORD_SCORES.items():
        if role in headline:
            score += role_score
            notes.append(f"Found role keyword: {role} (+{role_score})")
    
    # Score based on coaching keywords in headline
    for keyword in COACHING_KEYWORDS:
        if keyword.lower() in headline:
            score += 10
            notes.append(f"Found coaching keyword: {keyword} (+10)")
    
    # Score based on location
    for target_location in TARGET_LOCATIONS:
        if target_location in location:
            score += 15
            notes.append(f"Found target location: {target_location} (+15)")
            break
    
    # Cap the score at 100
    score = min(score, 100)
    
    # Add score and notes to profile data
    profile_data['coaching_fit_score'] = score
    profile_data['coaching_notes'] = "; ".join(notes)
    
    return profile_data