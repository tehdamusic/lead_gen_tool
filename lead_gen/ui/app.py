# lead_gen/ui/app.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import logging
import importlib
import sys
from pathlib import Path

from lead_gen.core.config import Config
from lead_gen.core.logging_setup import setup_logging, get_ui_log_handler

class LeadGenerationApp:
    """Main application controller"""
    
    def __init__(self):
        self.config = Config.load()
        
        # Initialize root window
        self.root = tk.Tk()
        self.root.title("Peak Transformation Coaching - Lead Generation")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set up logging
        self.logger = setup_logging(self.config.log_dir)
        
        # Initialize UI
        self._init_ui()
        
        # Add UI log handler
        ui_handler = get_ui_log_handler(self._append_log)
        logging.getLogger().addHandler(ui_handler)
        
        self.logger.info("Application initialized")
    
    def _init_ui(self):
        """Initialize the user interface"""
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self._create_main_tab()
        self._create_linkedin_tab()
        self._create_reddit_tab()
        self._create_lead_scoring_tab()
        self._create_message_tab()
        self._create_email_tab()
        self._create_logs_tab()
    
    def _create_main_tab(self):
        """Create the main dashboard tab"""
        from lead_gen.ui.views.main_view import MainView
        self.main_view = MainView(self.notebook, self)
    
    def _create_linkedin_tab(self):
        """Create the LinkedIn scraper tab"""
        from lead_gen.ui.views.linkedin_view import LinkedInView
        self.linkedin_view = LinkedInView(self.notebook, self)
    
    def _create_reddit_tab(self):
        """Create the Reddit scraper tab"""
        from lead_gen.ui.views.reddit_view import RedditView
        self.reddit_view = RedditView(self.notebook, self)
    
    def _create_lead_scoring_tab(self):
        """Create the lead scoring tab"""
        from lead_gen.ui.views.scoring_view import ScoringView
        self.scoring_view = ScoringView(self.notebook, self)
    
    def _create_message_tab(self):
        """Create the message generation tab"""
        from lead_gen.ui.views.message_view import MessageView
        self.message_view = MessageView(self.notebook, self)
    
    def _create_email_tab(self):
        """Create the email reporting tab"""
        from lead_gen.ui.views.email_view import EmailView
        self.email_view = EmailView(self.notebook, self)
    
    def _create_logs_tab(self):
        """Create the logs viewer tab"""
        from lead_gen.ui.views.logs_view import LogsView
        self.logs_view = LogsView(self.notebook, self)
    
    def _append_log(self, message):
        """Append a log message to the logs view"""
        if hasattr(self, 'logs_view'):
            self.logs_view.append_log(message)
    
    def show_tab(self, tab_name):
        """Switch to a specific tab"""
        tab_indices = {
            "main": 0,
            "linkedin": 1,
            "reddit": 2,
            "scoring": 3,
            "messages": 4,
            "email": 5,
            "logs": 6
        }
        
        if tab_name in tab_indices:
            self.notebook.select(tab_indices[tab_name])
    
    def run_thread(self, func, args=(), kwargs=None):
        """Run a function in a background thread"""
        if kwargs is None:
            kwargs = {}
            
        thread = threading.Thread(
            target=func,
            args=args,
            kwargs=kwargs,
            daemon=True
        )
        thread.start()
        return thread
    
    def run(self):
        """Run the application"""
        self.root.mainloop()