#!/usr/bin/env python3
"""
Lead Generation Tool Fix Script
------------------------------
This script automatically applies fixes to the lead generation project to resolve
syntax errors, integration issues, and improve error handling.
"""

import os
import sys
import re
import shutil
from pathlib import Path
import subprocess

# Define colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {message} ==={Colors.ENDC}")

def print_success(message):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def backup_file(file_path):
    """Create a backup of a file before modifying it."""
    if not os.path.exists(file_path):
        print_warning(f"File not found: {file_path}")
        return False
    
    backup_path = f"{file_path}.bak"
    shutil.copy2(file_path, backup_path)
    return True

def ensure_directory_exists(directory):
    """Ensure that a directory exists, creating it if necessary."""
    os.makedirs(directory, exist_ok=True)
    return os.path.isdir(directory)

def fix_file(file_path, patterns_and_replacements):
    """
    Apply multiple pattern replacements to a file.
    
    Args:
        file_path: Path to the file to modify
        patterns_and_replacements: List of tuples (pattern, replacement)
    
    Returns:
        True if any changes were made, False otherwise
    """
    if not os.path.exists(file_path):
        print_warning(f"File not found: {file_path}")
        return False
    
    # Read the file content
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply each pattern replacement
    original_content = content
    for pattern, replacement in patterns_and_replacements:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL | re.MULTILINE)
    
    # If content has changed, write it back to the file
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def fix_linkedin_scraper():
    """Fix issues in the LinkedIn scraper module."""
    print_header("Fixing LinkedIn Scraper")
    
    file_path = "scrapers/linkedin/scraper.py"
    if not backup_file(file_path):
        return
    
    patterns_and_replacements = [
        # Fix duplicate exception handler
        (r"return leads\s+except Exception as e:\s+logger\.error\(f\"Error running LinkedIn scraper: \{str\(e\)\}\"\)\s+return \[\]\s+\s+return leads\s+except Exception as e:",
         r"return leads\n    except Exception as e:"),
        # Add missing import for traceback
        (r"import random\nimport logging\nimport csv",
         r"import random\nimport logging\nimport csv\nimport traceback"),
        # Fix potential circular import
        (r"# Import here to avoid circular imports\s+sys\.path\.insert\(0, os\.path\.dirname\(os\.path\.dirname\(os\.path\.dirname\(os\.path\.abspath\(__file__\)\)\)\)\)\s+from utils\.sheets_manager import save_leads_to_sheet",
         r"# Import here to avoid circular imports\n            try:\n                from utils.sheets_manager import save_leads_to_sheet\n            except ImportError:\n                logger.error(\"Could not import save_leads_to_sheet from utils.sheets_manager\")\n                return unique_leads")
    ]
    
    if fix_file(file_path, patterns_and_replacements):
        print_success(f"Fixed issues in {file_path}")
    else:
        print_warning(f"No changes required in {file_path}")

def fix_reporting_init():
    """Fix the issues in reporting/__init__.py."""
    print_header("Fixing Reporting Init Module")
    
    file_path = "reporting/__init__.py"
    if not backup_file(file_path):
        return
    
    # Replace the incomplete class method with proper module initialization
    new_content = """\"\"\"
Reporting modules for the Lead Generation Tool.
\"\"\"

# Import reporting modules
from .email_reporter import EmailReporter, run_email_reporter

__all__ = ['EmailReporter', 'run_email_reporter']
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print_success(f"Fixed issues in {file_path}")

def fix_run_lead_gen():
    """Fix the empty run_lead_gen.py file."""
    print_header("Fixing run_lead_gen.py")
    
    file_path = "run_lead_gen.py"
    if not backup_file(file_path):
        # Create the file if it doesn't exist
        print_warning(f"Creating new {file_path}")
    
    new_content = """#!/usr/bin/env python3
\"\"\"
Lead Generation Tool Runner
---------------------------
Runner script for the Lead Generation Tool that provides a command-line interface.
\"\"\"

import sys
from pathlib import Path

# Add the project root to Python path to ensure modules can be imported
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main import main

if __name__ == "__main__":
    main()
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Make the file executable on Unix systems
    try:
        os.chmod(file_path, 0o755)
    except Exception as e:
        print_warning(f"Could not set executable permission: {e}")
    
    print_success(f"Fixed issues in {file_path}")

