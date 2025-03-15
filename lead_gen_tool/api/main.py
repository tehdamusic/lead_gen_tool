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

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI app
app = FastAPI()

# Connect to MongoDB
db = get_db()
leads_collection = db["leads"]
blacklist_collection = db["blacklist"]

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
    sheet.append_row(["Name", "Platform", "URL"])  # Add headers


# ✅ Check if service is running
@app.get("/")
async def root():
    return {"message": "Lead Generation API is running!"}


# 🔄 Run all scrapers sequentially
@app.get("/scrape-all")
async def scrape_all():
    total_leads = []

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

    # Consolidate leads into Google Sheets
    cleaned_leads = consolidate_leads_to_sheet(total_leads)

    return {"message": f"Scraped and saved {len(cleaned_leads)} new leads across all platforms."}


# 📋 Retrieve all stored leads
@app.get("/leads")
async def get_leads():
    leads = list(leads_collection.find({}, {"_id": 1, "name": 1, "platform": 1, "url": 1}))
    return [{"id": str(lead["_id"]), "name": lead.get("name", "Unknown"), "platform": lead["platform"], "url": lead["url"]} for lead in leads]


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
    all_leads = list(leads_collection.find({}, {"name": 1, "platform": 1, "url": 1}))

    # Fetch existing rows
    existing_rows = sheet.get_all_values()[1:]  # Skip headers
    existing_urls = {row[2] for row in existing_rows}  # Set of URLs in sheet

    new_leads = [lead for lead in leads if "url" in lead and lead["url"] not in existing_urls]

    if new_leads:
        sheet.append_rows([[lead.get("name", "Unknown"), lead["platform"], lead["url"]] for lead in new_leads])

    return new_leads
