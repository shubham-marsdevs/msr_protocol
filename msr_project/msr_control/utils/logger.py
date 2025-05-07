"""
Logging utility for the MSR Control application.
"""
import logging
import os
from django.conf import settings

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(settings.BASE_DIR, 'logs'), exist_ok=True)

# Configure the logger
logger = logging.getLogger('msr_control')

if not logger.handlers:
    # Set the logging level based on DEBUG setting
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    logger.setLevel(level)
    
    # Create file handler for logging to a file
    file_handler = logging.FileHandler(os.path.join(settings.BASE_DIR, 'logs/msr_control.log'))
    file_handler.setLevel(level)
    
    # Create console handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # Create a formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

def get_logger():
    """
    Returns the configured logger instance.
    """
    return logger
