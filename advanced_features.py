"""
Advanced features for YouTube Transcriber Pro.
Provides professional-level enhancements like recent files management,
auto-updates, system tray integration, keyboard shortcuts, session management,
and error reporting.
"""

import os
import sys
import json
import time
import logging
import platform
import traceback
import tempfile
import shutil
import socket
import threading
import subprocess
import webbrowser
from enum import Enum, auto
from typing import List, Dict, Any, Optional, Callable, Union, Tuple
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError
import ssl # Added for SSL context

from PyQt6.QtCore import (
    Qt, QObject, QSettings, QTimer, QSize, QPoint, QRect, QUrl, QEvent,
    QStandardPaths, QPropertyAnimation, QEasingCurve, QThread, pyqtSignal,
    pyqtSlot, QByteArray, QBuffer, QModelIndex, QSortFilterProxyModel,
    QShortcut
)
from PyQt6.QtGui import (
    QIcon, QAction, QPixmap, QDesktopServices, QFont,
    QColor, QCloseEvent, QImage, QFontMetrics, QMovie, QStandardItemModel,
    QStandardItem, QKeySequence
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QMenu, QSystemTrayIcon, QLabel,
    QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout, QListWidget,
    QListWidgetItem, QDialogButtonBox, QLineEdit, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QSizePolicy, QAbstractSpinBox, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QPushButton, QMessageBox
)

# Local application imports
# Ensure these imports match your file structure
try:
    # Import necessary classes and constants from ui and settings
    # Assuming SettingsDialog, AboutDialog, ErrorDialog, ShortcutConfigDialog are defined in ui.py
    from ui import (
        APP_NAME, APP_VERSION, SettingsDialog, AboutDialog, ErrorDialog,
        ShortcutConfigDialog, TaskStatus, BatchStatus, AVAILABLE_LANGUAGES, VALID_MODELS
    )
    from settings import load_settings, save_settings, DEFAULT_SETTINGS, APP_DATA_DIR
    from styles import style_manager, ColorRole, Spacing, Dimensions, IconSet, AnimationPresets # Import style components

    UI_COMPONENTS_AVAILABLE = True
except ImportError as e:
    logging.critical(f"Failed to import UI/Settings components into advanced_features: {e}. Some features may be disabled.")
    UI_COMPONENTS_AVAILABLE = False
    # Define mock/fallback classes and constants if imports fail
    APP_NAME = "Application"
    APP_VERSION = "N/A"
    DEFAULT_SETTINGS = {}
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".ytpro_default_app_data")
    load_settings = lambda: {}
    save_settings = lambda s: False
    TaskStatus = Enum("TaskStatus", ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "SKIPPED", "PAUSED", "RETRYING", "VALIDATING", "DOWNLOADING", "CONVERTING", "TRANSCRIBING", "TRANSLATING", "EXPORTING"])
    BatchStatus = Enum("BatchStatus", ["IDLE", "RUNNING", "PAUSED", "RESUMING", "COMPLETED", "CANCELLED", "FAILED", "THROTTLED", "STOPPING"])
    AVAILABLE_LANGUAGES = {"None": "None", "en": "English"}
    VALID_MODELS = ["small"]
    # Mock dialog classes if not available from ui
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
    # Mock style components if not available
    class MockStyleManager:
        def create_modern_button(self, *args, **kwargs): return QPushButton(*args, **kwargs)
        def create_status_indicator(self, status_type, parent=None): return QLabel(parent)
        def apply_card_style(self, widget): pass
        def apply_scrollable_style(self, widget): pass
        def apply_task_item_style(self, widget): pass
        def get_icon(self, name): return QIcon()
        
        class typography:
            @staticmethod
            def get_font(*args, **kwargs): 
                return QFont()
        
        class FontWeight:
            THIN, EXTRA_LIGHT, LIGHT, NORMAL, MEDIUM, DEMI_BOLD, BOLD, EXTRA_BOLD, BLACK = 0,1,2,3,4,5,6,7,8
    
    style_manager = MockStyleManager()
    
    class MockSpacing: 
        XXS, XS, S, M, L, XL, XXL = 2, 4, 8, 12, 16, 24, 32
    
    class MockDimensions: 
        ICON_SIZE_SMALL, ICON_SIZE_MEDIUM, ICON_SIZE_LARGE = QSize(16,16), QSize(24,24), QSize(32,32)
        DIALOG_MIN_WIDTH, DIALOG_MIN_HEIGHT = 400, 300
    
    class MockIconSet:
        ICON_ADD, ICON_REMOVE, ICON_EDIT, ICON_SAVE, ICON_OPEN, ICON_SETTINGS, ICON_REFRESH, ICON_CANCEL, ICON_BROWSE, ICON_CLIPBOARD = [""] * 10
        
        @staticmethod
        def get_icon(name): return QIcon()
    
    class MockAnimationPresets: 
        DURATION_M = 250
        @staticmethod
        def fade_in(widget, duration): return None
        @staticmethod
        def fade_out(widget, duration): return None
        EASE_OUT, EASE_IN = QEasingCurve.Type.Linear, QEasingCurve.Type.Linear
    
    Spacing = MockSpacing()
    Dimensions = MockDimensions()
    IconSet = MockIconSet()
    AnimationPresets = MockAnimationPresets()
    ColorRole = Enum("ColorRole", ["PRIMARY", "SECONDARY", "SUCCESS", "WARNING", "ERROR", "INFO", "BACKGROUND", "BACKGROUND_ALT", "BACKGROUND_HOVER", "BACKGROUND_PRESSED", "FOREGROUND", "FOREGROUND_DIM", "FOREGROUND_DISABLED", "BORDER", "BORDER_LIGHT", "BORDER_DARK", "SHADOW", "HIGHLIGHT", "HIGHLIGHTED_TEXT", "TOOLTIP_BG", "TOOLTIP_FG"])


# Setup logger
logger = logging.getLogger(__name__)

# --- Enums for Advanced Features ---

class UpdateStatus(Enum):
    """Represents the status of the auto-updater."""
    NO_UPDATE = auto()
    CHECKING = auto()
    UPDATE_AVAILABLE = auto()
    DOWNLOADING = auto()
    READY_TO_INSTALL = auto()
    ERROR = auto()
    DISABLED = auto() # Added for clarity when updates are disabled


class NotificationType(Enum):
    """Types of system tray notifications."""
    INFO = auto()
    WARNING = auto()
    CRITICAL = auto()


class ShortcutAction(Enum):
    """Defines available actions that can be assigned keyboard shortcuts."""
    START_BATCH = auto()
    PAUSE_BATCH = auto()
    CANCEL_BATCH = auto()
    SHOW_SETTINGS = auto()
    SHOW_ABOUT = auto()
    SHOW_HELP = auto()
    ADD_URLS_FROM_CLIPBOARD = auto()
    CLEAR_INPUT = auto()
    SHOW_SHORTCUTS = auto()
    PASS_THROUGH = auto() # Action for shortcuts that should be ignored by the manager


