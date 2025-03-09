# lead_gen/__main__.py
#!/usr/bin/env python3
"""
Lead Generation Tool - Main Entry Point
"""
import sys
import os
from pathlib import Path

# Ensure package is importable
package_dir = Path(__file__).parent.parent
if str(package_dir) not in sys.path:
    sys.path.insert(0, str(package_dir))

def main():
    """Main application entry point"""
    print("\n================================")
    print("Starting Lead Generation Tool...")
    print("================================\n")
    
    # Create required directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Start the application
    from lead_gen.ui.app import LeadGenerationApp
    app = LeadGenerationApp()
    app.run()

if __name__ == "__main__":
    main()