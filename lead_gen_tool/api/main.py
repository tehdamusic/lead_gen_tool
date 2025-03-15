from fastapi import FastAPI, HTTPException
from pymongo import MongoClient
from bson import ObjectId
import openai
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from time import sleep
import logging

# Import Scrapers & Database Functions
from scrapers.linkedin_scraper import scrape_google_for_linkedin_profiles
from scrapers.instagram_scraper import scrape_instagram_comments
from scrapers.twitter_scraper import scrape_serpapi_for_tweets
from database.mongodb import get_db
from ai.lead_scoring import score_lead, is_qualified_lead

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI app
app = FastAPI()

# Connect to MongoDB
db = get_db()
leads_collection = db["leads"]
blacklist_collection = db["blacklist"]
discarded_collection = db["discarded_leads"]  # New collection for low-scoring leads

# Google Sheets API Setup
SHEET_NAME = "Master Leads Sheet"
GOOGLE_SHEETS_CREDENTIALS = "config/google_sheets_credentials.json"
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Ensure the credentials file exists before proceeding
if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS):
    logging.error(f"❌ Google Sheets credentials file not found: {GOOGLE_SHEETS_CREDENTIALS}")
    raise FileNotFoundError(f"Google Sheets credentials file not found: {GOOGLE_SHEETS_CREDENTIALS}")

creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_CREDENTIALS, scope)
client = gspread.authorize(creds)

# Ensure the master sheet exists
try:
    sheet = client.open(SHEET_NAME).sheet1
except gspread.exceptions.SpreadsheetNotFound:
    sheet = client.create(SHEET_NAME).sheet1
    sheet.append_row(["Name", "Platform", "URL", "Score", "Rationale"])  # Added Score and Rationale columns


# ✅ Check if service is running
@app.get("/")
async def root():
    return {"message": "Lead Generation API is running!"}


# 🔄 Run all scrapers sequentially
@app.get("/scrape-all")
async def scrape_all():
    total_leads = []
    qualified_leads = []
    discarded_leads = []

    logging.info("🚀 Running LinkedIn Scraper...")
    linkedin_leads = scrape_google_for_linkedin_profiles(max_profiles=50)
    total_leads.extend(linkedin_leads)
    sleep(2)  # Prevent rate-limiting

    logging.info("🚀 Running Instagram Scraper...")
    instagram_leads = scrape_instagram_comments(max_comments=50)
    total_leads.extend(instagram_leads)
    sleep(2)

    logging.info("🚀 Running Twitter Scraper...")
    twitter_leads = scrape_serpapi_for_tweets(max_tweets=50)
    total_leads.extend(twitter_leads)

    # Score and filter leads
    for lead in total_leads:
        score, rationale = score_lead(lead)
        lead["score"] = score
        lead["rationale"] = rationale
        
        if score >= 4:
            qualified_leads.append(lead)
            logging.info(f"✅ Qualified lead: {lead.get('name', lead.get('username', 'Unknown'))} - Score: {score}")
        else:
            discarded_leads.append(lead)
            logging.info(f"❌ Discarded lead: {lead.get('name', lead.get('username', 'Unknown'))} - Score: {score}")
            
            # Store discarded lead in separate collection for analysis
            discarded_collection.insert_one(lead)

    # Consolidate qualified leads into Google Sheets
    cleaned_leads = consolidate_leads_to_sheet(qualified_leads)

    return {
        "message": f"Scraped {len(total_leads)} leads across all platforms.",
        "qualified": len(qualified_leads),
        "discarded": len(discarded_leads),
        "saved": len(cleaned_leads)
    }


# 📋 Retrieve all stored leads
@app.get("/leads")
async def get_leads():
    leads = list(leads_collection.find({}, {"_id": 1, "name": 1, "platform": 1, "url": 1, "score": 1, "rationale": 1}))
    return [{
        "id": str(lead["_id"]), 
        "name": lead.get("name", lead.get("username", "Unknown")), 
        "platform": lead["platform"], 
        "url": lead["url"],
        "score": lead.get("score", "Not scored"),
        "rationale": lead.get("rationale", "")
    } for lead in leads]


# 🚫 Blacklist a lead
@app.post("/blacklist/{lead_id}")
async def blacklist_lead(lead_id: str):
    lead = leads_collection.find_one({"_id": ObjectId(lead_id)})
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    blacklist_collection.insert_one(lead)
    leads_collection.delete_one({"_id": ObjectId(lead_id)})

    return {"message": "Lead blacklisted successfully"}


# 📊 Consolidate leads into Google Sheets
def consolidate_leads_to_sheet(leads):
    all_leads = list(leads_collection.find({}, {"name": 1, "username": 1, "platform": 1, "url": 1, "score": 1, "rationale": 1}))

    # Fetch existing rows
    existing_rows = sheet.get_all_values()[1:]  # Skip headers
    existing_urls = {row[2] for row in existing_rows}  # Set of URLs in sheet

    new_leads = []
    for lead in leads:
        if "url" in lead and lead["url"] not in existing_urls:
            # Add to MongoDB if not already present
            if not leads_collection.find_one({"url": lead["url"]}):
                leads_collection.insert_one(lead)
                
            # Add to list of new leads
            new_leads.append(lead)

    if new_leads:
        rows_to_append = []
        for lead in new_leads:
            name = lead.get("name", lead.get("username", "Unknown"))
            platform = lead["platform"]
            url = lead["url"]
            score = lead.get("score", "")
            rationale = lead.get("rationale", "")
            rows_to_append.append([name, platform, url, score, rationale])
            
        sheet.append_rows(rows_to_append)

    return new_leads


# 📈 Get discarded leads for analysis
@app.get("/discarded-leads")
async def get_discarded_leads():
    discarded = list(discarded_collection.find({}, {"_id": 1, "name": 1, "username": 1, "platform": 1, "url": 1, "score": 1, "rationale": 1}))
    return [{
        "id": str(lead["_id"]), 
        "name": lead.get("name", lead.get("username", "Unknown")), 
        "platform": lead["platform"], 
        "url": lead["url"],
        "score": lead.get("score", "Not scored"),
        "rationale": lead.get("rationale", "")
    } for lead in discarded]


# 🔄 Rescore a specific lead
@app.post("/rescore/{lead_id}")
async def rescore_lead(lead_id: str):
    # Check in both collections
    lead = leads_collection.find_one({"_id": ObjectId(lead_id)})
    collection = leads_collection
    
    if not lead:
        lead = discarded_collection.find_one({"_id": ObjectId(lead_id)})
        collection = discarded_collection
        
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Rescore the lead
    score, rationale = score_lead(lead)
    lead["score"] = score
    lead["rationale"] = rationale
    
    # Update the lead in its current collection
    collection.update_one({"_id": ObjectId(lead_id)}, {"$set": {"score": score, "rationale": rationale}})
    
    # Move between collections if necessary
    if score >= 4 and collection == discarded_collection:
        # Move to qualified leads
        leads_collection.insert_one(lead)
        discarded_collection.delete_one({"_id": ObjectId(lead_id)})
        return {"message": "Lead rescored and moved to qualified leads", "score": score, "rationale": rationale}
        
    elif score < 4 and collection == leads_collection:
        # Move to discarded leads
        discarded_collection.insert_one(lead)
        leads_collection.delete_one({"_id": ObjectId(lead_id)})
        return {"message": "Lead rescored and moved to discarded leads", "score": score, "rationale": rationale}
    
    return {"message": "Lead rescored", "score": score, "rationale": rationale}