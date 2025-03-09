#!/usr/bin/env python3
"""
GUI File Repair Tool
--------------------
This script analyzes and repairs the lead_gen_gui.py file to fix the
LeadGenerationGUI import error by correctly identifying the actual class name.
"""

import os
import re
import sys
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('gui_repair')

def backup_file(filepath):
    """Create a backup of the specified file."""
    if os.path.exists(filepath):
        backup_path = f"{filepath}.backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
        shutil.copy2(filepath, backup_path)
        logger.info(f"Created backup at {backup_path}")
        print(f"✅ Created backup: {backup_path}")
        return backup_path
    return None

def find_class_names(content):
    """Find all class names defined in the content."""
    # Look for class definitions in the content
    class_pattern = re.compile(r'class\s+(\w+)[\(:]')
    matches = class_pattern.finditer(content)
    
    class_names = []
    class_positions = []
    
    for match in matches:
        class_name = match.group(1)
        position = match.start()
        class_names.append(class_name)
        class_positions.append(position)
    
    return class_names, class_positions

def get_main_gui_class(content, class_names, class_positions):
    """Attempt to identify the main GUI class based on various heuristics."""
    if not class_names:
        return None
    
    # Try various heuristics to identify the main GUI class
    
    # 1. Look for a class with "GUI" in the name
    gui_classes = [name for name in class_names if "GUI" in name]
    if gui_classes:
        return gui_classes[0]
    
    # 2. Look for a class with tkinter/ttk imports nearby
    tk_related_classes = []
    for i, pos in enumerate(class_positions):
        # Extract a section of code around the class definition
        start = max(0, pos - 500)
        section = content[start:pos]
        
        # Check if this section has tkinter imports
        if any(tk_import in section for tk_import in ["tkinter", "ttk", "tk.", "Tk()"]):
            tk_related_classes.append(class_names[i])
    
    if tk_related_classes:
        return tk_related_classes[0]
    
    # 3. Look for the class with __init__ that takes root as parameter
    for i, name in enumerate(class_names):
        # Find the class definition and check its __init__ method
        class_pos = class_positions[i]
        # Get the class content (approximate)
        end_pos = class_positions[i+1] if i+1 < len(class_positions) else len(content)
        class_content = content[class_pos:end_pos]
        
        # Check for __init__ with root parameter
        if re.search(r'def\s+__init__\s*\(\s*self\s*,\s*root', class_content):
            return name
    
    # 4. If all else fails, return the first class that has an __init__ method
    for i, name in enumerate(class_names):
        class_pos = class_positions[i]
        end_pos = class_positions[i+1] if i+1 < len(class_positions) else len(content)
        class_content = content[class_pos:end_pos]
        
        if "__init__" in class_content:
            return name
    
    # 5. Last resort: return the largest class
    if len(class_names) == 1:
        return class_names[0]
    
    # Find the largest class by content size
    largest_class = class_names[0]
    largest_size = 0
    
    for i, name in enumerate(class_names):
        class_pos = class_positions[i]
        end_pos = class_positions[i+1] if i+1 < len(class_positions) else len(content)
        class_size = end_pos - class_pos
        
        if class_size > largest_size:
            largest_size = class_size
            largest_class = name
    
    return largest_class

