"""
Utilities module for YouTube Translator Pro.
Contains helper functions and utility classes used across the application.
"""

import os
import platform
import sys
import logging
import psutil
import socket
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

# Export system information for use in other modules
# This provides the functionality expected from 'src.utils.system_info'
# without needing to create a separate file
system_info = {
    'os': platform.system(),
    'os_version': platform.version(),
    'os_release': platform.release(),
    'python_version': platform.python_version(),
    'python_implementation': platform.python_implementation(),
    'architecture': platform.machine(),
    'processor': platform.processor(),
    'hostname': socket.gethostname(),
    'cpu_count': os.cpu_count(),
    'memory_total': getattr(psutil.virtual_memory(), 'total', 0),
    'timestamp': datetime.now().isoformat()
}

def get_system_info():
    """
    Returns system information dictionary.
    Used to provide compatibility with code expecting a system_info module.
    """
    return system_info

# Make system_info available as if it were imported from src.utils.system_info
# This allows imports like: from src.utils.system_info import system_info to work
sys.modules['src.utils.system_info'] = sys.modules[__name__]

logger.debug(f"System info initialized: {platform.system()} {platform.release()}")

# Validators module functionality
import re
from typing import Any, List, Dict, Optional, Union, Tuple

def is_valid_url(url: str) -> bool:
    """
    Validate if a string is a valid URL.
    """
    url_pattern = re.compile(
        r'^(?:http|https)://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    return bool(url_pattern.match(url))

def is_valid_youtube_url(url: str) -> bool:
    """
    Validate if a string is a valid YouTube URL.
    """
    youtube_patterns = [
        re.compile(r'^(?:https?://)?(?:www\.)?(?:youtube\.com|youtu\.be)/(?:watch\?v=)?([^\s&]+)', re.IGNORECASE),
        re.compile(r'^(?:https?://)?(?:www\.)?youtu\.be/([^\s&]+)', re.IGNORECASE)
    ]
    
    return any(pattern.match(url) for pattern in youtube_patterns)

def is_valid_email(email: str) -> bool:
    """
    Validate if a string is a valid email address.
    """
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_pattern.match(email))

def is_valid_file_path(path: str) -> bool:
    """
    Validate if a string is a valid file path.
    """
    try:
        # Attempt to create a Path object
        from pathlib import Path
        path_obj = Path(path)
        return True
    except Exception:
        return False

def validate_settings(settings: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate application settings dictionary.
    
    Args:
        settings: Dictionary of settings to validate
        
    Returns:
        Tuple of (is_valid, errors)
    """
    errors = []
    
    # Check for required keys
    required_keys = ['language', 'theme', 'auto_update']
    for key in required_keys:
        if key not in settings:
            errors.append(f"Missing required setting: {key}")
    
    # Validate specific settings
    if 'proxy_url' in settings and settings['proxy_url'] and not is_valid_url(settings['proxy_url']):
        errors.append("Invalid proxy URL format")
        
    if 'email' in settings and settings['email'] and not is_valid_email(settings['email']):
        errors.append("Invalid email format")
    
    return (len(errors) == 0, errors)

# Make validators module available
sys.modules['src.utils.validators'] = sys.modules[__name__]
logger.debug("Validators module initialized")

# File operations functionality
import shutil
import tempfile
import hashlib
from pathlib import Path
from typing import Optional, List, Union, Dict, BinaryIO, TextIO, Any, Iterator

def ensure_dir(directory: Union[str, Path]) -> Path:
    """
    Ensure a directory exists and create it if it doesn't.
    
    Args:
        directory: Directory path as string or Path object
        
    Returns:
        Path object of the directory
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory

def safe_delete(path: Union[str, Path]) -> bool:
    """
    Safely delete a file or directory.
    
    Args:
        path: Path to file or directory
        
    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        path = Path(path)
        if path.is_file():
            path.unlink()
        elif path.is_dir():
            shutil.rmtree(path)
        return True
    except Exception as e:
        logger.error(f"Failed to delete {path}: {e}")
        return False
        
def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256', buffer_size: int = 65536) -> str:
    """
    Calculate the hash of a file.
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm to use
        buffer_size: Size of buffer to use when reading file
        
    Returns:
        Hexadecimal string representation of the file hash
    """
    try:
        hash_obj = getattr(hashlib, algorithm)()
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(buffer_size)
                if not data:
                    break
                hash_obj.update(data)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to calculate hash for {file_path}: {e}")
        return ""

def create_temp_file(suffix: Optional[str] = None, prefix: Optional[str] = None, 
                    directory: Optional[Union[str, Path]] = None, text: bool = False) -> Path:
    """
    Create a temporary file and return its path.
    
    Args:
        suffix: File suffix
        prefix: File prefix
        directory: Directory to create the file in
        text: Whether to open the file in text mode
        
    Returns:
        Path object to the temporary file
    """
    if directory is not None:
        directory = str(directory)
    file_handle, file_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=directory, text=text)
    os.close(file_handle)  # Close the file handle
    return Path(file_path)

def find_files(directory: Union[str, Path], pattern: str = "*", recursive: bool = True) -> List[Path]:
    """
    Find files matching a pattern in a directory.
    
    Args:
        directory: Directory to search in
        pattern: Glob pattern to match files
        recursive: Whether to search recursively
        
    Returns:
        List of Path objects for matching files
    """
    directory = Path(directory)
    if recursive:
        return list(directory.glob(f"**/{pattern}"))
    else:
        return list(directory.glob(pattern))

# Make file_operations module available
sys.modules['src.utils.file_operations'] = sys.modules[__name__]
logger.debug("File operations module initialized")

# Logging configuration functionality
import logging.config
import json
from typing import Dict, Any, Optional

def configure_logging(log_level: int = logging.INFO, log_file: Optional[str] = None,
                    log_to_console: bool = True, log_format: Optional[str] = None):
    """
    Configure the logging system with the specified parameters.
    
    Args:
        log_level: Logging level (default: INFO)
        log_file: Path to log file (optional)
        log_to_console: Whether to log to console (default: True)
        log_format: Log format string (optional)
    """
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = {}
    if log_to_console:
        handlers['console'] = {
            'class': 'logging.StreamHandler',
            'level': log_level,
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        }
    
    if log_file:
        handlers['file'] = {
            'class': 'logging.FileHandler',
            'level': log_level,
            'formatter': 'standard',
            'filename': log_file,
            'mode': 'a',
            'encoding': 'utf-8'
        }
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': log_format
            },
        },
        'handlers': handlers,
        'loggers': {
            '': {  # Root logger
                'handlers': list(handlers.keys()),
                'level': log_level,
                'propagate': True
            },
        }
    }
    
    logging.config.dictConfig(config)
    logger.debug(f"Logging configured with level {logging.getLevelName(log_level)}")

def load_logging_config(config_file: str):
    """
    Load logging configuration from a JSON file.
    
    Args:
        config_file: Path to config file in JSON format
    """
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
        logger.debug(f"Logging configuration loaded from {config_file}")
        return True
    except Exception as e:
        logger.error(f"Failed to load logging configuration from {config_file}: {e}")
        return False

def get_logger(name: str, level: Optional[int] = None):
    """
    Get a logger with the specified name and level.
    
    Args:
        name: Logger name
        level: Logging level (optional)
        
    Returns:
        Logger instance
    """
    logger_instance = logging.getLogger(name)
    if level is not None:
        logger_instance.setLevel(level)
    return logger_instance

# Make logging_config module available
sys.modules['src.utils.logging_config'] = sys.modules[__name__]
logger.debug("Logging configuration module initialized")

