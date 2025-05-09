"""
Configuration module for YouTube Translator Pro.
Defines constants, paths, and default settings for the application.
"""

import os
import json
import logging
import platform
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Application metadata
APP_NAME = "YouTube Translator Pro"
APP_VERSION = "1.0.0"
VERSION = APP_VERSION  # For compatibility with other modules
APP_AUTHOR = "YouTube Translator Pro Team"
APP_DESCRIPTION = "Professional application for transcribing and translating YouTube videos"
APP_WEBSITE = "https://www.youtubetranslatorpro.com"
APP_REPOSITORY = "https://github.com/youtube-translator-pro/youtube-translator-pro"
APP_ISSUES = "https://github.com/youtube-translator-pro/youtube-translator-pro/issues"
APP_UPDATES_URL = "https://api.youtubetranslatorpro.com/updates.json"

# System information
SYSTEM_INFO = {
    "os": platform.system(),
    "os_version": platform.version(),
    "os_release": platform.release(),
    "python_version": platform.python_version(),
    "architecture": platform.machine(),
    "processor": platform.processor(),
}

# Application paths
APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
RESOURCES_DIR = ROOT_DIR / "resources"
DATA_DIR = Path(os.path.join(Path.home(), f".{APP_NAME.replace(' ', '_').lower()}"))
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = DATA_DIR / "logs"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Ensure necessary directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Advanced logging configuration
def setup_logging(log_level=logging.INFO):
    """Configure advanced logging with file rotation and console output.
    
    Args:
        log_level: The logging level to use (default: logging.INFO)
        
    Returns:
        Logger instance for the calling module
    """
    from logging.handlers import RotatingFileHandler
    import inspect
    
    # Generate timestamp for log filename
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = LOG_DIR / f"{APP_NAME.lower().replace(' ', '_')}_{timestamp}.log"
    
    # Get the caller's module name
    frame = inspect.stack()[1]
    module = inspect.getmodule(frame[0])
    logger_name = module.__name__ if module else __name__
    
    # Configure logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers = []
    
    # Create console handler with custom formatting
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Create file handler with rotation support
    file_handler = RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB max file size
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s'
    )
    file_handler.setFormatter(file_formatter)
    
    # Add both handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Log system information at startup
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    logger.debug(f"System Info: {SYSTEM_INFO}")
    
    return logger

# Initialize logger for this module
logger = setup_logging()

# Alias for backward compatibility
def get_settings():
    """Alias for load_settings for backward compatibility."""
    return load_settings()

# Application paths
APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent
RESOURCES_DIR = ROOT_DIR / "resources"
DATA_DIR = Path(os.path.join(Path.home(), f".{APP_NAME.replace(' ', '_').lower()}"))
CACHE_DIR = DATA_DIR / "cache"
LOG_DIR = DATA_DIR / "logs"
SETTINGS_FILE = DATA_DIR / "settings.json"

# Ensure necessary directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Default settings
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "dark",
    "output_dir": str(Path.home() / "Downloads" / "YouTubeTranslator"),
    "default_model": "small",
    "concurrency": 2,
    "default_language": "None",
    "cache_enabled": True,
    "cache_dir": str(CACHE_DIR),
    "cache_size_mb": 1000,  # 1 GB default cache size
    "cache_ttl": 60 * 60 * 24 * 30,  # 30 days in seconds
    "max_recent_files": 20,
    "update_config": {
        "update_url": "https://api.github.com/repos/youtube-translator-pro/youtube-translator-pro/releases/latest",
        "timeout": 10,
        "verify_ssl": True,
        "check_interval": 24,
        "auto_check": True,
        "retry_delay_hours": 6
    },
    "keyboard_shortcuts": {},
    "max_retries": 3,
    "retry_delay": 5.0,
    "max_retry_delay": 60.0,
}

# Transcription settings
TRANSCRIPTION_MODELS = ["tiny", "base", "small", "medium", "large"]
DEFAULT_TRANSCRIPTION_TIMEOUT = 1800  # 30 minutes max for transcription

# Translation settings
TRANSLATION_LANGUAGES = {
    "None": "None",  # Option to disable translation
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "pt": "Portuguese",
    "ru": "Russian",
    "zh": "Chinese",
}
DEFAULT_TRANSLATION_TIMEOUT = 300  # 5 minutes max for translation

def load_settings() -> Dict[str, Any]:
    """
    Load application settings from the settings file.
    
    Returns:
        Dictionary containing application settings with defaults for missing values.
    """
    try:
        if SETTINGS_FILE.exists():
            with SETTINGS_FILE.open('r', encoding='utf-8') as f:
                settings = json.load(f)
            logger.info(f"Settings loaded from {SETTINGS_FILE}")
            
            # Merge with defaults to handle new settings in updates
            merged_settings = DEFAULT_SETTINGS.copy()
            merged_settings.update(settings)
            return merged_settings
        else:
            logger.info(f"Settings file not found at {SETTINGS_FILE}. Using defaults.")
            return DEFAULT_SETTINGS.copy()
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return DEFAULT_SETTINGS.copy()

def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save application settings to the settings file.
    
    Args:
        settings: Dictionary containing the settings to save.
        
    Returns:
        True if saving was successful, False otherwise.
    """
    try:
        # Ensure settings directory exists
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        with SETTINGS_FILE.open('w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4, sort_keys=True)
        logger.info(f"Settings saved to {SETTINGS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return False
