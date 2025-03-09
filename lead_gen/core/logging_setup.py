# lead_gen/core/logging_setup.py
import os
import sys
import logging
from pathlib import Path
from typing import Optional

def setup_logging(log_dir: Path, level: int = logging.INFO, 
                log_to_console: bool = True) -> logging.Logger:
    """
    Configure logging for the application
    
    Args:
        log_dir: Directory for log files
        level: Logging level
        log_to_console: Whether to also log to console
        
    Returns:
        Root logger instance
    """
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplication
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create and add file handler
    file_handler = logging.FileHandler(log_dir / 'lead_generation.log')
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # Create and add console handler if requested
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Create module-specific loggers
    create_module_logger('linkedin', log_dir)
    create_module_logger('reddit', log_dir)
    create_module_logger('lead_scorer', log_dir)
    create_module_logger('message_generator', log_dir)
    create_module_logger('email_reporter', log_dir)
    
    return root_logger

def create_module_logger(name: str, log_dir: Path) -> logging.Logger:
    """
    Create a logger for a specific module
    
    Args:
        name: Module name
        log_dir: Directory for log files
        
    Returns:
        Module logger instance
    """
    logger = logging.getLogger(name)
    
    # Add file handler specific to this module
    file_handler = logging.FileHandler(log_dir / f'{name}.log')
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    )
    logger.addHandler(file_handler)
    
    return logger

def get_ui_log_handler(callback):
    """
    Create a handler that routes logs to the UI
    
    Args:
        callback: Function to call with log message
        
    Returns:
        Custom log handler
    """
    class UILogHandler(logging.Handler):
        def emit(self, record):
            msg = self.format(record)
            callback(msg)
    
    handler = UILogHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    return handler