"""
Application manager for YouTube Transcriber Pro.
Coordinates all advanced features and provides a centralized interface for the main application.
"""

import os
import sys
import logging
from typing import Dict, Any, List, Tuple, Union
import time
import json

# Add requests for HTTP functionality
try:
    import requests
except ImportError:
    # Create a mock requests module for testing purposes
    class MockResponse:
        def __init__(self, status_code=200, json_data=None, text=""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.text = text
        
        def json(self):
            return self._json_data
    
    class MockRequests:
        def get(self, *args, **kwargs):
            return MockResponse()
        def post(self, *args, **kwargs):
            return MockResponse()
    
    requests = MockRequests()
from datetime import datetime
from pathlib import Path
import traceback # Added for better error logging
from enum import Enum, auto # Added for enum support

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QSettings, QTimer, Qt, QStandardPaths
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QMenu, QSplashScreen, QSystemTrayIcon
from PyQt6.QtNetwork import QSslSocket # Potentially useful for update checks, etc.

# Import other application modules
# Ensure these imports match your file structure and availability
try:
    from ui import (
        APP_NAME, APP_VERSION, MainWindow, SettingsDialog, AboutDialog,
        ErrorDialog, ShortcutConfigDialog, TaskStatus, BatchStatus,
        AVAILABLE_LANGUAGES, VALID_MODELS # Import necessary enums/constants from UI
    )
    UI_AVAILABLE = True
except ImportError as e:
    logging.critical(f"Failed to import UI components into application_manager: {e}. Application cannot start without UI.")
    UI_AVAILABLE = False
    # Define mock/fallback classes if UI is unavailable
    class MainWindow(QMainWindow):
        def __init__(self, *args, **kwargs): super().__init__(); logger.warning("Mock MainWindow used.")
        def show(self): logger.warning("Mock MainWindow.show() called.")
        def hide(self): logger.warning("Mock MainWindow.hide() called.")
        def closeEvent(self, event): event.accept() # Accept close event
        def add_task_to_ui(self, url): pass # Mock method
        def remove_task_from_ui(self, url): pass # Mock method
        def _update_ui_progress(self, update): pass # Mock method
        def _handle_batch_completion(self, report): pass # Mock method
        def _handle_resource_warning(self, warning_data): pass # Mock method
        def _handle_error_report(self, message, details): pass # Mock method
        def _handle_update_ui_status(self, status, message): pass # Mock method
        def _handle_notification_request(self, title, message, type): pass # Mock method
        def _paste_from_clipboard(self): pass # Mock method
        def show_settings_dialog(self): pass # Mock method
        def show_about_dialog(self): pass # Mock method
        def show_help(self): pass # Mock method
        def show_shortcut_config_dialog(self): pass # Mock method
        def _update_ui_state(self, status): pass # Mock method
        def handle_file_open_request(self, file_path): pass # Mock method
        def set_recent_files_menu(self, menu): pass # Mock method
        def get_output_directory(self): return str(Path.home() / "Downloads") # Mock method
        def get_default_model(self): return "small" # Mock method
        def get_default_language(self): return "None" # Mock method
        def get_selected_formats(self): return ["srt"] # Mock method
        def get_concurrency_setting(self): return 2 # Mock method
        def update_batch_status_indicator(self, status): pass # Mock method
        def showNormal(self): pass # Mock method for tray icon restore
        def saveGeometry(self): return QByteArray() # Mock method for session
        def restoreGeometry(self, geometry): pass # Mock method for session
        def saveState(self): return QByteArray() # Mock method for session
        def restoreState(self, state): pass # Mock method for session
        def clear_urls_input(self): pass # Mock method for shortcuts

    class SettingsDialog(QDialog):
         def __init__(self, *args, **kwargs): super().__init__(); self.settings_saved = pyqtSignal(dict)
         def exec(self): return 0
    class AboutDialog(QDialog):
         def __init__(self, *args, **kwargs): super().__init__();
         def exec(self): return 0
    class ErrorDialog(QDialog):
         def __init__(self, *args, **kwargs): super().__init__();
         def exec(self): return 0
    class ShortcutConfigDialog(QDialog):
         def __init__(self, *args, **kwargs): super().__init__(); self.shortcuts_saved = pyqtSignal(dict)
         def exec(self): return 0
    TaskStatus = Enum("TaskStatus", ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "SKIPPED", "PAUSED", "RETRYING", "VALIDATING", "DOWNLOADING", "CONVERTING", "TRANSCRIBING", "TRANSLATING", "EXPORTING"])
    BatchStatus = Enum("BatchStatus", ["IDLE", "RUNNING", "PAUSED", "RESUMING", "COMPLETED", "CANCELLED", "FAILED", "THROTTLED", "STOPPING"])
    AVAILABLE_LANGUAGES = {"None": "None", "en": "English"}
    VALID_MODELS = ["small"]


# Import other core modules (conditional import handled in __init__)
BatchProcessor = None
CacheManager = None
RecentFilesManager = None
AutoUpdater = None
SystemTrayManager = None
KeyboardManager = None
SessionManager = None
ErrorReporter = None
CrashHandler = None
CacheType = None # Need CacheType enum
load_settings = lambda: {}
save_settings = lambda s: False
DEFAULT_SETTINGS = {}
APP_DATA_DIR = Path(os.path.join(os.path.expanduser("~"), ".ytpro_default_app_data"))

try:
    from batch import BatchProcessor, TaskStatus, BatchStatus # Re-import BatchStatus/TaskStatus to be safe
    BATCH_AVAILABLE = True
except ImportError as e:
    logging.critical(f"Failed to import batch module: {e}. Batch processing disabled.")
    BATCH_AVAILABLE = False

try:
    from cache import CacheManager, CacheType
    CACHE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Failed to import cache module: {e}. Caching disabled.")
    CACHE_AVAILABLE = False
    class MockCacheManager:
        def __init__(self, *args, **kwargs): pass
        def get(self, key, type): return None
        def set(self, key, type, data): return False
        def delete(self, key, type): pass
        def clear(self): pass
        def clear_unused(self, timeout_seconds): pass
        def get_cache_stats(self): return {"initialized": False}
    CacheManager = MockCacheManager
    CacheType = Enum("CacheType", ["TRANSCRIPTION", "TRANSLATION", "AUDIO"]) # Define if not imported

try:
    from settings import load_settings, save_settings, DEFAULT_SETTINGS, APP_DATA_DIR # Re-import settings components
    SETTINGS_AVAILABLE = True
