# lead_gen/ui/views/logs_view.py
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import logging
from pathlib import Path

from lead_gen.ui.components.widget_factory import WidgetFactory

class LogsView:
    """Logs viewer view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.config = app.config
        self.logger = logging.getLogger("logs_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Logs")
        
        # Create variables
        self.log_file_var = tk.StringVar(value="lead_generation.log")
        
        # Initialize UI
        self._create_widgets()
        
        # Load initial logs
        self.refresh_logs()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title
        WidgetFactory.create_title(self.tab, "System Logs")
        
        # Controls frame
        controls = ttk.Frame(self.tab)
        controls.pack(fill=tk.X, padx=10, pady=5)
        
        # Log file selector
        ttk.Label(controls, text="Log file:").pack(side=tk.LEFT, padx=5)
        log_files = self._get_log_files()
        ttk.Combobox(
            controls, 
            textvariable=self.log_file_var,
            values=log_files,
            width=30
        ).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        ttk.Button(
            controls, 
            text="Refresh",
            command=self.refresh_logs
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            controls, 
            text="Clear Log",
            command=self._clear_log_file
        ).pack(side=tk.LEFT, padx=5)
        
        # Log viewer
        log_frame = ttk.LabelFrame(self.tab, text="Log Contents", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, wrap=tk.NONE)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add vertical scrollbar
        v_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=v_scroll.set)
        
        # Add horizontal scrollbar
        h_scroll = ttk.Scrollbar(self.tab, orient=tk.HORIZONTAL, command=self.log_text.xview)
        h_scroll.pack(fill=tk.X, padx=10)
        self.log_text.config(xscrollcommand=h_scroll.set)
    
    def _get_log_files(self):
        """Get list of available log files"""
        log_dir = self.config.log_dir
        if not log_dir.exists():
            return ["lead_generation.log"]
        
        # Get all .log files in the log directory
        log_files = [f.name for f in log_dir.glob("*.log")]
        
        # Ensure lead_generation.log is first if it exists
        if "lead_generation.log" in log_files:
            log_files.remove("lead_generation.log")
            log_files.insert(0, "lead_generation.log")
            
        return log_files
    
    def refresh_logs(self):
        """Refresh the log display"""
        try:
            log_file = self.log_file_var.get()
            log_path = self.config.log_dir / log_file
            
            self.log_text.delete(1.0, tk.END)
            
            if not log_path.exists():
                self.log_text.insert(tk.END, f"Log file {log_file} not found.")
                return
            
            # Read last 1000 lines to avoid loading huge logs
            with open(log_path, "r") as f:
                lines = f.readlines()
                
            if len(lines) > 1000:
                self.log_text.insert(tk.END, f"Log file truncated, showing last 1000 of {len(lines)} lines...\n\n")
                lines = lines[-1000:]
                
            for line in lines:
                self.log_text.insert(tk.END, line)
                
            # Scroll to end
            self.log_text.see(tk.END)
            
        except Exception as e:
            self.logger.error(f"Error refreshing logs: {e}")
            messagebox.showerror("Error", f"Failed to refresh logs: {e}")
    
    def _clear_log_file(self):
        """Clear the current log file"""
        try:
            log_file = self.log_file_var.get()
            log_path = self.config.log_dir / log_file
            
            if not log_path.exists():
                messagebox.showinfo("Info", f"Log file {log_file} not found.")
                return
            
            # Confirm before clearing
            confirm = messagebox.askyesno(
                "Confirm",
                f"Are you sure you want to clear {log_file}?",
                icon="warning"
            )
            
            if not confirm:
                return
                
            # Clear the file
            with open(log_path, "w") as f:
                f.write("")
                
            # Refresh the display
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Log file {log_file} has been cleared.")
            
        except Exception as e:
            self.logger.error(f"Error clearing log file: {e}")
            messagebox.showerror("Error", f"Failed to clear log file: {e}")
    
    def append_log(self, message):
        """Append a log message to the log viewer"""
        # Only append if this is the current log file
        if self.log_file_var.get() == "lead_generation.log":
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)