class ErrorSeverity(Enum):
    """Severity levels for reported errors."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()


# --- Recent Files Management ---

class RecentFilesManager(QObject):
    """Manages a list of recently accessed files or directories."""

    recent_files_changed = pyqtSignal(list) # Emits the updated list of recent files

    def __init__(self, max_files: int = 20, parent: Optional[QObject] = None):
        """
        Initialize the Recent Files Manager.

        Args:
            max_files: Maximum number of recent files to keep.
            parent: The parent QObject.
        """
        super().__init__(parent)
        self.max_files = max_files
        self._recent_files: List[str] = []
        self._settings = QSettings() # Use QSettings for persistent storage
        self._settings_key = "recent_files/list"
        self._max_files_key = "recent_files/max_files"

        # Load recent files from settings on startup
        self._load_recent_files()


    def _load_recent_files(self):
        """Load the list of recent files from application settings."""
        try:
            # Get max_files from settings first, fallback to instance value
            self.max_files = self._settings.value(self._max_files_key, self.max_files, type=int)

            recent_files_variant = self._settings.value(self._settings_key)
            if recent_files_variant is not None:
                # QSettings stores list as QVariantList, convert to Python list
                self._recent_files = [str(item) for item in recent_files_variant]
                # Filter out non-existent files and trim to max_files
                self._recent_files = [f for f in self._recent_files if os.path.exists(f)][:self.max_files]
                logger.debug(f"Loaded {len(self._recent_files)} recent files from settings.")
            else:
                self._recent_files = []
                logger.debug("No recent files found in settings.")

            self.recent_files_changed.emit(self._recent_files) # Emit initial list

        except Exception as e:
            logger.error(f"Failed to load recent files: {e}")
            self._recent_files = [] # Clear list on error


    def _save_recent_files(self):
        """Save the current list of recent files to application settings."""
        try:
            self._settings.setValue(self._settings_key, self._recent_files)
            self._settings.setValue(self._max_files_key, self.max_files) # Save max_files as well
            logger.debug(f"Saved {len(self._recent_files)} recent files to settings.")
        except Exception as e:
            logger.error(f"Failed to save recent files: {e}")


    def add_file(self, path: str):
        """Add a file or directory path to the list of recent files."""
        if not path or not os.path.exists(path):
            logger.warning(f"Attempted to add non-existent path to recent files: {path}")
            return

        # Ensure path is absolute and normalized
        path = os.path.abspath(path)

        if path in self._recent_files:
            # Move to the top if already exists
            self._recent_files.remove(path)

        self._recent_files.insert(0, path) # Add to the beginning
        self._recent_files = self._recent_files[:self.max_files] # Trim list to max_files

        self._save_recent_files() # Save changes
        self.recent_files_changed.emit(self._recent_files) # Notify listeners


    def get_recent_files(self) -> List[str]:
        """Get the current list of recent files."""
        return self._recent_files.copy() # Return a copy to prevent external modification


    def clear_recent_files(self):
        """Clear the entire list of recent files."""
        if self._recent_files:
            self._recent_files = []
            self._save_recent_files() # Save changes
            self.recent_files_changed.emit(self._recent_files) # Notify listeners
            logger.info("Recent files list cleared.")
        else:
            logger.debug("Recent files list is already empty.")

    def delete_file(self, path: str):
        """Remove a specific file path from the recent files list."""
        if path in self._recent_files:
             self._recent_files.remove(path)
             self._save_recent_files()
             self.recent_files_changed.emit(self._recent_files)
             logger.debug(f"Removed {path} from recent files.")


class RecentFilesMenu(QMenu):
    """A QMenu that displays a list of recent files."""

    file_opened = pyqtSignal(str) # Emitted when a recent file is selected
    clear_recent_files_requested = pyqtSignal() # Emitted when "Clear Recent Files" is selected

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the Recent Files Menu.

        Args:
            parent: The parent widget (usually the MainWindow).
        """
        super().__init__("&Recent Files", parent)
        self._actions: List[QAction] = [] # To keep track of actions
        self._clear_action: Optional[QAction] = None # Action to clear the list

        self.aboutToShow.connect(self._update_menu_before_show) # Update menu just before showing


    def update_menu(self, recent_files: List[str]):
        """Update the menu with the given list of recent files."""
        # Clear existing actions, except the "Clear" action if it exists
        for action in self._actions:
            self.removeAction(action)
            action.deleteLater() # Schedule for deletion
        self._actions = [] # Clear the list of actions

        if not recent_files:
            # Add a disabled "No recent files" action
            no_files_action = QAction("No Recent Files", self)
            no_files_action.setEnabled(False)
            self._actions.append(no_files_action)
            self.addAction(no_files_action)
        else:
            # Add actions for each recent file
            for i, file_path in enumerate(recent_files):
                # Use the file name as the action text, with a number prefix
                file_name = os.path.basename(file_path)
                action_text = f"&{i+1} {file_name}"
                action = QAction(action_text, self)
                action.setData(file_path) # Store the full path in action data
                action.setToolTip(file_path) # Show full path as tooltip
                action.triggered.connect(lambda checked, path=file_path: self.file_opened.emit(path)) # Connect signal

                self._actions.append(action)
                self.addAction(action)

        # Add separator and "Clear Recent Files" action if there are files
        if recent_files:
            self.addSeparator()
            if self._clear_action is None:
                 self._clear_action = QAction("C&lear Recent Files", self)
                 self._clear_action.triggered.connect(self.clear_recent_files_requested.emit) # Connect signal
            self.addAction(self._clear_action)
            self._clear_action.setEnabled(True) # Ensure it's enabled if there are files
        elif self._clear_action:
             self._clear_action.setEnabled(False) # Disable if no files


    @pyqtSlot()
    def _update_menu_before_show(self):
        """Slot called just before the menu is shown. Requests the latest list."""
        # The ApplicationManager should be connected to RecentFilesManager's
        # recent_files_changed signal and update this menu directly.
        # This slot might not be strictly necessary if the AppManager keeps the menu updated.
        # However, it can serve as a fallback to request the latest list if needed.
        logger.debug("Recent Files Menu about to show. Requesting latest list.")
        # This would require a signal from the menu back to the AppManager,
        # or the AppManager having a direct reference to this menu and calling update_menu.
        # The current design has AppManager listening to RecentFilesManager and calling update_menu.
        # So, this slot is likely redundant unless there's a reason the AppManager
        # might not have the absolute latest list right before the menu is shown.
        # Let's keep it simple for now and rely on the AppManager connection.
        pass


# --- Auto Update Feature ---

