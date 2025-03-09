# lead_gen/ui/views/message_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
import importlib.util

from lead_gen.ui.components.widget_factory import WidgetFactory

class MessageView:
    """Message generation view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.config = app.config
        self.logger = logging.getLogger("message_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Message Generator")
        
        # Create variables
        self.model_var = tk.StringVar(value=self.config.openai_model)
        self.max_linkedin_var = tk.StringVar(value="10")
        self.max_reddit_var = tk.StringVar(value="10")
        
        # Initialize UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title
        WidgetFactory.create_title(self.tab, "Generate Personalized Outreach Messages")
        
        # Form container
        form = WidgetFactory.create_form_container(self.tab, "Generator Settings")
        
        # AI model
        WidgetFactory.create_combobox_row(
            form, "AI Model:", self.model_var,
            values=["gpt-4", "gpt-3.5-turbo"],
            width=15
        )
        
        # Max LinkedIn messages
        WidgetFactory.create_entry_row(
            form, "Max LinkedIn Messages:", self.max_linkedin_var, width=10)
        
        # Max Reddit messages
        WidgetFactory.create_entry_row(
            form, "Max Reddit Messages:", self.max_reddit_var, width=10)
        
        # Start button
        WidgetFactory.create_button_row(form, [
            {"text": "Generate Messages", "command": self._start_generation, "width": 20}
        ])
        
        # Results area
        _, self.results_text = WidgetFactory.create_results_area(
            self.tab, "Results")
        
        # Bottom buttons
        WidgetFactory.create_button_row(self.tab, [
            {"text": "View LinkedIn Messages", "command": lambda: self._view_results_file("linkedin")},
            {"text": "View Reddit Messages", "command": lambda: self._view_results_file("reddit")},
            {"text": "Clear Results", "command": self._clear_results}
        ])
    
    def _start_generation(self):
        """Start the message generation process"""
        try:
            # Validate inputs
            try:
                max_linkedin = int(self.max_linkedin_var.get())
                if max_linkedin < 0:
                    raise ValueError("Max LinkedIn messages must be non-negative")
                
                max_reddit = int(self.max_reddit_var.get())
                if max_reddit < 0:
                    raise ValueError("Max Reddit messages must be non-negative")
                
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return
            
            # Check if OpenAI API key is available
            if not self.config.openai_api_key:
                messagebox.showerror(
                    "Missing API Key", 
                    "OpenAI API key is required for message generation. Please check your .env file."
                )
                return
            
            # Clear results
            self.results_text.delete(1.0, tk.END)
            self.results_text.insert(tk.END, "Starting message generation...\n")
            self.results_text.insert(tk.END, f"- Max LinkedIn messages: {max_linkedin}\n")
            self.results_text.insert(tk.END, f"- Max Reddit messages: {max_reddit}\n")
            self.results_text.insert(tk.END, f"- AI model: {self.model_var.get()}\n")
            self.results_text.insert(tk.END, "\nGenerating personalized messages. Please be patient...\n")
            self.results_text.update()
            
            # Run in background thread
            self.app.run_thread(
                self._run_generator,
                kwargs={
                    "max_linkedin": max_linkedin,
                    "max_reddit": max_reddit,
                    "model": self.model_var.get()
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error starting message generator: {e}")
            messagebox.showerror("Error", f"Failed to start message generator: {e}")
    
    def _run_generator(self, max_linkedin, max_reddit, model):
        """Run the message generator"""
        try:
            # First check if message_generator module can be imported
            if importlib.util.find_spec("communication.message_generator") is None:
                self.results_text.insert(tk.END, "Error: Message generator module not found.\n")
                return
            
            # Import the message generator
            from communication.message_generator import run_message_generator
            
            # Log start
            self.logger.info(f"Starting message generation with model {model}")
            
            # Run the generator
            results = run_message_generator(
                sheets_client=None,  # We're not using sheets client directly in the UI
                max_linkedin_leads=max_linkedin,
                max_reddit_leads=max_reddit,
                model=model
            )
            
            # Update results on the main thread
            self.tab.after(0, lambda: self._update_results(results))
            
        except Exception as e:
            self.logger.error(f"Error in message generator: {e}")
            self.tab.after(0, lambda: self._show_error(str(e)))
    
    def _update_results(self, results):
        """Update the results text with message generation data"""
        linkedin_processed = results.get('linkedin_leads_processed', 0)
        reddit_processed = results.get('reddit_leads_processed', 0)
        linkedin_generated = results.get('linkedin_messages_generated', 0)
        reddit_generated = results.get('reddit_messages_generated', 0)
        total_generated = results.get('total_messages_generated', 0)
        
        self.results_text.insert(tk.END, f"\nMessage generation completed!\n")
        self.results_text.insert(tk.END, f"- LinkedIn leads processed: {linkedin_processed}\n")
        self.results_text.insert(tk.END, f"- LinkedIn messages generated: {linkedin_generated}\n")
        self.results_text.insert(tk.END, f"- Reddit leads processed: {reddit_processed}\n")
        self.results_text.insert(tk.END, f"- Reddit messages generated: {reddit_generated}\n")
        self.results_text.insert(tk.END, f"- Total messages generated: {total_generated}\n")
        
        if linkedin_processed > 0:
            success_rate = (linkedin_generated / linkedin_processed) * 100
            self.results_text.insert(tk.END, f"- LinkedIn success rate: {success_rate:.1f}%\n")
        
        if reddit_processed > 0:
            success_rate = (reddit_generated / reddit_processed) * 100
            self.results_text.insert(tk.END, f"- Reddit success rate: {success_rate:.1f}%\n")
        
        self.results_text.insert(tk.END, "\nGenerated messages have been saved to:\n")
        self.results_text.insert(tk.END, "- data/output/linkedin_messages.csv\n")
        self.results_text.insert(tk.END, "- data/output/reddit_messages.csv\n")
    
    def _show_error(self, error_message):
        """Show error in results area"""
        self.results_text.insert(tk.END, f"\nError: {error_message}\n")
        messagebox.showerror("Message Generator Error", error_message)
    
    def _view_results_file(self, source):
        """Open the results CSV file"""
        if source == "linkedin":
            csv_path = os.path.join("data", "output", "linkedin_messages.csv")
        else:
            csv_path = os.path.join("data", "output", "reddit_messages.csv")
            
        if not os.path.exists(csv_path):
            messagebox.showinfo(
                "File Not Found", 
                f"No {source} messages file found. Run the generator first."
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