except ImportError as e:
    logging.critical(f"Failed to import settings module: {e}. Application settings will not be persistent.")
    SETTINGS_AVAILABLE = False
    load_settings = lambda: {}
    save_settings = lambda s: False
    DEFAULT_SETTINGS = {}
    APP_DATA_DIR = Path(os.path.join(os.path.expanduser("~"), ".ytpro_default_app_data"))


try:
    from advanced_features import (
        RecentFilesManager, RecentFilesMenu,
        AutoUpdater, UpdateStatus, # UpdateDialog is in ui.py now
        SystemTrayManager, NotificationType,
        KeyboardManager, ShortcutAction, # ShortcutConfigDialog is in ui.py now
        SessionManager,
        ErrorReporter, ErrorSeverity, # ErrorDialog is in ui.py now
        CrashHandler
    )
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError as e:
    logging.critical(f"Failed to import advanced features module: {e}. Some features will be disabled.")
    ADVANCED_FEATURES_AVAILABLE = False
    # Define mock/fallback classes if advanced features are unavailable
    class MockRecentFilesManager(QObject):
        recent_files_changed = pyqtSignal(list)
        def add_file(self, path): pass
        def get_recent_files(self): return []
        def clear_recent_files(self): pass
        def delete_file(self, path): pass
    RecentFilesManager = MockRecentFilesManager
    class MockRecentFilesMenu(QMenu):
        file_opened = pyqtSignal(str)
        clear_recent_files_requested = pyqtSignal()
        def update_menu(self, files): pass
    RecentFilesMenu = MockRecentFilesMenu
    # Define enums for mock classes
    class UpdateStatus(Enum):
        NO_UPDATE = auto()
        CHECKING = auto()
        UPDATE_AVAILABLE = auto()
        DOWNLOADING = auto()
        READY_TO_INSTALL = auto()
        ERROR = auto()
        DISABLED = auto()
    
    class NotificationType(Enum):
        INFO = auto()
        WARNING = auto()
        CRITICAL = auto()
    
    class ErrorSeverity(Enum):
        INFO = auto()
        WARNING = auto()
        ERROR = auto()
        CRITICAL = auto()
    
    class ShortcutAction(Enum):
        START_BATCH = auto()
        PAUSE_BATCH = auto()
        CANCEL_BATCH = auto()
        SHOW_SETTINGS = auto()
        SHOW_ABOUT = auto()
        SHOW_HELP = auto()
        ADD_URLS_FROM_CLIPBOARD = auto()
        CLEAR_INPUT = auto()
        SHOW_SHORTCUTS = auto()
        PASS_THROUGH = auto()
    class MockAutoUpdater(QObject):
         # Changed to use str type directly instead of Optional[str] as PyQt signals don't work with Optional types
         update_status_changed = pyqtSignal(object, str)
         notification_requested = pyqtSignal(str, str, object)
         def __init__(self, config, parent=None): super().__init__(parent)
         def check_for_updates(self): self.update_status_changed.emit(UpdateStatus.DISABLED, "Updater unavailable.")
         def download_update(self): pass
         def install_update(self): pass
         def get_update_status(self): return UpdateStatus.DISABLED
    AutoUpdater = MockAutoUpdater
    # UpdateStatus already defined above as a class-based Enum
    class MockSystemTrayManager(QObject):
         tray_icon_activated = pyqtSignal(int)
         message_clicked = pyqtSignal()
         def __init__(self, parent=None): super().__init__(parent)
         def set_main_window(self, window): pass
         def show_message(self, title, message, type): logger.warning(f"Tray message (Tray unavailable): {title} - {message}")
    SystemTrayManager = MockSystemTrayManager
    # NotificationType already defined above, so this line is removed
    class MockKeyboardManager(QObject):
         shortcut_activated = pyqtSignal(ShortcutAction)
         def __init__(self, parent=None): super().__init__(parent)
         def set_main_window(self, window): pass
         def get_all_shortcuts(self): return {}
         def update_shortcut(self, action, key_sequence_str, enabled): return False
         def load_settings(self, settings): pass
         def save_settings(self): return {}
    KeyboardManager = MockKeyboardManager
    # ShortcutAction already defined above as a class-based Enum
    class MockSessionManager(QObject):
         def __init__(self, parent=None): super().__init__(parent)
         def save_session(self, window, data): pass
         def restore_session(self, window): return {}
    SessionManager = MockSessionManager
    class MockErrorReporter(QObject):
         error_reported = pyqtSignal(str, str, ErrorSeverity)
         def __init__(self, parent=None): super().__init__(parent)
         def report_error(self, message, details="", severity=ErrorSeverity.ERROR): logger.error(f"Error Reported (Reporter unavailable): {message} | {details} | {severity.name}")
    ErrorReporter = MockErrorReporter
    ErrorSeverity = Enum("ErrorSeverity", ["INFO", "WARNING", "ERROR", "CRITICAL"])
    class MockCrashHandler(QObject):
         def __init__(self, session_manager=None, parent=None): super().__init__(parent)
         def needs_recovery(self): return False
         def perform_recovery(self, window): return False
         def reset_crash_count(self): pass
         def handle_exception(self, exc_type, exc_value, exc_traceback): pass # Mock hook
    CrashHandler = MockCrashHandler


try:
     from splash import create_splash_screen # Assuming splash is available
     SPLASH_AVAILABLE = True
except ImportError as e:
     logging.warning(f"Failed to import splash module: {e}. Splash screen disabled.")
     SPLASH_AVAILABLE = False
     def create_splash_screen(app): return None # Mock function


# Set up logger
logger = logging.getLogger(__name__)

# Default configuration (can be overridden by settings.json)
DEFAULT_UPDATE_CONFIG = {
    "update_url": "https://api.github.com/repos/yourusername/YouTubeTranscriberPro/releases/latest", # Replace with your repo URL
    "timeout": 10,  # seconds
    "verify_ssl": True,
    "check_interval": 24,  # hours
    "auto_check": True,
    "retry_delay_hours": 6 # Delay after a failed update check before retrying
}


