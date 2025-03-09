# lead_gen/ui/views/linkedin_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys
import importlib.util
import logging
from typing import List, Dict, Any

from lead_gen.ui.components.widget_factory import WidgetFactory

class LinkedInView:
    """LinkedIn scraper view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.config = app.config
        self.logger = logging.getLogger("linkedin_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="LinkedIn Scraper")
        
        # Create variables
        self.industry_var = tk.StringVar(value="Technology")
        self.role_var = tk.StringVar(value="CEO")
        self.num_pages_var = tk.StringVar(value="3")
        self.headless_var = tk.BooleanVar(value=True)
        
        # Initialize UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title
        WidgetFactory.create_title(self.tab, "LinkedIn Lead Generation")
        
        # Form container
        form = WidgetFactory.create_form_container(self.tab, "Search Parameters")
        
        # Industry field
        WidgetFactory.create_entry_row(form, "Industry:", self.industry_var)
        
        # Industry suggestions
        industry_suggestions = [
            "Technology", "Finance", "Healthcare", "Education", "Consulting", 
            "Media", "Marketing", "Entrepreneurship", "Human Resources"
        ]
        WidgetFactory.create_combobox_row(
            form, "Suggestions:", self.industry_var, 
            values=industry_suggestions,
            on_select=lambda e: self.industry_var.set(e.widget.get())
        )
        
        # Role field
        WidgetFactory.create_entry_row(form, "Role:", self.role_var)
        
        # Role suggestions
        role_suggestions = [
            "CEO", "CTO", "CFO", "Director", "Manager", "Executive", 
            "VP", "President", "Founder", "Owner", "Leader"
        ]
        WidgetFactory.create_combobox_row(
            form, "Suggestions:", self.role_var, 
            values=role_suggestions,
            on_select=lambda e: self.role_var.set(e.widget.get())
        )
        
        # Number of pages
        WidgetFactory.create_entry_row(
            form, "Pages to scrape:", self.num_pages_var, width=10)
        
        # Headless option
        WidgetFactory.create_checkbox_row(
            form, "Run in headless mode (no visible browser)", self.headless_var)
        
        # Start button
        WidgetFactory.create_button_row(form, [
            {"text": "Start Scraping", "command": self._start_scraping, "width": 20}
        ])
        
        # Results area
        _, self.results_text = WidgetFactory.create_results_area(
            self.tab, "Results")
        
        # Bottom buttons
        WidgetFactory.create_button_row(self.tab, [
            {"text": "View Results File", "command": self._view_results_file},
            {"text": "Clear Results", "command": self._clear_results}
        ])
    
    def _start_scraping(self):
        """Start the LinkedIn scraping process"""
        try:
            # Validate inputs
            try:
                num_pages = int(self.num_pages_var.get())
                if num_pages <= 0:
                    raise ValueError("Number of pages must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return
            
            # Get LinkedIn credentials
            if not self.config.linkedin_username or not self.config.linkedin_password:
                messagebox.showerror(
                    "Missing Credentials", 
                    "LinkedIn username and password are required. Please check your .env file."
                )
                return
            
            # Clear results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, f"Starting LinkedIn search for {self.industry_var.get()} {self.role_var.get()}...\n")
            self.results_text.insert(tk.END, f"Using {num_pages} pages, headless mode: {self.headless_var.get()}\n\n")
            self.results_text.update()
            
            # Run in background thread
            self.app.run_thread(
                self._run_scraper,
                kwargs={
                    "industry": self.industry_var.get(),
                    "role": self.role_var.get(),
                    "num_pages": num_pages,
                    "headless": self.headless_var.get()
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error starting LinkedIn scraper: {e}")
            messagebox.showerror("Error", f"Failed to start scraper: {e}")
    
    def _run_scraper(self, industry, role, num_pages, headless):
        """Run the LinkedIn scraper"""
        try:
            # First check if scrapers module can be imported
            if importlib.util.find_spec("scrapers.linkedin") is None:
                self.results_text.insert(tk.END, "Error: LinkedIn scraper module not found.\n")
                return
            
            # Import the scraper module
            from scrapers.linkedin import LinkedInScraper
            
            # Create scraper instance
            scraper = LinkedInScraper(headless=headless)
            
            # Log start
            self.logger.info(f"Starting LinkedIn scrape for {industry} {role}")
            
            # Display scraping status
            def update_status(message):
                self.results_text.insert(tk.END, f"{message}\n")
                self.results_text.see(tk.END)
                self.results_text.update()
            
            update_status("Logging into LinkedIn...")
            
            # Login
            scraper.login()
            update_status("Login successful!")
            
            # Run the scraper
            update_status(f"Searching for {industry} {role}...")
            leads = scraper.scrape_by_industry_and_role(
                industry=industry,
                role=role,
                num_pages=num_pages
            )
            
            # Close the scraper
            scraper.close()
            
            # Update results on the main thread
            self.tab.after(0, lambda: self._update_results(leads))
            
        except Exception as e:
            self.logger.error(f"Error in LinkedIn scraper: {e}")
            self.tab.after(0, lambda: self._show_error(str(e)))
    
    def _update_results(self, leads):
        """Update the results text with scraped leads"""
        self.results_text.delete(1.0, tk.END)
        
        if not leads or len(leads) == 0:
            self.results_text.insert(tk.END, "No leads found.\n")
            return
        
        self.results_text.insert(tk.END, f"Found {len(leads)} leads:\n\n")
        
        for lead in leads[:10]:  # Show first 10 leads
            self.results_text.insert(tk.END, f"Name: {lead.get('name', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"Headline: {lead.get('headline', 'No headline')}\n")
            self.results_text.insert(tk.END, f"Location: {lead.get('location', 'Unknown location')}\n")
            self.results_text.insert(tk.END, f"Score: {lead.get('coaching_fit_score', 0)}/100\n")
            self.results_text.insert(tk.END, f"URL: {lead.get('profile_url', 'No URL')}\n")
            self.results_text.insert(tk.END, "-" * 50 + "\n\n")
        
        if len(leads) > 10:
            self.results_text.insert(tk.END, f"... and {len(leads) - 10} more leads.\n\n")
            
        self.results_text.insert(tk.END, f"All {len(leads)} leads saved to data/linkedin_leads.csv\n")
    
    def _show_error(self, error_message):
        """Show error in results area"""
        self.results_text.insert(tk.END, f"\nError: {error_message}\n")
        messagebox.showerror("LinkedIn Scraper Error", error_message)
    
    def _view_results_file(self):
        """Open the results CSV file"""
        csv_path = os.path.join("data", "linkedin_leads.csv")
        if not os.path.exists(csv_path):
            messagebox.showinfo("File Not Found", "No LinkedIn leads file found. Run the scraper first.")
            return
        
        # Open with default application based on platform
        if sys.platform == 'darwin':  # macOS
            os.system(f'open "{csv_path}"')
        elif sys.platform == 'win32':  # Windows
            os.startfile(csv_path)
        else:  # Linux
            os.system(f'xdg-open "{csv_path}"')
    
    def _clear_results(self):
        """Clear the results text area"""
        self.results_text.delete(1.0, tk.END)