def analyze_and_fix_gui_file(filepath):
    """Analyze and fix the GUI file to address the import issue."""
    try:
        # Read the file content
        with open(filepath, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check if LeadGenerationGUI is already defined
        if re.search(r'class\s+LeadGenerationGUI[\(:]', content):
            print("✅ LeadGenerationGUI class is already defined")
            
            # Check if there's a syntax error or indentation issue
            if "LeadGenerationGUI" in content and "= LeadGenGUI" in content:
                print("🔍 Found incorrect alias line. Removing it...")
                # Remove the problematic line
                content = re.sub(r'LeadGenerationGUI\s*=\s*LeadGenGUI.*$', '', content, flags=re.MULTILINE)
                
                # Write back the fixed content
                with open(filepath, 'w', encoding='utf-8') as file:
                    file.write(content)
                print("✅ Removed incorrect alias line")
                
            return True
        
        # Find all class definitions
        class_names, class_positions = find_class_names(content)
        
        print(f"📋 Found {len(class_names)} class definitions:")
        for i, name in enumerate(class_names):
            print(f"   {i+1}. {name}")
        
        # Try to identify the main GUI class
        main_class = get_main_gui_class(content, class_names, class_positions)
        
        if main_class:
            print(f"🔍 Identified '{main_class}' as the likely main GUI class")
            
            # First, remove any problematic LeadGenerationGUI alias
            content = re.sub(r'LeadGenerationGUI\s*=\s*\w+.*$', '', content, flags=re.MULTILINE)
            
            # Add the correct alias at the end of the file
            content += f"\n\n# Add alias for the GUI class\nLeadGenerationGUI = {main_class}  # Added by repair tool\n"
            
            # Write back the fixed content
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(content)
            
            print(f"✅ Added alias: LeadGenerationGUI = {main_class}")
            return True
        else:
            print("❌ Could not identify the main GUI class")
            if class_names:
                print("Please specify which class should be used:")
                for i, name in enumerate(class_names):
                    print(f"  {i+1}. {name}")
                
                try:
                    choice = int(input("Enter the number of the correct class: "))
                    if 1 <= choice <= len(class_names):
                        selected_class = class_names[choice-1]
                        
                        # Add the alias
                        content += f"\n\n# Add alias for the GUI class\nLeadGenerationGUI = {selected_class}  # Added by repair tool\n"
                        
                        # Write back the fixed content
                        with open(filepath, 'w', encoding='utf-8') as file:
                            file.write(content)
                        
                        print(f"✅ Added alias: LeadGenerationGUI = {selected_class}")
                        return True
                except (ValueError, IndexError):
                    print("❌ Invalid selection")
            
            return False
            
    except Exception as e:
        logger.error(f"Error analyzing GUI file: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def fix_main_py_import(main_path, actual_class_name):
    """Fix the import in main.py to use the correct class name."""
    try:
        # Read the main file content
        with open(main_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Check the import statement
        import_match = re.search(r'from\s+gui\.lead_gen_gui\s+import\s+LeadGenerationGUI', content)
        if import_match:
            # Change the import to use the actual class name
            new_content = re.sub(
                r'from\s+gui\.lead_gen_gui\s+import\s+LeadGenerationGUI', 
                f'from gui.lead_gen_gui import {actual_class_name} as LeadGenerationGUI', 
                content
            )
            
            # Write back the fixed content
            with open(main_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            
            print(f"✅ Updated main.py to import {actual_class_name} as LeadGenerationGUI")
            return True
        else:
            print("❓ Could not find the GUI import line in main.py")
            return False
            
    except Exception as e:
        logger.error(f"Error fixing main.py: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def create_minimal_gui_file(filepath):
    """Create a minimal working GUI file as a last resort."""
    minimal_content = """import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

class LeadGenerationGUI:
    \"\"\"GUI for the Lead Generation Tool.\"\"\"
    
    def __init__(self, root):
        \"\"\"Initialize the GUI.\"\"\"
        self.root = root
        self.root.title("Lead Generation Tool")
        self.root.geometry("900x600")
        
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        self.create_main_tab()
        self.create_linkedin_tab()
        self.create_reddit_tab()
    
    def create_main_tab(self):
        \"\"\"Create the main tab.\"\"\"
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="Main")
        
        ttk.Label(main_tab, text="Lead Generation Tool", font=("Arial", 16)).pack(pady=20)
        ttk.Button(main_tab, text="Run LinkedIn Scraper", command=self.run_linkedin).pack(pady=10)
        ttk.Button(main_tab, text="Run Reddit Scraper", command=self.run_reddit).pack(pady=10)
    
    def create_linkedin_tab(self):
        \"\"\"Create the LinkedIn tab.\"\"\"
        linkedin_tab = ttk.Frame(self.notebook)
        self.notebook.add(linkedin_tab, text="LinkedIn")
        
        ttk.Label(linkedin_tab, text="LinkedIn Scraper", font=("Arial", 14)).pack(pady=10)
        ttk.Button(linkedin_tab, text="Start Scraping", command=self.run_linkedin).pack(pady=10)
        
        self.linkedin_results = scrolledtext.ScrolledText(linkedin_tab, height=20)
        self.linkedin_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_reddit_tab(self):
        \"\"\"Create the Reddit tab.\"\"\"
        reddit_tab = ttk.Frame(self.notebook)
        self.notebook.add(reddit_tab, text="Reddit")
        
        ttk.Label(reddit_tab, text="Reddit Scraper", font=("Arial", 14)).pack(pady=10)
        ttk.Button(reddit_tab, text="Start Scraping", command=self.run_reddit).pack(pady=10)
        
        self.reddit_results = scrolledtext.ScrolledText(reddit_tab, height=20)
        self.reddit_results.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def run_linkedin(self):
        \"\"\"Run the LinkedIn scraper.\"\"\"
        messagebox.showinfo("LinkedIn", "Starting LinkedIn scraper...")
    
    def run_reddit(self):
        \"\"\"Run the Reddit scraper.\"\"\"
        messagebox.showinfo("Reddit", "Starting Reddit scraper...")

if __name__ == "__main__":
    root = tk.Tk()
    app = LeadGenerationGUI(root)
    root.mainloop()
"""
    try:
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write the minimal GUI file
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(minimal_content)
        
        print(f"✅ Created minimal GUI file at {filepath}")
        return True
    except Exception as e:
        logger.error(f"Error creating minimal GUI file: {str(e)}")
        print(f"❌ Error: {str(e)}")
        return False

def main():
    """Main function to repair the GUI file."""
    print("\n=============================================")
    print("  GUI File Repair Tool")
    print("  ---------------------")
    print("  Fixing LeadGenerationGUI import error")
    print("=============================================\n")
    
    # Default GUI path
    default_gui_path = "gui/lead_gen_gui.py"
    default_main_path = "main.py"
    
    # Get the actual paths from arguments or use defaults
    if len(sys.argv) > 1:
        gui_path = sys.argv[1]
    else:
        # Ask for the path
        gui_path = input(f"Enter the path to the GUI file (default: {default_gui_path}): ").strip() or default_gui_path
    
    # Adjust for Windows backslashes if needed
    gui_path = gui_path.replace('\\', '/')
    
    # Check if file exists
    if not os.path.exists(gui_path):
        print(f"❌ File not found: {gui_path}")
        create_new = input("Would you like to create a new minimal GUI file? (y/n): ")
        if create_new.lower() == 'y':
            create_minimal_gui_file(gui_path)
        return
    
    # Create backup
    backup_path = backup_file(gui_path)
    
    # Analyze and fix the GUI file
    print(f"🔍 Analyzing {gui_path}...")
    fix_result = analyze_and_fix_gui_file(gui_path)
    
    if fix_result:
        print("\n✅ GUI file fixed successfully!")
        print("Please try running your application again")
    else:
        print("\n❌ Could not fix the GUI file automatically")
        print(f"A backup was created at: {backup_path}")
        
        # Offer to create a minimal GUI file
        create_new = input("Would you like to create a minimal working GUI file? (y/n): ")
        if create_new.lower() == 'y':
            if backup_path:
                # Restore backup to avoid confusion
                shutil.copy2(backup_path, gui_path)
                print(f"✅ Restored original file from backup")
            
            # Create a minimal GUI file
            create_minimal_gui_file(gui_path)
    
    print("\n=============================================")

if __name__ == "__main__":
    main()