class AutoUpdater(QObject):
    """Handles checking for, downloading, and installing application updates."""

    update_status_changed = pyqtSignal(UpdateStatus, Optional[str]) # Status, message (e.g., version)
    notification_requested = pyqtSignal(str, str, NotificationType) # title, message, type

    def __init__(self, update_config: Dict[str, Any], parent: Optional[QObject] = None):
        """
        Initialize the Auto Updater.

        Args:
            update_config: Dictionary containing update settings.
            parent: The parent QObject.
        """
        super().__init__(parent)
        self.update_config = update_config
        self._current_status = UpdateStatus.NO_UPDATE
        self._update_info: Optional[Dict[str, Any]] = None # Store info about available update
        self._download_thread: Optional[QThread] = None # Thread for downloading
        self._install_thread: Optional[QThread] = None # Thread for installation

        self._update_timer = QTimer(self)
        self._update_timer.setSingleShot(False) # Repeat timer
        self._update_timer.timeout.connect(self.check_for_updates)

        self._start_update_timer() # Start the timer on initialization


    def _start_update_timer(self):
        """Start or restart the update check timer based on settings."""
        auto_check = self.update_config.get("auto_check", True)
        check_interval_hours = self.update_config.get("check_interval", 24) # Default 24 hours

        if auto_check and check_interval_hours > 0:
            interval_ms = check_interval_hours * 60 * 60 * 1000
            self._update_timer.start(interval_ms)
            logger.info(f"Auto update check enabled, checking every {check_interval_hours} hours.")
        else:
            self._update_timer.stop()
            self._current_status = UpdateStatus.DISABLED
            self.update_status_changed.emit(self._current_status, "Auto updates disabled.")
            logger.info("Auto update check disabled.")


    @pyqtSlot()
    def check_for_updates(self):
        """Check for available updates."""
        if self._current_status in [UpdateStatus.CHECKING, UpdateStatus.DOWNLOADING, UpdateStatus.READY_TO_INSTALL]:
            logger.debug("Update check already in progress or update ready.")
            return # Don't check if already busy

        update_url = self.update_config.get("update_url")
        if not update_url:
            logger.warning("Update URL not configured. Cannot check for updates.")
            self._current_status = UpdateStatus.ERROR
            self.update_status_changed.emit(self._current_status, "Update URL not configured.")
            return

        logger.info(f"Checking for updates from: {update_url}")
        self._current_status = UpdateStatus.CHECKING
        self.update_status_changed.emit(self._current_status, "Checking...")

        # Perform the check in a separate thread to avoid blocking the GUI
        check_thread = threading.Thread(target=self._perform_update_check, args=(update_url,))
        check_thread.daemon = True # Allow thread to exit with the application
        check_thread.start()


    def _perform_update_check(self, update_url: str):
        """Threaded function to perform the actual update check."""
        try:
            timeout = self.update_config.get("timeout", 10)
            verify_ssl = self.update_config.get("verify_ssl", True)

            # Create a default SSL context if verification is disabled (use with caution)
            if not verify_ssl:
                 ssl_context = ssl.create_default_context()
                 ssl_context.check_hostname = False
                 ssl_context.verify_mode = ssl.CERT_NONE
                 context = ssl_context
            else:
                 context = None # Use default SSL context

            req = Request(update_url, headers={'User-Agent': f'{APP_NAME}/{APP_VERSION}'})

            with urlopen(req, timeout=timeout, context=context) as response:
                if response.getcode() == 200:
                    update_data = json.loads(response.read().decode('utf-8'))
                    # Parse update data - assuming a simple structure like GitHub releases API
                    # Example: {"tag_name": "v1.1.0", "assets": [...], "body": "Release notes"}
                    latest_version = update_data.get("tag_name", "").lstrip("v") # Remove 'v' prefix
                    current_version = APP_VERSION.lstrip("v")

                    if latest_version and self._is_newer_version(latest_version, current_version):
                        logger.info(f"Update available: v{latest_version}")
                        self._current_status = UpdateStatus.UPDATE_AVAILABLE
                        self._update_info = update_data # Store the full update info
                        self.update_status_changed.emit(self._current_status, latest_version)
                        self.notification_requested.emit(f"{APP_NAME} Update Available", f"Version {latest_version} is available.", NotificationType.INFO)
                    else:
                        logger.info("No update available.")
                        self._current_status = UpdateStatus.NO_UPDATE
                        self._update_info = None
                        self.update_status_changed.emit(self._current_status, "No update available.")
                else:
                    logger.error(f"Failed to check for updates. HTTP Status: {response.getcode()}")
                    self._current_status = UpdateStatus.ERROR
                    self.update_status_changed.emit(self._current_status, f"HTTP Error: {response.getcode()}")

        except URLError as e:
            logger.error(f"Failed to check for updates. URL Error: {e.reason}")
            self._current_status = UpdateStatus.ERROR
            self.update_status_changed.emit(self._current_status, f"Network Error: {e.reason}")
        except socket.timeout:
            logger.error("Failed to check for updates. Request timed out.")
            self._current_status = UpdateStatus.ERROR
            self.update_status_changed.emit(self._current_status, "Request timed out.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during update check: {e}", exc_info=True)
            self._current_status = UpdateStatus.ERROR
            self.update_status_changed.emit(self._current_status, f"Error: {e}")

        # If auto-check is enabled and an error occurred, schedule a retry with a longer interval
        if self.update_config.get("auto_check", True) and self._current_status == UpdateStatus.ERROR:
             retry_delay_hours = self.update_config.get("retry_delay_hours", 6) # Default 6 hours retry
             retry_interval_ms = retry_delay_hours * 60 * 60 * 1000
             logger.warning(f"Update check failed, retrying in {retry_delay_hours} hours.")
             self._update_timer.start(retry_interval_ms) # Restart timer with retry delay


    def _is_newer_version(self, latest_version: str, current_version: str) -> bool:
        """Compares version strings (e.g., '1.1.0' vs '1.0.0')."""
        def parse_version(version_str):
            # Split by '.' and convert to integers, handling potential non-numeric parts
            parts = []
            for part in version_str.split('.'):
                 try:
                      parts.append(int(part))
                 except ValueError:
                      # Handle non-numeric parts (e.g., '1.0.0-beta') - treat them as smaller
                      parts.append(-1) # Use a value smaller than any valid integer version part
            return parts

        try:
            latest_parts = parse_version(latest_version)
            current_parts = parse_version(current_version)

            # Pad the shorter list with zeros for comparison
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))

            for i in range(max_len):
                if latest_parts[i] > current_parts[i]:
                    return True
                if latest_parts[i] < current_parts[i]:
                    return False
            return False # Versions are equal
        except Exception as e:
            logger.error(f"Error comparing versions '{latest_version}' and '{current_version}': {e}")
            return False # Assume not newer on error


    @pyqtSlot()
    def download_update(self):
        """Download the available update."""
        if self._current_status != UpdateStatus.UPDATE_AVAILABLE or not self._update_info:
            logger.warning("No update available to download.")
            return

        # Find the appropriate asset URL for the current platform (e.g., .exe for Windows, .dmg for macOS)
        # This logic depends heavily on how your releases are structured.
        # Assuming assets is a list of dicts, each with 'name' and 'browser_download_url'
        download_url = None
        assets = self._update_info.get("assets", [])
        platform_suffix = {
            "Windows": ".exe",
            "Darwin": ".dmg", # macOS
            "Linux": ".tar.gz" # Example for Linux
        }.get(platform.system())

        if platform_suffix:
             for asset in assets:
                  if asset.get("name", "").endswith(platform_suffix):
                       download_url = asset.get("browser_download_url")
                       break

        if not download_url:
             logger.error(f"No suitable update asset found for platform: {platform.system()}")
             self._current_status = UpdateStatus.ERROR
             self.update_status_changed.emit(self._current_status, "No suitable asset found.")
             return


        logger.info(f"Downloading update from: {download_url}")
        self._current_status = UpdateStatus.DOWNLOADING
        self.update_status_changed.emit(self._current_status, "Downloading...")

        # Download in a separate thread (using a QThread for better integration with Qt event loop)
        self._download_thread = QThread()
        downloader_worker = UpdateDownloaderWorker(download_url)
        downloader_worker.moveToThread(self._download_thread)

        downloader_worker.download_progress.connect(lambda progress: self.update_status_changed.emit(UpdateStatus.DOWNLOADING, f"Downloading... {progress}%"))
        downloader_worker.download_finished.connect(self._handle_download_finished)
        downloader_worker.download_failed.connect(self._handle_download_failed)

        self._download_thread.started.connect(downloader_worker.run)
        self._download_thread.finished.connect(self._download_thread.deleteLater) # Clean up thread object

        self._download_thread.start()


    @pyqtSlot(str)
    def _handle_download_finished(self, download_path: str):
        """Slot to handle successful update download."""
        logger.info(f"Update downloaded successfully to: {download_path}")
        self._current_status = UpdateStatus.READY_TO_INSTALL
        self._update_info["download_path"] = download_path # Store download path
        self.update_status_changed.emit(self._current_status, "Download complete. Ready to install.")
        self.notification_requested.emit("Update Ready", "Update downloaded. Ready to install.", NotificationType.INFO)

        self._download_thread = None # Clear thread reference


    @pyqtSlot(str)
    def _handle_download_failed(self, error_message: str):
        """Slot to handle failed update download."""
        logger.error(f"Update download failed: {error_message}")
        self._current_status = UpdateStatus.ERROR
        self.update_status_changed.emit(self._current_status, f"Download failed: {error_message}")
        self.notification_requested.emit("Update Failed", f"Download failed: {error_message}", NotificationType.CRITICAL)

        self._download_thread = None # Clear thread reference


    @pyqtSlot()
    def install_update(self):
        """Install the downloaded update."""
        if self._current_status != UpdateStatus.READY_TO_INSTALL or not self._update_info or "download_path" not in self._update_info:
            logger.warning("No update ready to install.")
            return

        download_path = self._update_info["download_path"]
        if not os.path.exists(download_path):
            logger.error(f"Downloaded update file not found: {download_path}")
            self._current_status = UpdateStatus.ERROR
            self.update_status_changed.emit(self._current_status, "Downloaded file not found.")
            return

        logger.info(f"Installing update from: {download_path}")
        self._current_status = UpdateStatus.CHECKING # Use checking status during install
        self.update_status_changed.emit(self._current_status, "Installing...")

        # Installation process is platform-dependent and usually involves running the downloaded file
        # This often requires elevated privileges and restarting the application.
        # A common approach is to run the installer and then exit the current application instance.
        try:
            if platform.system() == "Windows":
                # Run the installer executable
                subprocess.Popen([download_path])
            elif platform.system() == "Darwin": # macOS
                 # Open the .dmg file
                 subprocess.Popen(['open', download_path])
            elif platform.system() == "Linux":
                 # This is highly distribution-dependent. For a simple tar.gz,
                 # you might need a separate installer script or instruct the user.
                 # For AppImage, just make it executable and run it.
                 # Example for AppImage:
                 # os.chmod(download_path, 0o755) # Make executable
                 # subprocess.Popen([download_path])
                 logger.warning(f"Automatic update installation not fully implemented for Linux. Please run {download_path} manually.")
                 QMessageBox.information(None, "Manual Update Required",
                                         f"Please run the downloaded update file manually:\n{download_path}")
                 self._current_status = UpdateStatus.ERROR # Mark as error as automatic install failed
                 self.update_status_changed.emit(self._current_status, "Manual installation required.")
                 return # Don't exit if manual install is needed

            # If automatic installation was initiated, exit the current application
            logger.info("Update installation initiated. Exiting application.")
            QApplication.instance().quit()

        except Exception as e:
            logger.error(f"Failed to initiate update installation: {e}", exc_info=True)
            self._current_status = UpdateStatus.ERROR
            self.update_status_changed.emit(self._current_status, f"Installation failed: {e}")


    def get_update_status(self) -> UpdateStatus:
        """Get the current status of the auto-updater."""
        return self._current_status