def fix_main_py():
    """Fix issues in main.py."""
    print_header("Fixing main.py")
    
    file_path = "main.py"
    if not backup_file(file_path):
        return
    
    # Add missing import for traceback
    pattern1 = r"import os\nimport sys\nimport logging"
    replacement1 = r"import os\nimport sys\nimport logging\nimport traceback"
    
    # Remove duplicate run_reddit_scraper function
    pattern2 = r"def _original_run_reddit_scraper\(args\).*?def run_lead_scorer\(args\)"
    replacement2 = r"def run_lead_scorer(args)"
    
    # Fix start_gui function
    pattern3 = r"def start_gui\(\):\s+\"\"\"Start the Lead Generation GUI.\"\"\"\s+try:.*?sys\.exit\(1\)"
    replacement3 = """def start_gui():
    \"\"\"Start the Lead Generation GUI.\"\"\"
    try:
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        # First try to import the lead_gen GUI
        try:
            from lead_gen.ui.app import LeadGenerationApp
            app = LeadGenerationApp()
            app.run()
        except ImportError:
            # Fall back to the legacy GUI
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
        sys.exit(1)"""
    
    # Ensure directories exist
    pattern4 = r"# Ensure necessary directories exist\nos\.makedirs\('data', exist_ok=True\)\nos\.makedirs\('data/cache', exist_ok=True\)\nos\.makedirs\('data/output', exist_ok=True\)"
    replacement4 = """# Ensure necessary directories exist
def ensure_directories():
    \"\"\"Create all necessary directories for the application.\"\"\"
    directories = [
        'data',
        'data/cache',
        'data/output',
        'logs',
        'debug'
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        
ensure_directories()"""
    
    patterns_and_replacements = [
        (pattern1, replacement1),
        (pattern2, replacement2),
        (pattern3, replacement3),
        (pattern4, replacement4)
    ]
    
    if fix_file(file_path, patterns_and_replacements):
        print_success(f"Fixed issues in {file_path}")
    else:
        print_warning(f"No changes required in {file_path}")

def fix_lead_scorer():
    """Fix issues in the lead scorer module."""
    print_header("Fixing Lead Scorer")
    
    file_path = "analysis/lead_scorer.py"
    if not backup_file(file_path):
        return
    
    # Fix patterns individually to avoid syntax errors
    patterns_and_replacements = [
        # Fix potential division by zero in qualification rate calculation
        (r"if total_leads_scored > 0:\s+qualification_rate = \(high_priority_leads / total_leads_scored\) \* 100",
         r"if total_leads_scored > 0:\n            qualification_rate = (high_priority_leads / total_leads_scored) * 100 if total_leads_scored > 0 else 0"),
        
        # Improve OpenAI API error handling
        (r"except Exception as e:\s+logger\.error\(f\"Error in AI scoring: \{str\(e\)\}\"\)\s+return None",
         """except Exception as e:
            error_msg = str(e)
            if "Rate limit" in error_msg:
                logger.warning(f"OpenAI API rate limit reached: {error_msg}")
                # Sleep and retry could be implemented here
            elif "API key" in error_msg:
                logger.error(f"OpenAI API key issue: {error_msg}")
            else:
                logger.error(f"Error in AI scoring: {error_msg}")
            return None""")
    ]
    
    if fix_file(file_path, patterns_and_replacements):
        print_success(f"Fixed issues in {file_path}")
    else:
        print_warning(f"No changes required in {file_path}")

def fix_message_generator():
    """Fix issues in the message generator module."""
    print_header("Fixing Message Generator")
    
    file_path = "communication/message_generator.py"
    if not backup_file(file_path):
        return
    
    # Simplify OpenAI client initialization pattern
    pattern = r"# Initialize OpenAI client based on available version and capabilities.*?logger\.info\(\"Using legacy OpenAI client \(fallback after error\)\"\)"
    
    replacement = """# Initialize OpenAI client
        try:
            import openai
            self.api_key = os.getenv("OPENAI_API_KEY")
            
            # Check if we're using OpenAI v1.x API
            if hasattr(openai, '__version__') and openai.__version__.startswith('1.'):
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                self.client_version = "v1"
                logger.info("Using OpenAI API v1.x client")
            else:
                # Fallback to legacy API
                openai.api_key = self.api_key
                self.client = openai
                self.client_version = "legacy"
                logger.info("Using OpenAI API legacy client")
                
        except ImportError as e:
            logger.error(f"OpenAI package not installed: {str(e)}")
            raise ValueError("OpenAI package is required for message generation") from e
        except Exception as e:
            logger.error(f"Error initializing OpenAI client: {str(e)}")
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}") from e"""
    
    patterns_and_replacements = [(pattern, replacement)]
    
    if fix_file(file_path, patterns_and_replacements):
        print_success(f"Fixed issues in {file_path}")
    else:
        print_warning(f"No changes required in {file_path}")