class ApplicationManager(QObject):
    """
    Central manager for all application features.
    Coordinates UI, batch processing, settings, and advanced features.
    """

    # Signals to be emitted by the manager
    # Signal emitted when an error occurs
    error_occurred = pyqtSignal(str, str) # message, details
    # Signal emitted when batch processing status changes (for UI)
    batch_status_changed = pyqtSignal(BatchStatus)
    # Signal emitted when a task's status or progress changes (for UI)
    task_updated = pyqtSignal(dict) # Task data dictionary
    # Signal to update the main window's status bar message
    status_message = pyqtSignal(str)
    # Signal to update the batch progress indicator on the UI
    overall_progress_updated = pyqtSignal(float) # Progress 0.0-1.0
    # Signal to handle batch completion and report summary
    batch_completed = pyqtSignal(dict) # Completion report dictionary
    # Signal to request a system tray notification
    notification_requested = pyqtSignal(str, str, NotificationType) # title, message, type
    # Signal emitted when a resource warning occurs
    resource_warning = pyqtSignal(str, str) # warning_type, message
    # Signal to update the UI with recent files list
    recent_files_list_updated = pyqtSignal(list)
    # Signal to update the UI with update status
    update_status_updated = pyqtSignal(UpdateStatus, object) # status, message
    # Signal to trigger restoration of session data into relevant components (e.g., BatchProcessor)
    restore_session_data = pyqtSignal(dict) # session data


    def __init__(self, app: QApplication, splash: QSplashScreen = None):
        """
        Initialize the Application Manager.

        Args:
            app: The QApplication instance.
            splash: Optional splash screen instance.
        """
        super().__init__()
        self.app = app
        self._splash = splash # Store splash screen reference

        logger.info("ApplicationManager initializing...")

        # 1. Initialize core components (even if others fail)
        self.settings: dict = DEFAULT_SETTINGS.copy() # Start with defaults
        if SETTINGS_AVAILABLE:
             self.settings = load_settings() # Load settings if module is available

        self.error_reporter = ErrorReporter(parent=self) if ADVANCED_FEATURES_AVAILABLE else MockErrorReporter(parent=self)
        self.session_manager = SessionManager(parent=self) if ADVANCED_FEATURES_AVAILABLE else MockSessionManager(parent=self)
        self.crash_handler = CrashHandler(session_manager=self.session_manager, parent=self) if ADVANCED_FEATURES_AVAILABLE else MockCrashHandler(parent=self)


        # Set the global exception hook for crash handling
        if ADVANCED_FEATURES_AVAILABLE:
             sys.excepthook = self.crash_handler.handle_exception

        # 2. Initialize other managers based on module availability
        self.cache_manager = CacheManager(
             cache_dir=self.settings.get("cache_dir", str(APP_DATA_DIR / "cache")),
             max_size_mb=self.settings.get("cache_size_mb", 1000),
             ttl_seconds=self.settings.get("cache_ttl", 60*60*24*30)
        ) if CACHE_AVAILABLE else MockCacheManager()

        self.batch_processor = BatchProcessor(
            cache_manager=self.cache_manager,
            concurrency=self.settings.get("concurrency", 2),
            parent=self
        ) if BATCH_AVAILABLE else None # BatchProcessor will be None if module not available

        self.recent_files_manager = RecentFilesManager(
            max_files=self.settings.get("max_recent_files", 20),
            parent=self
        ) if ADVANCED_FEATURES_AVAILABLE else MockRecentFilesManager()

        self.system_tray_manager = SystemTrayManager(parent=self) if ADVANCED_FEATURES_AVAILABLE else MockSystemTrayManager(parent=self)

        self.keyboard_manager = KeyboardManager(parent=self) if ADVANCED_FEATURES_AVAILABLE else MockKeyboardManager(parent=self)
        if ADVANCED_FEATURES_AVAILABLE:
             self.keyboard_manager.load_settings(self.settings.get("keyboard_shortcuts", {}))


        # Auto-updater initialization (using settings, falling back to default config)
        update_config = self.settings.get("update_config", DEFAULT_UPDATE_CONFIG)
        self.auto_updater = AutoUpdater(update_config, parent=self) if ADVANCED_FEATURES_AVAILABLE else MockAutoUpdater(update_config, parent=self)

        # 3. Create Main Window (if UI is available)
        self.main_window: MainWindow = None
        if UI_AVAILABLE:
            self.main_window = MainWindow(app_manager=self) # Pass self to the UI
            self._apply_initial_style() # Apply style after creating the window

            # Set main window for managers that need it
            if ADVANCED_FEATURES_AVAILABLE:
                 self.system_tray_manager.set_main_window(self.main_window)
                 self.keyboard_manager.set_main_window(self.main_window)

            # Connect UI signals to manager slots
            self._connect_ui_signals()

            # Restore window state and geometry from the previous session
            if ADVANCED_FEATURES_AVAILABLE:
                 self.session_manager.restore_session(self.main_window)


        # 4. Connect signals from other managers to ApplicationManager/UI
        self._connect_manager_signals()

        # 5. Perform crash recovery check
        # This should happen early, before loading batch state, as recovery might need to
        # influence how the batch state is loaded or handled.
        if ADVANCED_FEATURES_AVAILABLE and self.crash_handler.needs_recovery() and self.main_window:
             logger.warning("Detected need for crash recovery.")
             # Perform recovery, which will attempt to restore session data
             # The session data will be loaded by the SessionManager instance already passed
             # to the CrashHandler. The BatchProcessor will need to load its state
             # from this restored session data in its `load_session` method, which
             # is called later.
             self.crash_handler.perform_recovery(self.main_window)


        # 6. Load Batch Processor state from session (if recovery didn't already, or if no crash)
        # The session data contains the state saved during the last clean shutdown.
        # If there was a crash, perform_recovery attempts to load the *last* saved state.
        # Here, we specifically load the state from the session saved during a clean exit.
        # We need to decide if crash recovery session data overrides clean exit session data.
        # A common pattern: if crash recovery occurred, its session load is primary.
        # Otherwise, load the session from the last *successful* exit.
        # QSettings stores the *last* saved state. The crash handler checks a *marker*.
        # If the marker exists, the last saved state corresponds to the crash state.
        # If the marker *doesn't* exist, the last saved state corresponds to the clean exit state.

        if BATCH_AVAILABLE and self.batch_processor and ADVANCED_FEATURES_AVAILABLE:
             # Load the batch processor state from the session manager
             # The session_manager.restore_session(self.main_window) in crash_handler/init
             # already put the session data into QSettings.
             # We need to *retrieve* that data and pass it to the batch processor.
             # session_data = self.session_manager.restore_session(self.main_window) # This already happened
             # Instead, load the state directly from settings:
             session_data_json = QSettings().value(self.session_manager._session_key) # Access the key used by SessionManager
             if session_data_json:
                  try:
                       restored_data = json.loads(session_data_json)
                       # Convert serializable types back (SessionManager has this logic)
                       restored_data = self.session_manager._restore_from_serialization(restored_data)
                       if restored_data.get("batch_processor_state"):
                            logger.info("Loading batch processor state from session.")
                            self.batch_processor.load_session(restored_data["batch_processor_state"])
                       else:
                            logger.debug("No batch processor state found in session data.")

                  except json.JSONDecodeError as e:
                       logger.error(f"Failed to decode session data for batch processor: {e}")
                  except Exception as e:
                       logger.error(f"Failed to load batch processor state from session: {e}", exc_info=True)
             else:
                  logger.info("No session data found to load for batch processor.")


        # 7. Perform initial checks (e.g., auto-update)
        if ADVANCED_FEATURES_AVAILABLE and self.auto_updater:
             self.auto_updater.check_for_updates()

        # 8. Reset crash count if we reached this point successfully
        if ADVANCED_FEATURES_AVAILABLE and self.crash_handler:
             self.crash_handler.reset_crash_count()


        logger.info("ApplicationManager initialization complete.")


    def _apply_initial_style(self):
        """Apply initial global styles after the main window is created."""
        if self.main_window and hasattr(self.main_window, 'style_manager'):
             # Assume style_manager is an attribute of the main_window or accessible globally
             # If using a global style_manager instance:
             from styles import style_manager # Import the global instance
             settings_theme = self.settings.get("theme", "dark")
             style_manager.apply_global_style(self.app, settings_theme)
             logger.info(f"Applied initial theme: {settings_theme}")
        else:
             logger.warning("Style manager not available to apply initial style.")


    def _connect_ui_signals(self):
        """Connect signals from the UI to slots in the manager or other managers."""
        if not self.main_window:
            logger.warning("Main window not available. Skipping UI signal connections.")
            return

        logger.debug("Connecting UI signals to manager/manager slots.")

        # Connect signals from MainWindow
        self.main_window.start_batch_requested.connect(self.start_batch)
        self.main_window.pause_batch_requested.connect(self.pause_batch)
        self.main_window.cancel_batch_requested.connect(self.cancel_batch)
        self.main_window.add_url_requested.connect(self.add_task) # Connect add URL from UI to add task
        self.main_window.cancel_task_requested.connect(self.cancel_task) # Connect cancel task from UI
        self.main_window.remove_task_requested.connect(self.remove_task) # Connect remove task from UI
        self.main_window.retry_task_requested.connect(self.retry_task) # Connect retry task from UI

        self.main_window.settings_requested.connect(self.show_settings_dialog)
        self.main_window.about_requested.connect(self.show_about_dialog)
        self.main_window.help_requested.connect(self.show_help)
        self.main_window.quit_requested.connect(self.shutdown) # Connect UI quit to manager shutdown

        self.main_window.output_dir_changed.connect(self._handle_output_dir_changed) # Handle output dir changes from UI

        # Connect signals for recent files menu integration
        if ADVANCED_FEATURES_AVAILABLE:
             self.recent_files_manager.recent_files_changed.connect(self._update_recent_files_menu)
             # Connect the RecentFilesMenu's signals to the manager
             # Assuming the MainWindow holds the RecentFilesMenu instance and can expose its signals
             if hasattr(self.main_window, 'recent_files_menu') and self.main_window.recent_files_menu:
                  self.main_window.recent_files_menu.file_opened.connect(self._handle_recent_file_open)
                  self.main_window.recent_files_menu.clear_recent_files_requested.connect(self.clear_recent_files)
                  # Initial population of the menu
                  self._update_recent_files_menu(self.recent_files_manager.get_recent_files())


        # Connect signals for system tray activation
        if ADVANCED_FEATURES_AVAILABLE and self.system_tray_manager:
             self.system_tray_manager.tray_icon_activated.connect(self._handle_tray_icon_activated)
             self.system_tray_manager.message_clicked.connect(self._handle_tray_message_clicked)

        # Connect signals for keyboard shortcuts
        if ADVANCED_FEATURES_AVAILABLE and self.keyboard_manager:
             self.keyboard_manager.shortcut_activated.connect(self._handle_shortcut_activated)
             # Connect the shortcut config dialog's saved signal to the manager
             # Assuming the MainWindow creates and shows the ShortcutConfigDialog
             # and the dialog emits a signal when saved.
             # The manager needs to receive this signal to update and save shortcuts.
             # Let's add a method in the manager that the dialog calls or connects to.
             # Or, the manager can connect to the dialog's signal when the dialog is created.
             # A cleaner way is for the manager to be responsible for creating/showing config dialogs.


        logger.debug("UI signal connections complete.")


    def _connect_manager_signals(self):
        """Connect signals from other managers to slots in the manager or UI."""
        logger.debug("Connecting manager signals.")

        # Connect BatchProcessor signals to UI update slots in MainWindow
        if BATCH_AVAILABLE and self.batch_processor and self.main_window:
            self.batch_processor.task_progress_updated.connect(self.main_window._update_ui_progress)
            self.batch_processor.batch_progress_updated.connect(self._handle_batch_progress_update) # Connect to manager first
            self.batch_processor.batch_completion_status.connect(self.main_window._handle_batch_completion) # Connect completion to UI
            self.batch_processor.resource_warning_occurred.connect(self._handle_resource_warning) # Connect resource warnings
            self.batch_processor.status_message.connect(self.status_message.emit) # Forward status messages to main window status bar

        # Connect ErrorReporter signals to ErrorDialog or logging
        if ADVANCED_FEATURES_AVAILABLE and self.error_reporter and self.main_window:
            self.error_reporter.error_reported.connect(self._handle_error_reported)

        # Connect AutoUpdater signals
        if ADVANCED_FEATURES_AVAILABLE and self.auto_updater and self.main_window:
             self.auto_updater.update_status_changed.connect(self._handle_update_status_changed)
             self.auto_updater.notification_requested.connect(self.system_tray_manager.show_message) # Forward notifications to tray

        # Connect RecentFilesManager signal
        if ADVANCED_FEATURES_AVAILABLE and self.recent_files_manager:
            self.recent_files_manager.recent_files_changed.connect(self.recent_files_list_updated.emit) # Forward to UI (if UI listens)


        # Connect signals from ApplicationManager to UI components (internal connections)
        self.batch_status_changed.connect(self.main_window.update_batch_status_indicator) # Update UI status indicator
        self.overall_progress_updated.connect(self.main_window.update_overall_progress_bar) # Update UI progress bar
        self.resource_warning.connect(self.main_window._handle_resource_warning) # Forward resource warnings to UI method
        self.update_status_updated.connect(self.main_window._handle_update_ui_status) # Update UI with updater status


        logger.debug("Manager signal connections complete.")


    def run(self):
        """Start the application event loop and show the main window."""
        logger.info("ApplicationManager starting event loop...")
        if self.main_window:
            self.main_window.show() # Show the main window

            # Hide splash screen if it exists
            if self._splash:
                 # Wait a moment before hiding to ensure main window is ready
                 QTimer.singleShot(100, self._splash.finish(self.main_window))
                 logger.debug("Splash screen hidden.")

            # Connect application aboutToQuit signal for graceful shutdown
            self.app.aboutToQuit.connect(self.shutdown)

            sys.exit(self.app.exec()) # Start the Qt event loop
        else:
             logger.critical("Main window could not be created. Exiting.")
             sys.exit(1)


    @pyqtSlot()
    def shutdown(self, wait: bool = True, timeout: float = 10.0):
        """
        Perform graceful application shutdown.

        Args:
            wait: If True, wait for background processes/threads to finish.
            timeout: Maximum time to wait for processes/threads.
        """
        logger.info("ApplicationManager initiating shutdown...")

        # Disconnect signals to prevent issues during shutdown
        # (Optional but can help with complex signal connections)
        # self._disconnect_all_signals() # Implement if needed

        # Save session state
        if ADVANCED_FEATURES_AVAILABLE and self.session_manager and self.main_window:
            logger.info("Saving session state...")
            # Get state from components that manage state (e.g., BatchProcessor)
            session_data: dict = {
                 "batch_processor_state": self.batch_processor.get_session_state() if BATCH_AVAILABLE and self.batch_processor else {},
                 # Add state from other managers/components here if they have state to save
            }
            self.session_manager.save_session(self.main_window, session_data)


        # Shutdown Batch Processor (handles its threads and processes)
        if BATCH_AVAILABLE and self.batch_processor:
            logger.info("Shutting down batch processor...")
            self.batch_processor.shutdown(wait=wait, timeout=timeout)

        # Clean up cache (e.g., remove expired entries)
        if CACHE_AVAILABLE and self.cache_manager:
            logger.info("Cleaning up cache...")
            # Clear entries older than TTL, or maybe just ensure size limit is enforced
            self.cache_manager.clear_unused() # Clear expired entries
            # self.cache_manager._enforce_size_limit() # Ensure size limit is met

        # Perform any final cleanup (e.g., temporary files)
        # The BatchProcessor's atexit handler already handles final temp file cleanup.

        # Disconnect signals manually if not using _disconnect_all_signals()
        # Ensure threads and processes managed outside the batch processor are terminated
        # The transcribe module has its own atexit handler for processes.

        logger.info("ApplicationManager shutdown complete.")

        # The QApplication event loop will exit after this method returns
        # because of app.aboutToQuit.connect(self.shutdown).


    # --- Application Logic / Slots connected to UI ---

    @pyqtSlot(list)
    def start_batch(self, urls: list):
        """Handle request to start or resume batch processing."""
        if not BATCH_AVAILABLE or not self.batch_processor:
            self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
            return

        # Get current settings for batch processing
        output_dir = self.main_window.get_output_directory() if self.main_window else self.settings.get("output_dir")
        default_model = self.main_window.get_default_model() if self.main_window else self.settings.get("default_model")
        default_language = self.main_window.get_default_language() if self.main_window else self.settings.get("default_language")
        selected_formats = self.main_window.get_selected_formats() if self.main_window else ["srt"]
        concurrency = self.main_window.get_concurrency_setting() if self.main_window else self.settings.get("concurrency")

        # Ensure concurrency setting in batch processor is up-to-date
        self.batch_processor.concurrency = concurrency

        # If URLs are provided, add them as new tasks
        if urls:
             self.batch_processor.process_batch(
                 urls=urls,
                 model=default_model,
                 target_lang=default_language,
                 output_dir=output_dir,
                 formats=selected_formats
             )
        elif self.batch_processor.status == BatchStatus.PAUSED:
             # If no new URLs, and batch is paused, resume it
             self.pause_batch() # Calling pause_batch again toggles to resume


        # Update UI state to reflect batch status
        if self.main_window:
             self.main_window._update_ui_state(self.batch_processor.status)


    @pyqtSlot()
    def pause_batch(self):
        """Handle request to pause batch processing."""
        if not BATCH_AVAILABLE or not self.batch_processor:
            self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
            return

        if self.batch_processor.status == BatchStatus.RUNNING:
             self.batch_processor.pause()
             logger.info("Batch processing paused.")
        elif self.batch_processor.status == BatchStatus.PAUSED:
             self.batch_processor.resume()
             logger.info("Batch processing resumed.")

        # Update UI state
        if self.main_window and self.batch_processor:
             self.main_window._update_ui_state(self.batch_processor.status)


    @pyqtSlot()
    def cancel_batch(self):
        """Handle request to cancel batch processing."""
        if not BATCH_AVAILABLE or not self.batch_processor:
            self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
            return

        if self.batch_processor.status in [BatchStatus.RUNNING, BatchStatus.PAUSED, BatchStatus.THROTTLED, BatchStatus.RESUMING]:
             reply = QMessageBox.question(self.main_window, "Confirm Cancel",
                                          "Are you sure you want to cancel the current batch?",
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
             if reply == QMessageBox.StandardButton.Yes:
                  self.batch_processor.cancel()
                  logger.info("Batch processing cancelled.")
                  # Update UI state
                  if self.main_window:
                       self.main_window._update_ui_state(self.batch_processor.status) # Status will be STOPPING initially, then CANCELLED


    @pyqtSlot(str, str, object, str, list)
    def add_task(self, url: str, model: str, target_lang: str, output_dir: str, formats: list):
         """Handle request to add a single task."""
         if not BATCH_AVAILABLE or not self.batch_processor:
              self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
              return

         # Add the task to the batch processor
         self.batch_processor.add_task(url, model, target_lang, output_dir, formats)
         logger.info(f"Task added to batch: {url}")

         # Update UI (MainWindow should add the task to its list model)
         if self.main_window:
              self.main_window.add_task_to_ui(url) # Signal MainWindow to add the task to UI list

         # If the batch is currently idle, start it automatically after adding a task
         if self.batch_processor.status == BatchStatus.IDLE:
              logger.info("Batch was idle, starting processing after adding task.")
              self.start_batch(urls=[]) # Start processing any pending tasks


    @pyqtSlot(str)
    def cancel_task(self, url: str):
        """Handle request to cancel a specific task."""
        if not BATCH_AVAILABLE or not self.batch_processor:
             self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
             return

        self.batch_processor.cancel_task(url)
        logger.info(f"Task cancelled: {url}")
        # UI update handled by batch_processor.task_progress_updated signal


    @pyqtSlot(str)
    def remove_task(self, url: str):
        """Handle request to remove a specific task."""
        if not BATCH_AVAILABLE or not self.batch_processor:
             self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
             return

        reply = QMessageBox.question(self.main_window, "Confirm Remove Task",
                                     f"Are you sure you want to remove the task for:\n{url}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
             self.batch_processor.remove_task(url)
             logger.info(f"Task removed: {url}")
             # Update UI (MainWindow should remove the task from its list model)
             if self.main_window:
                  self.main_window.remove_task_from_ui(url) # Signal MainWindow to remove task from UI list


    @pyqtSlot(str)
    def retry_task(self, url: str):
        """Handle request to retry a failed task."""
        if not BATCH_AVAILABLE or not self.batch_processor:
             self.error_reporter.report_error("Batch processing module is not available.", severity=ErrorSeverity.CRITICAL)
             return

        self.batch_processor.retry_task(url)
        logger.info(f"Task retried: {url}")
        # UI update handled by batch_processor.task_progress_updated signal


    @pyqtSlot(dict)
    def _handle_batch_progress_update(self, update: dict):
        """Handle updates to the overall batch progress and status."""
        batch_progress = update.get("batch_progress", 0.0)
        batch_status_name = update.get("batch_status", "IDLE")
        try:
            batch_status = BatchStatus[batch_status_name] if batch_status_name in BatchStatus.__members__ else BatchStatus.IDLE
        except KeyError:
            logger.warning(f"Unknown batch status received: {batch_status_name}")
            batch_status = BatchStatus.IDLE

        # Emit signals for UI to update
        self.overall_progress_updated.emit(batch_progress)
        self.batch_status_changed.emit(batch_status)

        # Update main window status bar with general status messages from batch processor
        # This is already connected via batch_processor.status_message -> self.status_message -> main_window.statusBar().showMessage


    @pyqtSlot(dict)
    def _handle_resource_warning(self, warning_data: dict):
        """Handle resource warning signals from BatchProcessor."""
        warning_type = warning_data.get("warning_type", "unknown")
        message = warning_data.get("message", "A resource warning occurred.")
        # Emit a simplified signal that the UI can listen to
        self.resource_warning.emit(warning_type, message)

        # Optionally show a temporary message in the status bar
        if self.main_window:
             self.status_message.emit(message)
             # The status bar message might need to be managed more carefully
             # if multiple messages are emitted quickly.


    # --- Settings Management ---

    @pyqtSlot()
    def show_settings_dialog(self):
        """Show the settings dialog."""
        if not UI_AVAILABLE or not SETTINGS_AVAILABLE:
            self.error_reporter.report_error("Settings dialog or settings module is not available.", severity=ErrorSeverity.WARNING)
            return

        logger.debug("Showing settings dialog.")
        dialog = SettingsDialog(current_settings=self.settings, parent=self.main_window)
        dialog.settings_saved.connect(self.save_settings) # Connect dialog's saved signal

        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.debug("Settings dialog accepted.")
        else:
            logger.debug("Settings dialog cancelled.")


    @pyqtSlot(dict)
    def save_settings(self, new_settings: dict):
        """Save application settings and re-apply them."""
        if not SETTINGS_AVAILABLE:
            logger.warning("Settings module not available. Cannot save settings.")
            return

        logger.info("Saving settings.")
        # Update internal settings dictionary
        self.settings.update(new_settings)

        # Save to file
        if save_settings(self.settings):
            logger.info("Settings saved successfully.")
            # Re-apply settings to relevant components
            self._apply_settings()
        else:
            self.error_reporter.report_error("Failed to save settings.", severity=ErrorSeverity.ERROR)


    def _apply_settings(self):
        """Apply current settings to application components."""
        logger.info("Applying settings.")

        # Apply theme setting
        if self.main_window and hasattr(self.main_window, 'style_manager'):
             from styles import style_manager # Import the global instance
             theme_name = self.settings.get("theme", "dark")
             style_manager.set_theme(theme_name) # This also regenerates and applies stylesheet/palette
             logger.debug(f"Applied theme setting: {theme_name}")
        elif self.main_window:
             # Fallback if style_manager isn't directly accessible
             logger.warning("Could not access style manager to apply theme.")


        # Apply batch processing settings
        if BATCH_AVAILABLE and self.batch_processor:
            self.batch_processor.concurrency = self.settings.get("concurrency", 2)
            # Note: Default model, language, output dir, formats are applied when batch is started
            logger.debug(f"Applied batch concurrency setting: {self.batch_processor.concurrency}")

        # Apply cache settings
        if CACHE_AVAILABLE and self.cache_manager:
             # Cache settings might require re-initialization or updating manager properties
             # Assuming CacheManager can update its settings after initialization
             self.cache_manager.max_size_bytes = self.settings.get("cache_size_mb", 1000) * 1024 * 1024
             self.cache_manager.ttl_seconds = self.settings.get("cache_ttl", 60*60*24*30)
             # If cache directory changed, might need to re-initialize or show warning
             # For simplicity, assume cache_dir is set only on initialisation.
             logger.debug(f"Applied cache settings: size={self.cache_manager.max_size_bytes}, ttl={self.cache_manager.ttl_seconds}")

        # Apply recent files settings
        if ADVANCED_FEATURES_AVAILABLE and self.recent_files_manager:
             self.recent_files_manager.max_files = self.settings.get("max_recent_files", 20)
             self.recent_files_manager._load_recent_files() # Reload recent files with new max limit
             logger.debug(f"Applied max recent files setting: {self.recent_files_manager.max_files}")


        # Apply auto-update settings
        if ADVANCED_FEATURES_AVAILABLE and self.auto_updater:
             update_config = self.settings.get("update_config", DEFAULT_UPDATE_CONFIG)
             self.auto_updater.update_config = update_config # Update updater config
             self.auto_updater._start_update_timer() # Restart timer with new interval/auto-check setting
             logger.debug("Applied auto-update settings.")


        # Apply keyboard shortcut settings
        if ADVANCED_FEATURES_AVAILABLE and self.keyboard_manager:
             self.keyboard_manager.load_settings(self.settings.get("keyboard_shortcuts", {}))
             logger.debug("Applied keyboard shortcut settings.")


        logger.info("Settings applied to components.")


    # --- Information Dialogs ---

    @pyqtSlot()
    def show_about_dialog(self):
        """Show the about dialog."""
        if not UI_AVAILABLE:
            self.error_reporter.report_error("About dialog is not available.", severity=ErrorSeverity.WARNING)
            return

        logger.debug("Showing about dialog.")
        dialog = AboutDialog(parent=self.main_window)
        dialog.exec()


    @pyqtSlot()
    def show_help(self):
        """Show the help documentation (e.g., open a help URL)."""
        # This could open a local help file or an online documentation page.
        help_url = "https://your_documentation_url.com" # Replace with your help URL
        try:
            import webbrowser
            webbrowser.open(help_url)
            logger.info(f"Opened help URL: {help_url}")
        except Exception as e:
            error_message = f"Failed to open help URL {help_url}: {e}"
            logger.error(error_message)
            self.error_reporter.report_error(error_message, severity=ErrorSeverity.ERROR)
            # Optionally show a message box if opening URL fails
            if self.main_window:
                 QMessageBox.warning(self.main_window, "Open Help",
                                     f"Failed to open help. Please visit:\n{help_url}\n\nError: {e}")


    @pyqtSlot()
    def show_shortcut_config_dialog(self):
        """Show the shortcut configuration dialog."""
        if not UI_AVAILABLE or not ADVANCED_FEATURES_AVAILABLE or not self.keyboard_manager:
            self.error_reporter.report_error("Shortcut configuration is not available.", severity=ErrorSeverity.WARNING)
            return

        logger.debug("Showing shortcut configuration dialog.")
        # Get current shortcuts from the keyboard manager
        current_shortcuts = self.keyboard_manager.get_all_shortcuts()
        dialog = ShortcutConfigDialog(current_shortcuts=current_shortcuts, parent=self.main_window)

        # Connect the dialog's saved signal to the manager's save_shortcut_settings slot
        dialog.shortcuts_saved.connect(self.save_shortcut_settings)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            logger.debug("Shortcut configuration dialog accepted.")
        else:
            logger.debug("Shortcut configuration dialog cancelled.")


    @pyqtSlot(dict)
    def save_shortcut_settings(self, new_shortcut_configs):  # Removed problematic type annotation
        """Save updated keyboard shortcut configurations."""
        if not ADVANCED_FEATURES_AVAILABLE or not self.keyboard_manager or not SETTINGS_AVAILABLE:
            logger.warning("Cannot save shortcut settings: feature or settings module not available.")
            return

        logger.info("Saving new keyboard shortcut settings.")
        # Update the keyboard manager's internal config and re-register shortcuts
        # The keyboard_manager.update_shortcut method handles the internal update and re-registration.
        # We need to apply these changes and then save the entire settings.
        # The keyboard_manager already has a load/save mechanism for its config.
        # We just need to tell the main settings manager to save the updated state from the keyboard manager.

        # Update keyboard manager's internal config (done by load_settings or update_shortcut)
        # For simplicity, let's just tell the keyboard manager to load this config,
        # which will handle updating internal state and re-registering shortcuts.
        # Assuming new_shortcut_configs is in the format expected by keyboard_manager.load_settings
        # It's a dict mapping ShortcutAction to (key_sequence_str, enabled).
        # keyboard_manager.load_settings expects a dict of {action_name: [key_sequence_str, enabled]}
        # Let's convert the received dict to the expected format.
        serializable_configs = {
             action.name: [key_sequence_str, enabled]
             for action, (key_sequence_str, enabled) in new_shortcut_configs.items()
        }

        self.keyboard_manager.load_settings(serializable_configs) # Update keyboard manager

        # Update the keyboard_shortcuts entry in the main settings dictionary
        self.settings["keyboard_shortcuts"] = self.keyboard_manager.save_settings() # Get serializable state from KM

        # Save the entire settings
        if save_settings(self.settings):
            logger.info("Keyboard shortcut settings saved successfully.")
        else:
            self.error_reporter.report_error("Failed to save keyboard shortcut settings.", severity=ErrorSeverity.ERROR)


    # --- Error Handling ---

    @pyqtSlot(str, str, ErrorSeverity)
    def _handle_error_reported(self, message: str, details: str, severity: ErrorSeverity):
        """Handle errors reported by the ErrorReporter."""
        # Log the error (already done by ErrorReporter)
        # logger.log(getattr(logging, severity.name), f"Error: {message}\nDetails: {details}")

        # Decide how to present the error to the user based on severity
        if self.main_window:
            if severity in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
                 # Show a modal error dialog for errors and critical errors
                 dialog = ErrorDialog(message, details, parent=self.main_window)
                 dialog.exec() # Show the dialog

            elif severity == ErrorSeverity.WARNING:
                 # Show a non-modal message (e.g., in status bar or a temporary notification)
                 # Or a simple warning message box
                 QMessageBox.warning(self.main_window, f"{APP_NAME} - Warning", f"{message}\n\nDetails: {details}")

            elif severity == ErrorSeverity.INFO:
                 # Show an information message (e.g., in status bar or tray notification)
                 if ADVANCED_FEATURES_AVAILABLE and self.system_tray_manager:
                      self.system_tray_manager.show_message(f"{APP_NAME} - Information", message, NotificationType.INFO)
                 else:
                      logger.info(f"Info: {message}") # Just log if tray not available


    # --- Recent Files Handling ---

    @pyqtSlot(str)
    def _handle_recent_file_open(self, file_path: str):
        """Handle request to open a recent file."""
        logger.info(f"Handling request to open recent file: {file_path}")
        # Delegate the actual file opening logic to the MainWindow
        if self.main_window and hasattr(self.main_window, 'handle_file_open_request'):
             self.main_window.handle_file_open_request(file_path)
        else:
             logger.warning("Main window or file open handler not available. Cannot open recent file.")
             if self.main_window:
                  QMessageBox.warning(self.main_window, "Cannot Open File",
                                     f"Could not open the recent file:\n{file_path}\n\nFile opening functionality is not available.")


    @pyqtSlot(list)
    def _update_recent_files_menu(self, recent_files: list):
        """Update the recent files menu in the UI."""
        if self.main_window and hasattr(self.main_window, 'recent_files_menu') and self.main_window.recent_files_menu:
             logger.debug(f"Updating recent files menu with {len(recent_files)} files.")
             self.main_window.recent_files_menu.update_menu(recent_files)
        else:
             logger.debug("Recent files menu not available in main window. Skipping menu update.")


    @pyqtSlot()
    def clear_recent_files(self):
        """Handle request to clear the recent files list."""
        if ADVANCED_FEATURES_AVAILABLE and self.recent_files_manager:
            self.recent_files_manager.clear_recent_files()
            logger.info("Recent files list cleared by user request.")
            # The recent_files_changed signal will trigger the menu update


    # --- System Tray Handling ---

    @pyqtSlot(QSystemTrayIcon.ActivationReason)
    def _handle_tray_icon_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Handle system tray icon activation (click)."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger or reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Restore/show the main window when the icon is clicked/double-clicked
            if self.main_window:
                 self.main_window.showNormal() # Restore from minimized/hidden state
                 self.main_window.activateWindow() # Bring to front


    @pyqtSlot()
    def _handle_tray_message_clicked(self):
        """Handle click on a system tray notification message."""
        logger.debug("System tray message clicked.")
        # Depending on the message content, you might want to perform an action,
        # like showing the main window, opening a log file, etc.
        # For now, just show the main window.
        if self.main_window:
            self.main_window.showNormal()
            self.main_window.activateWindow()


    # --- Auto-Update Handling ---

    @pyqtSlot(UpdateStatus, object)
    def _handle_update_status_changed(self, status: UpdateStatus, message: str):
        """Handle changes in auto-updater status."""
        logger.info(f"Auto-updater status changed: {status.name} - {message or ''}")
        # Update UI elements that show update status
        # The main_window._handle_update_ui_status method is connected to self.update_status_updated signal.
        self.update_status_updated.emit(status, message)

        # If an update is ready to install, potentially prompt the user
        if status == UpdateStatus.READY_TO_INSTALL:
            if self.main_window:
                 reply = QMessageBox.information(self.main_window, "Update Ready",
                                                 f"Version {message} is ready to install.\n\nInstall now and restart?",
                                                 QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                 if reply == QMessageBox.StandardButton.Yes:
                      self.auto_updater.install_update()


    # --- Keyboard Shortcut Handling ---

    @pyqtSlot(object)
    def _handle_shortcut_activated(self, action: ShortcutAction):
        """Handle activation of a keyboard shortcut."""
        logger.debug(f"Shortcut activated: {action.name}")

        # Perform the action associated with the shortcut
        if not self.main_window or not BATCH_AVAILABLE or not self.batch_processor:
             logger.warning(f"Cannot execute shortcut action {action.name}: Main window or batch processor unavailable.")
             return # Cannot execute actions without main window or batch processor


        if action == ShortcutAction.START_BATCH:
             # Get URLs from input field (assuming main window has this)
             urls_text = self.main_window.urls_input.toPlainText() if hasattr(self.main_window, 'urls_input') else ""
             urls = [url.strip() for url in urls_text.splitlines() if url.strip()]
             self.start_batch(urls)
        elif action == ShortcutAction.PAUSE_BATCH:
             self.pause_batch() # Toggles pause/resume
        elif action == ShortcutAction.CANCEL_BATCH:
             self.cancel_batch()
        elif action == ShortcutAction.SHOW_SETTINGS:
             self.show_settings_dialog()
        elif action == ShortcutAction.SHOW_ABOUT:
             self.show_about_dialog()
        elif action == ShortcutAction.SHOW_HELP:
             self.show_help()
        elif action == ShortcutAction.ADD_URLS_FROM_CLIPBOARD:
             if hasattr(self.main_window, '_paste_from_clipboard'):
                  self.main_window._paste_from_clipboard() # Use the UI's paste method
             else:
                  logger.warning("Cannot paste from clipboard: UI method not available.")
        elif action == ShortcutAction.CLEAR_INPUT:
             if hasattr(self.main_window, 'clear_urls_input'):
                  self.main_window.clear_urls_input() # Use the UI's method to clear input
             else:
                  logger.warning("Cannot clear input: UI method not available.")
        elif action == ShortcutAction.SHOW_SHORTCUTS:
             self.show_shortcut_config_dialog()
        elif action == ShortcutAction.PASS_THROUGH:
             logger.debug("Shortcut action PASS_THROUGH ignored.")
             pass # Do nothing for pass-through actions


    # --- Helper Slots/Methods ---

    @pyqtSlot(str)
    def _handle_output_dir_changed(self, new_dir: str):
        """Handle changes to the output directory setting from the UI."""
        logger.debug(f"Output directory changed via UI: {new_dir}")
        # Update the setting in the manager's settings dictionary
        self.settings["output_dir"] = new_dir
        # Save the updated setting (optional, could save only on app exit)
        # if SETTINGS_AVAILABLE:
        #      save_settings(self.settings)


# --- Application Entry Point ---

def main():
    """Main entry point for the application."""
    # Configure root logger early
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger.info("Application started.")

    # Ensure application data directory exists before loading settings or other components
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # Set application metadata for QSettings
    QCoreApplication.setOrganizationName("YourCompanyName") # Replace with your organization name
    QCoreApplication.setApplicationName(APP_NAME if 'APP_NAME' in globals() else "Application")
    if 'APP_VERSION' in globals():
         QCoreApplication.setApplicationVersion(APP_VERSION)

    # Create the QApplication instance
    app = QApplication(sys.argv)

    # Create and show splash screen (if available)
    splash = create_splash_screen(app) if SPLASH_AVAILABLE else None
    if splash:
         splash.show()
         logger.debug("Splash screen shown.")
         # Process events to ensure splash screen is visible
         app.processEvents()


    # Initialize the ApplicationManager
    # Pass the splash screen to the manager so it can hide it when ready
    app_manager = ApplicationManager(app, splash=splash)

    # Start the application event loop
    app_manager.run()

    logger.info("Application finished.")


# Example usage (run the application):
# if __name__ == '__main__':
#     main()
