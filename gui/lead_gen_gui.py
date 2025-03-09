import os
import sys
import logging
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, StringVar
from dotenv import load_dotenv
import traceback

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='logs/gui.log'
)
logger = logging.getLogger('lead_gen_gui')

# Load environment variables
load_dotenv()

# Import the LinkedIn scraper from the scrapers package
try:
    # Make sure the parent directory is in the Python path
    import os
    
    # Add the root directory to the path if not already there
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    
    # Now try to import from the modular scrapers package
    from scrapers.linkedin import LinkedInScraper
    logger.info("Successfully imported LinkedInScraper from modular scrapers package")
except ImportError as e:
    logger.error(f"Failed to import LinkedInScraper: {str(e)}")
    messagebox.showerror("Import Error", 
                        f"Could not import LinkedInScraper.\n\nError: {str(e)}\n\n"
                        f"Please ensure the scrapers/linkedin package exists with the necessary files.")

# Import other modules dynamically
try:
    from scrapers.reddit.scraper import RedditScraper, run_reddit_scraper
    from analysis.lead_scorer import LeadScorer, run_lead_scorer
    from communication.message_generator import MessageGenerator, run_message_generator
    from reporting.email_reporter import EmailReporter, run_email_reporter
    from utils.sheets_manager import get_sheets_client
    logger.info("Successfully imported all optional modules")
except ImportError as e:
    logger.warning(f"Optional module import error: {str(e)}")
    # We'll continue even if these modules aren't available
