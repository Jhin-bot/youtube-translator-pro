""""
Main entry point for the YouTube Translator Pro application.
Initializes the application, creates the main window, and starts the event loop.
""""

import sys
import os
import logging
from pathlib import Path
try:
    try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    try:
        from PyQt5.QtWidgets import QApplication
    except ImportError:
        raise ImportError("Could not import QApplication from either PyQt6 or PyQt5")

# Add the project root directory to Python path if needed
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import application components
from src.core.application_manager import ApplicationManager
from src.config import APP_NAME, LOG_DIR

# Set up logging configuration
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"{APP_NAME.lower().replace(' ', '_')}_{__name__}.log"

logging.basicConfig()
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    """"
    Initializes the application and starts the main event loop.
    """"
    logger.info(f"Starting {APP_NAME} application...")

    # Create the QApplication instance. This is the foundation of any PyQt application.
    app = QApplication(sys.argv)

    # --- Optional: Create and show splash screen ---
    # Assuming the 'splash' module exists and has a create_splash_screen function
    # The ApplicationManager will handle hiding the splash screen when the main window is ready.
    splash = None
    try:
         from splash import create_splash_screen
         splash = create_splash_screen(app)
         if splash:
              splash.show()
              logger.debug("Splash screen shown.")
              # Process events to ensure the splash screen is displayed immediately
              app.processEvents()
    except ImportError:
         logger.warning("Splash module not found. Skipping splash screen.")
    except Exception as e:
         logger.error(f"Failed to create or show splash screen: {e}", exc_info=True)
         splash = None # Ensure splash is None if creation fails


    # Create the ApplicationManager instance.
    # The ApplicationManager is responsible for coordinating all other parts
    # of the application (UI, batch processing, settings, etc.).
    # Pass the QApplication instance and the splash screen (if created).
    app_manager = ApplicationManager(app, splash=splash)

    # Start the application's main event loop.'
    # The ApplicationManager's run() method will typically show the main window'
    # and then call app.exec() to enter the event loop.
    app_manager.run()

    logger.info(f"{APP_NAME} application finished.")
    # sys.exit() is called implicitly by app.exec() returning


# This block ensures that the main() function is called when the script is executed directly.
if __name__ == '__main__':
    main()