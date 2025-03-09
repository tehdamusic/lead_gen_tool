#!/usr/bin/env python3
"""
Script to fix the missing start_gui function in main.py
"""

import os
import re
import shutil
from datetime import datetime

def backup_file(filepath):
    """Create a backup of a file."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f'{filepath}.bak_{timestamp}'
        shutil.copy2(filepath, backup_file)
        print(f"Created backup of {filepath} as {backup_file}")
        return True
    else:
        print(f"Error: {filepath} file not found!")
        return False

def fix_main_py():
    """Fix the main.py file by properly implementing the start_gui function."""
    main_py_path = 'main.py'
    
    if not os.path.exists(main_py_path):
        print(f"Error: {main_py_path} not found!")
        return False
    
    # Backup the file
    backup_file(main_py_path)
    
    try:
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the main function
        main_func_pattern = r'def main\(\):'
        main_func_match = re.search(main_func_pattern, content)
        
        if not main_func_match:
            print("Could not find main() function in main.py!")
            return False
        
        # Look for the start_gui function
        start_gui_pattern = r'def start_gui\(\):'
        start_gui_match = re.search(start_gui_pattern, content)
        
        # If start_gui is already defined but not properly referenced, this will fix it
        # If start_gui is not defined, we'll add it
        if not start_gui_match:
            # Define the start_gui function
            start_gui_func = """
def start_gui():
    \"\"\"Start the Lead Generation GUI.\"\"\"
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Import gui module and create the GUI application
        from gui.lead_gen_gui import LeadGenerationGUI
        import tkinter as tk
        
        root = tk.Tk()
        app = LeadGenerationGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error starting GUI: {str(e)}")
        print(f"Error starting GUI: {str(e)}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        print("\\nPossible troubleshooting steps:")
        print("1. Check that GUI module exists in the correct location")
        print("2. Ensure all required dependencies are installed (especially tkinter)")
        print("3. Check the import paths in main.py and GUI files")
        sys.exit(1)
"""
            
            # Find a good place to insert the start_gui function
            # Look for other function definitions near the top of the file
            functions_pattern = r'def [a-zA-Z_]+\(\):'
            function_matches = list(re.finditer(functions_pattern, content))
            
            if function_matches:
                # Insert after one of the earlier functions
                insert_idx = function_matches[min(3, len(function_matches)-1)].end()
                # Find the end of this function to insert after it
                next_function_idx = content.find("def ", insert_idx)
                if next_function_idx > 0:
                    # Go back to the previous line break before the next function
                    insert_idx = content.rfind("\n\n", 0, next_function_idx)
                
                # Insert the start_gui function
                new_content = content[:insert_idx] + "\n" + start_gui_func + content[insert_idx:]
            else:
                # If we couldn't find a good spot, add it near the top after imports
                import_section_end = max(content.rfind("import ", 0, 1000), content.rfind("from ", 0, 1000))
                if import_section_end > 0:
                    # Find the end of the import section
                    import_section_end = content.find("\n\n", import_section_end)
                    if import_section_end > 0:
                        new_content = content[:import_section_end] + "\n\n" + start_gui_func + content[import_section_end:]
                    else:
                        # Fall back to adding at the beginning
                        new_content = start_gui_func + "\n\n" + content
                else:
                    # Fall back to adding at the beginning
                    new_content = start_gui_func + "\n\n" + content
        else:
            # If start_gui is already defined but just not found in main(), no changes needed
            print("start_gui function is already defined in main.py")
            new_content = content
        
        # Write the updated content back to the file
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        print(f"✓ Fixed main.py by adding/updating the start_gui function")
        return True
        
    except Exception as e:
        print(f"Error fixing {main_py_path}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the fix script."""
    print("==================================================")
    print("Fixing missing start_gui function in main.py")
    print("==================================================")
    
    success = fix_main_py()
    
    if success:
        print("\nFix applied successfully!")
        print("\nNext steps:")
        print("1. Run the main.py file again:")
        print("   python main.py")
        print("==================================================")
    else:
        print("\nFix failed. You may need to manually add the start_gui function.")
        print("\nAdd this function to main.py:")
        print("""
def start_gui():
    \"\"\"Start the Lead Generation GUI.\"\"\"
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # Import gui module and create the GUI application
        from gui.lead_gen_gui import LeadGenerationGUI
        import tkinter as tk
        
        root = tk.Tk()
        app = LeadGenerationGUI(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Error starting GUI: {str(e)}")
        print(f"Error starting GUI: {str(e)}")
        print(f"Error details: {type(e).__name__}: {str(e)}")
        traceback.print_exc()
        print("\\nPossible troubleshooting steps:")
        print("1. Check that GUI module exists in the correct location")
        print("2. Ensure all required dependencies are installed (especially tkinter)")
        print("3. Check the import paths in main.py and GUI files")
        sys.exit(1)
""")
        print("==================================================")

if __name__ == "__main__":
    main()
