#!/usr/bin/env python3
"""
Lead Generation Tool - Unified Entry Point
This script provides a unified way to run the lead generation tool,
whether installed as a package or run directly from the source.
"""
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Create required directories
os.makedirs("data", exist_ok=True)
os.makedirs("data/output", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# Check if we should run CLI or GUI
if __name__ == "__main__":
    print("\n================================")
    print("Starting Lead Generation Tool...")
    print("================================\n")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        # Run CLI version
        from main import main
        main()
    else:
        # Run GUI version
        try:
            from lead_gen.ui.app import LeadGenerationApp
            app = LeadGenerationApp()
            app.run()
        except ImportError as e:
            print(f"Failed to start GUI: {e}")
            print("Falling back to CLI mode...")
            from main import main
            main()
