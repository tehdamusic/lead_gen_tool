# lead_gen/ui/views/email_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import logging
import importlib.util

from lead_gen.ui.components.widget_factory import WidgetFactory

class EmailView:
    """Email reporting view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.config = app.config
        self.logger = logging.getLogger("email_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Email Reports")
        
        # Create variables
        self.days_back_var = tk.StringVar(value="1")
        self.response_days_var = tk.StringVar(value="7")
        self.recipient_var = tk.StringVar(value=self.config.email_recipient or self.config.email_address)
        
        # Initialize UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title
        WidgetFactory.create_title(self.tab, "Send Lead Generation Reports by Email")
        
        # Form container
        form = WidgetFactory.create_form_container(self.tab, "Report Settings")
        
        # Days back
        WidgetFactory.create_entry_row(
            form, "Days to look back:", self.days_back_var, width=10)
        
        # Response days
        WidgetFactory.create_entry_row(
            form, "Response days to analyze:", self.response_days_var, width=10)
        
        # Recipient email
        WidgetFactory.create_entry_row(
            form, "Recipient Email:", self.recipient_var, width=30)
        
        # Buttons
        WidgetFactory.create_button_row(form, [
            {"text": "Generate Preview", "command": self._generate_preview, "width": 20},
            {"text": "Send Email Report", "command": self._send_report, "width": 20}
        ])
        
        # Preview area
        _, self.preview_text = WidgetFactory.create_results_area(
            self.tab, "Report Preview")
        
        # Bottom button
        WidgetFactory.create_button_row(self.tab, [
            {"text": "Clear Preview", "command": self._clear_preview}
        ])
    
    def _generate_preview(self):
        """Generate a preview of the email report"""
        try:
            # Validate inputs
            try:
                days_back = int(self.days_back_var.get())
                if days_back < 1:
                    raise ValueError("Days to look back must be at least 1")
                
                response_days = int(self.response_days_var.get())
                if response_days < 1:
                    raise ValueError("Response days must be at least 1")
                
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return
            
            # Clear preview
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, "Generating report preview...\n\n")
            self.preview_text.update()
            
            # Run in background thread
            self.app.run_thread(
                self._generate_preview_thread,
                kwargs={
                    "days_back": days_back,
                    "response_days": response_days
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error generating preview: {e}")
            messagebox.showerror("Error", f"Failed to generate preview: {e}")
    
    def _generate_preview_thread(self, days_back, response_days):
        """Generate preview in a background thread"""
        try:
            # First check if email_reporter module can be imported
            if importlib.util.find_spec("reporting.email_reporter") is None:
                self.preview_text.insert(tk.END, "Error: Email reporter module not found.\n")
                return
            
            # Import the email reporter
            from reporting.email_reporter import EmailReporter
            
            # Log start
            self.logger.info(f"Generating email report preview")
            
            # Create reporter and generate report
            reporter = EmailReporter()
            report_content = reporter.generate_daily_report(
                days_back=days_back,
                response_days=response_days
            )
            
            # Update preview on the main thread
            self.tab.after(0, lambda: self._update_preview(report_content))
            
        except Exception as e:
            self.logger.error(f"Error generating report: {e}")
            self.tab.after(0, lambda: self._show_error(str(e)))
    
    def _send_report(self):
        """Send the email report"""
        try:
            # Validate inputs
            try:
                days_back = int(self.days_back_var.get())
                if days_back < 1:
                    raise ValueError("Days to look back must be at least 1")
                
                response_days = int(self.response_days_var.get())
                if response_days < 1:
                    raise ValueError("Response days must be at least 1")
                
                recipient = self.recipient_var.get().strip()
                if not recipient:
                    raise ValueError("Recipient email is required")
                
            except ValueError as e:
                messagebox.showerror("Input Error", str(e))
                return
            
            # Check email credentials
            if not self.config.email_address or not self.config.email_password:
                messagebox.showerror(
                    "Missing Credentials",
                    "Email address and password are required. Please check your .env file."
                )
                return
            
            # Confirm sending
            confirm = messagebox.askyesno(
                "Confirm",
                f"Send email report to {recipient}?",
                icon="question"
            )
            
            if not confirm:
                return
            
            # Update preview area
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(tk.END, f"Sending email report to {recipient}...\n\n")
            self.preview_text.update()
            
            # Set recipient in env var
            import os
            os.environ["EMAIL_RECIPIENT"] = recipient
            
            # Run in background thread
            self.app.run_thread(
                self._send_report_thread,
                kwargs={
                    "days_back": days_back,
                    "response_days": response_days
                }
            )
        
        except Exception as e:
            self.logger.error(f"Error sending report: {e}")
            messagebox.showerror("Error", f"Failed to send report: {e}")
    
    def _send_report_thread(self, days_back, response_days):
        """Send report in a background thread"""
        try:
            # First check if email_reporter module can be imported
            if importlib.util.find_spec("reporting.email_reporter") is None:
                self.preview_text.insert(tk.END, "Error: Email reporter module not found.\n")
                return
            
            # Import the email reporter
            from reporting.email_reporter import run_email_reporter
            
            # Log start
            self.logger.info(f"Sending email report")
            
            # Run the email reporter
            success = run_email_reporter(
                days_back=days_back,
                response_days=response_days
            )
            
            # Update UI on the main thread
            self.tab.after(0, lambda: self._update_send_result(success))
            
        except Exception as e:
            self.logger.error(f"Error sending report: {e}")
            self.tab.after(0, lambda: self._show_error(str(e)))
    
    def _update_preview(self, content):
        """Update the preview text with the report content"""
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.insert(tk.END, content)
    
    def _update_send_result(self, success):
        """Update the UI with the sending result"""
        if success:
            self.preview_text.insert(tk.END, "\n\n=== Email sent successfully! ===\n")
            messagebox.showinfo("Success", "Email report sent successfully!")
        else:
            self.preview_text.insert(tk.END, "\n\n=== Failed to send email. See logs for details. ===\n")
            messagebox.showerror("Error", "Failed to send email report. Check logs for details.")
    
    def _show_error(self, error_message):
        """Show error in preview area"""
        self.preview_text.insert(tk.END, f"\nError: {error_message}\n")
        messagebox.showerror("Email Reporter Error", error_message)
    
    def _clear_preview(self):
        """Clear the preview text area"""
        self.preview_text.delete(1.0, tk.END)