def fix_utils_sheets_manager():
    """Fix issues in the Google Sheets manager utility."""
    print_header("Fixing Sheets Manager")
    
    file_path = "utils/sheets_manager.py"
    if not backup_file(file_path):
        return
    
    pattern = r"except Exception as e:\s+logger\.error\(f\"Error saving leads to Google Sheets: \{str\(e\)\}\"\)\s+return False"
    
    replacement = """except gspread.exceptions.APIError as e:
        logger.error(f"Google Sheets API error: {str(e)}")
        return False
    except (ValueError, KeyError) as e:
        logger.error(f"Data formatting error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error saving leads to Google Sheets: {str(e)}")
        return False"""
    
    patterns_and_replacements = [(pattern, replacement)]
    
    if fix_file(file_path, patterns_and_replacements):
        print_success(f"Fixed issues in {file_path}")
    else:
        print_warning(f"No changes required in {file_path}")

def create_integration_test():
    """Create an integration test script."""
    print_header("Creating Integration Test")
    
    file_path = "test_integration.py"
    
    new_content = """#!/usr/bin/env python3
\"\"\"
Lead Generation Tool Integration Test
------------------------------------
This script tests the integration between different components of the lead generation tool.
\"\"\"

import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('integration_test')

def test_imports():
    \"\"\"Test if all modules can be imported correctly.\"\"\"
    logger.info("Testing imports...")
    
    modules = [
        "main",
        "scrapers.linkedin",
        "scrapers.reddit",
        "analysis.lead_scorer",
        "communication.message_generator",
        "reporting.email_reporter",
        "utils.sheets_manager",
        "utils.logging_system"
    ]
    
    success = True
    for module in modules:
        try:
            __import__(module)
            logger.info(f"✓ Successfully imported {module}")
        except ImportError as e:
            logger.error(f"✗ Failed to import {module}: {e}")
            success = False
    
    return success

def test_directory_structure():
    \"\"\"Test if all required directories exist.\"\"\"
    logger.info("Testing directory structure...")
    
    directories = [
        "data",
        "data/output",
        "logs",
        "debug"
    ]
    
    success = True
    for directory in directories:
        if os.path.isdir(directory):
            logger.info(f"✓ Directory exists: {directory}")
        else:
            logger.error(f"✗ Directory missing: {directory}")
            success = False
    
    return success

def test_script_execution():
    \"\"\"Test if the main script can be executed without errors.\"\"\"
    logger.info("Testing script execution...")
    
    try:
        import main
        logger.info("✓ Successfully imported main module")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import main module: {e}")
        return False

def main():
    \"\"\"Run all integration tests.\"\"\"
    print("=" * 80)
    print("LEAD GENERATION TOOL INTEGRATION TEST")
    print("=" * 80)
    
    # Add the current directory to the Python path
    sys.path.insert(0, os.path.abspath('.'))
    
    # Run tests
    import_success = test_imports()
    directory_success = test_directory_structure()
    execution_success = test_script_execution()
    
    # Print summary
    print("\\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Import Test: {'PASS' if import_success else 'FAIL'}")
    print(f"Directory Test: {'PASS' if directory_success else 'FAIL'}")
    print(f"Execution Test: {'PASS' if execution_success else 'FAIL'}")
    print("=" * 80)
    
    # Exit with appropriate code
    if import_success and directory_success and execution_success:
        print("All tests passed!")
        return 0
    else:
        print("Some tests failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    # Make the file executable on Unix systems
    try:
        os.chmod(file_path, 0o755)
    except Exception as e:
        print_warning(f"Could not set executable permission: {e}")
    
    print_success(f"Created integration test: {file_path}")

def main():
    """Apply all fixes to the lead generation project."""
    print_header("LEAD GENERATION TOOL FIX SCRIPT")
    
    # Ensure base directories exist
    ensure_directory_exists("logs")
    ensure_directory_exists("data")
    ensure_directory_exists("data/output")
    ensure_directory_exists("debug")
    
    # Apply fixes
    fix_linkedin_scraper()
    fix_reporting_init()
    fix_run_lead_gen()
    fix_main_py()
    fix_lead_scorer()
    fix_message_generator()
    fix_utils_sheets_manager()
    
    # Create integration test
    create_integration_test()
    
    print_header("FIX SCRIPT COMPLETED")
    print("All fixes have been applied. Run the integration test to verify:")
    print("  python test_integration.py")

if __name__ == "__main__":
    main()