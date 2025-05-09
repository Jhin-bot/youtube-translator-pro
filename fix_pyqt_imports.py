"""
Fix PyQt and other import issues in the YouTube Translator Pro codebase.

This script:
1. Adds proper PyQt import fallbacks
2. Fixes missing config imports
3. Resolves module path conflicts
4. Creates stub implementations for missing modules
"""

import os
import re
import sys
import logging
from pathlib import Path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fix_pyqt_imports")

# Common PyQt related fixes
PYQT_IMPORT_FIXES = {
    # Fix nested PyQt6 QtCore imports with proper fallbacks
    r"try:\s*try:\s*try:\s*from PyQt6.QtCore": 
        "try:\n    from PyQt6.QtCore",
        
    # Fix nested PyQt6 QtWidgets imports with proper fallbacks
    r"try:\s*try:\s*from PyQt6.QtWidgets": 
        "try:\n    from PyQt6.QtWidgets",
        
    # Fix nested PyQt6 QtGui imports with proper fallbacks
    r"try:\s*try:\s*from PyQt6.QtGui": 
        "try:\n    from PyQt6.QtGui",
        
    # Fix multi-level nested try-except blocks
    r"except ImportError:\s*from PyQt5.QtCore\s*except ImportError:": 
        "except ImportError:\n    from PyQt5.QtCore",
        
    # Fix multi-level nested try-except blocks for QtWidgets
    r"except ImportError:\s*from PyQt5.QtWidgets\s*except ImportError:": 
        "except ImportError:\n    from PyQt5.QtWidgets",
        
    # Fix multi-level nested try-except blocks for QtGui
    r"except ImportError:\s*from PyQt5.QtGui\s*except ImportError:": 
        "except ImportError:\n    from PyQt5.QtGui",
    
    # Fix Queue import with proper fallbacks
    r"try:\s*from queue import Queue\s*except ImportError:\s*from Queue import Queue": 
        "try:\n    from queue import Queue\nexcept ImportError:\n    from Queue import Queue"
}

# Config module fixes
CONFIG_FIXES = {
    # Add missing config constants if they're referenced but not defined
    "APP_NAME": "'YouTube Translator Pro'",
    "CACHE_DIR": "os.path.join(os.path.expanduser('~'), '.youtube_translator_pro', 'cache')",
    "VERSION": "'1.0.0'",
    "DEBUG": "False",
    "LOG_LEVEL": "logging.INFO",
}

def fix_file(file_path):
    """Apply fixes to a single file."""
    logger.info(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    
    # Apply PyQt import fixes
    for pattern, replacement in PYQT_IMPORT_FIXES.items():
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    # Check if file contains imports from src.config
    if "from src.config import" in content or "import src.config" in content:
        # Add missing constants if they're referenced but not defined in src/config.py
        if file_path.endswith('config.py'):
            for const_name, const_value in CONFIG_FIXES.items():
                if const_name not in content:
                    content += f"\n# Added by import fixer\n{const_name} = {const_value}\n"
    
    # Fix relative imports issues in the src package
    if "src" in file_path:
        if "PerformanceMonitor" in content:
            content = re.sub(
                r"from src\.utils\.performance_monitor import PerformanceMonitor",
                "try:\n    from src.utils.performance_monitor import PerformanceMonitor\nexcept ImportError:\n    # Mock PerformanceMonitor if not available\n    class PerformanceMonitor:\n        def __init__(self, *args, **kwargs):\n            pass\n        def start(self, *args, **kwargs):\n            pass\n        def stop(self, *args, **kwargs):\n            pass",
                content
            )
    
    # Only write to the file if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"Fixed imports in {file_path}")
        return True
    
    return False

def ensure_config_module():
    """Ensure the config module has all required constants."""
    config_path = os.path.join("src", "config.py")
    
    if not os.path.exists(config_path):
        logger.error(f"Config file not found at {config_path}")
        return
    
    logger.info(f"Checking config module at {config_path}")
    
    with open(config_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    missing_constants = []
    
    for const_name, const_value in CONFIG_FIXES.items():
        if const_name not in content:
            missing_constants.append(f"{const_name} = {const_value}")
    
    if missing_constants:
        with open(config_path, 'a', encoding='utf-8') as f:
            f.write("\n# Added by config fixer\n")
            for const in missing_constants:
                f.write(f"{const}\n")
        
        logger.info(f"Added missing constants to {config_path}: {', '.join(const.split(' = ')[0] for const in missing_constants)}")

def create_performance_monitor():
    """Create a performance monitor module if it doesn't exist."""
    perf_monitor_path = os.path.join("src", "utils", "performance_monitor.py")
    
    if not os.path.exists(perf_monitor_path):
        os.makedirs(os.path.dirname(perf_monitor_path), exist_ok=True)
        
        with open(perf_monitor_path, 'w', encoding='utf-8') as f:
            f.write('''"""
Performance monitoring utilities for the application.
"""
import time
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Monitor performance of operations."""
    
    def __init__(self, name=None, log_level=logging.DEBUG):
        self.name = name or "PerformanceMonitor"
        self.log_level = log_level
        self.start_time = None
        self.end_time = None
        self.elapsed_time = None
    
    def start(self, operation_name=None):
        """Start timing an operation."""
        self.operation_name = operation_name or f"{self.name}_operation"
        self.start_time = time.time()
        logger.log(self.log_level, f"Starting {self.operation_name}")
        return self
    
    def stop(self):
        """Stop timing and log the elapsed time."""
        if not self.start_time:
            logger.warning(f"Cannot stop timing for {self.name}, was never started")
            return 0
        
        self.end_time = time.time()
        self.elapsed_time = self.end_time - self.start_time
        logger.log(self.log_level, f"{self.operation_name} completed in {self.elapsed_time:.4f} seconds")
        return self.elapsed_time

def run_with_performance_monitoring(func):
    """Decorator to monitor the performance of a function."""
    def wrapper(*args, **kwargs):
        monitor = PerformanceMonitor(name=func.__name__)
        monitor.start(f"{func.__name__}")
        result = func(*args, **kwargs)
        monitor.stop()
        return result
    return wrapper
''')
        logger.info(f"Created performance monitor module at {perf_monitor_path}")

def main():
    """Main entry point of the script."""
    logger.info("Starting PyQt import fixer...")
    
    # Get Python files in the current directory and subdirectories
    python_files = []
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(python_files)} Python files to process")
    
    # Ensure config module has all necessary constants
    ensure_config_module()
    
    # Create performance monitor if it doesn't exist
    create_performance_monitor()
    
    # Fix imports in all Python files
    fixed_count = 0
    for file_path in python_files:
        if fix_file(file_path):
            fixed_count += 1
    
    logger.info(f"Fixed imports in {fixed_count} files")

if __name__ == "__main__":
    main()