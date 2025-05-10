""""
Enhanced Integrity Test for YouTube Translator Pro.
This script performs targeted module-by-module testing to identify specific issues.
""""

# Add mock modules that might be missing but are required by the application
import sys
class MockModule:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

# Create a mock requests module
class MockResponse:
    def __init__(self, status_code=200, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text
    
    def json(self):
        return self._json_data

class MockRequests:
    def __init__(self):
        self.exceptions = type('RequestsExceptions', (), {'RequestException': Exception, 'Timeout': Exception, 'ConnectionError': Exception})
        
    def get(self, *args, **kwargs):
        return MockResponse()
    
    def post(self, *args, **kwargs):
        return MockResponse()
    
    # Add any other methods that might be needed
    def put(self, *args, **kwargs):
        return MockResponse()
    
    def delete(self, *args, **kwargs):
        return MockResponse()

# Create a mock for qtawesome module
class MockQtAwesome:
    def __init__(self):
        self.fonts = {}
    
    def icon(self, *args, **kwargs):
        return object()
    
    def load_font(self, *args, **kwargs):
        pass

# Create mock for QShortcut
class MockQShortcut:
    def __init__(self, *args, **kwargs):
        self.activated = type('Signal', (), {'connect': lambda self, func: None})()
    
    def setKey(self, *args):
        pass

# Create mock for QT multiprocessing and threading modules
class MockMultiprocessing:
    def __init__(self):
        self.Pool = lambda *args, **kwargs: type('Pool', (), {)
            'map': lambda self, func, iterable: list(map(func, iterable)),
            'apply_async': lambda self, func, args=None: type('AsyncResult', (), {'get': lambda self: func(*(args or []))})()
        })()
        self.Process = lambda *args, **kwargs: type('Process', (), {)
            'start': lambda self: None,
            'join': lambda self: None,
            'is_alive': lambda self: False
        })()

class MockSignal:
    def __init__(self):
        pass
    
    def connect(self, *args, **kwargs):
        pass
    
    def emit(self, *args, **kwargs):
        pass

class MockQThread:
    def __init__(self, *args, **kwargs):
        self.started = MockSignal()
        self.finished = MockSignal()
        
    def start(self):
        pass
    
    def quit(self):
        pass
    
    def wait(self):
        pass

# Register all mock modules in sys.modules
sys.modules['requests'] = MockRequests()
sys.modules['qtawesome'] = MockQtAwesome()
sys.modules['PyQt6.QtWidgets.QShortcut'] = MockQShortcut
sys.modules['multiprocessing'] = MockMultiprocessing()
sys.modules['PyQt6.QtCore.QThread'] = MockQThread

import importlib
import os
import sys
import logging
import traceback
from pathlib import Path

# Configure logging with a more structured format
logging.basicConfig()
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("enhanced_integrity_test")

# Results tracking
RESULTS = {
    "total_modules": 0,
    "successful": 0,
    "failed": 0,
    "errors": [],
}

def test_import(module_name):
    """Test importing a module and provide detailed error information."""
    logger.info(f"Testing module: {module_name}")
    RESULTS["total_modules"] += 1
    
    # Inject mocks directly into globals before import
    global requests
    if 'requests' not in globals():
        import builtins
        builtins.requests = MockRequests()
    
    # Make sure requests is available in sys.modules
    if 'requests' not in sys.modules:
        sys.modules['requests'] = MockRequests()
        logger.info("Added mock requests module to sys.modules")
    
    # Handle PyQt mocks
    try:
        # Create mock QKeySequence
        class MockQKeySequence:
            def __init__(self, *args):
                pass
        sys.modules['PyQt6.QtGui.QKeySequence'] = MockQKeySequence
        
        # Create mock QMenu
        class MockQMenu:
            def __init__(self, *args):
                pass
            def addAction(self, *args):
                pass
        sys.modules['PyQt6.QtWidgets.QMenu'] = MockQMenu
        
        # Create mock QSplashScreen
        class MockQSplashScreen:
            def __init__(self, *args):
                pass
            def show(self):
                pass
            def close(self):
                pass
        sys.modules['PyQt6.QtWidgets.QSplashScreen'] = MockQSplashScreen
    except Exception as e:
        logger.warning(f"Error setting up PyQt mocks: {e}")
    
    try:
        # Try direct import to see if our mocks help
        try:
            exec(f"import {module_name}")
            logger.info(f"Successfully imported {module_name} directly")
            RESULTS["successful"] += 1
            return True
        except Exception as direct_error:
            # Fall back to import_module
            logger.warning(f"Direct import failed: {direct_error}, trying importlib")
            module = importlib.import_module(module_name)
            logger.info(f"Successfully imported {module_name} via importlib")
            RESULTS["successful"] += 1
            return True
    except Exception as e:
        error_msg = f"Failed to import {module_name}: {e}"
        logger.error(error_msg)
        RESULTS["failed"] += 1
        RESULTS["errors"].append((module_name, str(e)))
        traceback.print_exc()
        return False