class UpdateDownloaderWorker(QObject):
    """Worker object for downloading update files in a separate thread."""

    download_progress = pyqtSignal(int) # Emits progress percentage (0-100)
    download_finished = pyqtSignal(str) # Emits the path to the downloaded file
    download_failed = pyqtSignal(str) # Emits an error message

    def __init__(self, url: str, parent: Optional[QObject] = None):
        super().__init__(parent)
        self.url = url
        self._stop_event = threading.Event() # Event to signal stopping the download

    def stop(self):
        """Signal the worker to stop the download."""
        self._stop_event.set()

    @pyqtSlot()
    def run(self):
        """The main download logic running in the thread."""
        logger.debug(f"Update downloader worker started for: {self.url}")
        temp_dir = None
        download_path = None

        try:
            # Create a temporary file to save the download
            temp_dir = tempfile.mkdtemp(prefix="ytpro_update_")
            # Get filename from URL
            filename = self.url.split('/')[-1] or "update_file"
            download_path = os.path.join(temp_dir, filename)

            req = Request(self.url, headers={'User-Agent': f'{APP_NAME}/{APP_VERSION}'})

            with urlopen(req, timeout=600) as response, open(download_path, 'wb') as out_file:
                total_size = int(response.getheader('Content-Length', 0))
                downloaded_size = 0
                block_size = 8192 # 8 KB chunks

                start_time = time.time()
                last_progress_update_time = time.time()

                while True:
                    if self._stop_event.is_set():
                        logger.warning("Update download cancelled.")
                        self.download_failed.emit("Download cancelled.")
                        return # Exit the thread

                    buffer = response.read(block_size)
                    if not buffer:
                        break # End of file

                    out_file.write(buffer)
                    downloaded_size += len(buffer)

                    # Report progress periodically
                    current_time = time.time()
                    if current_time - last_progress_update_time > 0.5: # Update every 0.5 seconds
                         progress_percent = (downloaded_size / total_size) * 100 if total_size > 0 else 0
                         self.download_progress.emit(int(progress_percent))
                         last_progress_update_time = current_time


            logger.debug(f"Update download finished: {download_path}")
            self.download_finished.emit(download_path) # Emit success signal

        except URLError as e:
            logger.error(f"Update download URL Error: {e.reason}")
            self.download_failed.emit(f"Network Error: {e.reason}")
        except socket.timeout:
            logger.error("Update download timed out.")
            self.download_failed.emit("Download timed out.")
        except Exception as e:
            logger.error(f"An unexpected error occurred during update download: {e}", exc_info=True)
            self.download_failed.emit(f"Download failed: {e}")

        finally:
            # Clean up temporary directory if download failed or was cancelled
            if self._stop_event.is_set() or download_path is None or not os.path.exists(download_path):
                 if temp_dir and os.path.exists(temp_dir):
                      try:
                           shutil.rmtree(temp_dir)
                           logger.debug(f"Cleaned up temporary download directory: {temp_dir}")
                      except Exception as e:
                           logger.warning(f"Failed to clean up temporary download directory {temp_dir}: {e}")


# --- System Tray Management ---

class SystemTrayManager(QObject):
    """Manages the application's system tray icon and notifications."""

    # Signals for tray icon activation (e.g., restore window)
    tray_icon_activated = pyqtSignal(QSystemTrayIcon.ActivationReason)
    message_clicked = pyqtSignal() # Emitted when a tray message is clicked

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the System Tray Manager.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._tray_icon: Optional[QSystemTrayIcon] = None
        self._tray_menu: Optional[QMenu] = None
        self._main_window: Optional[QMainWindow] = None # Reference to the main window

        # Create the system tray icon (only if supported by the system)
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._tray_icon = QSystemTrayIcon(self)
            self._tray_icon.setIcon(IconSet.get_icon(IconSet.APP_ICON) if IconSet else QIcon())
            self._tray_icon.setToolTip(APP_NAME)

            # Create the context menu
            self._tray_menu = QMenu()
            self._tray_icon.setContextMenu(self._tray_menu)

            # Connect signals
            self._tray_icon.activated.connect(self.tray_icon_activated)
            self._tray_icon.messageClicked.connect(self.message_clicked)

            # Show the icon
            self._tray_icon.show()
            logger.info("System tray icon created and shown.")
        else:
            logger.warning("System tray is not available on this system.")


    def set_main_window(self, window: QMainWindow):
        """Set the reference to the main application window."""
        self._main_window = window
        self._create_tray_menu() # Create the menu after window is set


    def _create_tray_menu(self):
        """Create the context menu for the system tray icon."""
        if not self._tray_menu or not self._main_window:
            return

        self._tray_menu.clear() # Clear existing actions

        # Restore/Show Window Action
        restore_action = QAction("&Show/Restore Window", self)
        restore_action.triggered.connect(self._main_window.showNormal) # Show the window
        self._tray_menu.addAction(restore_action)

        self._tray_menu.addSeparator()

        # Exit Action
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit) # Quit the application
        self._tray_menu.addAction(exit_action)


    def show_message(self, title: str, message: str, type: NotificationType = NotificationType.INFO):
        """Show a system tray notification message."""
        if self._tray_icon:
            icon_type = QSystemTrayIcon.MessageIcon.Information # Default icon

            if type == NotificationType.WARNING:
                icon_type = QSystemTrayIcon.MessageIcon.Warning
            elif type == NotificationType.CRITICAL:
                icon_type = QSystemTrayIcon.MessageIcon.Critical

            self._tray_icon.showMessage(title, message, icon_type, 5000) # Show for 5 seconds
            logger.debug(f"System Tray Message: {title} - {message} ({type.name})")
        else:
            logger.warning(f"System Tray Message (Tray not available): {title} - {message} ({type.name})")


# --- Keyboard Shortcut Management ---

