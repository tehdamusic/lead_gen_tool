# lead_gen/ui/views/scoring_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
import importlib.util

from lead_gen.ui.components.widget_factory import WidgetFactory

class ScoringView:
    """Lead scoring view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.config = app.config
        self.logger = logging.getLogger("scoring_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Lead Scoring")
        
        # Create variables
        self.use_ai_var = tk.BooleanVar(value=self.config.use_ai)
        self.threshold_var = tk.StringVar(value="0.5")
        self.max_linkedin_var = tk.StringVar(value="50")
        self.max_reddit_var = tk.StringVar(value="50")
        self.model_var = tk.StringVar(value=self.config.openai_model)
        
        # Initialize UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title
        WidgetFactory.create_title(self.tab, "Score and Qualify Leads")
        
        # Form container
        form = WidgetFactory.create_form_container(self.tab, "Scoring Settings")
        
        # Use AI option
        WidgetFactory.create_checkbox_row(
            form, "Use AI for Advanced Scoring (requires OpenAI API key)", self.use_ai_var)
        
        # AI Model
        WidgetFactory.create_combobox_row(
            form, "AI Model:", self.model_var,
            values=["gpt-4", "gpt-3.5-turbo"],
            width=15
        )
        
        # Threshold
        WidgetFactory.create_entry_row(
            form, "Qualification Threshold:", self.threshold_var, width=10)
        ttk.Label(form, text="(0.0 - 1.0, higher is more selective)").pack(padx=5, pady=2)
        
        # Max LinkedIn leads
        WidgetFactory.create_entry_row(
            form, "Max LinkedIn Leads:", self.max_linkedin_var, width=10)
        
        # Max Reddit leads
        WidgetFactory.create_entry_row(
            form, "Max Reddit Leads:", self.max_reddit_var, width=10)
        
        # Start button
        WidgetFactory.create_button_row(form, [
            {"text": "Start Scoring Leads", "command": self._start_scoring, "width": 20}
        ])
        
        # Results area
        _, self.results_text = WidgetFactory.create_results_area(
            self.tab, "Results")
        
        # Bottom buttons
        WidgetFactory.create_button_row(self.tab, [
            {"text": "View LinkedIn Scores", "command": lambda: self._view_results_file("linkedin")},
            {"text": "View Reddit Scores", "command": lambda: self._view_results_file("reddit")},
            {"text": "Clear Results", "command": self._clear_results}
        ])
    
    def _start_scoring(self):
        """Start the lead scoring process"""
        try:
            # Validate inputs
            try:
                threshold = float(self.threshold_var.get())
                if threshold < 0 or threshold > 1:
                    raise ValueError("Threshold must be between 0.0 and 1.0")
                
                max_linkedin = int(self.max_linkedin_var.get())
                if max_linkedin < 0:
                    raise ValueError("Max LinkedIn leads must be non-negative")
                
                max_reddit = int(self.max_reddit_var.get())
                if max_reddit < 0:
                    raise ValueError("Max Reddit leads must be non-negative")
                
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return
            
            # Check if OpenAI API key is available if AI is enabled
            if self.use_ai_var.get() and not self.config.openai_api_key:
                messagebox.showerror(
                    "Missing API Key", 
                    "OpenAI API key is required for AI scoring. Please check your .env file."
                )
                return
            
            # Clear results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Starting lead scoring...\n")
            self.results_text.insert(tk.END, f"- Qualification threshold: {threshold}\n")
            self.results_text.insert(tk.END, f"- Max LinkedIn leads: {max_linkedin}\n")
            self.results_text.insert(tk.END, f"- Max Reddit leads: {max_reddit}\n")
            self.results_text.insert(tk.END, f"- Using AI analysis: {self.use_ai_var.get()}\n")
            if self.use_ai_var.get():
                self.results_text.insert(tk.END, f"- AI model: {self.model_var.get()}\n")
            self.results_text.insert(tk.END, "\nScoring leads. Please be patient...\n")
            self.results_text.update()
            
            # Run in background thread
            self.app.run_thread(
                self._run_scorer,
                kwargs={
                    "threshold": threshold,
                    "max_linkedin": max_linkedin,
                    "max_reddit": max_reddit,
                    "use_ai": self.use_ai_var.get(),
                    "model": self.model_var.get()
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error starting lead scorer: {e}")
            messagebox.showerror("Error", f"Failed to start lead scorer: {e}")
    
    def _run_scorer(self, threshold, max_linkedin, max_reddit, use_ai, model):
        """Run the lead scorer"""
        try:
            # First check if lead_scorer module can be imported
            if importlib.util.find_spec("analysis.lead_scorer") is None:
                self.results_text.insert(tk.END, "Error: Lead scorer module not found.\n")
                return
            
            # Import the lead scorer
            from analysis.lead_scorer import run_lead_scorer
            
            # Log start
            self.logger.info(f"Starting lead scoring (AI: {use_ai}, Model: {model})")
            
            # Display status
            def update_status(message):
                self.results_text.insert(tk.END, f"{message}\n")
                self.results_text.see(tk.END)
                self.results_text.update()
            
            update_status("Processing leads...")
            
            # Run the scorer
            results = run_lead_scorer(
                sheets_client=None,  # We're not using sheets client directly in the UI
                max_linkedin_leads=max_linkedin,
                max_reddit_leads=max_reddit,
                use_ai_analysis=use_ai,
                model=model,
                threshold=threshold
            )
            
            # Update results on the main thread
            self.tab.after(0, lambda: self._update_results(results))
            
        except Exception as e:
            self.logger.error(f"Error in lead scorer: {e}")
            self.tab.after(0, lambda: self._show_error(str(e)))
    
    def _update_results(self, results):
        """Update the results text with scoring data"""
        linkedin_leads_scored = results.get('linkedin_leads_scored', 0)
        reddit_leads_scored = results.get('reddit_leads_scored', 0)
        total_leads_scored = results.get('total_leads_scored', 0)
        high_priority_leads = results.get('high_priority_leads', 0)
        
        self.results_text.insert(tk.END, f"\nScoring completed!\n")
        self.results_text.insert(tk.END, f"- LinkedIn leads scored: {linkedin_leads_scored}\n")
        self.results_text.insert(tk.END, f"- Reddit leads scored: {reddit_leads_scored}\n")
        self.results_text.insert(tk.END, f"- Total leads scored: {total_leads_scored}\n")
        self.results_text.insert(tk.END, f"- High priority leads: {high_priority_leads}\n")
        
        if total_leads_scored > 0:
            qualification_rate = (high_priority_leads / total_leads_scored) * 100
            self.results_text.insert(tk.END, f"- Qualification rate: {qualification_rate:.1f}%\n")
        
        self.results_text.insert(tk.END, "\nScored leads have been saved to:\n")
        self.results_text.insert(tk.END, "- data/output/scored_linkedin_leads.csv\n")
        self.results_text.insert(tk.END, "- data/output/scored_reddit_leads.csv\n")
    
    def _show_error(self, error_message):
        """Show error in results area"""
        self.results_text.insert(tk.END, f"\nError: {error_message}\n")
        messagebox.showerror("Lead Scoring Error", error_message)
    
    def _view_results_file(self, source):
        """Open the results CSV file"""
        if source == "linkedin":
            csv_path = os.path.join("data", "output", "scored_linkedin_leads.csv")
        else:
            csv_path = os.path.join("data", "output", "scored_reddit_leads.csv")
            
        if not os.path.exists(csv_path):
            messagebox.showinfo(
                "File Not Found", 
                f"No scored {source} leads file found. Run the scorer first."
            )
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