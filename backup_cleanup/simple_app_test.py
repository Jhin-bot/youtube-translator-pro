""""
Simple test script to verify the basic functionality of the YouTube Translator Pro application.
This will initialize the application without launching the full UI.
""""

import sys
import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("simple_app_test")

# Add the project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

def test_imports():
    """Test importing the basic modules."""
    logger.info("Testing basic imports...")
    
    # Test PyQt import
    try:
        logger.info("Importing PyQt...")
        try:
            try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    from PyQt5.QtWidgets import QApplication
            logger.info("Successfully imported PyQt6")
        except ImportError:
            from PyQt5.QtWidgets import QApplication
            logger.info("Successfully imported PyQt5")
        
        # Create a QApplication instance (needed for any Qt functionality)
        app = QApplication(sys.argv)
        logger.info("Successfully created QApplication instance")
        
        return True
    except Exception as e:
        logger.error(f"Failed to import PyQt: {e}")
        return False

def test_config():
    """Test loading the application configuration."""
    logger.info("Testing configuration...")
    
    try:
        from src.config import APP_NAME, VERSION
        logger.info(f"Successfully loaded configuration: {APP_NAME} v{VERSION}")
        return True
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False

def test_core_components():
    """Test loading core application components."""
    logger.info("Testing core components...")
    
    try:
        # Import just the classes, not instantiate
        from src.core.application_manager import ApplicationManager
        logger.info("Successfully imported ApplicationManager")
        
        # Let's try importing other key modules'
        import cache
        logger.info("Successfully imported cache module")
        
        import transcribe
        logger.info("Successfully imported transcribe module")
        
        import translate
        logger.info("Successfully imported translate module")
        
        logger.info("All core component imports successful")
        return True
    except Exception as e:
        logger.error(f"Failed to import core components: {e}")
        return False

def main():
    """Run the simple application test."""
    logger.info("Starting YouTube Translator Pro simple test...")
    
    results = {
        "PyQt": test_imports(),
        "Config": test_config(),
        "Core Components": test_core_components(),
    }
    
    # Print summary
    logger.info("\n" + "="*50)
    logger.info("TEST RESULTS SUMMARY")
    logger.info("="*50)
    
    for test_name, result in results.items():
        status = "PASSED" if result else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    overall_success = all(results.values())
    logger.info("\nOverall Status: %s", "PASSED" if overall_success else "FAILED")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())