class KeyboardManager(QObject):
    """Manages application-wide keyboard shortcuts."""

    shortcut_activated = pyqtSignal(ShortcutAction) # Emits the action of the activated shortcut

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the Keyboard Manager.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._main_window: Optional[QMainWindow] = None # Reference to the main window
        self._shortcuts: Dict[ShortcutAction, QShortcut] = {} # Dictionary to hold QShortcut objects
        # Default shortcut configurations (action: (key_sequence_str, enabled))
        self._default_configs: Dict[ShortcutAction, Tuple[str, bool]] = {
            ShortcutAction.START_BATCH: ("Ctrl+R", True),
            ShortcutAction.PAUSE_BATCH: ("Ctrl+P", True),
            ShortcutAction.CANCEL_BATCH: ("Ctrl+C", True),
            ShortcutAction.SHOW_SETTINGS: ("Ctrl+,", True),
            ShortcutAction.SHOW_ABOUT: ("Ctrl+A", True),
            ShortcutAction.SHOW_HELP: ("F1", True),
            ShortcutAction.ADD_URLS_FROM_CLIPBOARD: ("Ctrl+Shift+V", True),
            ShortcutAction.CLEAR_INPUT: ("Ctrl+L", True),
            ShortcutAction.SHOW_SHORTCUTS: ("Ctrl+Shift+S", True),
            # Add more default shortcuts here
        }
        self._current_configs = self._default_configs.copy() # Start with default configs


    def set_main_window(self, window: QMainWindow):
        """Set the main window and register shortcuts."""
        if self._main_window is not None:
             logger.warning("Main window already set in KeyboardManager. Clearing existing shortcuts.")
             self.clear_shortcuts() # Clear existing shortcuts before setting a new window

        self._main_window = window
        if self._main_window:
             logger.info("Main window set in KeyboardManager. Registering shortcuts.")
             self._register_shortcuts()
        else:
             logger.warning("Main window set to None in KeyboardManager.")


    def _register_shortcuts(self):
        """Register QShortcut objects with the main window based on current configurations."""
        if not self._main_window:
            logger.warning("Cannot register shortcuts: Main window is not set.")
            return

        # Clear existing QShortcut objects before re-registering
        self.clear_shortcuts()

        for action, (key_sequence_str, enabled) in self._current_configs.items():
            if key_sequence_str:
                try:
                    key_sequence = QKeySequence(key_sequence_str)
                    if not key_sequence.isEmpty():
                        # Create QShortcut attached to the main window
                        shortcut = QShortcut(key_sequence, self._main_window)
                        shortcut.setEnabled(enabled)
                        # Store the action in the shortcut's properties for easy retrieval
                        shortcut.setProperty("shortcut_action", action.value)
                        # Connect the activated signal to a handler
                        shortcut.activated.connect(lambda a=action: self.shortcut_activated.emit(a))

                        self._shortcuts[action] = shortcut
                        logger.debug(f"Registered shortcut for {action.name}: {key_sequence_str} (Enabled: {enabled})")
                    else:
                        logger.warning(f"Invalid key sequence for {action.name}: '{key_sequence_str}'. Skipping registration.")
                except Exception as e:
                    logger.error(f"Error registering shortcut for {action.name} ('{key_sequence_str}'): {e}")


    def clear_shortcuts(self):
        """Remove all registered QShortcut objects."""
        for shortcut in self._shortcuts.values():
            if shortcut:
                try:
                    shortcut.activated.disconnect() # Disconnect signal
                    shortcut.setKey(QKeySequence()) # Clear the key sequence
                    shortcut.setEnabled(False) # Disable
                    shortcut.deleteLater() # Schedule for deletion
                except Exception as e:
                    logger.warning(f"Error cleaning up shortcut: {e}")

        self._shortcuts.clear()
        logger.debug("Cleared all registered shortcuts.")


    def get_all_shortcuts(self) -> Dict[ShortcutAction, Tuple[str, bool]]:
        """Get the current configuration of all shortcuts."""
        return self._current_configs.copy()


    def get_shortcut_key_sequence(self, action: ShortcutAction) -> str:
        """Get the key sequence string for a specific shortcut action."""
        return self._current_configs.get(action, ("", False))[0]


    def update_shortcut(self, action: ShortcutAction, key_sequence_str: str, enabled: bool) -> bool:
        """
        Update the key sequence and enabled state for a specific shortcut action.
        Re-registers the shortcut after updating.

        Args:
            action: The shortcut action to update.
            key_sequence_str: The new key sequence string (e.g., "Ctrl+S").
            enabled: The new enabled state.

        Returns:
            True if the shortcut was updated successfully, False otherwise.
        """
        if action not in self._default_configs:
            logger.error(f"Cannot update unknown shortcut action: {action.name}")
            return False

        # Validate the new key sequence (optional but recommended)
        new_key_sequence = QKeySequence(key_sequence_str)
        if key_sequence_str and new_key_sequence.isEmpty():
             logger.warning(f"Invalid key sequence provided for {action.name}: '{key_sequence_str}'. Shortcut will be disabled.")
             # Continue, but the shortcut will be effectively disabled if the string is invalid

        # Check for conflicts with existing shortcuts (optional but recommended)
        # Iterate through other shortcuts and see if their key sequence matches the new one
        for other_action, (other_key_seq_str, other_enabled) in self._current_configs.items():
             if other_action != action and other_enabled and enabled and other_key_seq_str == key_sequence_str and key_sequence_str:
                  logger.warning(f"Shortcut conflict detected: '{key_sequence_str}' for {action.name} conflicts with {other_action.name}.")
                  # You might want to inform the user via a message box here
                  # For now, just log the warning and allow the conflict (Qt handles which one gets activated)
                  # A more robust solution would prevent saving conflicting shortcuts


        # Update the configuration
        self._current_configs[action] = (key_sequence_str, enabled)
        logger.debug(f"Updated config for {action.name}: {key_sequence_str} (Enabled: {enabled})")

        # Re-register all shortcuts to apply the change
        self._register_shortcuts()

        return True


    def load_settings(self, settings: Dict[str, Any]):
        """Load shortcut configurations from settings."""
        logger.info("Loading keyboard shortcut settings.")
        loaded_configs = {}
        for action_name, config in settings.items():
            try:
                # Find the corresponding ShortcutAction enum member
                action = ShortcutAction[action_name] if action_name in ShortcutAction.__members__ else None
                if action and isinstance(config, list) and len(config) == 2:
                    key_sequence_str, enabled = config
                    if isinstance(key_sequence_str, str) and isinstance(enabled, bool):
                        loaded_configs[action] = (key_sequence_str, enabled)
                    else:
                        logger.warning(f"Invalid format for shortcut setting for {action_name}: {config}. Skipping.")
                elif action:
                    logger.warning(f"Invalid format for shortcut setting for {action_name}: {config}. Skipping.")
                else:
                    logger.warning(f"Unknown shortcut action '{action_name}' in settings. Skipping.")
            except Exception as e:
                logger.error(f"Error loading shortcut setting for '{action_name}': {e}")

        # Merge loaded configs with default configs (loaded overrides default)
        self._current_configs = self._default_configs.copy()
        self._current_configs.update(loaded_configs)

        logger.info(f"Loaded {len(loaded_configs)} shortcut configurations from settings.")

        # Re-register shortcuts after loading settings
        self._register_shortcuts()


    def save_settings(self) -> Dict[str, Any]:
        """Save the current shortcut configurations to a serializable dictionary."""
        logger.info("Saving keyboard shortcut settings.")
        settings_data = {}
        for action, (key_sequence_str, enabled) in self._current_configs.items():
            # Save only if the action is valid
            if action in ShortcutAction:
                 settings_data[action.name] = [key_sequence_str, enabled]
            else:
                 logger.warning(f"Skipping save for invalid shortcut action: {action}")

        return settings_data


