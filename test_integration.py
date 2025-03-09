#!/usr/bin/env python3
"""
Lead Generation Tool Integration Test
------------------------------------
This script tests the integration between different components of the lead generation tool.
"""

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
    """Test if all modules can be imported correctly."""
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
    """Test if all required directories exist."""
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
    """Test if the main script can be executed without errors."""
    logger.info("Testing script execution...")
    
    try:
        import main
        logger.info("✓ Successfully imported main module")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to import main module: {e}")
        return False

def main():
    """Run all integration tests."""
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
    print("\n" + "=" * 80)
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
