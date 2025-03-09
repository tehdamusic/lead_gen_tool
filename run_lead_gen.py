#!/usr/bin/env python3
"""
Lead Generation Tool Runner
---------------------------
Runner script for the Lead Generation Tool that provides a command-line interface.
"""

import sys
from pathlib import Path

# Add the project root to Python path to ensure modules can be imported
project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from main import main

if __name__ == "__main__":
    main()
