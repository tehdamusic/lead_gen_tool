"""
Google Sheets integration for the Lead Generation Tool.
"""

import os
import pickle
import logging
from typing import Any, Optional
from datetime import datetime

import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/sheets_manager.log'
)
logger = logging.getLogger('sheets_manager')

# Define scopes
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

def get_credentials() -> Credentials:
    """
    Get Google API credentials.
    
    Returns:
        Credentials object for Google API
    """
    credentials = None
    
    # Get credentials file path from environment variable
    creds_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
    token_file = os.getenv('GOOGLE_SHEETS_TOKEN_FILE', 'token.pickle')
    
    # Try to load existing token
    if os.path.exists(token_file):
        with open(token_file, 'rb') as token:
            try:
                credentials = pickle.load(token)
            except Exception as e:
                logger.error(f"Error loading token: {str(e)}")
    
    # If there are no valid credentials, let the user log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            try:
                credentials.refresh(Request())
            except Exception as e:
                logger.error(f"Error refreshing credentials: {str(e)}")
                credentials = None
        
        if not credentials:
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    creds_file, SCOPES)
                credentials = flow.run_local_server(port=0)
            except Exception as e:
                logger.error(f"Error getting new credentials: {str(e)}")
                raise
        
        # Save the credentials for the next run
        with open(token_file, 'wb') as token:
            pickle.dump(credentials, token)
    
    return credentials

def get_sheets_client() -> gspread.Client:
    """
    Get authenticated gspread client.
    
    Returns:
        Authenticated gspread client
    """
    try:
        credentials = get_credentials()
        client = gspread.authorize(credentials)
        logger.info("Successfully connected to Google Sheets")
        return client
    except Exception as e:
        logger.error(f"Error getting sheets client: {str(e)}")
        raise

def get_spreadsheet_id() -> str:
    """
    Get the spreadsheet ID from environment variable.
    
    Returns:
        Spreadsheet ID from environment or a default value
    """
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_SPREADSHEET_ID')
    if not spreadsheet_id:
        logger.warning("GOOGLE_SHEETS_SPREADSHEET_ID not found in environment variables")
        return ""
    logger.info(f"Using Google Sheets ID: {spreadsheet_id}")
    return spreadsheet_id

def open_spreadsheet_by_id(client=None):
    """
    Open a spreadsheet by its ID from environment variable.
    
    Args:
        client: gspread client (optional, will create if not provided)
        
    Returns:
        gspread Spreadsheet object
    """
    if client is None:
        client = get_sheets_client()
        
    spreadsheet_id = get_spreadsheet_id()
    if not spreadsheet_id:
        raise ValueError("No spreadsheet ID found. Set GOOGLE_SHEETS_SPREADSHEET_ID in your .env file.")
        
    try:
        spreadsheet = client.open_by_key(spreadsheet_id)
        logger.info(f"Successfully opened spreadsheet: {spreadsheet.title}")
        return spreadsheet
    except Exception as e:
        logger.error(f"Error opening spreadsheet: {str(e)}")
        raise

def create_sheet_if_not_exists(spreadsheet_name: str, worksheet_name: str) -> gspread.Worksheet:
    """
    Create a worksheet if it doesn't exist.
    
    Args:
        spreadsheet_name: Name of the spreadsheet
        worksheet_name: Name of the worksheet
        
    Returns:
        Worksheet object
    """
    try:
        client = get_sheets_client()
        
        # Check if we should use ID from environment
        spreadsheet_id = get_spreadsheet_id()
        if spreadsheet_id:
            try:
                # Try opening by ID first
                spreadsheet = client.open_by_key(spreadsheet_id)
                logger.info(f"Using spreadsheet from ID: {spreadsheet.title}")
            except:
                # Fall back to opening by name
                try:
                    spreadsheet = client.open(spreadsheet_name)
                except:
                    spreadsheet = client.create(spreadsheet_name)
                    logger.info(f"Created new spreadsheet: {spreadsheet_name}")
        else:
            # Try to open the spreadsheet, create if it doesn't exist
            try:
                spreadsheet = client.open(spreadsheet_name)
            except:
                spreadsheet = client.create(spreadsheet_name)
                logger.info(f"Created new spreadsheet: {spreadsheet_name}")
        
        # Try to get the worksheet, create if it doesn't exist
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=20
            )
            logger.info(f"Created new worksheet: {worksheet_name}")
        
        return worksheet
    except Exception as e:
        logger.error(f"Error creating sheet {spreadsheet_name}/{worksheet_name}: {str(e)}")
        raise

def save_leads_to_sheet(leads, worksheet_name="LinkedInLeads"):
    """
    Save leads to a specified worksheet.
    
    Args:
        leads: List of lead dictionaries
        worksheet_name: Name of the worksheet to save to
        
    Returns:
        True if successful, False otherwise
    """
    try:
        if not leads:
            logger.warning("No leads to save to Google Sheets")
            return False
            
        client = get_sheets_client()
        spreadsheet_id = get_spreadsheet_id()
        
        if not spreadsheet_id:
            logger.warning("No Google Sheets ID specified in environment variables")
            return False
            
        # Open spreadsheet by ID
        spreadsheet = client.open_by_key(spreadsheet_id)
        
        # Try to get the worksheet, create if it doesn't exist
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
        except:
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name, rows=1000, cols=20
            )
            
            # Add header row for LinkedIn leads
            header = ["Name", "Headline", "Location", "Profile URL", "Coaching Fit Score", "Notes", "Date Added"]
            worksheet.append_row(header)
            logger.info(f"Created new worksheet: {worksheet_name} with headers")
        
        # Prepare data for sheets
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
            
        logger.info(f"Successfully saved {len(rows)} leads to Google Sheets in worksheet {worksheet_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving leads to Google Sheets: {str(e)}")
        return False

def append_rows(worksheet: gspread.Worksheet, rows: list) -> None:
    """
    Append multiple rows to a worksheet.
    
    Args:
        worksheet: Worksheet object
        rows: List of rows to append
    """
    try:
        if rows:
            worksheet.append_rows(rows)
            logger.info(f"Appended {len(rows)} rows to {worksheet.title}")
    except Exception as e:
        logger.error(f"Error appending rows to {worksheet.title}: {str(e)}")
        raise

if __name__ == "__main__":
    # Test functionality
    try:
        # Import datetime here for the test
        from datetime import datetime
        
        print("Testing Google Sheets integration...")
        spreadsheet_id = get_spreadsheet_id()
        print(f"Spreadsheet ID from environment: {spreadsheet_id}")
        
        client = get_sheets_client()
        if spreadsheet_id:
            # Test with ID
            try:
                spreadsheet = client.open_by_key(spreadsheet_id)
                print(f"Successfully opened spreadsheet: {spreadsheet.title}")
                
                worksheet = create_sheet_if_not_exists('', 'TestData')
                append_rows(worksheet, [['Test', 'Data', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
                print("Successfully appended test data!")
            except Exception as e:
                print(f"Error testing with ID: {str(e)}")
        else:
            # Test with name
            worksheet = create_sheet_if_not_exists('LeadGenerationData', 'TestData')
            append_rows(worksheet, [['Test', 'Data', datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
            print("Test successful!")
    except Exception as e:
        print(f"Error: {str(e)}")