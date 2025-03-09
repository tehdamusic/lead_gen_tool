# lead_gen/ui/views/main_view.py
import tkinter as tk
from tkinter import ttk
import logging

from lead_gen.ui.components.widget_factory import WidgetFactory

class MainView:
    """Main dashboard view"""
    
    def __init__(self, notebook, app):
        self.app = app
        self.logger = logging.getLogger("main_view")
        
        # Create tab
        self.tab = ttk.Frame(notebook)
        notebook.add(self.tab, text="Lead Gen Tasks")
        
        # Initialize UI
        self._create_widgets()
    
    def _create_widgets(self):
        """Create view widgets"""
        # Title area
        title_frame = ttk.Frame(self.tab)
        title_frame.pack(fill=tk.X, pady=20)
        
        ttk.Label(title_frame, text="Peak Transformation Coaching LTD", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(title_frame, text="Professional Lead Generation Tool", 
                 font=("Arial", 12)).pack()
        
        # Divider
        ttk.Separator(self.tab, orient='horizontal').pack(fill=tk.X, padx=20, pady=10)
        
        # Main buttons
        buttons_frame = ttk.Frame(self.tab)
        buttons_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=20)

        tasks = [
            {"text": "LinkedIn Lead Generation", "command": lambda: self.app.show_tab("linkedin")},
            {"text": "Reddit Lead Finder", "command": lambda: self.app.show_tab("reddit")},
            {"text": "Score Leads", "command": lambda: self.app.show_tab("scoring")},
            {"text": "Generate AI Messages", "command": lambda: self.app.show_tab("messages")},
            {"text": "Send Email Report", "command": lambda: self.app.show_tab("email")},
            {"text": "View Logs", "command": lambda: self.app.show_tab("logs")}
        ]
        
        for task in tasks:
            btn = ttk.Button(buttons_frame, text=task["text"], command=task["command"], width=30)
            btn.pack(pady=10)
        
        # Footer
        version = self.app.config.__class__.__module__.split('.')[0]
        ttk.Label(self.tab, text=f"v2.0.0 | © 2025 Peak Transformation Coaching LTD", 
                 font=("Arial", 8)).pack(side=tk.BOTTOM, pady=10)