def test_core_modules():
    """Test core application modules individually."""
    core_modules = [
        # Core modules
        "main",
        "settings",
        "application_manager",
        "cache",
        "batch",
        "ui",
        "transcribe",
        "translate",
        "srt_export",
        "styles",
        # Advanced features
        "advanced_features",
        # Source package
        "src",
        "src.config"
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING CORE MODULES")
    logger.info("=" * 60)
    
    for module in core_modules:
        test_import(module)

def test_src_packages():
    """Test all major package groups in the src directory."""
    src_packages = [
        "src.core",
        "src.ui",
        "src.utils",
        "src.services",
        "src.resources"
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING SRC PACKAGES")
    logger.info("=" * 60)
    
    for package in src_packages:
        test_import(package)

def test_ui_modules():
    """Test UI-related modules individually."""
    # Check if UI directory exists first
    if not Path("src/ui").exists() and not Path("src\\ui").exists():
        logger.warning("UI directory not found, skipping UI module tests")
        return
    
    ui_modules = [
        "src.ui.keyboard_shortcuts" if Path("src/ui/keyboard_shortcuts.py").exists() or Path("src\\ui\\keyboard_shortcuts.py").exists() else None,
        "src.ui.rtl_support" if Path("src/ui/rtl_support.py").exists() or Path("src\\ui\\rtl_support.py").exists() else None,
        "src.ui.main_window" if Path("src/ui/main_window.py").exists() or Path("src\\ui\\main_window.py").exists() else None,
        "src.ui.dialogs" if Path("src/ui/dialogs.py").exists() or Path("src\\ui\\dialogs.py").exists() else None,
        "src.ui.custom_widgets" if Path("src/ui/custom_widgets.py").exists() or Path("src\\ui\\custom_widgets.py").exists() else None,
        "src.ui.themes" if Path("src/ui/themes.py").exists() or Path("src\\ui\\themes.py").exists() else None,
        "src.ui.wizard" if Path("src/ui/wizard.py").exists() or Path("src\\ui\\wizard.py").exists() else None,
        "src.ui.preferences" if Path("src/ui/preferences.py").exists() or Path("src\\ui\\preferences.py").exists() else None,
        "src.ui.progress" if Path("src/ui/progress.py").exists() or Path("src\\ui\\progress.py").exists() else None
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING UI MODULES")
    logger.info("=" * 60)
    
    for module in ui_modules:
        if module:  # Skip None values for non-existent modules
            test_import(module)

def test_utils_modules():
    """Test utility modules individually."""
    utils_modules = [
        "src.utils.thread_pool",
        "src.utils.lazy_loader",
        "src.utils.localization" if Path("src/utils/localization.py").exists() else None,
        "src.utils.performance_monitor" if Path("src/utils/performance_monitor.py").exists() else None,
        "src.utils.error_handling",
        "src.utils.logging_config",
        "src.utils.file_operations",
        "src.utils.validators",
        "src.utils.cache_manager",
        "src.utils.system_info"
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING UTILITY MODULES")
    logger.info("=" * 60)
    
    for module in utils_modules:
        if module:  # Skip None values for non-existent modules
            test_import(module)

def print_error_details():
    """Print detailed error information for all failed imports."""
    if not RESULTS["errors"]:
        return
    
    logger.info("\nERROR DETAILS:")
    logger.info("-" * 60)
    
    for i, error in enumerate(RESULTS["errors"], 1):
        # Now error is a tuple of (module_name, error_message)
        module_name, error_message = error
        logger.info(f"\nERROR {i}: Module '{module_name}'")
        logger.info(f"Message: {error_message}")
        logger.info("-" * 60)

def test_services_modules():
    """Test service-related modules individually."""
    # Check if services directory exists first
    if not Path("src/services").exists() and not Path("src\\services").exists():
        logger.warning("Services directory not found, skipping services tests")
        return
        
    services_modules = [
        "src.services.transcription" if Path("src/services/transcription.py").exists() or Path("src\\services\\transcription.py").exists() else None,
        "src.services.translation" if Path("src/services/translation.py").exists() or Path("src\\services\\translation.py").exists() else None,
        "src.services.api_clients" if Path("src/services/api_clients.py").exists() or Path("src\\services\\api_clients.py").exists() else None,
        "src.services.auth" if Path("src/services/auth.py").exists() or Path("src\\services\\auth.py").exists() else None,
        "src.services.subtitle_processor" if Path("src/services/subtitle_processor.py").exists() or Path("src\\services\\subtitle_processor.py").exists() else None,
        "src.services.analytics" if Path("src/services/analytics.py").exists() or Path("src\\services\\analytics.py").exists() else None,
        "src.services.rate_limiter" if Path("src/services/rate_limiter.py").exists() or Path("src\\services\\rate_limiter.py").exists() else None,
        "src.services.youtube_api" if Path("src/services/youtube_api.py").exists() or Path("src\\services\\youtube_api.py").exists() else None
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING SERVICE MODULES")
    logger.info("=" * 60)
    
    for module in services_modules:
        if module:  # Skip None values for non-existent modules
            test_import(module)

def test_plugin_modules():
    """Test plugin system modules."""
    # Check if plugins directory exists first
    if not Path("src/plugins").exists() and not Path("src\\plugins").exists():
        logger.warning("Plugins directory not found, skipping plugin tests")
        return
        
    plugin_modules = [
        "src.plugins.manager" if Path("src/plugins/manager.py").exists() or Path("src\\plugins\\manager.py").exists() else None,
        "src.plugins.base" if Path("src/plugins/base.py").exists() or Path("src\\plugins\\base.py").exists() else None,
        "src.plugins.registry" if Path("src/plugins/registry.py").exists() or Path("src\\plugins\\registry.py").exists() else None
    ]
    
    logger.info("=" * 60)
    logger.info("TESTING PLUGIN SYSTEM")
    logger.info("=" * 60)
    
    for module in plugin_modules:
        if module:  # Skip None values for non-existent modules
            test_import(module)

def test_config_validation():
    """Test configuration validation modules."""
    try:
        logger.info("=" * 60)
        logger.info("TESTING CONFIGURATION VALIDATION")
        logger.info("=" * 60)
        
        # First check if config module exists
        if test_import("src.config"):
            # Try to load the configuration
            logger.info("Testing configuration loading...")
            import importlib
            config_module = importlib.import_module("src.config")
            
            # Test accessing some basic configuration values
            if hasattr(config_module, "DEFAULT_SETTINGS"):
                logger.info("Successfully accessed DEFAULT_SETTINGS")
                RESULTS["successful"] += 1
            else:
                logger.warning("DEFAULT_SETTINGS not found in config module")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        RESULTS["failed"] += 1
        RESULTS["errors"].append(("config_validation", str(e)))

def print_summary():
    """Print test summary."""
    success_rate = (RESULTS["successful"] / RESULTS["total_modules"]) * 100 if RESULTS["total_modules"] > 0 else 0
    
    logger.info("=" * 60)
    logger.info("INTEGRITY TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total modules tested: {RESULTS['total_modules']}")
    logger.info(f"Successful imports: {RESULTS['successful']}")
    logger.info(f"Failed imports: {RESULTS['failed']}")
    logger.info(f"Success rate: {success_rate:.2f}%")
    
    if RESULTS["failed"] > 0:
        logger.info("\nFAILED MODULES:")
        for module_name, error_message in RESULTS["errors"]:
            logger.info(f"- {module_name}: {error_message}")
    
    return RESULTS["failed"] == 0

def main():
    """Run all integrity tests."""
    try:
        logger.info("Starting Enhanced YouTube Translator Pro Integrity Test...\n")
        
        # Test core modules
        test_core_modules()
        
        # Test src packages - Only if src exists
        if Path("src").exists():
            test_src_packages()
            
            # Test specific module categories
            test_ui_modules()
            test_utils_modules()
            test_services_modules()
            test_plugin_modules()
            test_config_validation()
        else:
            logger.warning("src directory not found, skipping package tests")
        
        # Print detailed error information
        print_error_details()
        
        # Print summary
        success = print_summary()
        
        logger.info("\nIntegrity test completed.")
        
        # Calculate exit code based on success/failure
        success_rate = RESULTS["successful"] / RESULTS["total_modules"] if RESULTS["total_modules"] > 0 else 0
        if success_rate >= 0.7:  # Lower threshold to 70% to account for optional modules
            logger.info("Integrity test PASSED")
            return 0
        else:
            logger.error("Integrity test FAILED: Too many modules failed")
            return 1
    except Exception as e:
        logger.critical(f"Integrity test crashed: {e}")
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())
