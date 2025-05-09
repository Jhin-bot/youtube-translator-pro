"""
Main entry point for YouTube Translator Pro when run as a module.
"""

import sys
import os
from pathlib import Path

# Ensure the package's parent directory is in the Python path
package_parent = Path(__file__).parent.parent
if str(package_parent) not in sys.path:
    sys.path.insert(0, str(package_parent))

# Import necessary modules
from src.config import APP_NAME, setup_logging
from src.core.application_manager import ApplicationManager

def main():
    """
    Main entry point function for the application.
    This allows the application to be run as a module: `python -m src`
    or after installation: `youtube-translator-pro`
    """
    # Setup logging
    logger = setup_logging()
    logger.info(f"Starting {APP_NAME} application...")
    
    # Import Qt modules here to avoid circular imports
    from PyQt6.QtWidgets import QApplication
    
    # Create application instance
    app = QApplication(sys.argv)
    
    # Initialize application manager
    app_manager = ApplicationManager(app)
    
    # Start application
    exit_code = app_manager.run()
    
    # Exit with appropriate code
    return exit_code

if __name__ == "__main__":
    sys.exit(main())