class LeadGenerationGUI:
    # ...

    def create_coaching_tab(self):
        coaching_tab = ttk.Frame(self.notebook)
        self.notebook.add(coaching_tab, text="Coaching")

    """GUI for controlling lead generation tasks."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Peak Transformation Coaching - Lead Generation")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Initialize variables for user input
        self.industry_var = StringVar(value="Technology")
        self.role_var = StringVar(value="CEO")
        self.num_pages_var = StringVar(value="3")
        self.keyword_var = StringVar(value="leadership development")
        
        # Initialize variables for Reddit
        self.reddit_max_leads_var = StringVar(value="50")
        self.reddit_subreddits_var = StringVar(value="Entrepreneur,Productivity,MentalHealth,WorkReform,careerguidance")
        self.reddit_keywords_var = StringVar(value="burnout,work stress,career transition,work-life balance,leadership")
        self.reddit_time_filter_var = StringVar(value="month")
        
        # Initialize variables for lead scoring
        self.use_ai_var = tk.BooleanVar(value=True)
        self.ai_model_var = StringVar(value="gpt-4")
        self.threshold_var = StringVar(value="0.5")
        self.max_linkedin_leads_var = StringVar(value="50")
        self.max_reddit_leads_var = StringVar(value="50")
        
        # Initialize variables for message generation
        self.message_model_var = StringVar(value="gpt-4")
        self.max_linkedin_messages_var = StringVar(value="10")
        self.max_reddit_messages_var = StringVar(value="10")
        
        # Initialize variables for email reporting
        self.days_back_var = StringVar(value="1")
        self.response_days_var = StringVar(value="7")
        self.recipient_email_var = StringVar(value=os.getenv("EMAIL_RECIPIENT", os.getenv("EMAIL_ADDRESS", "")))

        # Initialize LinkedIn Scraper
        self.linkedin_scraper = None
        try:
            if LinkedInScraper is not None:
                self.linkedin_scraper = LinkedInScraper(headless=False)
                logger.info("LinkedIn Scraper initialized")
            else:
                raise ImportError("LinkedInScraper module not found")
        except Exception as e:
            logger.error(f"Failed to initialize LinkedIn Scraper: {str(e)}")
            messagebox.showerror("Initialization Error", f"Failed to initialize LinkedIn Scraper: {str(e)}\n\nPlease ensure all LinkedIn scraper modules are in the correct locations.")

        self.create_widgets()
        logger.info("GUI Initialized")
    def create_widgets(self):
        """Create GUI elements."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_main_tab()
        self.create_linkedin_tab()
        self.create_coaching_tab()
        self.create_reddit_tab()
        self.create_lead_scoring_tab()
        self.create_message_tab()
        self.create_email_tab()
        self.create_logs_tab()
    
    def create_main_tab(self):
        """Create controls for running scripts."""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Lead Gen Tasks")

        # Add a logo or title header
        title_frame = ttk.Frame(main_tab)
        title_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(title_frame, text="Peak Transformation Coaching LTD", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(title_frame, text="Professional Lead Generation Tool", 
                 font=("Arial", 12)).pack()
        
        # Divider
        ttk.Separator(main_tab, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Main buttons
        buttons_frame = ttk.Frame(main_tab)
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        ttk.Button(buttons_frame, text="LinkedIn Lead Generation", 
                  command=self.show_linkedin_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Coaching Prospect Finder", 
                  command=self.show_coaching_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Run Reddit Scraper", 
                  command=self.show_reddit_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Score Leads", 
                  command=self.show_lead_scoring_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Generate AI Messages", 
                  command=self.show_message_tab, width=30).pack(pady=10)
        ttk.Button(buttons_frame, text="Send Email Report", 
                  command=self.show_email_tab, width=30).pack(pady=10)
        
        # Footer with version info
        ttk.Label(main_tab, text="v1.2.0 | © 2025 Peak Transformation Coaching LTD", 
                 font=("Arial", 8)).pack(side=tk.BOTTOM, pady=10)
    
    def create_linkedin_tab(self):
        """Create LinkedIn specific controls."""
        linkedin_tab = ttk.Frame(self.notebook)
        self.notebook.add(linkedin_tab, text="LinkedIn Scraper")
        
        # Create form for LinkedIn parameters
        form_frame = ttk.LabelFrame(linkedin_tab, text="Search Parameters", padding=20)
        form_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Industry field
        ttk.Label(form_frame, text="Industry:").grid(row=0, column=0, sticky=tk.W, pady=5)
        industry_entry = ttk.Entry(form_frame, textvariable=self.industry_var, width=30)
        industry_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Industry dropdown suggestions
        ttk.Label(form_frame, text="Suggestions:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        industry_combo = ttk.Combobox(form_frame, values=[
            "Technology", "Finance", "Healthcare", "Education", "Consulting", 
            "Media", "Marketing", "Entrepreneurship", "Human Resources"
        ])
        industry_combo.bind("<<ComboboxSelected>>", 
                          lambda e: self.industry_var.set(industry_combo.get()))
        industry_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Role field
        ttk.Label(form_frame, text="Role:").grid(row=1, column=0, sticky=tk.W, pady=5)
        role_entry = ttk.Entry(form_frame, textvariable=self.role_var, width=30)
        role_entry.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Role dropdown suggestions
        ttk.Label(form_frame, text="Suggestions:").grid(row=1, column=2, sticky=tk.W, pady=5, padx=5)
        role_combo = ttk.Combobox(form_frame, values=[
            "CEO", "CTO", "CFO", "Director", "Manager", "Executive", 
            "VP", "President", "Founder", "Owner", "Leader"
        ])
        role_combo.bind("<<ComboboxSelected>>", 
                      lambda e: self.role_var.set(role_combo.get()))
        role_combo.grid(row=1, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Number of pages
        ttk.Label(form_frame, text="Pages to scrape:").grid(row=2, column=0, sticky=tk.W, pady=5)
        pages_entry = ttk.Entry(form_frame, textvariable=self.num_pages_var, width=10)
        pages_entry.grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Run button
        ttk.Button(form_frame, text="Start Scraping", 
                  command=self.run_linkedin_with_params).grid(row=3, column=0, columnspan=4, pady=20)
        
        # Results frame
        results_frame = ttk.LabelFrame(linkedin_tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.linkedin_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.linkedin_results.pack(fill=tk.BOTH, expand=True)
        
        # Add a save button for results
        button_frame = ttk.Frame(linkedin_tab)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Save Results to CSV", 
                  command=self.save_linkedin_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_linkedin_results).pack(side=tk.LEFT, padx=5)
    def create_coaching_tab(self):
        """Create coaching prospects-specific tab."""
        coaching_tab = ttk.Frame(self.notebook)
        self.notebook.add(coaching_tab, text="Coaching Prospects")
        
        # Header
        ttk.Label(coaching_tab, text="Find Professional Life Coaching Prospects", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(coaching_tab, text="Search Options", padding=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Keyword search
        ttk.Label(options_frame, text="Search Keyword:").grid(row=0, column=0, sticky=tk.W, pady=5)
        keyword_entry = ttk.Entry(options_frame, textvariable=self.keyword_var, width=30)
        keyword_entry.grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Keyword suggestions
        ttk.Label(options_frame, text="Suggestions:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=5)
        keyword_combo = ttk.Combobox(options_frame, values=[
            "leadership development", "career transition", "professional development",
            "work life balance", "burnout", "career growth", "executive coaching"
        ], width=25)
        keyword_combo.bind("<<ComboboxSelected>>", 
                         lambda e: self.keyword_var.set(keyword_combo.get()))
        keyword_combo.grid(row=0, column=3, sticky=tk.W, pady=5, padx=5)
        
        # Search buttons
        buttons_frame = ttk.Frame(options_frame)
        buttons_frame.grid(row=1, column=0, columnspan=4, pady=10)
        
        ttk.Button(buttons_frame, text="Search by Keyword", 
                  command=self.search_coaching_by_keyword).pack(side=tk.LEFT, padx=10)
                  
        ttk.Button(buttons_frame, text="Run Full Coaching Prospect Search", 
                  command=self.run_coaching_prospect_search).pack(side=tk.LEFT, padx=10)
        
        # Results frame
        results_frame = ttk.LabelFrame(coaching_tab, text="Coaching Prospects", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.coaching_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.coaching_results.pack(fill=tk.BOTH, expand=True)
        
        # Actions frame
        actions_frame = ttk.Frame(coaching_tab)
        actions_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(actions_frame, text="Save Prospects to CSV", 
                  command=self.save_coaching_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(actions_frame, text="Clear Results", 
                  command=self.clear_coaching_results).pack(side=tk.LEFT, padx=5)
    
    def create_reddit_tab(self):
        """Create Reddit scraper tab."""
        reddit_tab = ttk.Frame(self.notebook)
        self.notebook.add(reddit_tab, text="Reddit Scraper")
        
        # Header
        ttk.Label(reddit_tab, text="Collect Leads from Reddit", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(reddit_tab, text="Scraper Settings", padding=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Max leads
        ttk.Label(options_frame, text="Max leads to collect:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.reddit_max_leads_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Subreddits
        ttk.Label(options_frame, text="Subreddits:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.reddit_subreddits_var, width=40).grid(row=1, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Subreddit suggestions
        ttk.Label(options_frame, text="Suggestions:").grid(row=2, column=0, sticky=tk.W, pady=5)
        subreddit_combo = ttk.Combobox(options_frame, values=[
            "Entrepreneur,Productivity,MentalHealth",
            "WorkReform,careerguidance,jobs",
            "careeradvice,personalfinance,cscareerquestions",
            "leadership,ExecutiveAssistants,LifeCoaching"
        ], width=40)
        subreddit_combo.bind("<<ComboboxSelected>>", 
                          lambda e: self.reddit_subreddits_var.set(subreddit_combo.get()))
        subreddit_combo.grid(row=2, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Keywords
        ttk.Label(options_frame, text="Keywords:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.reddit_keywords_var, width=40).grid(row=3, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Keyword suggestions
        ttk.Label(options_frame, text="Suggestions:").grid(row=4, column=0, sticky=tk.W, pady=5)
        keyword_combo = ttk.Combobox(options_frame, values=[
            "burnout,work stress,career transition",
            "work-life balance,leadership,feeling lost",
            "overwhelmed,anxiety,career change",
            "quit my job,overworked,toxic workplace"
        ], width=40)
        keyword_combo.bind("<<ComboboxSelected>>", 
                         lambda e: self.reddit_keywords_var.set(keyword_combo.get()))
        keyword_combo.grid(row=4, column=1, columnspan=3, sticky=tk.W+tk.E, pady=5, padx=5)
        
        # Time filter
        ttk.Label(options_frame, text="Time filter:").grid(row=5, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(options_frame, textvariable=self.reddit_time_filter_var, 
                   values=["day", "week", "month", "year", "all"], width=10).grid(row=5, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start button
        ttk.Button(options_frame, text="Start Reddit Scraper", 
                  command=self.run_reddit_scraper).grid(row=6, column=0, columnspan=4, pady=20)
        
        # Results frame
        results_frame = ttk.LabelFrame(reddit_tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.reddit_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.reddit_results.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons for results
        button_frame = ttk.Frame(reddit_tab)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="View Results in CSV", 
                  command=self.view_reddit_results).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_reddit_results).pack(side=tk.LEFT, padx=5)
    def create_lead_scoring_tab(self):
        """Create lead scoring tab."""
        scoring_tab = ttk.Frame(self.notebook)
        self.notebook.add(scoring_tab, text="Lead Scoring")
        
        # Header
        ttk.Label(scoring_tab, text="Score and Qualify Leads", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(scoring_tab, text="Scoring Settings", padding=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # AI Analysis option
        ttk.Checkbutton(options_frame, text="Use AI for Advanced Scoring (requires OpenAI API key)", 
                      variable=self.use_ai_var).grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # AI Model selection
        ttk.Label(options_frame, text="AI Model:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(options_frame, textvariable=self.ai_model_var, 
                   values=["gpt-4", "gpt-3.5-turbo"], width=15).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Threshold
        ttk.Label(options_frame, text="Qualification Threshold:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.threshold_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        ttk.Label(options_frame, text="(0.0 - 1.0, higher is more selective)").grid(row=2, column=2, sticky=tk.W, pady=5)
        
        # LinkedIn leads limit
        ttk.Label(options_frame, text="Max LinkedIn Leads:").grid(row=3, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.max_linkedin_leads_var, width=10).grid(row=3, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Reddit leads limit
        ttk.Label(options_frame, text="Max Reddit Leads:").grid(row=4, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.max_reddit_leads_var, width=10).grid(row=4, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start button
        ttk.Button(options_frame, text="Start Scoring Leads", 
                  command=self.run_lead_scorer).grid(row=5, column=0, columnspan=3, pady=20)
        
        # Results frame
        results_frame = ttk.LabelFrame(scoring_tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.scoring_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.scoring_results.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons for results
        button_frame = ttk.Frame(scoring_tab)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="View Scored Leads", 
                  command=self.view_scored_leads).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_scoring_results).pack(side=tk.LEFT, padx=5)
    
    def create_message_tab(self):
        """Create message generation tab."""
        message_tab = ttk.Frame(self.notebook)
        self.notebook.add(message_tab, text="Message Generator")
        
        # Header
        ttk.Label(message_tab, text="Generate Personalized Outreach Messages", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(message_tab, text="Generator Settings", padding=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # AI Model selection
        ttk.Label(options_frame, text="AI Model:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Combobox(options_frame, textvariable=self.message_model_var, 
                   values=["gpt-4", "gpt-3.5-turbo"], width=15).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # LinkedIn messages limit
        ttk.Label(options_frame, text="Max LinkedIn Messages:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.max_linkedin_messages_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Reddit messages limit
        ttk.Label(options_frame, text="Max Reddit Messages:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.max_reddit_messages_var, width=10).grid(row=2, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Start button
        ttk.Button(options_frame, text="Generate Messages", 
                  command=self.run_message_generator).grid(row=3, column=0, columnspan=2, pady=20)
        
        # Results frame
        results_frame = ttk.LabelFrame(message_tab, text="Results", padding=10)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.message_results = scrolledtext.ScrolledText(results_frame, height=15)
        self.message_results.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons for results
        button_frame = ttk.Frame(message_tab)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="View Generated Messages", 
                  command=self.view_generated_messages).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Results", 
                  command=self.clear_message_results).pack(side=tk.LEFT, padx=5)
    
    def create_email_tab(self):
        """Create email reporting tab."""
        email_tab = ttk.Frame(self.notebook)
        self.notebook.add(email_tab, text="Email Reports")
        
        # Header
        ttk.Label(email_tab, text="Send Lead Generation Reports by Email", 
                 font=("Arial", 12, "bold")).pack(pady=10)
        
        # Options frame
        options_frame = ttk.LabelFrame(email_tab, text="Report Settings", padding=20)
        options_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Days back
        ttk.Label(options_frame, text="Days to look back:").grid(row=0, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.days_back_var, width=10).grid(row=0, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Response days
        ttk.Label(options_frame, text="Response days to analyze:").grid(row=1, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.response_days_var, width=10).grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)
        
        # Recipient email
        ttk.Label(options_frame, text="Recipient Email:").grid(row=2, column=0, sticky=tk.W, pady=5)
        ttk.Entry(options_frame, textvariable=self.recipient_email_var, width=30).grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5, padx=5)
        
        # Start button
        ttk.Button(options_frame, text="Send Email Report", 
                  command=self.run_email_reporter).grid(row=3, column=0, columnspan=3, pady=20)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(email_tab, text="Report Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.email_preview = scrolledtext.ScrolledText(preview_frame, height=15)
        self.email_preview.pack(fill=tk.BOTH, expand=True)
        
        # Add buttons for preview
        button_frame = ttk.Frame(email_tab)
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        ttk.Button(button_frame, text="Generate Preview", 
                  command=self.generate_email_preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Clear Preview", 
                  command=self.clear_email_preview).pack(side=tk.LEFT, padx=5)
    
    def create_logs_tab(self):
        """Create a log viewer tab."""
        logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(logs_tab, text="Logs")
        
        self.log_console = scrolledtext.ScrolledText(logs_tab, height=20)
        self.log_console.pack(fill=tk.BOTH, expand=True)
        
        controls_frame = ttk.Frame(logs_tab)
        controls_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(controls_frame, text="Refresh Logs", 
                  command=self.refresh_logs).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Clear Logs", 
                  command=self.clear_logs).pack(side=tk.LEFT, padx=5)
    def show_linkedin_tab(self):
        """Switch to LinkedIn tab."""
        self.notebook.select(1)  # Adjust index if needed

    def show_coaching_tab(self):
        """Switch to Coaching Prospects tab."""
        self.notebook.select(2)  # Index 2 is the Coaching tab

    def show_reddit_tab(self):
        """Switch to Reddit tab."""
        self.notebook.select(3)  # Index 3 is the Reddit tab

    def show_lead_scoring_tab(self):
        """Switch to Lead Scoring tab."""
        self.notebook.select(4)  # Index 4 is the Lead Scoring tab

    def show_message_tab(self):
        """Switch to Message Generator tab."""
        self.notebook.select(5)  # Index 5 is the Message Generator tab

    def show_email_tab(self):
        """Switch to Email Reports tab."""
        self.notebook.select(6)  # Index 6 is the Email Reports tab
    
    def refresh_logs(self):
        """Refresh log output in the log tab."""
        try:
            if not os.path.exists("logs/gui.log"):
                open("logs/gui.log", "w").close()
            with open("logs/gui.log", "r") as log_file:
                content = log_file.read()
            self.log_console.delete(1.0, tk.END)
            self.log_console.insert(tk.END, content)
        except Exception as e:
            logger.error(f"Failed to load logs: {str(e)}")
    
    def clear_logs(self):
        """Clear the log file."""
        try:
            with open("logs/gui.log", "w") as log_file:
                log_file.write("")
            self.refresh_logs()
            logger.info("Logs cleared")
        except Exception as e:
            logger.error(f"Failed to clear logs: {str(e)}")
    
    def run_task(self, task_func, task_name):
        """Run a task in a separate thread."""
        threading.Thread(target=self.task_wrapper, args=(task_func, task_name), daemon=True).start()
    
    def task_wrapper(self, task_func, task_name):
        """Run a task and handle errors."""
        try:
            logger.info(f"Starting {task_name}...")
            result = task_func()
            logger.info(f"{task_name} completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Error running {task_name}: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Task Error", f"Error running {task_name}: {str(e)}"))
    def run_linkedin_with_params(self):
        """Run LinkedIn scraper with parameters from the form."""
        if not self.linkedin_scraper:
            messagebox.showerror("Error", "LinkedIn scraper not initialized")
            return
        
        industry = self.industry_var.get()
        role = self.role_var.get()
        try:
            num_pages = int(self.num_pages_var.get())
        except ValueError:
            messagebox.showerror("Error", "Number of pages must be a number")
            return
        
        self.linkedin_results.delete(1.0, tk.END)
        self.linkedin_results.insert(tk.END, f"Starting LinkedIn search for {industry} {role}...\n")

        # Run in a separate thread
        self.run_task(
            lambda: self._execute_linkedin_search(industry, role, num_pages),
            f"LinkedIn search for {industry} {role}"
        )

    def _execute_linkedin_search(self, industry, role, num_pages):
        """Execute LinkedIn search and update results."""
        try:
            results = self.linkedin_scraper.scrape_by_industry_and_role(
                industry=industry, 
                role=role, 
                num_pages=num_pages
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._update_linkedin_results(results))
            return results
        except Exception as e:
            logger.error(f"Error in LinkedIn search: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", f"Error: {str(e)}"))

    def _update_linkedin_results(self, results):
        """Update the results text area with search results."""
        self.linkedin_results.delete(1.0, tk.END)
        
        if not results or len(results) == 0:
            self.linkedin_results.insert(tk.END, "No results found.")
            return
        
        self.linkedin_results.insert(tk.END, f"Found {len(results)} profiles:\n\n")
        
        for profile in results:
            name = profile.get('name', 'Unknown')
            headline = profile.get('headline', 'No headline')
            location = profile.get('location', 'Unknown location')
            url = profile.get('profile_url', 'No URL')
            score = profile.get('coaching_fit_score', 0)
            
            self.linkedin_results.insert(tk.END, f"Name: {name}\n")
            self.linkedin_results.insert(tk.END, f"Headline: {headline}\n")
            self.linkedin_results.insert(tk.END, f"Location: {location}\n")
            self.linkedin_results.insert(tk.END, f"Score: {score}/100\n")
            self.linkedin_results.insert(tk.END, f"URL: {url}\n")
            self.linkedin_results.insert(tk.END, "-" * 50 + "\n\n")

    def save_linkedin_results(self):
        """Save LinkedIn results to CSV."""
        messagebox.showinfo("Save", "Results are automatically saved to data/linkedin_leads.csv")
        logger.info("LinkedIn results save function called")

    def clear_linkedin_results(self):
        """Clear LinkedIn results."""
        self.linkedin_results.delete(1.0, tk.END)
        logger.info("LinkedIn results cleared")
    def search_coaching_by_keyword(self):
        """Search LinkedIn for coaching prospects using keyword."""
        if not self.linkedin_scraper:
            messagebox.showerror("Error", "LinkedIn scraper not initialized")
            return
        
        keyword = self.keyword_var.get()
        if not keyword:
            messagebox.showerror("Error", "Please enter a keyword")
            return
        
        self.coaching_results.delete(1.0, tk.END)
        self.coaching_results.insert(tk.END, f"Searching for prospects with keyword: {keyword}...\n")
        
        # Construct search URL
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ', '%20')}&origin=GLOBAL_SEARCH_HEADER"
        
        # Run in a separate thread
        self.run_task(
            lambda: self._execute_keyword_search(search_url),
            f"Coaching prospect search for '{keyword}'"
        )

    def _execute_keyword_search(self, search_url):
        """Execute a keyword search and update results."""
        try:
            results = self.linkedin_scraper.scrape_profiles(
                search_url=search_url,
                num_pages=2
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._update_coaching_results(results))
            return results
        except Exception as e:
            logger.error(f"Error in keyword search: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", f"Error: {str(e)}"))

    def run_coaching_prospect_search(self):
        """Run comprehensive coaching prospect search."""
        if not self.linkedin_scraper:
            messagebox.showerror("Error", "LinkedIn scraper not initialized")
            return
        
        self.coaching_results.delete(1.0, tk.END)
        self.coaching_results.insert(tk.END, "Starting comprehensive coaching prospect search...\n")
        self.coaching_results.insert(tk.END, "This may take several minutes. Please be patient.\n\n")
        
        # Run in a separate thread
        self.run_task(
            lambda: self._execute_comprehensive_search(),
            "Comprehensive coaching prospect search"
        )

    def _execute_comprehensive_search(self):
        """Execute comprehensive search for coaching prospects."""
        try:
            results = self.linkedin_scraper.scrape_for_coaching_leads(
                num_pages=2,
                target_count=30
            )
            
            # Update UI from main thread
            self.root.after(0, lambda: self._update_coaching_results(results))
            return results
        except Exception as e:
            logger.error(f"Error in comprehensive search: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Search Error", f"Error: {str(e)}"))

    def _update_coaching_results(self, results):
        """Update the coaching results text area."""
        self.coaching_results.delete(1.0, tk.END)
        
        if not results or len(results) == 0:
            self.coaching_results.insert(tk.END, "No coaching prospects found.")
            return
        
        self.coaching_results.insert(tk.END, f"Found {len(results)} potential coaching prospects:\n\n")
        
        for profile in results:
            name = profile.get('name', 'Unknown')
            headline = profile.get('headline', 'No headline')
            location = profile.get('location', 'Unknown location')
            url = profile.get('profile_url', 'No URL')
            score = profile.get('coaching_fit_score', 0)
            notes = profile.get('coaching_notes', '')
            
            self.coaching_results.insert(tk.END, f"Name: {name}\n")
            self.coaching_results.insert(tk.END, f"Headline: {headline}\n")
            self.coaching_results.insert(tk.END, f"Location: {location}\n")
            self.coaching_results.insert(tk.END, f"Coaching Fit Score: {score}/100\n")
            if notes:
                self.coaching_results.insert(tk.END, f"Notes: {notes}\n")
            self.coaching_results.insert(tk.END, f"URL: {url}\n")
            self.coaching_results.insert(tk.END, "-" * 50 + "\n\n")

    def save_coaching_results(self):
        """Save coaching results to CSV."""
        messagebox.showinfo("Save", "Results are automatically saved to data/life_coaching_leads.csv")
        logger.info("Coaching results save function called")

    def clear_coaching_results(self):
        """Clear coaching results."""
        self.coaching_results.delete(1.0, tk.END)
        logger.info("Coaching results cleared")
    def run_reddit_scraper(self):
        """Run Reddit scraper with configured parameters."""
        # Check if Reddit scraper can be imported
        try:
            from scrapers.reddit.scraper import run_reddit_scraper
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import Reddit scraper: {str(e)}")
            logger.error(f"Reddit scraper import error: {str(e)}")
            return
        
        try:
            # Parse inputs
            max_leads = int(self.reddit_max_leads_var.get())
            subreddits = [s.strip() for s in self.reddit_subreddits_var.get().split(",") if s.strip()]
            keywords = [k.strip() for k in self.reddit_keywords_var.get().split(",") if k.strip()]
            time_filter = self.reddit_time_filter_var.get()
            
            # Update results area
            self.reddit_results.delete(1.0, tk.END)
            self.reddit_results.insert(tk.END, "Starting Reddit scraper...\n")
            self.reddit_results.insert(tk.END, f"- Collecting up to {max_leads} leads\n")
            self.reddit_results.insert(tk.END, f"- Checking {len(subreddits)} subreddits: {', '.join(subreddits)}\n")
            self.reddit_results.insert(tk.END, f"- Using {len(keywords)} keywords: {', '.join(keywords)}\n")
            self.reddit_results.insert(tk.END, f"- Time filter: {time_filter}\n\n")
            self.reddit_results.insert(tk.END, "This might take several minutes. Please be patient...\n")
            
            # Run in a separate thread
            self.run_task(
                lambda: self._execute_reddit_scraper(max_leads, subreddits, keywords, time_filter),
                "Reddit scraper"
            )
        except ValueError:
            messagebox.showerror("Error", "Max leads must be a number")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Reddit scraper: {str(e)}")
            logger.error(f"Error starting Reddit scraper: {str(e)}")
    
    def _execute_reddit_scraper(self, max_leads, subreddits, keywords, time_filter):
        """Execute the Reddit scraper and update results."""
        try:
            from scrapers.reddit.scraper import run_reddit_scraper
            
            # Run the scraper
            results = run_reddit_scraper(
                sheets_client=None,  # We'll handle Google Sheets separately
                subreddits=subreddits,
                keywords=keywords,
                time_filter=time_filter,
                post_limit=max_leads,
                save_csv=True,
                max_leads=max_leads
            )
            
            # Update UI from the main thread
            self.root.after(0, lambda: self._update_reddit_results(results))
            return results
            
        except Exception as e:
            logger.error(f"Error running Reddit scraper: {str(e)}")
            self.root.after(0, lambda: self._handle_reddit_error(str(e)))
    
    def _update_reddit_results(self, results):
        """Update the results widget with the scraped data."""
        self.reddit_results.insert(tk.END, f"\nCompleted! Collected {len(results)} leads.\n")
        
        if not results:
            self.reddit_results.insert(tk.END, "No leads found.")
            return
        
        self.reddit_results.insert(tk.END, "\nSample results:\n")
        
        # Show first 5 results as a sample
        for i, lead in enumerate(results[:5]):
            self.reddit_results.insert(tk.END, f"\n{i+1}. u/{lead.get('username', 'Unknown')} in r/{lead.get('subreddit', 'Unknown')}\n")
            self.reddit_results.insert(tk.END, f"   Title: {lead.get('post_title', '')[:100]}...\n")
            self.reddit_results.insert(tk.END, f"   Matched keywords: {lead.get('matched_keywords', '')}\n")
            self.reddit_results.insert(tk.END, f"   Score: {lead.get('score', 0)}, Comments: {lead.get('comment_count', 0)}\n")
        
        self.reddit_results.insert(tk.END, f"\nAll {len(results)} leads saved to data/reddit_leads.csv\n")
        
        # Try to upload to Google Sheets
        try:
            from utils.sheets_manager import get_sheets_client, create_sheet_if_not_exists
            
            # Try to get a sheets client
            client = get_sheets_client()
            worksheet = create_sheet_if_not_exists('LeadGenerationData', 'RedditLeads')
            
            # Add header row if worksheet is empty
            if worksheet.row_count <= 1:
                header = ["Username", "Post Title", "Subreddit", "Post URL", "Matched Keywords", 
                         "Score", "Comments", "Created Date", "Added Date"]
                worksheet.append_row(header)
            
            # Prepare data for sheets
            rows = []
            for lead in results:
                row = [
                    lead.get('username', ''),
                    lead.get('post_title', ''),
                    lead.get('subreddit', ''),
                    lead.get('post_url', ''),
                    lead.get('matched_keywords', ''),
                    lead.get('score', 0),
                    lead.get('comment_count', 0),
                    lead.get('created_utc', ''),
                    lead.get('date_added', '')
                ]
                rows.append(row)
            
            # Append to Google Sheet (one by one to avoid rate limits)
            for row in rows:
                worksheet.append_row(row)
                
            self.reddit_results.insert(tk.END, f"\nSuccessfully uploaded leads to Google Sheets.\n")
        except Exception as e:
            logger.error(f"Error uploading to Google Sheets: {str(e)}")
            self.reddit_results.insert(tk.END, f"\nFailed to upload to Google Sheets: {str(e)}\n")
    
    def _handle_reddit_error(self, error_msg):
        """Handle and display errors from the Reddit scraper."""
        self.reddit_results.insert(tk.END, f"\nError running Reddit scraper: {error_msg}\n")
        self.reddit_results.insert(tk.END, "Please check logs for more details.\n")
    
    def view_reddit_results(self):
        """Open the Reddit leads CSV file."""
        csv_path = "data/reddit_leads.csv"
        if os.path.exists(csv_path):
            try:
                # Try to use the default CSV viewer
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{csv_path}"')
                elif sys.platform == 'win32':  # Windows
                    os.startfile(csv_path)
                else:  # Linux
                    os.system(f'xdg-open "{csv_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open CSV file: {str(e)}")
        else:
            messagebox.showinfo("Info", "No Reddit leads CSV found. Run the scraper first.")
    
    def clear_reddit_results(self):
        """Clear Reddit results."""
        self.reddit_results.delete(1.0, tk.END)
        logger.info("Reddit results cleared")
    def run_lead_scorer(self):
        """Run lead scoring with the configured parameters."""
        try:
            from analysis.lead_scorer import run_lead_scorer
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import lead scorer: {str(e)}")
            logger.error(f"Lead scorer import error: {str(e)}")
            return
        
        try:
            # Parse inputs
            threshold = float(self.threshold_var.get())
            max_linkedin_leads = int(self.max_linkedin_leads_var.get())
            max_reddit_leads = int(self.max_reddit_leads_var.get())
            use_ai = self.use_ai_var.get()
            model = self.ai_model_var.get()
            
            # Validate inputs
            if threshold < 0 or threshold > 1:
                messagebox.showerror("Error", "Threshold must be between 0.0 and 1.0")
                return
            
            # Update results area
            self.scoring_results.delete(1.0, tk.END)
            self.scoring_results.insert(tk.END, "Starting lead scoring...\n")
            self.scoring_results.insert(tk.END, f"- Qualification threshold: {threshold}\n")
            self.scoring_results.insert(tk.END, f"- Max LinkedIn leads: {max_linkedin_leads}\n")
            self.scoring_results.insert(tk.END, f"- Max Reddit leads: {max_reddit_leads}\n")
            self.scoring_results.insert(tk.END, f"- Using AI analysis: {use_ai}\n")
            if use_ai:
                self.scoring_results.insert(tk.END, f"- AI model: {model}\n")
            self.scoring_results.insert(tk.END, "\nScoring leads. Please be patient...\n")
            
            # Run in a separate thread
            self.run_task(
                lambda: self._execute_lead_scoring(threshold, max_linkedin_leads, max_reddit_leads, use_ai, model),
                "Lead scoring"
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values. Check threshold and lead limits.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start lead scoring: {str(e)}")
            logger.error(f"Error starting lead scoring: {str(e)}")
    
    def _execute_lead_scoring(self, threshold, max_linkedin_leads, max_reddit_leads, use_ai, model):
        """Execute lead scoring and update results."""
        try:
            from analysis.lead_scorer import run_lead_scorer
            from utils.sheets_manager import get_sheets_client
            
            # Try to get a sheets client
            try:
                sheets_client = get_sheets_client()
            except Exception as e:
                logger.warning(f"Could not connect to Google Sheets: {str(e)}")
                sheets_client = None
            
            # Run the lead scorer
            results = run_lead_scorer(
                sheets_client=sheets_client,
                max_linkedin_leads=max_linkedin_leads,
                max_reddit_leads=max_reddit_leads,
                use_ai_analysis=use_ai,
                model=model,
                threshold=threshold
            )
            
            # Update UI from the main thread
            self.root.after(0, lambda: self._update_scoring_results(results))
            return results
            
        except Exception as e:
            logger.error(f"Error running lead scorer: {str(e)}")
            self.root.after(0, lambda: self._handle_scoring_error(str(e)))
    
    def _update_scoring_results(self, results):
        """Update the results widget with the scoring data."""
        linkedin_leads_scored = results.get('linkedin_leads_scored', 0)
        reddit_leads_scored = results.get('reddit_leads_scored', 0)
        total_leads_scored = results.get('total_leads_scored', 0)
        high_priority_leads = results.get('high_priority_leads', 0)
        
        self.scoring_results.insert(tk.END, f"\nScoring completed!\n")
        self.scoring_results.insert(tk.END, f"- LinkedIn leads scored: {linkedin_leads_scored}\n")
        self.scoring_results.insert(tk.END, f"- Reddit leads scored: {reddit_leads_scored}\n")
        self.scoring_results.insert(tk.END, f"- Total leads scored: {total_leads_scored}\n")
        self.scoring_results.insert(tk.END, f"- High priority leads: {high_priority_leads}\n")
        
        if high_priority_leads > 0:
            qualification_rate = (high_priority_leads / total_leads_scored) * 100 if total_leads_scored > 0 else 0
            self.scoring_results.insert(tk.END, f"- Qualification rate: {qualification_rate:.1f}%\n")
        
        self.scoring_results.insert(tk.END, "\nScored leads have been saved to data/output/scored_linkedin_leads.csv ")
        self.scoring_results.insert(tk.END, "and data/output/scored_reddit_leads.csv\n")
        
        if results.get('success', False):
            self.scoring_results.insert(tk.END, "\nHigh priority leads have been uploaded to Google Sheets.\n")
    
    def _handle_scoring_error(self, error_msg):
        """Handle and display errors from the lead scorer."""
        self.scoring_results.insert(tk.END, f"\nError running lead scorer: {error_msg}\n")
        self.scoring_results.insert(tk.END, "Please check logs for more details.\n")
    
    def view_scored_leads(self):
        """View the scored leads CSV files."""
        linkedin_path = "data/output/scored_linkedin_leads.csv"
        reddit_path = "data/output/scored_reddit_leads.csv"
        
        if os.path.exists(linkedin_path) or os.path.exists(reddit_path):
            try:
                # Show a file selector dialog
                file_options = []
                if os.path.exists(linkedin_path):
                    file_options.append("LinkedIn Leads")
                if os.path.exists(reddit_path):
                    file_options.append("Reddit Leads")
                
                selected_file = messagebox.askquestion("Select File", 
                                                     f"Which scored leads do you want to view?\n\n"
                                                     f"Available files: {', '.join(file_options)}")
                
                if selected_file == "yes":  # Yes means LinkedIn in this context
                    file_path = linkedin_path
                else:
                    file_path = reddit_path
                
                # Try to use the default CSV viewer
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{file_path}"')
                elif sys.platform == 'win32':  # Windows
                    os.startfile(file_path)
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open CSV file: {str(e)}")
        else:
            messagebox.showinfo("Info", "No scored leads CSV found. Run the lead scorer first.")
    
    def clear_scoring_results(self):
        """Clear scoring results."""
        self.scoring_results.delete(1.0, tk.END)
        logger.info("Scoring results cleared")
    def run_message_generator(self):
        """Run message generator with the configured parameters."""
        try:
            from communication.message_generator import run_message_generator
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import message generator: {str(e)}")
            logger.error(f"Message generator import error: {str(e)}")
            return
        
        try:
            # Parse inputs
            max_linkedin_messages = int(self.max_linkedin_messages_var.get())
            max_reddit_messages = int(self.max_reddit_messages_var.get())
            model = self.message_model_var.get()
            
            # Update results area
            self.message_results.delete(1.0, tk.END)
            self.message_results.insert(tk.END, "Starting message generation...\n")
            self.message_results.insert(tk.END, f"- Max LinkedIn messages: {max_linkedin_messages}\n")
            self.message_results.insert(tk.END, f"- Max Reddit messages: {max_reddit_messages}\n")
            self.message_results.insert(tk.END, f"- AI model: {model}\n")
            self.message_results.insert(tk.END, "\nGenerating personalized messages. Please be patient...\n")
            
            # Run in a separate thread
            self.run_task(
                lambda: self._execute_message_generation(max_linkedin_messages, max_reddit_messages, model),
                "Message generation"
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values. Check message limits.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start message generation: {str(e)}")
            logger.error(f"Error starting message generation: {str(e)}")
    
    def _execute_message_generation(self, max_linkedin_messages, max_reddit_messages, model):
        """Execute message generation and update results."""
        try:
            from communication.message_generator import run_message_generator
            from utils.sheets_manager import get_sheets_client
            
            # Try to get a sheets client
            try:
                sheets_client = get_sheets_client()
            except Exception as e:
                logger.warning(f"Could not connect to Google Sheets: {str(e)}")
                sheets_client = None
            
            # Run the message generator
            results = run_message_generator(
                sheets_client=sheets_client,
                max_linkedin_leads=max_linkedin_messages,
                max_reddit_leads=max_reddit_messages,
                model=model
            )
            
            # Update UI from the main thread
            self.root.after(0, lambda: self._update_message_results(results))
            return results
            
        except Exception as e:
            logger.error(f"Error running message generator: {str(e)}")
            self.root.after(0, lambda: self._handle_message_error(str(e)))
    
    def _update_message_results(self, results):
        """Update the results widget with the message generation data."""
        linkedin_processed = results.get('linkedin_leads_processed', 0)
        reddit_processed = results.get('reddit_leads_processed', 0)
        linkedin_generated = results.get('linkedin_messages_generated', 0)
        reddit_generated = results.get('reddit_messages_generated', 0)
        total_generated = results.get('total_messages_generated', 0)
        
        self.message_results.insert(tk.END, f"\nMessage generation completed!\n")
        self.message_results.insert(tk.END, f"- LinkedIn leads processed: {linkedin_processed}\n")
        self.message_results.insert(tk.END, f"- LinkedIn messages generated: {linkedin_generated}\n")
        self.message_results.insert(tk.END, f"- Reddit leads processed: {reddit_processed}\n")
        self.message_results.insert(tk.END, f"- Reddit messages generated: {reddit_generated}\n")
        self.message_results.insert(tk.END, f"- Total messages generated: {total_generated}\n")
        
        if linkedin_generated > 0:
            success_rate = (linkedin_generated / linkedin_processed) * 100 if linkedin_processed > 0 else 0
            self.message_results.insert(tk.END, f"- LinkedIn success rate: {success_rate:.1f}%\n")
        
        if reddit_generated > 0:
            success_rate = (reddit_generated / reddit_processed) * 100 if reddit_processed > 0 else 0
            self.message_results.insert(tk.END, f"- Reddit success rate: {success_rate:.1f}%\n")
        
        self.message_results.insert(tk.END, "\nGenerated messages have been saved to data/output/linkedin_messages.csv ")
        self.message_results.insert(tk.END, "and data/output/reddit_messages.csv\n")
        
        if not results.get('error'):
            self.message_results.insert(tk.END, "\nMessages have been uploaded to Google Sheets.\n")
    
    def _handle_message_error(self, error_msg):
        """Handle and display errors from the message generator."""
        self.message_results.insert(tk.END, f"\nError running message generator: {error_msg}\n")
        self.message_results.insert(tk.END, "Please check logs for more details.\n")
    
    def view_generated_messages(self):
        """View the generated messages CSV files."""
        linkedin_path = "data/output/linkedin_messages.csv"
        reddit_path = "data/output/reddit_messages.csv"
        
        if os.path.exists(linkedin_path) or os.path.exists(reddit_path):
            try:
                # Show a file selector dialog
                file_options = []
                if os.path.exists(linkedin_path):
                    file_options.append("LinkedIn Messages")
                if os.path.exists(reddit_path):
                    file_options.append("Reddit Messages")
                
                selected_file = messagebox.askquestion("Select File", 
                                                     f"Which messages do you want to view?\n\n"
                                                     f"Available files: {', '.join(file_options)}")
                
                if selected_file == "yes":  # Yes means LinkedIn in this context
                    file_path = linkedin_path
                else:
                    file_path = reddit_path
                
                # Try to use the default CSV viewer
                if sys.platform == 'darwin':  # macOS
                    os.system(f'open "{file_path}"')
                elif sys.platform == 'win32':  # Windows
                    os.startfile(file_path)
                else:  # Linux
                    os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open CSV file: {str(e)}")
        else:
            messagebox.showinfo("Info", "No message CSV files found. Run the message generator first.")
    
    def clear_message_results(self):
        """Clear message generation results."""
        self.message_results.delete(1.0, tk.END)
        logger.info("Message results cleared")
    def run_email_reporter(self):
        """Run email reporter with the configured parameters."""
        try:
            from reporting.email_reporter import run_email_reporter
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import email reporter: {str(e)}")
            logger.error(f"Email reporter import error: {str(e)}")
            return
        
        try:
            # Parse inputs
            days_back = int(self.days_back_var.get())
            response_days = int(self.response_days_var.get())
            
            # Email settings
            email_address = os.getenv("EMAIL_ADDRESS")
            email_password = os.getenv("EMAIL_PASSWORD")
            recipient = self.recipient_email_var.get()
            
            if not email_address or not email_password:
                messagebox.showerror("Error", "Email credentials missing. Check your .env file")
                return
            
            # Update preview area
            self.email_preview.delete(1.0, tk.END)
            self.email_preview.insert(tk.END, "Preparing email report...\n")
            self.email_preview.insert(tk.END, f"- Days back for new leads: {days_back}\n")
            self.email_preview.insert(tk.END, f"- Response days to analyze: {response_days}\n")
            self.email_preview.insert(tk.END, f"- Sender email: {email_address}\n")
            self.email_preview.insert(tk.END, f"- Recipient email: {recipient}\n")
            self.email_preview.insert(tk.END, "\nGenerating and sending report. Please wait...\n")
            
            # Update env var if recipient has changed
            if recipient != os.getenv("EMAIL_RECIPIENT", ""):
                os.environ["EMAIL_RECIPIENT"] = recipient
            
            # Run in a separate thread
            self.run_task(
                lambda: self._execute_email_reporter(days_back, response_days),
                "Email reporter"
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values. Check days settings.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start email reporter: {str(e)}")
            logger.error(f"Error starting email reporter: {str(e)}")
    
    def _execute_email_reporter(self, days_back, response_days):
        """Execute email reporter and update results."""
        try:
            from reporting.email_reporter import run_email_reporter, EmailReporter
            from utils.sheets_manager import get_sheets_client
            
            # Try to get a sheets client
            try:
                sheets_client = get_sheets_client()
            except Exception as e:
                logger.warning(f"Could not connect to Google Sheets: {str(e)}")
                sheets_client = None
            
            # First generate a preview of the report
            reporter = EmailReporter()
            report_content = reporter.generate_daily_report(
                days_back=days_back,
                response_days=response_days
            )
            
            # Update UI with the preview
            self.root.after(0, lambda: self._update_email_preview(report_content))
            
            # Run the email sender
            success = run_email_reporter(
                sheets_client=sheets_client,
                days_back=days_back,
                response_days=response_days
            )
            
            # Update UI from the main thread with the result
            self.root.after(0, lambda: self._update_email_results(success))
            return success
            
        except Exception as e:
            logger.error(f"Error running email reporter: {str(e)}")
            self.root.after(0, lambda: self._handle_email_error(str(e)))
    
    def _update_email_preview(self, report_content):
        """Update the preview widget with the report content."""
        self.email_preview.delete(1.0, tk.END)
        self.email_preview.insert(tk.END, report_content)
    
    def _update_email_results(self, success):
        """Update the UI with the email sending result."""
        if success:
            self.email_preview.insert(tk.END, "\n\n=== Email sent successfully! ===\n")
        else:
            self.email_preview.insert(tk.END, "\n\n=== Failed to send email. Check logs for details. ===\n")
    
    def _handle_email_error(self, error_msg):
        """Handle and display errors from the email reporter."""
        self.email_preview.insert(tk.END, f"\nError running email reporter: {error_msg}\n")
        self.email_preview.insert(tk.END, "Please check logs for more details.\n")
    
    def generate_email_preview(self):
        """Generate a preview of the email report without sending it."""
        try:
            from reporting.email_reporter import EmailReporter
        except ImportError as e:
            messagebox.showerror("Import Error", f"Could not import email reporter: {str(e)}")
            logger.error(f"Email reporter import error: {str(e)}")
            return
        
        try:
            # Parse inputs
            days_back = int(self.days_back_var.get())
            response_days = int(self.response_days_var.get())
            
            # Update preview area
            self.email_preview.delete(1.0, tk.END)
            self.email_preview.insert(tk.END, "Generating report preview...\n\n")
            
            # Run in a separate thread
            self.run_task(
                lambda: self._execute_preview_generation(days_back, response_days),
                "Email preview generation"
            )
        except ValueError:
            messagebox.showerror("Error", "Invalid numeric values. Check days settings.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate preview: {str(e)}")
            logger.error(f"Error generating preview: {str(e)}")
    
    def _execute_preview_generation(self, days_back, response_days):
        """Generate a preview of the email report."""
        try:
            from reporting.email_reporter import EmailReporter
            
            # Generate the report
            reporter = EmailReporter()
            report_content = reporter.generate_daily_report(
                days_back=days_back,
                response_days=response_days
            )
            
            # Update UI with the preview
            self.root.after(0, lambda: self._update_email_preview(report_content))
            return report_content
            
        except Exception as e:
            logger.error(f"Error generating email preview: {str(e)}")
            self.root.after(0, lambda: self._handle_email_error(f"Preview generation failed: {str(e)}"))
    
    def clear_email_preview(self):
        """Clear email preview."""
        self.email_preview.delete(1.0, tk.END)
        logger.info("Email preview cleared")


if __name__ == "__main__":
    root = tk.Tk()
    app = LeadGenerationGUI(root)
    root.mainloop()