class ShortcutConfigDialog(QDialog):
    """Dialog for configuring keyboard shortcuts."""

    shortcuts_saved = pyqtSignal(dict) # Emits the new shortcut configuration dictionary

    def __init__(self, current_shortcuts: Dict[ShortcutAction, Tuple[str, bool]], parent: Optional[QWidget] = None):
        """
        Initialize the Shortcut Configuration Dialog.

        Args:
            current_shortcuts: Dictionary of current shortcut configurations.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Configure Shortcuts")
        self.setMinimumSize(500, 400)
        self._current_shortcuts = current_shortcuts.copy() # Work on a copy

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(Spacing.L, Spacing.L, Spacing.L, Spacing.L)
        self.layout.setSpacing(Spacing.M)

        self.heading = style_manager.create_modern_heading("Keyboard Shortcuts", self)
        self.layout.addWidget(self.heading)

        # Table to display and edit shortcuts
        self.shortcut_table = QTableWidget(self)
        self.shortcut_table.setColumnCount(3) # Action, Shortcut, Enabled
        self.shortcut_table.setHorizontalHeaderLabels(["Action", "Shortcut", "Enabled"])
        self.shortcut_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Stretch Action column
        self.shortcut_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents) # Resize Shortcut column
        self.shortcut_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents) # Resize Enabled column
        self.shortcut_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows) # Select entire row
        self.shortcut_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection) # Only one row selectable
        self.shortcut_table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel) # Smooth scrolling (optional)
        self.shortcut_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff) # Hide horizontal scroll bar


        # Populate the table
        self._populate_table()

        self.layout.addWidget(self.shortcut_table, 1) # Give table stretch factor

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel | QDialogButtonBox.StandardButton.RestoreDefaults)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.StandardButton.RestoreDefaults).clicked.connect(self._restore_defaults)

        self.layout.addWidget(self.button_box)


    def _populate_table(self):
        """Populate the table with current shortcut configurations."""
        # Sort shortcuts by action name for consistent display
        sorted_shortcuts = sorted(self._current_shortcuts.items(), key=lambda item: item[0].name)
        self.shortcut_table.setRowCount(len(sorted_shortcuts))

        for row, (action, (key_sequence_str, enabled)) in enumerate(sorted_shortcuts):
            # Action Name (Read-only)
            action_name_item = QTableWidgetItem(action.name.replace("_", " ").title())
            action_name_item.setFlags(action_name_item.flags() & ~Qt.ItemFlag.ItemIsEditable) # Make read-only
            self.shortcut_table.setItem(row, 0, action_name_item)

            # Shortcut Key Sequence (Editable)
            shortcut_item = QTableWidgetItem(key_sequence_str)
            # Add a delegate or custom editor for better key sequence input if needed
            # For now, just allow text editing
            self.shortcut_table.setItem(row, 1, shortcut_item)

            # Enabled Checkbox
            enabled_checkbox = QCheckBox(self)
            enabled_checkbox.setChecked(enabled)
            # Center the checkbox in the cell
            checkbox_widget = QWidget(self)
            checkbox_layout = QHBoxLayout(checkbox_widget)
            checkbox_layout.addWidget(enabled_checkbox)
            checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            checkbox_layout.setContentsMargins(0, 0, 0, 0)
            self.shortcut_table.setCellWidget(row, 2, checkbox_widget)

            # Store the action in the row's data (optional, but can be useful)
            # self.shortcut_table.verticalHeaderItem(row).setData(Qt.UserRole, action)


    def _restore_defaults(self):
        """Restore shortcut configurations to default values."""
        logger.info("Restoring shortcut defaults.")
        # Get default configs from KeyboardManager (assuming it's the parent or accessible)
        if self.parent() and hasattr(self.parent(), 'app_manager') and self.parent().app_manager and hasattr(self.parent().app_manager, 'keyboard_manager') and self.parent().app_manager.keyboard_manager:
             default_configs = self.parent().app_manager.keyboard_manager._default_configs.copy()
             self._current_shortcuts = default_configs
             self._populate_table() # Repopulate the table with defaults
        else:
             logger.warning("KeyboardManager not available to restore defaults.")
             QMessageBox.warning(self, "Restore Defaults", "Keyboard manager not available. Cannot restore defaults.")


    def accept(self):
        """Handle OK button click - collect and save shortcuts."""
        new_shortcuts_config: Dict[ShortcutAction, Tuple[str, bool]] = {}

        # Iterate through the table rows and collect the updated configurations
        # Iterate through the original sorted keys to maintain order
        sorted_actions = sorted(self._current_shortcuts.keys(), key=lambda action: action.name)

        for row, action in enumerate(sorted_actions):
            # Find the corresponding items and widget in the table
            action_name_item = self.shortcut_table.item(row, 0)
            shortcut_item = self.shortcut_table.item(row, 1)
            enabled_checkbox_widget = self.shortcut_table.cellWidget(row, 2)
            enabled_checkbox = enabled_checkbox_widget.findChild(QCheckBox) if enabled_checkbox_widget else None


            if action_name_item and shortcut_item and enabled_checkbox:
                # action_name = action_name_item.text().replace(" ", "_").upper() # Not needed, we have the action enum
                try:
                    # action = ShortcutAction[action_name] # Convert back to enum
                    key_sequence_str = shortcut_item.text().strip()
                    enabled = enabled_checkbox.isChecked()

                    # Basic validation for key sequence string
                    if key_sequence_str and QKeySequence(key_sequence_str).isEmpty():
                         logger.warning(f"Invalid key sequence entered for {action.name}: '{key_sequence_str}'. Saving as empty string.")
                         key_sequence_str = "" # Save as empty string if invalid

                    new_shortcuts_config[action] = (key_sequence_str, enabled)

                except KeyError:
                    logger.error(f"Internal error: Unknown action enum found in table processing: {action.name}. Skipping.")
                except Exception as e:
                    logger.error(f"Error collecting shortcut config for row {row} ({action.name}): {e}")


        # Emit signal with the new configuration
        self.shortcuts_saved.emit(new_shortcuts_config)

        # Close the dialog
        super().accept()

    def reject(self):
        """Handle Cancel button click - close without saving."""
        super().reject()


# --- Session Management ---

class SessionManager(QObject):
    """Manages saving and restoring the application session state."""

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the Session Manager.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        self._settings = QSettings() # Use QSettings for session data
        self._session_key = "session/state"
        self._geometry_key = "session/geometry"
        self._state_key = "session/window_state"


    def save_session(self, window: QMainWindow, data: Dict[str, Any]):
        """
        Save the current application session state.

        Args:
            window: The main application window.
            data: A dictionary containing application-specific state data.
        """
        logger.info("Saving application session.")
        try:
            # Save window geometry and state
            self._settings.setValue(self._geometry_key, window.saveGeometry())
            self._settings.setValue(self._state_key, window.saveState())

            # Save application-specific data (e.g., batch processor state)
            # Convert complex objects (like Enums) to serializable types
            serializable_data = self._prepare_for_serialization(data)
            self._settings.setValue(self._session_key, json.dumps(serializable_data))

            logger.info("Session saved successfully.")

        except Exception as e:
            logger.error(f"Failed to save application session: {e}", exc_info=True)


    def restore_session(self, window: QMainWindow) -> Dict[str, Any]:
        """
        Restore the application session state.

        Args:
            window: The main application window.

        Returns:
            A dictionary containing the restored application-specific state data.
        """
        logger.info("Restoring application session.")
        restored_data: Dict[str, Any] = {}

        try:
            # Restore window geometry and state
            geometry = self._settings.value(self._geometry_key)
            if geometry:
                window.restoreGeometry(geometry)
                logger.debug("Window geometry restored.")
            state = self._settings.value(self._state_key)
            if state:
                window.restoreState(state)
                logger.debug("Window state restored.")

            # Restore application-specific data
            session_data_json = self._settings.value(self._session_key)
            if session_data_json:
                try:
                    restored_data = json.loads(session_data_json)
                    # Convert serializable types back to original objects if needed
                    restored_data = self._restore_from_serialization(restored_data)
                    logger.info("Application-specific session data restored.")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode session data: {e}")
                    restored_data = {} # Return empty data on decode error

            logger.info("Session restoration complete.")
            return restored_data

        except Exception as e:
            logger.error(f"Failed to restore application session: {e}", exc_info=True)
            return {} # Return empty data on any restoration error


    def _prepare_for_serialization(self, data: Any) -> Any:
        """Recursively prepare data for JSON serialization."""
        if isinstance(data, dict):
            return {k: self._prepare_for_serialization(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._prepare_for_serialization(item) for item in data]
        elif isinstance(data, Enum):
            return {"__enum__": data.__class__.__name__, "value": data.value, "name": data.name}
        elif isinstance(data, QSize):
             return {"__qsize__": True, "width": data.width(), "height": data.height()}
        # Add more types as needed (e.g., QPoint, QRect)
        else:
            # Return primitive types directly
            return data

    def _restore_from_serialization(self, data: Any) -> Any:
        """Recursively restore data from JSON deserialization."""
        if isinstance(data, dict):
            if "__enum__" in data:
                # Restore Enum
                enum_name = data["__enum__"]
                enum_value = data["value"]
                enum_member_name = data["name"]
                try:
                    # Find the enum class by name (requires access to the class definition)
                    # This is a simplification; a robust solution might need a registry
                    # or pass available enum classes.
                    # For now, assume common enums are globally accessible or can be imported.
                    if enum_name == "TaskStatus" and 'TaskStatus' in globals():
                         return TaskStatus[enum_member_name]
                    elif enum_name == "BatchStatus" and 'BatchStatus' in globals():
                         return BatchStatus[enum_member_name]
                    elif enum_name == "UpdateStatus" and 'UpdateStatus' in globals():
                         return UpdateStatus[enum_member_name]
                    elif enum_name == "NotificationType" and 'NotificationType' in globals():
                         return NotificationType[enum_member_name]
                    elif enum_name == "ShortcutAction" and 'ShortcutAction' in globals():
                         return ShortcutAction[enum_member_name]
                    elif enum_name == "ErrorSeverity" and 'ErrorSeverity' in globals():
                         return ErrorSeverity[enum_member_name]
                    elif enum_name == "CacheType" and 'CacheType' in globals():
                         return CacheType[enum_member_name]
                    # Add other enum types here
                    else:
                         logger.warning(f"Unknown enum type during session restore: {enum_name}")
                         return None # Return None for unknown enums
                except (KeyError, AttributeError) as e:
                    logger.error(f"Failed to restore enum {enum_name}.{enum_member_name}: {e}")
                    return None # Return None on error
            elif "__qsize__" in data:
                 return QSize(data.get("width", 0), data.get("height", 0))
            # Add more types as needed
            else:
                # Recursively restore dictionary values
                return {k: self._restore_from_serialization(v) for k, v in data.items()}
        elif isinstance(data, list):
            # Recursively restore list items
            return [self._restore_from_serialization(item) for item in data]
        else:
            # Return primitive types directly
            return data


# --- Error Reporting ---

class ErrorReporter(QObject):
    """Centralized error reporting mechanism."""

    error_reported = pyqtSignal(str, str, ErrorSeverity) # Emits message, details, severity

    def __init__(self, parent: Optional[QObject] = None):
        """
        Initialize the Error Reporter.

        Args:
            parent: The parent QObject.
        """
        super().__init__(parent)
        # You might add logging configuration or other setup here
        # The main logging is typically configured in the application entry point.


    def report_error(self, message: str, details: str = "", severity: ErrorSeverity = ErrorSeverity.ERROR):
        """
        Report an error to the system.

        Args:
            message: A concise error message.
            details: Detailed information about the error (e.g., traceback).
            severity: The severity level of the error.
        """
        # Log the error
        if severity == ErrorSeverity.INFO:
            logger.info(f"Reported Info: {message}")
            if details: logger.info(f"Details: {details}")
        elif severity == ErrorSeverity.WARNING:
            logger.warning(f"Reported Warning: {message}")
            if details: logger.warning(f"Details: {details}")
        elif severity == ErrorSeverity.ERROR:
            logger.error(f"Reported Error: {message}")
            if details: logger.error(f"Details: {details}")
        elif severity == ErrorSeverity.CRITICAL:
            logger.critical(f"Reported Critical Error: {message}")
            if details: logger.critical(f"Details: {details}")

        # Emit signal for UI or other components to handle
        self.error_reported.emit(message, details, severity)

        # For critical errors, also show a message box immediately
        if severity == ErrorSeverity.CRITICAL:
             QMessageBox.critical(None, f"{APP_NAME} - Critical Error",
                                  f"A critical error occurred:\n{message}\n\nDetails: {details}")


# --- Crash Handling and Recovery ---

class CrashHandler(QObject):
    """Handles application crashes and attempts session recovery."""

    def __init__(self, session_manager: Optional[SessionManager] = None, parent: Optional[QObject] = None):
        """
        Initialize the Crash Handler.

        Args:
            session_manager: An optional SessionManager instance for recovery.
            parent: The parent QObject.
        """
        super().__init__(parent)
        self.session_manager = session_manager
        self._settings = QSettings() # Use QSettings to track crash count
        self._crash_count_key = "crash_handler/crash_count"
        self._recovery_marker_key = "crash_handler/needs_recovery"

        # Load crash count on startup
        self.crash_count = self._settings.value(self._crash_count_key, 0, type=int)
        logger.debug(f"CrashHandler initialized. Previous crash count: {self.crash_count}")

        # Check for recovery marker (set by a previous crash)
        self._needs_recovery_flag = self._settings.value(self._recovery_marker_key, False, type=bool)
        if self._needs_recovery_flag:
             logger.warning("Recovery marker found. Application needs recovery.")


    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Global exception hook to catch unhandled exceptions.

        Args:
            exc_type: The exception type.
            exc_value: The exception instance.
            exc_traceback: The traceback object.
        """
        # Log the unhandled exception
        logger.critical("An unhandled exception occurred!", exc_info=(exc_type, exc_value, exc_traceback))

        # Increment crash count
        self.crash_count += 1
        self._settings.setValue(self._crash_count_key, self.crash_count)

        # Set recovery marker
        self._needs_recovery_flag = True
        self._settings.setValue(self._recovery_marker_key, True)

        # Optionally save session data before crashing (best effort)
        # This requires the main window to be available and the session manager
        # This is better handled by the ApplicationManager's shutdown logic
        # which is triggered by QCoreApplication.instance().aboutToQuit.connect(self.shutdown)
        # The crash handler's role is primarily to *detect* the crash and mark for recovery.

        # Call the default exception handler to print to console/stderr
        sys.__excepsecthook__(exc_type, exc_value, exc_traceback)

        # Exit the application after handling the crash
        # QApplication.instance().quit() # Or sys.exit(1)


    def needs_recovery(self) -> bool:
        """Check if the application needs recovery after a previous crash."""
        return self._needs_recovery_flag


    def perform_recovery(self, window: QMainWindow) -> bool:
        """
        Perform recovery after a crash.

        Args:
            window: Main window to restore session data into.

        Returns:
            True if recovery was initiated (even if session restore fails), False otherwise.
        """
        if not self.needs_recovery():
            logger.debug("Recovery not needed.")
            return False

        logger.info("Initiating crash recovery.")

        try:
            # Clear the recovery marker immediately
            self._needs_recovery_flag = False
            self._settings.setValue(self._recovery_marker_key, False)

            # Attempt to restore session if SessionManager is available
            session_restored = False
            if self.session_manager:
                 try:
                      # Restore session data into the ApplicationManager via a signal
                      # The AppManager will then load the batch state etc.
                      # Need a signal like `restore_session_data = pyqtSignal(dict)` in AppManager
                      # and SessionManager emits this signal after restoring data.
                      # For now, let's just call restore_session and return the data to AppManager.
                      restored_data = self.session_manager.restore_session(window)
                      if restored_data:
                           logger.info("Session data restored during recovery attempt.")
                           # The ApplicationManager will need to consume this data
                           # Let's return the data to the AppManager's initialize method
                           # which called perform_recovery. This requires a change in AppManager.
                           # For now, just indicate that session restore was attempted.
                           session_restored = True
                      else:
                           logger.warning("No session data found to restore during recovery.")

                 except Exception as e:
                      logger.error(f"Failed to restore session during recovery: {e}")
                      # Report this error via ErrorReporter if available (needs AppManager reference)
                      # if self.parent() and hasattr(self.parent(), 'error_reporter') and self.parent().error_reporter:
                      #      self.parent().error_reporter.report_error("Session Restore Failed", str(e), ErrorSeverity.ERROR)


            # Show a recovery message to the user
            recovery_message = "The application has recovered after an unexpected shutdown."
            if session_restored:
                 recovery_message += "\nYour previous session has been restored."
            else:
                 recovery_message += "\nNo previous session data was found to restore."

            QMessageBox.information(
                 window,
                 "Application Recovery",
                 recovery_message
            )

            logger.info("Crash recovery process completed.")
            return True # Indicate that recovery was initiated

        except Exception as e:
            logger.critical(f"A critical error occurred during crash recovery: {e}", exc_info=True)
            # If recovery itself fails critically, we might be in a bad state.
            # Log the error and let the application continue (or exit) as it would normally.
            return False # Indicate that recovery failed


    def reset_crash_count(self) -> None:
        """Reset the crash counter after successful application startup."""
        if self.crash_count > 0:
            logger.info(f"Resetting crash count from {self.crash_count} to 0 after successful startup.")
            self.crash_count = 0
            self._settings.setValue(self._crash_count_key, 0)


