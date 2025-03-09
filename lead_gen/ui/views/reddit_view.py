# lead_gen/ui/views/reddit_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
import importlib.util

from lead_gen.ui.components.widget_factory import WidgetFactory

class RedditView:
    """Reddit scraper view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.config = app.config
        self.logger = logging.getLogger("reddit_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Reddit Scraper")
        
        # Create variables
        self.max_leads_var = tk.StringVar(value="50")
        self.subreddits_var = tk.StringVar(value=",".join(self.config.reddit_subreddits))
        self.keywords_var = tk.StringVar(value=",".join(self.config.reddit_keywords))
        self.time_filter_var = tk.StringVar(value=self.config.reddit_time_filter)
        
        # Initialize UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title
        WidgetFactory.create_title(self.tab, "Reddit Lead Finder")
        
        # Form container
        form = WidgetFactory.create_form_container(self.tab, "Scraper Settings")
        
        # Max leads
        WidgetFactory.create_entry_row(form, "Max leads to collect:", self.max_leads_var, width=10)
        
        # Subreddits
        WidgetFactory.create_entry_row(form, "Subreddits:", self.subreddits_var)
        
        # Subreddit suggestions
        subreddit_suggestions = [
            "Entrepreneur,Productivity,MentalHealth",
            "WorkReform,careerguidance,jobs",
            "careeradvice,personalfinance,cscareerquestions",
            "leadership,ExecutiveAssistants,LifeCoaching"
        ]
        WidgetFactory.create_combobox_row(
            form, "Suggestions:", self.subreddits_var, 
            values=subreddit_suggestions,
            on_select=lambda e: self.subreddits_var.set(e.widget.get())
        )
        
        # Keywords
        WidgetFactory.create_entry_row(form, "Keywords:", self.keywords_var)
        
        # Keyword suggestions
        keyword_suggestions = [
            "burnout,work stress,career transition",
            "work-life balance,leadership,feeling lost",
            "overwhelmed,anxiety,career change",
            "quit my job,overworked,toxic workplace"
        ]
        WidgetFactory.create_combobox_row(
            form, "Suggestions:", self.keywords_var, 
            values=keyword_suggestions,
            on_select=lambda e: self.keywords_var.set(e.widget.get())
        )
        
        # Time filter
        WidgetFactory.create_combobox_row(
            form, "Time filter:", self.time_filter_var,
            values=["day", "week", "month", "year", "all"],
            width=15
        )
        
        # Start button
        WidgetFactory.create_button_row(form, [
            {"text": "Start Reddit Scraper", "command": self._start_scraping, "width": 20}
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
        """Start the Reddit scraping process"""
        try:
            # Validate inputs
            try:
                max_leads = int(self.max_leads_var.get())
                if max_leads <= 0:
                    raise ValueError("Maximum leads must be greater than 0")
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return
            
            # Parse subreddits and keywords
            subreddits = [s.strip() for s in self.subreddits_var.get().split(",") if s.strip()]
            keywords = [k.strip() for k in self.keywords_var.get().split(",") if k.strip()]
            
            if not subreddits:
                messagebox.showerror("Input Error", "Please specify at least one subreddit")
                return
                
            if not keywords:
                messagebox.showerror("Input Error", "Please specify at least one keyword")
                return
            
            # Clear results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Starting Reddit scraper...\n")
            self.results_text.insert(tk.END, f"- Collecting up to {max_leads} leads\n")
            self.results_text.insert(tk.END, f"- Checking {len(subreddits)} subreddits: {', '.join(subreddits)}\n")
            self.results_text.insert(tk.END, f"- Using {len(keywords)} keywords: {', '.join(keywords)}\n")
            self.results_text.insert(tk.END, f"- Time filter: {self.time_filter_var.get()}\n\n")
            self.results_text.insert(tk.END, "This might take several minutes. Please be patient...\n")
            self.results_text.update()
            
            # Run in background thread
            self.app.run_thread(
                self._run_scraper,
                kwargs={
                    "subreddits": subreddits,
                    "keywords": keywords,
                    "time_filter": self.time_filter_var.get(),
                    "max_leads": max_leads
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error starting Reddit scraper: {e}")
            messagebox.showerror("Error", f"Failed to start scraper: {e}")
    
    def _run_scraper(self, subreddits, keywords, time_filter, max_leads):
        """Run the Reddit scraper"""
        try:
            # First check if scrapers module can be imported
            if importlib.util.find_spec("scrapers.reddit.scraper") is None:
                self.results_text.insert(tk.END, "Error: Reddit scraper module not found.\n")
                return
            
            # Import the scraper module
            from scrapers.reddit.scraper import RedditScraper, run_reddit_scraper
            
            # Log start
            self.logger.info(f"Starting Reddit scrape with {len(subreddits)} subreddits and {len(keywords)} keywords")
            
            # Run the scraper
            scraper = RedditScraper(
                subreddits=subreddits,
                keywords=keywords,
                time_filter=time_filter,
                post_limit=max_leads
            )
            
            # Display scraping status
            def update_status(message):
                self.results_text.insert(tk.END, f"{message}\n")
                self.results_text.see(tk.END)
                self.results_text.update()
            
            update_status("Scraping subreddits...")
            leads = scraper.run_full_scrape(save_csv=True)
            
            # Update results on the main thread
            self.tab.after(0, lambda: self._update_results(leads))
            
        except Exception as e:
            self.logger.error(f"Error in Reddit scraper: {e}")
            self.tab.after(0, lambda: self._show_error(str(e)))
    
    def _update_results(self, leads):
        """Update the results text with scraped leads"""
        self.results_text.insert(tk.END, f"\nCompleted! Collected {len(leads)} leads.\n")
        
        if not leads:
            self.results_text.insert(tk.END, "No leads found.")
            return
        
        self.results_text.insert(tk.END, "\nSample results:\n")
        
        # Show first 5 results as a sample
        for i, lead in enumerate(leads[:5]):
            self.results_text.insert(tk.END, f"\n{i+1}. u/{lead.get('username', 'Unknown')} in r/{lead.get('subreddit', 'Unknown')}\n")
            self.results_text.insert(tk.END, f"   Title: {lead.get('post_title', '')[:100]}...\n")
            self.results_text.insert(tk.END, f"   Matched keywords: {lead.get('matched_keywords', '')}\n")
            self.results_text.insert(tk.END, f"   Score: {lead.get('score', 0)}, Comments: {lead.get('comment_count', 0)}\n")
        
        self.results_text.insert(tk.END, f"\nAll {len(leads)} leads saved to data/reddit_leads.csv\n")
    
    def _show_error(self, error_message):
        """Show error in results area"""
        self.results_text.insert(tk.END, f"\nError: {error_message}\n")
        messagebox.showerror("Reddit Scraper Error", error_message)
    
    def _view_results_file(self):
        """Open the results CSV file"""
        csv_path = os.path.join("data", "reddit_leads.csv")
        if not os.path.exists(csv_path):
            messagebox.showinfo("File Not Found", "No Reddit leads file found. Run the scraper first.")
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