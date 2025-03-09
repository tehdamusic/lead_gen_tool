# lead_gen/ui/components/widget_factory.py
import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Callable, Dict, Any, List, Optional, Union, Tuple

class WidgetFactory:
    """Factory for creating consistent UI widgets"""
    
    @staticmethod
    def create_title(parent, text: str, font_size: int = 12) -> ttk.Label:
        """Create a title label"""
        title = ttk.Label(parent, text=text, font=("Arial", font_size, "bold"))
        title.pack(pady=10)
        return title
    
    @staticmethod
    def create_form_container(parent, title: str, padding: int = 10) -> ttk.LabelFrame:
        """Create a form container with a title"""
        container = ttk.LabelFrame(parent, text=title, padding=padding)
        container.pack(fill=tk.X, padx=10, pady=10)
        return container
    
    @staticmethod
    def create_entry_row(parent, label_text: str, variable: tk.Variable, 
                       width: int = 30) -> ttk.Entry:
        """Create a labeled entry field in a row"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        label = ttk.Label(frame, text=label_text, width=20, anchor="w")
        label.pack(side=tk.LEFT, padx=5)
        
        entry = ttk.Entry(frame, textvariable=variable, width=width)
        entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        return entry
    
    @staticmethod
    def create_combobox_row(parent, label_text: str, variable: tk.Variable,
                          values: List[str], width: int = 30,
                          on_select: Optional[Callable] = None) -> ttk.Combobox:
        """Create a labeled combobox in a row"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        label = ttk.Label(frame, text=label_text, width=20, anchor="w")
        label.pack(side=tk.LEFT, padx=5)
        
        combo = ttk.Combobox(frame, textvariable=variable, values=values, width=width)
        combo.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        if on_select:
            combo.bind("<<ComboboxSelected>>", on_select)
            
        return combo
    
    @staticmethod
    def create_checkbox_row(parent, text: str, variable: tk.BooleanVar) -> ttk.Checkbutton:
        """Create a checkbox in a row"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        checkbox = ttk.Checkbutton(frame, text=text, variable=variable)
        checkbox.pack(side=tk.LEFT, padx=5)
        
        return checkbox
    
    @staticmethod
    def create_button_row(parent, buttons: List[Dict[str, Any]]) -> List[ttk.Button]:
        """Create a row of buttons"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=10)
        
        created_buttons = []
        for btn_config in buttons:
            btn = ttk.Button(
                frame,
                text=btn_config.get("text", "Button"),
                command=btn_config.get("command"),
                width=btn_config.get("width", 15)
            )
            btn.pack(side=tk.LEFT, padx=5)
            created_buttons.append(btn)
            
        return created_buttons
    
    @staticmethod
    def create_results_area(parent, title: str) -> Tuple[ttk.LabelFrame, scrolledtext.ScrolledText]:
        """Create a scrollable results area with a title"""
        container = ttk.LabelFrame(parent, text=title, padding=10)
        container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        results = scrolledtext.ScrolledText(container, height=15)
        results.pack(fill=tk.BOTH, expand=True)
        
        return container, results