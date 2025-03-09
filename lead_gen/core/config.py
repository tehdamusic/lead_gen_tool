# lead_gen/core/config.py
import os
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Centralized application configuration"""
    # LinkedIn config
    linkedin_username: str = field(default_factory=lambda: os.getenv("LINKEDIN_USERNAME", ""))
    linkedin_password: str = field(default_factory=lambda: os.getenv("LINKEDIN_PASSWORD", ""))
    linkedin_headless: bool = True
    linkedin_max_leads: int = 50
    
    # Reddit config
    reddit_subreddits: List[str] = field(default_factory=lambda: [
        "Entrepreneur", "Productivity", "MentalHealth",
        "WorkReform", "careerguidance"
    ])
    reddit_keywords: List[str] = field(default_factory=lambda: [
        "burnout", "career transition", "work-life balance"
    ])
    reddit_time_filter: str = "month"
    reddit_max_leads: int = 50
    
    # AI config
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = "gpt-4"
    use_ai: bool = True
    
    # Email config
    email_address: str = field(default_factory=lambda: os.getenv("EMAIL_ADDRESS", ""))
    email_password: str = field(default_factory=lambda: os.getenv("EMAIL_PASSWORD", ""))
    email_recipient: str = field(default_factory=lambda: os.getenv("EMAIL_RECIPIENT", ""))
    
    # Google Sheets config
    sheets_credentials_file: str = field(default_factory=lambda: 
                                     os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE", "credentials.json"))
    sheets_spreadsheet_id: str = field(default_factory=lambda: 
                                    os.getenv("GOOGLE_SHEETS_SPREADSHEET_ID", ""))
    
    # Directory paths
    data_dir: Path = Path("data")
    output_dir: Path = Path("data/output")
    log_dir: Path = Path("logs")
    
    @classmethod
    def load(cls) -> 'Config':
        """Load configuration from environment variables and config file"""
        # Create config with env variables
        config = cls()
        
        # Load from config file if exists
        config_file = Path("config.json")
        if config_file.exists():
            with open(config_file, "r") as f:
                try:
                    file_config = json.load(f)
                    # Update config with file values - implementation omitted for brevity
                except json.JSONDecodeError:
                    logging.warning(f"Could not parse config file: {config_file}")
        
        # Ensure directories exist
        config._create_dirs()
        
        return config
    
    def _create_dirs(self):
        """Ensure required directories exist"""
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.log_dir.mkdir(exist_ok=True)