# --- Helper Classes/Functions (e.g., for dialogs if needed here) ---

# Note: SettingsDialog, AboutDialog, ErrorDialog, ShortcutConfigDialog
# are expected to be defined in ui.py based on the user-provided code.
# If they were intended to be here, their full definitions would be included.
# The current implementation assumes they are imported from ui.


# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     # Create the application instance
#     app = QApplication(sys.argv)

#     # Set application metadata for QSettings
#     app.setOrganizationName("YourCompanyName") # Replace with your organization name
#     app.setApplicationName(APP_NAME if 'APP_NAME' in globals() else "Application")
#     if 'APP_VERSION' in globals():
#          app.setApplicationVersion(APP_VERSION)


#     # --- Standalone Testing of Advanced Features ---

#     # Mock Main Window for testing components that need it
#     class MockMainWindow(QMainWindow):
#          def __init__(self):
#               super().__init__()
#               self.setGeometry(100, 100, 800, 600)
#               self.setWindowTitle("Mock Main Window")
#               self.statusBar().showMessage("Mock Status Bar")
#               self.url_input = QLineEdit(self) # Mock attribute for keyboard manager
#               self.model_combo = QComboBox(self) # Mock attribute for keyboard manager
#               self.language_combo = QComboBox(self) # Mock attribute for keyboard manager
#               self.output_dir_edit = QLineEdit(self) # Mock attribute for keyboard manager
#               self.format_srt_checkbox = QCheckBox(self) # Mock attribute for keyboard manager
#               self.format_json_checkbox = QCheckBox(self) # Mock attribute for keyboard manager
#               self.format_vtt_checkbox = QCheckBox(self) # Mock attribute for keyboard manager
#               self.task_widgets = {} # Mock attribute for UI updates
#               self.recent_files_menu = RecentFilesMenu(self) # Mock Recent Files Menu

#               # Mock methods needed by other components
#               def add_task_to_ui(self, url): logger.debug(f"Mock UI: add_task_to_ui({url})")
#               def remove_task_from_ui(self, url): logger.debug(f"Mock UI: remove_task_from_ui({url})")
#               def _update_ui_progress(self, update): logger.debug(f"Mock UI: _update_ui_progress({update})")
#               def _handle_batch_completion(self, report): logger.debug(f"Mock UI: _handle_batch_completion({report})")
#               def _handle_resource_warning(self, warning_data): logger.debug(f"Mock UI: _handle_resource_warning({warning_data})")
#               def _handle_error_report(self, message, details): logger.debug(f"Mock UI: _handle_error_report({message}, {details})")
#               def _handle_update_ui_status(self, status, message): logger.debug(f"Mock UI: _handle_update_ui_status({status}, {message})")
#               def _handle_notification_request(self, title, message, type): logger.debug(f"Mock UI: _handle_notification_request({title}, {message}, {type})")
#               def _paste_from_clipboard(self): logger.debug("Mock UI: _paste_from_clipboard()")
#               def show_settings_dialog(self, settings): logger.debug("Mock UI: show_settings_dialog()")
#               def show_about_dialog(self): logger.debug("Mock UI: show_about_dialog()")
#               def show_help(self): logger.debug("Mock UI: show_help()")
#               def show_shortcut_config_dialog(self, shortcuts): logger.debug("Mock UI: show_shortcut_config_dialog()")
#               def _update_ui_state(self, status): logger.debug(f"Mock UI: _update_ui_state({status})")

#               self.add_task_to_ui = add_task_to_ui.__get__(self)
#               self.remove_task_from_ui = remove_task_from_ui.__get__(self)
#               self._update_ui_progress = _update_ui_progress.__get__(self)
#               self._handle_batch_completion = _handle_batch_completion.__get__(self)
#               self._handle_resource_warning = _handle_resource_warning.__get__(self)
#               self._handle_error_report = _handle_error_report.__get__(self)
#               self._handle_update_ui_status = _handle_update_ui_status.__get__(self)
#               self._handle_notification_request = _handle_notification_request.__get__(self)
#               self._paste_from_clipboard = _paste_from_clipboard.__get__(self)
#               self.show_settings_dialog = show_settings_dialog.__get__(self)
#               self.show_about_dialog = show_about_dialog.__get__(self)
#               self.show_help = show_help.__get__(self)
#               self.show_shortcut_config_dialog = show_shortcut_config_dialog.__get__(self)
#               self._update_ui_state = _update_ui_state.__get__(self)


#     mock_window = MockMainWindow()


#     # Test RecentFilesManager
#     # rfm = RecentFilesManager(max_files=5)
#     # rfm.recent_files_changed.connect(lambda files: logger.info(f"Recent files changed: {files}"))
#     # rfm.add_file("/path/to/file1.txt")
#     # rfm.add_file("/path/to/file2.txt")
#     # rfm.add_file("/path/to/file3.txt")
#     # rfm.add_file("/path/to/file1.txt") # Add again to move to top
#     # rfm.add_file("/path/to/file4.txt")
#     # rfm.add_file("/path/to/file5.txt")
#     # rfm.add_file("/path/to/file6.txt") # Should push out file2
#     # rfm.clear_recent_files()


#     # Test SystemTrayManager
#     # stm = SystemTrayManager()
#     # stm.set_main_window(mock_window) # Set mock window
#     # stm.show_message("Test Notification", "This is a test message.", NotificationType.INFO)
#     # stm.show_message("Warning Test", "This is a warning message.", NotificationType.WARNING)
#     # stm.show_message("Critical Test", "This is a critical message.", NotificationType.CRITICAL)


#     # Test ErrorReporter
#     # er = ErrorReporter()
#     # er.error_reported.connect(lambda msg, det, sev: logger.info(f"Error Reported Signal: {msg} | {det} | {sev.name}"))
#     # er.report_error("Test Error Message", "Some detailed error information.")
#     # er.report_error("Test Warning", severity=ErrorSeverity.WARNING)
#     # er.report_error("Test Critical Error", "Details about a critical issue.", ErrorSeverity.CRITICAL)


#     # Test SessionManager
#     # sm = SessionManager()
#     # mock_data = {"test_key": "test_value", "batch_state": {"tasks": {"url1": {"status": TaskStatus.COMPLETED.name if 'TaskStatus' in globals() else 'COMPLETED'}} if 'TaskStatus' in globals() else {}}}
#     # sm.save_session(mock_window, mock_data)
#     # restored_data = sm.restore_session(mock_window)
#     # logger.info(f"Restored session data: {restored_data}")


#     # Test CrashHandler (requires careful testing, might crash the app)
#     # ch = CrashHandler(session_manager=sm)
#     # Set the global exception hook temporarily for testing
#     # sys.excepthook = ch.handle_exception
#     # Simulate a crash:
#     # try:
#     #      raise RuntimeError("Simulated crash for testing CrashHandler")
#     # except Exception:
#     #      # Call the handler directly if the hook isn't catching it as expected
#     #      ch.handle_exception(*sys.exc_info())

#     # Test recovery on next run by checking ch.needs_recovery()


#     # Test KeyboardManager
#     # km = KeyboardManager()
#     # km.set_main_window(mock_window)
#     # km.shortcut_activated.connect(lambda action: logger.info(f"Shortcut Activated: {action.name}"))
#     # Test updating a shortcut
#     # km.update_shortcut(ShortcutAction.START_BATCH, "Ctrl+Shift+R", True)
#     # Test getting shortcuts
#     # all_shortcuts = km.get_all_shortcuts()
#     # logger.info(f"All shortcuts: {all_shortcuts}")
#     # Test saving/loading settings
#     # shortcut_settings = km.save_settings()
#     # logger.info(f"Saved shortcut settings: {shortcut_settings}")
#     # km.load_settings(shortcut_settings)


#     # Test AutoUpdater (requires a valid update_url in settings)
#     # Assuming you have a settings.json with an update_config
#     # settings = load_settings()
#     # update_config = settings.get("update_config", {})
#     # au = AutoUpdater(update_config)
#     # au.update_status_changed.connect(lambda status, msg: logger.info(f"Update Status: {status.name} - {msg}"))
#     # au.notification_requested.connect(lambda title, msg, type: logger.info(f"Notification: {title} - {msg} ({type.name})"))
#     # au.check_for_updates()
#     # Example to trigger download/install (after check_for_updates finds an update):
#     # if au.get_update_status() == UpdateStatus.UPDATE_AVAILABLE:
#     #      au.download_update()
#     #      # After download finishes (handle in _handle_download_finished)
#     #      # if au.get_update_status() == UpdateStatus.READY_TO_INSTALL:
#     #      #      au.install_update()


#     # Start the application event loop for GUI components
#     # sys.exit(app.exec())
