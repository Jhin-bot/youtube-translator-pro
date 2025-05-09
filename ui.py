import os
import sys
import json
import logging
import platform
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Set, Tuple

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
from pathlib import Path
import webbrowser # Added for opening URLs or files

# Try to import qtawesome, but provide a fallback if it's not available
try:
    import qtawesome as qta
    QTA_AVAILABLE = True
except ImportError:
    QTA_AVAILABLE = False
    # Create a mock qtawesome for testing purposes
    class QtAwesomeMock:
        def icon(self, *args, **kwargs):
            from PyQt6.QtGui import QIcon
            return QIcon()
        
    qta = QtAwesomeMock()

from PyQt6.QtCore import (
    Qt, QSize, QUrl, QTimer, QThread, QObject, QSettings, QStandardPaths,
    pyqtSignal, pyqtSlot, QMimeData, QEvent, QPoint, QRect, QPropertyAnimation,
    QAbstractAnimation, QEasingCurve # Added QEasingCurve for animations
)
from PyQt6.QtGui import (
    QIcon, QAction, QFont, QColor, QPalette, QDragEnterEvent, QDropEvent,
    QPixmap, QPainter, QBrush, QPen, QMovie, QLinearGradient, QGradient,
    QFontMetrics, QCloseEvent, QStandardItemModel, QStandardItem, QDesktopServices,
    QValidator, QIntValidator, QDoubleValidator, QShortcut, QKeySequence # Added QKeySequence
)
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QLineEdit, QTextEdit, QProgressBar, QFileDialog, QMessageBox,
    QScrollArea, QFrame, QSplitter, QComboBox, QCheckBox, QGroupBox, QTabWidget,
    QDialog, QDialogButtonBox, QFormLayout, QSpinBox, QListWidget, QListWidgetItem,
    QSystemTrayIcon, QMenu, QSizePolicy, QToolBar, QStatusBar, QToolButton,
    QGridLayout, QSlider, QSpacerItem, QStackedWidget, QToolTip, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView, QStyleFactory, QGraphicsOpacityEffect,
    QDoubleSpinBox # Added DoubleSpinBox for float values
)

# Local application imports
# Ensure these imports match your file structure
try:
    # Import necessary classes and constants from other modules
    from batch import BatchProcessor, TaskStatus, BatchStatus
except ImportError as e:
    logging.error(f"Could not import batch module: {e}. Batch processing features may be limited.")
    # Define placeholder/mock classes and enums if import fails
    BatchProcessor = None
    TaskStatus = Enum("TaskStatus", ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED", "SKIPPED", "PAUSED", "RETRYING", "VALIDATING", "DOWNLOADING", "CONVERTING", "TRANSCRIBING", "TRANSLATING", "EXPORTING"])
    BatchStatus = Enum("BatchStatus", ["IDLE", "RUNNING", "PAUSED", "RESUMING", "COMPLETED", "CANCELLED", "FAILED", "THROTTLED", "STOPPING"])


try:
    from cache import CacheManager, CacheType # Assuming CacheManager and CacheType exist
except ImportError as e:
    logging.warning(f"Could not import cache module: {e}. Caching features disabled.")
    # Define placeholder/mock classes and enums if import fails
    CacheManager = None
    CacheType = Enum("CacheType", ["TRANSCRIPTION", "TRANSLATION", "AUDIO_INFO"])


try:
    from settings import load_settings, save_settings, DEFAULT_SETTINGS, APP_DATA_DIR # Import APP_DATA_DIR
except ImportError as e:
    logging.error(f"Could not import settings module: {e}. Application settings may not load/save.")
    # Define placeholder/mock functions and constants if import fails
    load_settings = lambda: {}
    save_settings = lambda s: False
    APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".ytpro_default_app_data") # Default fallback
    DEFAULT_SETTINGS = {} # Provide a default empty dict


try:
    from styles import style_manager, ColorRole, Spacing, Dimensions, IconSet, AnimationPresets # Import necessary styles
except ImportError as e:
    logging.error(f"Could not import styles module: {e}. Application will use default Qt styling.")
    # Provide fallback style manager if import fails
    class MockStyleManager:
        def get_app_stylesheet(self, theme="dark"): return ""
        def get_color(self, role): return QColor("black")
        def create_modern_button(self, *args, **kwargs): return QPushButton(*args, **kwargs)
        def create_modern_heading(self, *args, **kwargs): return QLabel(*args, **kwargs)
        def apply_card_style(self, widget): pass
        def apply_scrollable_style(self, widget): pass
        def apply_task_item_style(self, widget): pass
        def create_status_indicator(self, status_type, parent=None): return QLabel(parent)
        def apply_global_style(self, app, theme="dark"): pass
        def create_shadow_effect(self, widget, *args, **kwargs): return QGraphicsDropShadowEffect(widget)
        def create_fade_animation(self, widget, *args, **kwargs): return QPropertyAnimation(widget, b"opacity")
        def get_button_style(self, *args, **kwargs): return ""
        def get_label_style(self, *args, **kwargs): return ""
        class typography: # Add typography fallback
             @staticmethod
             def get_font(size_scale="M", weight=None, monospace=False): return QFont()
             class FontWeight: THIN, EXTRA_LIGHT, LIGHT, NORMAL, MEDIUM, DEMI_BOLD, BOLD, EXTRA_BOLD, BLACK = 0,1,2,3,4,5,6,7,8

    style_manager = MockStyleManager()
    # Provide fallback constants
    class MockSpacing: XXS, XS, S, M, L, XL, XXL = 2, 4, 8, 12, 16, 24, 32
    class MockDimensions: BUTTON_HEIGHT, INPUT_HEIGHT = 30, 30; ICON_SIZE_SMALL, ICON_SIZE_MEDIUM, ICON_SIZE_LARGE, ICON_SIZE_XL = QSize(16,16), QSize(24,24), QSize(32,32), QSize(48,48); BORDER_RADIUS_S, BORDER_RADIUS_M, BORDER_RADIUS_L = 4, 8, 12; DIALOG_MIN_WIDTH, DIALOG_MIN_HEIGHT, MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT = 400, 300, 600, 400 # Add dialog/window sizes
    class MockIconSet:
        APP_ICON, SPLASH_ICON = "", ""
        ICON_ADD, ICON_REMOVE, ICON_EDIT, ICON_SAVE, ICON_OPEN, ICON_SETTINGS, ICON_SEARCH, ICON_DOWNLOAD, ICON_UPLOAD = [""]*9
        ICON_PLAY, ICON_PAUSE, ICON_STOP, ICON_CANCEL, ICON_REFRESH, ICON_INFO, ICON_WARNING, ICON_ERROR = [""]*8
        ICON_SUCCESS, ICON_BROWSE, ICON_CLIPBOARD = [""]*3
        ICON_FILE, ICON_FOLDER, ICON_AUDIO, ICON_VIDEO, ICON_TEXT, ICON_SRT, ICON_JSON, ICON_VTT = [""]*8
        
        @staticmethod
        def get_icon(name):
            return QIcon()
        
        @staticmethod
        def get_pixmap(name, size):
            return QPixmap(size)
    class MockAnimationPresets:
        DURATION_M = 250
        EASE_OUT = QEasingCurve.Type.Linear
        EASE_IN = QEasingCurve.Type.Linear
        
        @staticmethod
        def fade_in(widget, duration):
            return None
            
        @staticmethod
        def fade_out(widget, duration):
            return None
    Spacing = MockSpacing()
    Dimensions = MockDimensions()
    IconSet = MockIconSet()
    AnimationPresets = MockAnimationPresets()
    ColorRole = Enum("ColorRole", ["PRIMARY", "SECONDARY", "SUCCESS", "WARNING", "ERROR", "INFO", "BACKGROUND", "BACKGROUND_ALT", "BACKGROUND_HOVER", "BACKGROUND_PRESSED", "FOREGROUND", "FOREGROUND_DIM", "FOREGROUND_DISABLED", "BORDER", "BORDER_LIGHT", "BORDER_DARK", "SHADOW", "HIGHLIGHT", "HIGHLIGHTED_TEXT", "TOOLTIP_BG", "TOOLTIP_FG"])


try:
    # Import advanced features components if available
    from advanced_features import (
        RecentFilesManager, RecentFilesMenu,
        AutoUpdater, UpdateStatus, UpdateDialog,
        SystemTrayManager, NotificationType,
        KeyboardManager, ShortcutAction, ShortcutConfigDialog,
        SessionManager,
        ErrorReporter, ErrorSeverity, ErrorDialog, CrashHandler
    )
    ADVANCED_FEATURES_AVAILABLE = True
    # Ensure enums are available even if the full classes are not used directly in UI
    if 'UpdateStatus' not in locals(): UpdateStatus = Enum("UpdateStatus", ["NO_UPDATE", "CHECKING", "UPDATE_AVAILABLE", "DOWNLOADING", "READY_TO_INSTALL", "ERROR", "DISABLED"])
    if 'NotificationType' not in locals(): NotificationType = Enum("NotificationType", ["INFO", "WARNING", "CRITICAL"])
    if 'ShortcutAction' not in locals(): ShortcutAction = Enum("ShortcutAction", ["START_BATCH", "PAUSE_BATCH", "CANCEL_BATCH", "SHOW_SETTINGS", "SHOW_ABOUT", "SHOW_HELP", "ADD_URLS_FROM_CLIPBOARD", "CLEAR_INPUT", "SHOW_SHORTCUTS", "PASS_THROUGH"])
    if 'ErrorSeverity' not in locals(): ErrorSeverity = Enum("ErrorSeverity", ["INFO", "WARNING", "ERROR", "CRITICAL"])

except ImportError as e:
    logging.error(f"Could not import advanced_features module: {e}. Advanced features disabled.")
    ADVANCED_FEATURES_AVAILABLE = False
    # Define enums for mock classes when advanced_features is not available
    UpdateStatus = Enum("UpdateStatus", ["NO_UPDATE", "CHECKING", "UPDATE_AVAILABLE", "DOWNLOADING", "READY_TO_INSTALL", "ERROR", "DISABLED"])
    NotificationType = Enum("NotificationType", ["INFO", "WARNING", "CRITICAL"])
    ShortcutAction = Enum("ShortcutAction", ["START_BATCH", "PAUSE_BATCH", "CANCEL_BATCH", "SHOW_SETTINGS", "SHOW_ABOUT", "SHOW_HELP", "ADD_URLS_FROM_CLIPBOARD", "CLEAR_INPUT", "SHOW_SHORTCUTS", "PASS_THROUGH"])
    ErrorSeverity = Enum("ErrorSeverity", ["INFO", "WARNING", "ERROR", "CRITICAL"])
    # Mock classes if import fails
    class RecentFilesManager(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def add_file(self, path): pass
        def get_recent_files(self): return []
        def clear_recent_files(self): pass
        recent_files_changed = pyqtSignal(list) # Mock signal
        def delete_file(self, path): pass # Mock method

    class RecentFilesMenu(QMenu): # Inherit from QMenu for compatibility
        def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
        def update_menu(self, recent_files): pass
        file_opened = pyqtSignal(str) # Mock signal
        clear_recent_files_requested = pyqtSignal() # Mock signal

    class AutoUpdater(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def check_for_updates(self): pass
        def download_update(self): pass
        def install_update(self): pass
        def get_update_status(self): return UpdateStatus.NO_UPDATE if 'UpdateStatus' in locals() else None
        # Using object instead of enum types and removing Optional to avoid pyqtSignal type issues
        update_status_changed = pyqtSignal(object, str) # Mock signal
        notification_requested = pyqtSignal(str, str, object) # Mock signal
        def _start_update_timer(self): pass # Mock method


    class UpdateStatus(Enum): NO_UPDATE, CHECKING, UPDATE_AVAILABLE, DOWNLOADING, READY_TO_INSTALL, ERROR, DISABLED = auto(), auto(), auto(), auto(), auto(), auto(), auto()
    class UpdateDialog(QDialog):
        def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
        def exec(self): return 0

    class SystemTrayManager(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def show_message(self, title, message, type): pass


    class NotificationType(Enum): INFO, WARNING, CRITICAL = auto(), auto(), auto()


    class KeyboardManager(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def register_shortcut(self, action, key_sequence, callback): pass
        def update_shortcut(self, action, key_sequence, enabled): return False
        def get_shortcut_key_sequence(self, action): return ""
        def get_all_shortcuts(self): return {}
        def load_settings(self, settings): pass
        def save_settings(self): return {}
        def set_main_window(self, window): pass
        shortcut_activated = pyqtSignal(ShortcutAction) # Mock signal
        _current_configs = {} # Mock attribute


    class ShortcutAction(Enum): # Define basic actions if missing
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


    class ShortcutConfigDialog(QDialog): # Mock dialog
        def __init__(self, *args, **kwargs): super().__init__(); self.shortcuts_saved = pyqtSignal(dict)
        def exec(self): return 0


    class SessionManager(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def save_session(self, window, data): pass
        def restore_session(self, window): return {}
        def _prepare_for_serialization(self, data): return data # Mock method


    class ErrorReporter(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def report_error(self, message, details, severity): pass
        error_reported = pyqtSignal(str, str, ErrorSeverity) # Mock signal


    class ErrorSeverity(Enum): INFO, WARNING, ERROR, CRITICAL = auto(), auto(), auto(), auto()


    class ErrorDialog(QDialog): # Mock dialog
        def __init__(self, *args, **kwargs): super().__init__();
        def exec(self): return 0


    class CrashHandler(QObject): # Inherit from QObject
        def __init__(self, *args, **kwargs): super().__init__(); pass
        def handle_exception(self, exc_type, exc_value, exc_traceback): pass
        def needs_recovery(self): return False
        def perform_recovery(self, window): return False
        def reset_crash_count(self): pass


# Application metadata (should be defined once, ideally in a config file or main.py)
# Keeping here for UI module's self-sufficiency if needed, but main.py is the source of truth
APP_NAME = "YouTube Transcriber Pro"
APP_VERSION = "1.0.0" # Updated version

# Try importing VALID_MODELS from transcribe, fallback if not available
try:
    from transcribe import VALID_MODELS
except ImportError:
    VALID_MODELS = ["tiny", "base", "small", "medium", "large"] # Default list

# Try importing AVAILABLE_LANGUAGES from translate, fallback if not available
try:
    from translate import get_available_languages
    AVAILABLE_LANGUAGES = get_available_languages()
except ImportError:
    AVAILABLE_LANGUAGES = {"None": "None", "en": "English"} # Default list


# Setup logger for the UI module
logger = logging.getLogger(__name__)


# ==============================================================================
# DIALOGS (Defined here or imported from advanced_features.py)
# ==============================================================================

# SettingsDialog, AboutDialog, ErrorDialog, ShortcutConfigDialog are defined here
# to make ui.py runnable standalone for development, but the ApplicationManager
# will use the imported versions if advanced_features is available.


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    settings_saved = pyqtSignal(dict) # Signal to emit when settings are saved

    def __init__(self, current_settings: Dict[str, Any], parent: Optional[QWidget] = None):
        """
        Initialize the Settings Dialog.

        Args:
            current_settings: The current application settings dictionary.
            parent: The parent widget.
        """
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Settings")
        self.setMinimumSize(Dimensions.DIALOG_MIN_WIDTH, Dimensions.DIALOG_MIN_HEIGHT)
        self.settings = current_settings.copy() # Work on a copy

        # Apply dialog styling (can be done via QSS or direct palette)
        # style_manager.apply_dialog_style(self) # Assuming a dialog style exists

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(Spacing.L, Spacing.L, Spacing.L, Spacing.L)
        self.layout.setSpacing(Spacing.M)

        self.tabs = QTabWidget(self)
        self.layout.addWidget(self.tabs)

        # --- General Tab ---
        self.general_tab = QWidget()
        self.general_layout = QFormLayout(self.general_tab)
        self.general_layout.setContentsMargins(Spacing.M, Spacing.M, Spacing.M, Spacing.M)
        self.general_layout.setSpacing(Spacing.S)

        # Theme Selection
        self.theme_combo = QComboBox(self.general_tab)
        self.theme_combo.addItems(["dark", "light"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "dark"))
        self.general_layout.addRow("Theme:", self.theme_combo)

        # Output Directory
        self.output_dir_edit = QLineEdit(self.general_tab)
        # Use .get with default and Path.home() for a more robust default
        default_output_dir = str(Path.home() / "Downloads" / "YouTubeTranscriber")
        self.output_dir_edit.setText(self.settings.get("output_dir", default_output_dir))
        self.browse_output_button = style_manager.create_modern_button(
            "", parent=self.general_tab, is_flat=True,
            icon=IconSet.get_icon(IconSet.ICON_BROWSE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.browse_output_button.clicked.connect(self._browse_output_dir)
        self.output_dir_layout = QHBoxLayout()
        self.output_dir_layout.addWidget(self.output_dir_edit)
        self.output_dir_layout.addWidget(self.browse_output_button)
        self.general_layout.addRow("Default Output Directory:", self.output_dir_layout)

        # Default Model
        self.default_model_combo = QComboBox(self.general_tab)
        self.default_model_combo.addItems(VALID_MODELS) # Use VALID_MODELS
        default_model = self.settings.get("default_model", "small")
        if default_model in VALID_MODELS:
             self.default_model_combo.setCurrentText(default_model)
        else:
             self.default_model_combo.setCurrentIndex(0) # Select first item if default is invalid

        self.general_layout.addRow("Default Whisper Model:", self.default_model_combo)

        # Default Language (for translation)
        self.default_language_combo = QComboBox(self.general_tab)
        # Convert AVAILABLE_LANGUAGES dict to a list of names for the combo box
        lang_names = list(AVAILABLE_LANGUAGES.values())
        self.default_language_combo.addItems(lang_names)
        default_lang_code = self.settings.get("default_language", "None")
        # Find the language name corresponding to the default code
        default_lang_name = AVAILABLE_LANGUAGES.get(default_lang_code, "None")
        self.default_language_combo.setCurrentText(default_lang_name)

        self.general_layout.addRow("Default Translation Language:", self.default_language_combo)

        # Max Recent Files
        self.max_recent_spinbox = QSpinBox(self.general_tab)
        self.max_recent_spinbox.setRange(0, 100) # Allow 0 to disable recent files
        self.max_recent_spinbox.setValue(self.settings.get("max_recent_files", DEFAULT_SETTINGS.get("max_recent_files", 20))) # Use .get with default
        self.general_layout.addRow("Max Recent Files:", self.max_recent_spinbox)


        self.tabs.addTab(self.general_tab, "General")

        # --- Batch Tab ---
        self.batch_tab = QWidget()
        self.batch_layout = QFormLayout(self.batch_tab)
        self.batch_layout.setContentsMargins(Spacing.M, Spacing.M, Spacing.M, Spacing.M)
        self.batch_layout.setSpacing(Spacing.S)

        # Concurrency
        self.concurrency_spinbox = QSpinBox(self.batch_tab)
        self.concurrency_spinbox.setRange(1, os.cpu_count() or 4) # Max concurrency based on CPU cores
        self.concurrency_spinbox.setValue(self.settings.get("concurrency", DEFAULT_SETTINGS.get("concurrency", 2))) # Use .get with default
        self.batch_layout.addRow("Max Concurrent Tasks:", self.concurrency_spinbox)

        # Max Retries
        self.max_retries_spinbox = QSpinBox(self.batch_tab)
        self.max_retries_spinbox.setRange(0, 10)
        # Use default from BatchProcessor if available, else a hardcoded default
        default_max_retries = getattr(BatchProcessor, 'DEFAULT_RETRY_COUNT', 3) if BatchProcessor else 3
        self.max_retries_spinbox.setValue(self.settings.get("max_retries", default_max_retries))
        self.batch_layout.addRow("Max Retries per Task:", self.max_retries_spinbox)

        # Initial Retry Delay
        self.retry_delay_spinbox = QDoubleSpinBox(self.batch_tab)
        self.retry_delay_spinbox.setRange(1.0, 60.0)
        self.retry_delay_spinbox.setSingleStep(0.5)
        # Use default from BatchProcessor if available, else a hardcoded default
        default_retry_delay = getattr(BatchProcessor, 'DEFAULT_RETRY_DELAY', 5.0) if BatchProcessor else 5.0
        self.retry_delay_spinbox.setValue(self.settings.get("retry_delay", default_retry_delay))
        self.retry_delay_spinbox.setSuffix(" s")
        self.batch_layout.addRow("Initial Retry Delay:", self.retry_delay_spinbox)


        self.tabs.addTab(self.batch_tab, "Batch Processing")

        # --- Cache Tab ---
        self.cache_tab = QWidget()
        self.cache_layout = QFormLayout(self.cache_tab)
        self.cache_layout.setContentsMargins(Spacing.M, Spacing.M, Spacing.M, Spacing.M)
        self.cache_layout.setSpacing(Spacing.S)

        # Cache Enabled
        self.cache_enabled_checkbox = QCheckBox("Enable Caching", self.cache_tab)
        self.cache_enabled_checkbox.setChecked(self.settings.get("cache_enabled", DEFAULT_SETTINGS.get("cache_enabled", True))) # Use .get with default
        self.cache_enabled_checkbox.toggled.connect(self._toggle_cache_options) # Connect toggle signal
        self.cache_layout.addRow("Caching:", self.cache_enabled_checkbox)

        # Cache Directory
        self.cache_dir_edit = QLineEdit(self.cache_tab)
        # Use .get with default and Path.home() for a more robust default
        default_cache_dir = str(Path.home() / ".ytpro_cache")
        self.cache_dir_edit.setText(self.settings.get("cache_dir", default_cache_dir))
        self.browse_cache_button = style_manager.create_modern_button(
            "", parent=self.cache_tab, is_flat=True,
            icon=IconSet.get_icon(IconSet.ICON_BROWSE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.browse_cache_button.clicked.connect(self._browse_cache_dir)
        self.cache_dir_layout = QHBoxLayout()
        self.cache_dir_layout.addWidget(self.cache_dir_edit)
        self.cache_dir_layout.addWidget(self.browse_cache_button)
        self.cache_layout.addRow("Cache Directory:", self.cache_dir_layout)

        # Cache Size Limit
        self.cache_size_spinbox = QSpinBox(self.cache_tab)
        self.cache_size_spinbox.setRange(100, 100000) # 100 MB to 100 GB
        self.cache_size_spinbox.setValue(self.settings.get("cache_size_mb", DEFAULT_SETTINGS.get("cache_size_mb", 1000))) # Use .get with default
        self.cache_size_spinbox.setSuffix(" MB")
        self.cache_layout.addRow("Max Cache Size:", self.cache_size_spinbox)

        # Cache TTL
        self.cache_ttl_spinbox = QSpinBox(self.cache_tab)
        self.cache_ttl_spinbox.setRange(60, 365 * 24 * 3600) # 1 minute to 1 year in seconds
        self.cache_ttl_spinbox.setValue(self.settings.get("cache_ttl", DEFAULT_SETTINGS.get("cache_ttl", 60 * 60 * 24 * 30))) # Use .get with default
        self.cache_ttl_spinbox.setSuffix(" s")
        self.cache_layout.addRow("Cache TTL:", self.cache_ttl_spinbox)

        # Cache Stats and Clear Button
        self.cache_stats_label = QLabel("Loading cache stats...", self.cache_tab)
        self.cache_layout.addRow("Current Cache:", self.cache_stats_label)

        self.clear_cache_button = style_manager.create_modern_button(
            "Clear Cache", parent=self.cache_tab, is_danger=True,
            icon=IconSet.get_icon(IconSet.ICON_REMOVE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.clear_cache_button.clicked.connect(self._clear_cache)
        self.cache_layout.addRow("", self.clear_cache_button) # Add button without label

        self.tabs.addTab(self.cache_tab, "Cache")

        # Initial state of cache options based on settings
        self._toggle_cache_options(self.settings.get("cache_enabled", DEFAULT_SETTINGS.get("cache_enabled", True)))

        # --- Update Tab ---
        self.update_tab = QWidget()
        self.update_layout = QFormLayout(self.update_tab)
        self.update_layout.setContentsMargins(Spacing.M, Spacing.M, Spacing.M, Spacing.M)
        self.update_layout.setSpacing(Spacing.S)

        # Auto Check for Updates
        self.auto_check_updates_checkbox = QCheckBox("Automatically check for updates", self.update_tab)
        self.auto_check_updates_checkbox.setChecked(self.settings.get("update_config", {}).get("auto_check", True))
        self.update_layout.addRow("Auto Updates:", self.auto_check_updates_checkbox)

        # Check Interval
        self.check_interval_spinbox = QSpinBox(self.update_tab)
        self.check_interval_spinbox.setRange(1, 720) # Hours (1 hour to 30 days)
        self.check_interval_spinbox.setValue(self.settings.get("update_config", {}).get("check_interval", 24))
        self.check_interval_spinbox.setSuffix(" hours")
        self.update_layout.addRow("Check Interval:", self.check_interval_spinbox)

        # Update URL (for advanced users)
        self.update_url_edit = QLineEdit(self.update_tab)
        # Use default from AppManager or a hardcoded default
        default_update_url = getattr(ApplicationManager, 'DEFAULT_UPDATE_CONFIG', {}).get("update_url", "")
        self.update_url_edit.setText(self.settings.get("update_config", {}).get("update_url", default_update_url))
        self.update_layout.addRow("Update URL:", self.update_url_edit)

        # Check for Updates Button
        self.check_now_button = style_manager.create_modern_button(
            "Check for Updates Now", parent=self.update_tab, is_primary=True,
            icon=IconSet.get_icon(IconSet.ICON_REFRESH) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        # Connect this button to a signal that the ApplicationManager handles
        self.check_now_button.clicked.connect(self._check_for_updates_now)
        self.update_layout.addRow("", self.check_now_button)

        self.tabs.addTab(self.update_tab, "Updates")

        # --- Buttons ---
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        # Load initial cache stats
        self._update_cache_stats()


    def _browse_output_dir(self):
        """Open a dialog to select the default output directory."""
        current_dir = self.output_dir_edit.text()
        if not os.path.isdir(current_dir):
             current_dir = str(Path.home()) # Default to home if current is invalid

        directory = QFileDialog.getExistingDirectory(self, "Select Default Output Directory", current_dir)
        if directory:
            self.output_dir_edit.setText(directory)

    def _browse_cache_dir(self):
        """Open a dialog to select the cache directory."""
        current_dir = self.cache_dir_edit.text()
        if not os.path.isdir(current_dir):
             current_dir = str(Path.home()) # Default to home if current is invalid

        directory = QFileDialog.getExistingDirectory(self, "Select Cache Directory", current_dir)
        if directory:
            self.cache_dir_edit.setText(directory)

    def _toggle_cache_options(self, enabled: bool):
        """Enable or disable cache-related options based on checkbox state."""
        self.cache_dir_edit.setEnabled(enabled)
        self.browse_cache_button.setEnabled(enabled)
        self.cache_size_spinbox.setEnabled(enabled)
        self.cache_ttl_spinbox.setEnabled(enabled)
        self.clear_cache_button.setEnabled(enabled)
        self.cache_stats_label.setEnabled(enabled) # Also dim the stats label


    def _update_cache_stats(self):
        """Request and display current cache statistics."""
        # This should ideally be handled by the ApplicationManager
        # which has access to the CacheManager instance.
        # We'll emit a signal requesting the stats, and AppManager will respond.
        # Need a signal like `request_cache_stats = pyqtSignal()` in MainWindow
        # and a slot in AppManager that calls CacheManager.get_cache_stats()
        # and emits a signal back with the results, connected to a slot here.

        # For now, directly access AppManager if available
        if self.parent() and hasattr(self.parent(), 'app_manager') and self.parent().app_manager and hasattr(self.parent().app_manager, 'cache_manager') and self.parent().app_manager.cache_manager:
             cache_manager = self.parent().app_manager.cache_manager
             cache_stats = cache_manager.get_cache_stats()
             if cache_stats.get("initialized"):
                 size_mb = cache_stats.get("total_size_mb", 0)
                 entry_count = cache_stats.get("entry_count", 0)
                 self.cache_stats_label.setText(f"Size: {size_mb:.1f} MB, Entries: {entry_count}")
             else:
                 self.cache_stats_label.setText("Cache not initialized or accessible.")
        else:
             self.cache_stats_label.setText("Cache stats not available.")


    def _clear_cache(self):
        """Request to clear the cache."""
        reply = QMessageBox.question(self, "Confirm Clear Cache",
                                     "Are you sure you want to clear the entire cache? This cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # This should be handled by the ApplicationManager
            # Need a signal like `clear_cache_requested = pyqtSignal()` in MainWindow
            # and a slot in AppManager that calls CacheManager.clear()
            if self.parent() and hasattr(self.parent(), 'app_manager') and self.parent().app_manager and hasattr(self.parent().app_manager, 'cache_manager') and self.parent().app_manager.cache_manager:
                 try:
                     self.parent().app_manager.cache_manager.clear()
                     QMessageBox.information(self, "Cache Cleared", "The cache has been cleared.")
                     self._update_cache_stats() # Update stats after clearing
                 except Exception as e:
                      QMessageBox.critical(self, "Cache Error", f"Failed to clear cache: {e}")
                      # Report error via ErrorReporter if available
                      if self.parent().app_manager.error_reporter:
                           self.parent().app_manager.error_reporter.report_error("Failed to Clear Cache", str(e), ErrorSeverity.ERROR if 'ErrorSeverity' in globals() else None)

            else:
                 QMessageBox.warning(self, "Cache Not Available", "Cache manager is not available to clear the cache.")


    def _check_for_updates_now(self):
        """Emit signal to check for updates immediately."""
        # Need a signal like `check_updates_now_requested = pyqtSignal()` in MainWindow
        # and a slot in AppManager that calls AutoUpdater.check_for_updates()
        if self.parent() and hasattr(self.parent(), 'app_manager') and self.parent().app_manager and hasattr(self.parent().app_manager, 'auto_updater') and self.parent().app_manager.auto_updater:
             self.parent().app_manager.auto_updater.check_for_updates()
             QMessageBox.information(self, "Checking for Updates", "Checking for updates in the background...")
        else:
             QMessageBox.warning(self, "Updater Not Available", "Auto-updater is not available.")


    def accept(self):
        """Handle OK button click - save settings and close."""
        # Collect settings from UI widgets
        new_settings = self.settings.copy()

        # General Tab
        new_settings["theme"] = self.theme_combo.currentText()
        new_settings["output_dir"] = self.output_dir_edit.text().strip()
        new_settings["default_model"] = self.default_model_combo.currentText()
        # Convert language name back to code
        selected_lang_name = self.default_language_combo.currentText()
        # Find the corresponding language code
        selected_lang_code = next((code for code, name in AVAILABLE_LANGUAGES.items() if name == selected_lang_name), "None")
        new_settings["default_language"] = selected_lang_code
        new_settings["max_recent_files"] = self.max_recent_spinbox.value()

        # Batch Tab
        new_settings["concurrency"] = self.concurrency_spinbox.value()
        new_settings["max_retries"] = self.max_retries_spinbox.value()
        new_settings["retry_delay"] = self.retry_delay_spinbox.value()


        # Cache Tab
        new_settings["cache_enabled"] = self.cache_enabled_checkbox.isChecked()
        new_settings["cache_dir"] = self.cache_dir_edit.text().strip()
        new_settings["cache_size_mb"] = self.cache_size_spinbox.value()
        new_settings["cache_ttl"] = self.cache_ttl_spinbox.value()

        # Update Tab
        update_config = new_settings.get("update_config", {})
        update_config["auto_check"] = self.auto_check_updates_checkbox.isChecked()
        update_config["check_interval"] = self.check_interval_spinbox.value()
        update_url = self.update_url_edit.text().strip()
        # Basic URL validation for update URL
        if update_url and not QUrl(update_url).isValid():
             QMessageBox.warning(self, "Invalid Update URL", "The provided update URL is not valid. Please correct it.")
             # Do not save the invalid URL
             if "update_url" in update_config:
                  del update_config["update_url"]
        else:
             update_config["update_url"] = update_url

        new_settings["update_config"] = update_config


        # Emit signal with new settings
        self.settings_saved.emit(new_settings)

        # Close the dialog
        super().accept()

    def reject(self):
        """Handle Cancel button click - close without saving."""
        super().reject()


class AboutDialog(QDialog):
    """Dialog for displaying application information."""
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(400, 300) # Fixed size for about dialog

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(Spacing.L, Spacing.L, Spacing.L, Spacing.L)
        self.layout.setSpacing(Spacing.M)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content

        # Application Icon/Logo
        self.logo_label = QLabel(self)
        # Use a larger icon for the about dialog
        logo_pixmap = IconSet.get_pixmap(IconSet.APP_ICON, QSize(64, 64)) if IconSet else QPixmap(QSize(64,64))
        self.logo_label.setPixmap(logo_pixmap)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.logo_label)

        # Application Name and Version
        self.name_version_label = QLabel(f"<b>{APP_NAME}</b> v{APP_VERSION}", self)
        self.name_version_label.setFont(style_manager.typography.get_font("L", style_manager.typography.FontWeight.BOLD) if hasattr(style_manager, 'typography') else QFont())
        self.name_version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.name_version_label)

        # Description
        self.description_label = QLabel("A powerful YouTube transcription tool.", self)
        self.description_label.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.description_label)

        # Copyright
        self.copyright_label = QLabel("© 2023 Your Name/Company", self) # Update copyright
        self.copyright_label.setFont(style_manager.typography.get_font("S") if hasattr(style_manager, 'typography') else QFont())
        self.copyright_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.copyright_label)

        # Spacer
        self.layout.addStretch(1)

        # Close Button
        self.close_button = style_manager.create_modern_button("Close", parent=self, is_primary=True)
        self.close_button.clicked.connect(self.accept)
        self.button_layout = QHBoxLayout()
        self.button_layout.addStretch(1)
        self.button_layout.addWidget(self.close_button)
        self.button_layout.addStretch(1)
        self.layout.addLayout(self.button_layout)


class ErrorDialog(QDialog):
    """Dialog for displaying detailed error information."""

    def __init__(self, message: str, details: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle(f"{APP_NAME} - Error")
        self.setMinimumSize(500, 400)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(Spacing.L, Spacing.L, Spacing.L, Spacing.L)
        self.layout.setSpacing(Spacing.M)

        self.heading = style_manager.create_modern_heading("An Error Occurred", self)
        self.layout.addWidget(self.heading)

        self.message_label = QLabel(f"<b>Message:</b> {message}", self)
        self.message_label.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.message_label.setWordWrap(True) # Allow wrapping long messages
        self.layout.addWidget(self.message_label)

        self.details_label = QLabel("<b>Details:</b>", self)
        self.details_label.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.layout.addWidget(self.details_label)

        self.details_text_edit = QTextEdit(self)
        self.details_text_edit.setPlainText(details)
        self.details_text_edit.setReadOnly(True) # Make details read-only
        self.details_text_edit.setFont(style_manager.typography.get_font("S", monospace=True) if hasattr(style_manager, 'typography') else QFont()) # Monospace font for details
        self.layout.addWidget(self.details_text_edit, 1) # Give details text edit stretch factor

        # Buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        self.button_box.accepted.connect(self.accept)
        self.layout.addWidget(self.button_box)


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


# ==============================================================================
# TASK LIST ITEM (Continued)
# ==============================================================================

class TaskListItem(QFrame):
    """Widget to display a single task in the batch list."""

    # Signals for task actions
    cancel_requested = pyqtSignal(str)
    remove_requested = pyqtSignal(str)
    retry_requested = pyqtSignal(str)
    open_output_requested = pyqtSignal(str) # Signal to open output directory/file

    def __init__(self, url: str, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.url = url
        self.status = TaskStatus.PENDING if TaskStatus else None
        self.progress = 0.0
        self.error: Optional[str] = None
        self.output_dir: Optional[str] = None # Store output directory for opening

        style_manager.apply_card_style(self) # Apply card style to the frame
        style_manager.apply_task_item_style(self) # Apply specific task item style
        self.setContentsMargins(Spacing.M, Spacing.S, Spacing.M, Spacing.S)

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(Spacing.S, Spacing.S, Spacing.S, Spacing.S)
        self.layout.setSpacing(Spacing.M)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft) # Align content to top-left

        # Status Indicator (Icon/Label)
        self.status_indicator = style_manager.create_status_indicator(self.status, self) # Use style manager to create
        self.layout.addWidget(self.status_indicator)

        # Task Info (URL, Status Text, Progress Bar)
        self.info_layout = QVBoxLayout()
        self.info_layout.setContentsMargins(0, 0, 0, 0)
        self.info_layout.setSpacing(Spacing.XS)

        self.url_label = QLabel(self.url, self)
        self.url_label.setFont(style_manager.typography.get_font("M", style_manager.typography.FontWeight.BOLD) if hasattr(style_manager, 'typography') else QFont())
        self.url_label.setToolTip(self.url) # Show full URL on hover
        self.url_label.setWordWrap(True) # Wrap long URLs
        self.info_layout.addWidget(self.url_label)

        self.status_label = QLabel("Pending", self)
        self.status_label.setFont(style_manager.typography.get_font("S", style_manager.typography.FontWeight.MEDIUM) if hasattr(style_manager, 'typography') else QFont())
        self.info_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFont(style_manager.typography.get_font("S") if hasattr(style_manager, 'typography') else QFont())
        self.info_layout.addWidget(self.progress_bar)

        self.layout.addLayout(self.info_layout, 1) # Give info layout stretch factor

        # Actions (Cancel, Remove, Retry, Open Output)
        self.actions_layout = QVBoxLayout()
        self.actions_layout.setContentsMargins(0, 0, 0, 0)
        self.actions_layout.setSpacing(Spacing.XS)
        self.actions_layout.setAlignment(Qt.AlignmentFlag.AlignTop) # Align actions to the top

        self.cancel_button = style_manager.create_modern_button(
            "", parent=self, is_flat=True, icon=IconSet.get_icon(IconSet.ICON_CANCEL) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_SMALL if Dimensions else QSize(16,16)
        )
        self.cancel_button.setToolTip("Cancel Task")
        self.cancel_button.clicked.connect(lambda: self.cancel_requested.emit(self.url))
        self.actions_layout.addWidget(self.cancel_button)

        self.remove_button = style_manager.create_modern_button(
            "", parent=self, is_flat=True, icon=IconSet.get_icon(IconSet.ICON_REMOVE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_SMALL if Dimensions else QSize(16,16)
        )
        self.remove_button.setToolTip("Remove Task")
        self.remove_button.clicked.connect(lambda: self.remove_requested.emit(self.url))
        self.remove_button.setVisible(False) # Initially hidden
        self.actions_layout.addWidget(self.remove_button)

        self.retry_button = style_manager.create_modern_button(
            "", parent=self, is_flat=True, icon=IconSet.get_icon(IconSet.ICON_REFRESH) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_SMALL if Dimensions else QSize(16,16)
        )
        self.retry_button.setToolTip("Retry Task")
        self.retry_button.clicked.connect(lambda: self.retry_requested.emit(self.url))
        self.retry_button.setVisible(False) # Initially hidden
        self.actions_layout.addWidget(self.retry_button)

        self.open_output_button = style_manager.create_modern_button(
            "", parent=self, is_flat=True, icon=IconSet.get_icon(IconSet.ICON_OPEN) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_SMALL if Dimensions else QSize(16,16)
        )
        self.open_output_button.setToolTip("Open Output Directory")
        self.open_output_button.clicked.connect(self._on_open_output_clicked) # Connect to internal slot
        self.open_output_button.setVisible(False) # Initially hidden
        self.actions_layout.addWidget(self.open_output_button)


        self.layout.addLayout(self.actions_layout)

        # Initial UI state based on status
        self._update_action_buttons()


    def update_status(self, status: TaskStatus):
        """Update the task status and UI elements."""
        if self.status != status:
            self.status = status
            self.status_label.setText(status.name.replace("_", " ").title())
            # Ensure status_indicator has the update_status method
            if hasattr(self.status_indicator, 'update_status'):
                 self.status_indicator.update_status(status) # Update indicator icon/color
            self._update_action_buttons()
            logger.debug(f"Task {self.url} status updated to: {status.name}")


    def update_progress(self, progress: float):
        """Update the task progress."""
        # Ensure progress is between 0.0 and 1.0
        self.progress = max(0.0, min(1.0, progress))
        self.progress_bar.setValue(int(self.progress * 100))
        # Optionally update progress text
        self.progress_bar.setFormat(f"{int(self.progress * 100)}%")


    def update_error(self, error: Optional[str]):
        """Update the task error message."""
        self.error = error
        if error:
            self.status_label.setText(f"Failed: {error}") # Display error in status label
            self.setToolTip(f"Error: {error}") # Show full error on tooltip
            logger.error(f"Task {self.url} failed with error: {error}")
        else:
             self.setToolTip("") # Clear tooltip if no error


    def set_output_dir(self, output_dir: str):
        """Set the output directory for the task."""
        self.output_dir = output_dir
        # The open output button visibility is handled by _update_action_buttons


    def _update_action_buttons(self):
        """Update visibility and state of action buttons based on task status."""
        # Ensure TaskStatus enum is available
        if TaskStatus is None:
             logger.warning("TaskStatus enum not available. Cannot update task item buttons.")
             return

        if self.status in [TaskStatus.PENDING, TaskStatus.VALIDATING, TaskStatus.DOWNLOADING, TaskStatus.CONVERTING, TaskStatus.TRANSCRIBING, TaskStatus.TRANSLATING, TaskStatus.RETRYING]:
            self.cancel_button.setVisible(True)
            self.remove_button.setVisible(False)
            self.retry_button.setVisible(False)
            self.open_output_button.setVisible(False)
            self.progress_bar.setVisible(True)

        elif self.status == TaskStatus.PAUSED:
            self.cancel_button.setVisible(True)
            self.remove_button.setVisible(False) # Maybe allow removal when paused?
            self.retry_button.setVisible(False)
            self.open_output_button.setVisible(False)
            self.progress_bar.setVisible(True)

        elif self.status == TaskStatus.COMPLETED:
            self.cancel_button.setVisible(False)
            self.remove_button.setVisible(True)
            self.retry_button.setVisible(False)
            # Show open output button if output directory is set and exists
            self.open_output_button.setVisible(self.output_dir is not None and os.path.exists(self.output_dir))
            self.progress_bar.setVisible(False) # Hide progress bar when completed

        elif self.status in [TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SKIPPED]:
            self.cancel_button.setVisible(False)
            self.remove_button.setVisible(True)
            # Show retry button only if status is FAILED
            self.retry_button.setVisible(self.status == TaskStatus.FAILED)
            self.open_output_button.setVisible(False) # Hide open output button on failure/cancel/skip
            self.progress_bar.setVisible(False) # Hide progress bar

        else: # Default or unknown status
            self.cancel_button.setVisible(False)
            self.remove_button.setVisible(True)
            self.retry_button.setVisible(False)
            self.open_output_button.setVisible(False)
            self.progress_bar.setVisible(False)


    @pyqtSlot()
    def _on_open_output_clicked(self):
        """Handle click on the 'Open Output Directory' button."""
        if self.output_dir and os.path.exists(self.output_dir):
            logger.info(f"Opening output directory: {self.output_dir}")
            try:
                # Use QDesktopServices to open the directory in the file browser
                QDesktopServices.openUrl(QUrl.fromLocalFile(self.output_dir))
                # Add the opened directory to recent files (via AppManager)
                # Access AppManager via parent chain
                if self.parent() and hasattr(self.parent(), 'parent') and self.parent().parent() and hasattr(self.parent().parent(), 'app_manager') and self.parent().parent().app_manager and hasattr(self.parent().parent().app_manager, 'recent_files_manager'):
                    self.parent().parent().app_manager.recent_files_manager.add_file(self.output_dir)

            except Exception as e:
                logger.error(f"Failed to open output directory {self.output_dir}: {e}")
                QMessageBox.critical(self, "Error Opening Directory", f"Failed to open directory:\n{self.output_dir}\nError: {e}")
                # Report error via ErrorReporter if available
                if self.parent() and hasattr(self.parent(), 'parent') and self.parent().parent() and hasattr(self.parent().parent(), 'app_manager') and self.parent().parent().app_manager and hasattr(self.parent().parent().app_manager, 'error_reporter'):
                     self.parent().parent().app_manager.error_reporter.report_error("Failed to Open Output Directory", str(e), ErrorSeverity.ERROR if 'ErrorSeverity' in globals() else None)


# ==============================================================================
# MAIN WINDOW (Continued)
# ==============================================================================

class MainWindow(QMainWindow):
    """Main application window for YouTube Transcriber Pro."""

    # Define signals for interacting with the ApplicationManager/BatchProcessor
    # Modified to avoid Optional type issues with pyqtSignal
    start_batch_requested = pyqtSignal(list, str, object, object, object)
    pause_batch_requested = pyqtSignal()
    resume_batch_requested = pyqtSignal()
    cancel_batch_requested = pyqtSignal()
    cancel_task_requested = pyqtSignal(str)
    remove_task_requested = pyqtSignal(str)
    retry_task_requested = pyqtSignal(str)
    settings_requested = pyqtSignal() # Signal to open settings dialog
    about_requested = pyqtSignal() # Signal to show about dialog
    help_requested = pyqtSignal() # Signal to show help/documentation
    # Add signals for advanced features dialogs
    show_shortcut_config_requested = pyqtSignal()


    def __init__(self, app_manager: Optional[QObject] = None):
        """
        Initialize the main window.

        Args:
            app_manager: Optional reference to the ApplicationManager.
        """
        super().__init__()
        self.app_manager = app_manager # Store reference to application manager
        self.settings = {} # To store current application settings
        self.task_widgets: Dict[str, TaskListItem] = {} # Dictionary to hold TaskListItem widgets by URL

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(Dimensions.MAIN_WINDOW_MIN_WIDTH if Dimensions else 600, Dimensions.MAIN_WINDOW_MIN_HEIGHT if Dimensions else 400)

        # Set window icon
        self.setWindowIcon(IconSet.get_icon(IconSet.APP_ICON) if IconSet else QIcon())

        # Get settings from ApplicationManager or load defaults
        if self.app_manager and hasattr(self.app_manager, 'settings'):
             self.settings = self.app_manager.settings
        else:
             logger.warning("ApplicationManager not provided or settings not accessible. Loading default settings.")
             self.settings = load_settings()

        # Apply global styling (handled by ApplicationManager during initialization)
        # style_manager.apply_global_style(QApplication.instance(), self.settings.get("theme", "dark"))


        # Central Widget and Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(Spacing.L if Spacing else 12, Spacing.L if Spacing else 12, Spacing.L if Spacing else 12, Spacing.L if Spacing else 12)
        self.main_layout.setSpacing(Spacing.L if Spacing else 12)

        # --- Input Area ---
        self.input_card = style_manager.create_card_widget(self.central_widget) if hasattr(style_manager, 'create_card_widget') else QFrame(self.central_widget)
        style_manager.apply_card_style(self.input_card) # Ensure style is applied
        self.input_layout = QVBoxLayout(self.input_card)
        self.input_layout.setContentsMargins(Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12)
        self.input_layout.setSpacing(Spacing.S if Spacing else 8)

        self.input_heading = style_manager.create_modern_heading("Add YouTube URLs", self.input_card) if hasattr(style_manager, 'create_modern_heading') else QLabel("Add YouTube URLs", self.input_card)
        self.input_layout.addWidget(self.input_heading)

        self.url_input = QTextEdit(self.input_card)
        self.url_input.setPlaceholderText("Paste YouTube video or playlist URLs here (one per line)")
        self.url_input.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.url_input.setFixedHeight(100) # Fixed height for input area
        self.url_input.setAcceptRichText(False) # Only accept plain text
        self.input_layout.addWidget(self.url_input)

        # Drag and Drop support
        self.url_input.setAcceptDrops(True)
        self.url_input.dragEnterEvent = self._drag_enter_event
        self.url_input.dropEvent = self._drop_event

        # Input Actions (Add Button)
        self.input_actions_layout = QHBoxLayout()
        self.input_actions_layout.setContentsMargins(0, 0, 0, 0)
        self.input_actions_layout.setSpacing(Spacing.S if Spacing else 8)

        self.add_button = style_manager.create_modern_button(
            "Add to Batch", parent=self.input_card, is_primary=True,
            icon=IconSet.get_icon(IconSet.ICON_ADD) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.add_button.clicked.connect(self._add_urls_to_batch)
        self.input_actions_layout.addWidget(self.add_button)

        self.paste_button = style_manager.create_modern_button(
            "Paste from Clipboard", parent=self.input_card, is_flat=True,
            icon=IconSet.get_icon(IconSet.ICON_CLIPBOARD) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        self.input_actions_layout.addWidget(self.paste_button)

        self.clear_input_button = style_manager.create_modern_button(
            "Clear Input", parent=self.input_card, is_flat=True,
            icon=IconSet.get_icon(IconSet.ICON_REMOVE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.clear_input_button.clicked.connect(self.url_input.clear)
        self.input_actions_layout.addWidget(self.clear_input_button)


        self.input_actions_layout.addStretch(1) # Push buttons to the left
        self.input_layout.addLayout(self.input_actions_layout)

        self.main_layout.addWidget(self.input_card)

        # --- Options Area ---
        self.options_card = style_manager.create_card_widget(self.central_widget) if hasattr(style_manager, 'create_card_widget') else QFrame(self.central_widget)
        style_manager.apply_card_style(self.options_card) # Ensure style is applied
        self.options_layout = QFormLayout(self.options_card)
        self.options_layout.setContentsMargins(Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12)
        self.options_layout.setSpacing(Spacing.S if Spacing else 8)
        self.options_layout.setHorizontalSpacing(Spacing.L if Spacing else 12)
        self.options_layout.setVerticalSpacing(Spacing.S if Spacing else 8)


        self.options_heading = style_manager.create_modern_heading("Options", self.options_card, is_subheading=True) if hasattr(style_manager, 'create_modern_heading') else QLabel("Options", self.options_card)
        # Add heading to the layout (FormLayout doesn't have addWidget directly, need a container or addRow)
        self.options_layout.addRow(self.options_heading)


        # Model Selection
        self.model_combo = QComboBox(self.options_card)
        self.model_combo.addItems(VALID_MODELS) # Use VALID_MODELS from transcribe
        default_model = self.settings.get("default_model", "small")
        if default_model in VALID_MODELS:
             self.model_combo.setCurrentText(default_model)
        else:
             self.model_combo.setCurrentIndex(0) # Select first item if default is invalid or models not loaded

        self.model_combo.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.options_layout.addRow("Whisper Model:", self.model_combo)

        # Language Selection (for translation)
        self.language_combo = QComboBox(self.options_card)
        # Populate with available languages (use names from AVAILABLE_LANGUAGES)
        lang_names = list(AVAILABLE_LANGUAGES.values())
        self.language_combo.addItems(lang_names)
        default_lang_code = self.settings.get("default_language", "None")
        # Find the language name corresponding to the default code
        default_lang_name = AVAILABLE_LANGUAGES.get(default_lang_code, "None")
        self.language_combo.setCurrentText(default_lang_name)


        self.language_combo.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.options_layout.addRow("Translate to:", self.language_combo)

        # Output Directory Selection
        self.output_dir_edit = QLineEdit(self.options_card)
        self.output_dir_edit.setPlaceholderText("Select output directory")
        self.output_dir_edit.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        # Use default from settings or a robust fallback
        default_output_dir = self.settings.get("output_dir", str(Path.home() / "Downloads" / "YouTubeTranscriber"))
        self.output_dir_edit.setText(default_output_dir)

        self.browse_output_button = style_manager.create_modern_button(
            "", parent=self.options_card, is_flat=True,
            icon=IconSet.get_icon(IconSet.ICON_BROWSE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.browse_output_button.clicked.connect(self._browse_output_dir)

        self.output_dir_layout = QHBoxLayout()
        self.output_dir_layout.addWidget(self.output_dir_edit)
        self.output_dir_layout.addWidget(self.browse_output_button)
        self.options_layout.addRow("Output Directory:", self.output_dir_layout)

        # Output Formats Selection (e.g., SRT, JSON)
        self.formats_layout = QHBoxLayout()
        self.formats_layout.setSpacing(Spacing.S if Spacing else 8)
        self.format_srt_checkbox = QCheckBox("SRT", self.options_card)
        self.format_srt_checkbox.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.format_srt_checkbox.setChecked(True) # SRT is often default
        self.formats_layout.addWidget(self.format_srt_checkbox)

        self.format_json_checkbox = QCheckBox("JSON", self.options_card)
        self.format_json_checkbox.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.formats_layout.addWidget(self.format_json_checkbox)

        self.format_vtt_checkbox = QCheckBox("VTT", self.options_card)
        self.format_vtt_checkbox.setFont(style_manager.typography.get_font("M") if hasattr(style_manager, 'typography') else QFont())
        self.formats_layout.addWidget(self.format_vtt_checkbox)

        self.formats_layout.addStretch(1) # Push checkboxes to the left
        self.options_layout.addRow("Export Formats:", self.formats_layout)


        self.main_layout.addWidget(self.options_card)

        # --- Batch Control Area ---
        self.control_card = style_manager.create_card_widget(self.central_widget) if hasattr(style_manager, 'create_card_widget') else QFrame(self.central_widget)
        style_manager.apply_card_style(self.control_card) # Ensure style is applied
        self.control_layout = QHBoxLayout(self.control_card)
        self.control_layout.setContentsMargins(Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12)
        self.control_layout.setSpacing(Spacing.M if Spacing else 12)

        self.start_button = style_manager.create_modern_button(
            "Start Batch", parent=self.control_card, is_primary=True,
            icon=IconSet.get_icon(IconSet.ICON_PLAY) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.start_button.clicked.connect(self._start_batch_processing)
        self.control_layout.addWidget(self.start_button)

        self.pause_button = style_manager.create_modern_button(
            "Pause", parent=self.control_card,
            icon=IconSet.get_icon(IconSet.ICON_PAUSE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.pause_button.clicked.connect(self._pause_batch_processing)
        self.pause_button.setEnabled(False) # Disabled when not running
        self.control_layout.addWidget(self.pause_button)

        self.cancel_button = style_manager.create_modern_button(
            "Cancel", parent=self.control_card, is_danger=True,
            icon=IconSet.get_icon(IconSet.ICON_CANCEL) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.cancel_button.clicked.connect(self._cancel_batch_processing)
        self.cancel_button.setEnabled(False) # Disabled when not running
        self.control_layout.addWidget(self.cancel_button)

        self.control_layout.addStretch(1) # Push buttons to the left

        self.main_layout.addWidget(self.control_card)

        # --- Task List Area ---
        self.task_list_card = style_manager.create_card_widget(self.central_widget) if hasattr(style_manager, 'create_card_widget') else QFrame(self.central_widget)
        style_manager.apply_card_style(self.task_list_card) # Ensure style is applied
        self.task_list_layout = QVBoxLayout(self.task_list_card)
        self.task_list_layout.setContentsMargins(Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12, Spacing.M if Spacing else 12)
        self.task_list_layout.setSpacing(Spacing.S if Spacing else 8)

        self.task_list_heading = style_manager.create_modern_heading("Batch Tasks", self.task_list_card) if hasattr(style_manager, 'create_modern_heading') else QLabel("Batch Tasks", self.task_list_card)
        self.task_list_layout.addWidget(self.task_list_heading)

        self.task_scroll_area = QScrollArea(self.task_list_card)
        style_manager.apply_scrollable_style(self.task_scroll_area) # Apply scrollable style
        self.task_scroll_area.setWidgetResizable(True)

        self.task_list_container = QWidget()
        self.task_list_container_layout = QVBoxLayout(self.task_list_container)
        self.task_list_container_layout.setContentsMargins(0, 0, 0, 0)
        self.task_list_container_layout.setSpacing(Spacing.XS if Spacing else 4) # Smaller spacing between task items
        self.task_list_container_layout.addStretch(1) # Push items to the top

        self.task_scroll_area.setWidget(self.task_list_container)
        self.task_list_layout.addWidget(self.task_scroll_area, 1) # Give task list stretch factor

        # Add a button to clear completed tasks
        self.clear_completed_button = style_manager.create_modern_button(
            "Clear Completed", parent=self.task_list_card, is_flat=True,
            icon=IconSet.get_icon(IconSet.ICON_REMOVE) if IconSet else QIcon(), icon_size=Dimensions.ICON_SIZE_MEDIUM if Dimensions else QSize(24,24)
        )
        self.clear_completed_button.clicked.connect(self.clear_completed_tasks)
        self.clear_completed_button.setVisible(False) # Initially hidden
        self.task_list_layout.addWidget(self.clear_completed_button)


        self.main_layout.addWidget(self.task_list_card, 1) # Give task list stretch factor

        # --- Status Bar ---
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label = QLabel("Ready")
        self.status_label.setFont(style_manager.typography.get_font("S") if hasattr(style_manager, 'typography') else QFont())
        self.statusBar.addWidget(self.status_label)

        self.batch_progress_bar = QProgressBar()
        self.batch_progress_bar.setRange(0, 100)
        self.batch_progress_bar.setValue(0)
        self.batch_progress_bar.setTextVisible(True)
        self.batch_progress_bar.setFont(style_manager.typography.get_font("S") if hasattr(style_manager, 'typography') else QFont())
        self.batch_progress_bar.setVisible(False) # Hidden when idle
        self.statusBar.addPermanentWidget(self.batch_progress_bar)

        # --- Menu Bar ---
        self._create_menu_bar()

        # Batch Processor Instance (managed by ApplicationManager in a real app)
        # For standalone UI development/testing, create a mock or real instance here
        if self.app_manager and hasattr(self.app_manager, 'batch_processor'):
             self.batch_processor = self.app_manager.batch_processor
             # Connect signals from batch processor to UI slots
             # These connections are handled by ApplicationManager forwarding signals
             pass
        else:
             logger.warning("ApplicationManager or BatchProcessor not available. Batch processing disabled.")
             self.batch_processor = None # Disable batch processing if not available
             # Disable batch control buttons
             self.start_button.setEnabled(False)
             self.pause_button.setEnabled(False)
             self.cancel_button.setEnabled(False)


        # Initial UI state update
        self._update_ui_state(BatchStatus.IDLE if BatchStatus else None) # Handle case where BatchStatus is not imported

        # Timer to periodically update UI elements that might not be covered by signals
        # e.g., elapsed time, general status checks
        self.ui_update_timer = QTimer(self)
        self.ui_update_timer.timeout.connect(self._periodic_ui_update)
        self.ui_update_timer.start(1000) # Update every 1 second


    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")

        # Add Recent Files Menu (managed by ApplicationManager)
        # RecentFilesMenu should be a QMenu subclass
        # Create the RecentFilesMenu instance here
        self.recent_files_menu = RecentFilesMenu(self) if ADVANCED_FEATURES_AVAILABLE and 'RecentFilesMenu' in globals() else QMenu("Recent Files (Not Available)", self)

        if ADVANCED_FEATURES_AVAILABLE and 'RecentFilesMenu' in globals():
             # Connect recent file clicked signal from the RecentFilesMenu instance
             # This is connected in AppManager now: self.recent_files_menu.file_opened.connect(self.app_manager._open_recent_file)
             # Connect the RecentFilesManager's signal to this menu's update method
             # This is connected in AppManager now: self.app_manager.recent_files_changed.connect(self.recent_files_menu.update_menu)
             # Connect the menu's clear recent files signal back to AppManager
             # This is connected in AppManager now: self.recent_files_menu.clear_recent_files_requested.connect(self.app_manager._clear_recent_files)

             # Add the recent files menu to the file menu
             file_menu.addMenu(self.recent_files_menu)
             # The AppManager will call update_menu after restoring session/loading settings


        else:
             # Add a disabled placeholder menu if manager is not available
             self.recent_files_menu.setEnabled(False)
             file_menu.addMenu(self.recent_files_menu)


        file_menu.addSeparator()

        # Exit Action
        exit_action = QAction(IconSet.get_icon("exit.svg") if IconSet else QIcon(), "&Exit", self) # Assuming an exit icon exists
        exit_action.setShortcuts([QKeySequence("Ctrl+Q"), QKeySequence(Qt.Key.Key_F4 | Qt.Modifier.AltModifier)]) # Add Alt+F4
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit Menu
        edit_menu = menu_bar.addMenu("&Edit")
        # Add standard edit actions (Cut, Copy, Paste - might need to connect to focused widget)
        # These actions are typically handled by the focused widget (QLineEdit, QTextEdit)
        # We can add them here for completeness but their triggered signals would need
        # to be connected dynamically based on which widget has focus.
        # Or, use QAction.setShortcut and let Qt handle it if the focused widget
        # has standard cut/copy/paste slots.

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence("Ctrl+X"))
        # cut_action.triggered.connect(...) # Connect dynamically or rely on Qt
        edit_menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence("Ctrl+C"))
        # copy_action.triggered.connect(...) # Connect dynamically or rely on Qt
        edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence("Ctrl+V"))
        # paste_action.triggered.connect(...) # Connect dynamically or rely on Qt
        edit_menu.addAction(paste_action)

        edit_menu.addSeparator()

        # Settings Action
        settings_action = QAction(IconSet.get_icon(IconSet.ICON_SETTINGS) if IconSet else QIcon(), "&Settings...", self)
        settings_action.setShortcut(QKeySequence("Ctrl+,"))
        settings_action.triggered.connect(self.settings_requested.emit) # Emit signal
        edit_menu.addAction(settings_action)

        # Shortcut Configuration Action (if KeyboardManager is available)
        if ADVANCED_FEATURES_AVAILABLE and 'KeyboardManager' in globals():
             shortcut_config_action = QAction("Keyboard &Shortcuts...", self)
             shortcut_config_action.triggered.connect(self.show_shortcut_config_requested.emit) # Emit signal
             edit_menu.addAction(shortcut_config_action)


        # Help Menu
        help_menu = menu_bar.addMenu("&Help")

        # Help Content Action
        help_action = QAction("&Help Content", self)
        help_action.setShortcut(QKeySequence("F1"))
        help_action.triggered.connect(self.help_requested.emit) # Emit signal
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        # About Action
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.about_requested.emit) # Emit signal
        help_menu.addAction(about_action)

        # Add Check for Updates Action (managed by ApplicationManager)
        if ADVANCED_FEATURES_AVAILABLE and 'AutoUpdater' in globals():
            check_updates_action = QAction("Check for &Updates...", self)
            # Connect this action to a signal that the ApplicationManager handles
            check_updates_action.triggered.connect(self._check_for_updates_now_from_menu)
            help_menu.addAction(check_updates_action)


    def _drag_enter_event(self, event: QDragEnterEvent):
        """Handle drag enter event for URL input."""
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def _drop_event(self, event: QDropEvent):
        """Handle drop event for URL input."""
        if event.mimeData().hasText():
            # Append dropped text (URLs) to the current text
            current_text = self.url_input.toPlainText()
            dropped_text = event.mimeData().text()
            new_text = f"{current_text}\n{dropped_text}".strip()
            self.url_input.setPlainText(new_text)
            event.acceptProposedAction()

    def _paste_from_clipboard(self):
        """Paste text from clipboard into the URL input."""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        if mime_data.hasText():
            current_text = self.url_input.toPlainText()
            pasted_text = mime_data.text()
            new_text = f"{current_text}\n{pasted_text}".strip()
            self.url_input.setPlainText(new_text)


    def _add_urls_to_batch(self):
        """Add URLs from the input field to the batch processor."""
        urls_text = self.url_input.toPlainText().strip()
        if not urls_text:
            QMessageBox.warning(self, "No URLs", "Please enter at least one YouTube URL.")
            return

        urls = [url.strip() for url in urls_text.split('\n') if url.strip()] # Split by newline and clean up

        if not urls:
             QMessageBox.warning(self, "No Valid URLs", "No valid URLs found in the input.")
             return

        # Get selected options
        model = self.model_combo.currentText()
        target_lang_name = self.language_combo.currentText()
        # Convert language name back to code
        target_lang_code = next((code for code, name in AVAILABLE_LANGUAGES.items() if name == target_lang_name), "None")
        target_lang = target_lang_code if target_lang_code != "None" else None # Use None if "None" is selected

        output_dir = self.output_dir_edit.text().strip()
        selected_formats = []
        if self.format_srt_checkbox.isChecked():
            selected_formats.append("srt")
        if self.format_json_checkbox.isChecked():
            selected_formats.append("json")
        if self.format_vtt_checkbox.isChecked():
            selected_formats.append("vtt")

        if not output_dir:
             QMessageBox.warning(self, "Output Directory Not Set", "Please select an output directory.")
             return

        if not selected_formats:
             QMessageBox.warning(self, "No Output Format Selected", "Please select at least one output format.")
             return


        logger.info(f"Adding {len(urls)} URLs to batch.")
        # Clear the input field after adding
        self.url_input.clear()

        # Emit signal to ApplicationManager to handle adding tasks and potentially starting the batch
        self.start_batch_requested.emit(urls, model, target_lang, output_dir, selected_formats)


    def _start_batch_processing(self):
        """Initiate batch processing."""
        if self.batch_processor:
            # Ensure there are tasks to process
            if not self.batch_processor.tasks:
                QMessageBox.information(self, "No Tasks", "Please add URLs to the batch before starting.")
                return

            # If batch is paused, clicking start should resume it
            if self.batch_processor.status == (BatchStatus.PAUSED if BatchStatus else None):
                 self._resume_batch_processing()
            # If batch is idle, completed, failed, or cancelled, clicking start should process existing tasks
            elif self.batch_processor.status in [(BatchStatus.IDLE if BatchStatus else None), (BatchStatus.COMPLETED if BatchStatus else None), (BatchStatus.FAILED if BatchStatus else None), (BatchStatus.CANCELLED if BatchStatus else None)]:
                 logger.info("Initiating batch processing for existing tasks.")
                 # Emit signal to ApplicationManager to start processing current tasks
                 # Send empty list of URLs to indicate processing existing tasks
                 self.start_batch_requested.emit([], "", None, None, [])
            # If batch is already running or stopping, do nothing
            elif self.batch_processor.status in [(BatchStatus.RUNNING if BatchStatus else None), (BatchStatus.THROTTLED if BatchStatus else None), (BatchStatus.STOPPING if BatchStatus else None)]:
                 logger.debug("Batch is already running or stopping.")
                 pass # Do nothing

            # UI state will be updated by signals from BatchProcessor forwarded by AppManager


    def _pause_batch_processing(self):
        """Pause batch processing."""
        logger.info("Pause batch button clicked.")
        self.pause_batch_requested.emit() # Emit signal
        # UI state will be updated by signals from BatchProcessor forwarded by AppManager

    def _resume_batch_processing(self):
        """Resume the paused batch processing."""
        logger.info("Resume batch button clicked.")
        self.resume_batch_requested.emit() # Emit signal
        # UI state will be updated by signals from BatchProcessor forwarded by AppManager


    def _cancel_batch_processing(self):
        """Cancel batch processing."""
        logger.info("Cancel batch button clicked.")
        # Confirm cancellation with the user
        reply = QMessageBox.question(self, "Confirm Cancellation",
                                     "Are you sure you want to cancel the current batch?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.cancel_batch_requested.emit() # Emit signal
            # UI state will be updated by signals from BatchProcessor forwarded by AppManager


    def _browse_output_dir(self):
        """Open a dialog to select the output directory."""
        current_dir = self.output_dir_edit.text()
        if not os.path.isdir(current_dir):
             current_dir = str(Path.home()) # Default to home if current is invalid

        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", current_dir)
        if directory:
            self.output_dir_edit.setText(directory)
            # Optionally save this selected directory to settings immediately
            # This should be handled by the Settings Dialog or AppManager's settings saving logic
            # For now, just update the UI field.


    @pyqtSlot(dict)
    def _update_ui_progress(self, update: Dict[str, Any]):
        """
        Slot to receive progress updates from the ApplicationManager and update the UI.
        This slot is called from the main GUI thread, so direct UI updates are safe.
        """
        update_type = update.get("type")

        if update_type == "task_progress":
            task_data = update.get("task")
            if task_data:
                url = task_data.get("url")
                if url in self.task_widgets:
                    task_widget = self.task_widgets[url]
                    # Update task-specific UI elements
                    # Use getattr with default to handle potential missing keys safely
                    status = TaskStatus[task_data.get("status", "PENDING")] if TaskStatus and task_data.get("status") else (TaskStatus.PENDING if TaskStatus else None)
                    if status:
                         task_widget.update_status(status)
                    task_widget.update_progress(task_data.get("progress", 0.0))
                    if task_data.get("error") is not None:
                        task_widget.update_error(task_data.get("error"))
                    if task_data.get("output_dir") is not None:
                         task_widget.set_output_dir(task_data.get("output_dir"))

                    # Update overall batch progress bar in status bar
                    batch_progress = update.get("batch_progress", 0.0)
                    self.batch_progress_bar.setValue(int(batch_progress * 100))
                    self.batch_progress_bar.setFormat(f"Batch: {batch_progress:.1%}")

        elif update_type == "batch_progress":
            # Update overall batch progress bar and status label
            batch_progress = update.get("batch_progress", 0.0)
            batch_status_str = update.get("batch_status", "IDLE")
            batch_status = BatchStatus[batch_status_str] if BatchStatus and batch_status_str else (BatchStatus.IDLE if BatchStatus else None)

            self.batch_progress_bar.setValue(int(batch_progress * 100))
            self.batch_progress_bar.setFormat(f"Batch: {batch_progress:.1%}")
            self.status_label.setText(f"Batch Status: {batch_status_str.replace('_', ' ').title()}")

            # Update batch control buttons based on batch status
            if batch_status:
                 self._update_ui_state(batch_status)

        elif update_type == "status":
             # General status updates (e.g., "Loading model...")
             status_message = update.get("message", "Updating...")
             self.statusBar.showMessage(status_message) # Use showMessage for temporary status


    @pyqtSlot(dict)
    def _handle_batch_completion(self, report: Dict[str, Any]):
        """Slot to handle batch completion, failure, or cancellation."""
        status_str = report.get("status", "UNKNOWN")
        status = BatchStatus[status_str] if BatchStatus and status_str else (BatchStatus.IDLE if BatchStatus else None)
        logger.info(f"Batch processing finished with status: {status_str}")

        # Update UI state based on final batch status
        if status:
             self._update_ui_state(status)

        # Update individual task widgets with their final status
        for url, task_data in report.get("tasks", {}).items():
            if url in self.task_widgets:
                task_widget = self.task_widgets[url]
                task_status = TaskStatus[task_data.get("status", "FAILED")] if TaskStatus and task_data.get("status") else (TaskStatus.FAILED if TaskStatus else None)
                if task_status:
                     task_widget.update_status(task_status)
                task_widget.update_progress(task_data.get("progress", 0.0))
                if task_data.get("error") is not None:
                    task_widget.update_error(task_data.get("error"))
                if task_data.get("output_dir") is not None:
                     task_widget.set_output_dir(task_data.get("output_dir"))


        # Show a message box summarizing the result
        total = report.get("total", 0)
        completed = report.get("completed", 0)
        failed = report.get("failed", 0)
        cancelled = report.get("cancelled", 0)
        skipped = report.get("skipped", 0)

        summary_message = f"Batch processing finished.\n\n" \
                          f"Status: {status_str.replace('_', ' ').title()}\n" \
                          f"Total Tasks: {total}\n" \
                          f"Completed: {completed}\n" \
                          f"Failed: {failed}\n" \
                          f"Cancelled: {cancelled}\n" \
                          f"Skipped: {skipped}"

        if status == (BatchStatus.COMPLETED if BatchStatus else None):
            QMessageBox.information(self, "Batch Completed", summary_message)
        elif status == (BatchStatus.FAILED if BatchStatus else None):
            QMessageBox.critical(self, "Batch Failed", summary_message)
        elif status == (BatchStatus.CANCELLED if BatchStatus else None):
            QMessageBox.warning(self, "Batch Cancelled", summary_message)
        else:
            QMessageBox.information(self, "Batch Finished", summary_message)

        # Show the Clear Completed button if there are completed/failed/cancelled tasks
        if completed > 0 or failed > 0 or cancelled > 0 or skipped > 0:
             self.clear_completed_button.setVisible(True)


    @pyqtSlot(dict)
    def _handle_resource_warning(self, warning_data: Dict[str, Any]):
        """Slot to handle resource constraint warnings."""
        warning_type = warning_data.get("warning_type", "unknown")
        message = warning_data.get("message", "Resource warning detected.")
        value = warning_data.get("value")

        logger.warning(f"UI received resource warning: {warning_type} - {message}")

        # Display a non-blocking notification or update status bar
        # Using SystemTrayManager via ApplicationManager (handled in AppManager)

        # Also update status bar
        self.statusBar.showMessage(f"WARNING: {message}", 5000) # Show in status bar for 5 seconds
        # Consider changing status bar color temporarily for warnings


    @pyqtSlot(str, str)
    def _handle_error_report(self, message: str, details: str):
        """Slot to handle errors reported by the ApplicationManager and display an ErrorDialog."""
        logger.error(f"UI received error report: {message}")
        # Ensure ErrorDialog class is available
        if 'ErrorDialog' in globals() and ErrorDialog is not None:
             error_dialog = ErrorDialog(message, details, self)
             error_dialog.exec() # Show dialog modally
        else:
             logger.warning("ErrorDialog class not available. Cannot show error details.")
             QMessageBox.critical(self, f"{APP_NAME} - Error", f"An error occurred:\n{message}")


    @pyqtSlot(object, str)
    def _handle_update_ui_status(self, status: UpdateStatus, message: str):
        """Slot to handle update status changes and update UI elements."""
        logger.debug(f"UI received update status change: {status.name if status else 'N/A'}, message: {message}")
        # Update UI elements related to updates (e.g., show status in status bar, enable/disable update buttons)
        update_status_text = f"Update Status: {status.name.replace('_', ' ').title() if status else 'Unknown'}"
        if message:
             update_status_text += f" - {message}"
        self.statusBar.showMessage(update_status_text, 5000) # Show in status bar for 5 seconds

        # You might also want to update the "Check for Updates Now" button state or text
        # based on the update status (e.g., disable while checking/downloading)


    @pyqtSlot(str, str, NotificationType)
    def _handle_notification_request(self, title: str, message: str, type: NotificationType):
        """Slot to handle notification requests and show a system tray message."""
        # This signal is forwarded from AppManager to SystemTrayManager,
        # but we can keep a slot here in case the UI needs to react to notifications
        # (e.g., showing a message box in addition to tray icon).
        logger.debug(f"UI received notification request: {title} - {message} ({type.name if type else 'N/A'})")
        # Example: show a message box for critical notifications
        # if type == (NotificationType.CRITICAL if NotificationType else None):
        #      QMessageBox.critical(self, title, message)


    @pyqtSlot()
    def _check_for_updates_now_from_menu(self):
        """Handle 'Check for Updates Now' action from the menu."""
        # Emit signal to ApplicationManager
        if self.app_manager and hasattr(self.app_manager, 'auto_updater') and self.app_manager.auto_updater:
             self.app_manager.auto_updater.check_for_updates()
             self.statusBar.showMessage("Checking for updates...", 3000) # Show temporary status
        else:
             QMessageBox.warning(self, "Updater Not Available", "Auto-updater is not available.")


    def _update_ui_state(self, batch_status: Optional[BatchStatus]):
        """Update the state of UI elements based on the batch status."""
        # Handle case where BatchStatus is not imported
        if BatchStatus is None:
             logger.warning("BatchStatus enum not available. Cannot update UI state accurately.")
             return

        is_idle_or_finished = batch_status in [BatchStatus.IDLE, BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]
        is_running = batch_status in [BatchStatus.RUNNING, BatchStatus.THROTTLED]
        is_paused = batch_status == BatchStatus.PAUSED
        is_stopping = batch_status == BatchStatus.STOPPING

        self.start_button.setEnabled(is_idle_or_finished or is_paused)
        self.pause_button.setEnabled(is_running or is_paused) # Can pause/resume when paused
        self.cancel_button.setEnabled(is_running or is_paused or is_stopping) # Can cancel when running, paused, or stopping
        self.batch_progress_bar.setVisible(not is_idle_or_finished) # Hide progress bar when idle/finished

        # Enable/Disable input area and options based on running/stopping state
        input_options_enabled = not is_running and not is_stopping and not is_paused # Disable input/options when running, paused, or stopping
        self.url_input.setEnabled(input_options_enabled)
        self.add_button.setEnabled(input_options_enabled)
        self.paste_button.setEnabled(input_options_enabled)
        self.clear_input_button.setEnabled(input_options_enabled)
        self.model_combo.setEnabled(input_options_enabled)
        self.language_combo.setEnabled(input_options_enabled)
        self.output_dir_edit.setEnabled(input_options_enabled)
        self.browse_output_button.setEnabled(input_options_enabled)
        self.format_srt_checkbox.setEnabled(input_options_enabled)
        self.format_json_checkbox.setEnabled(input_options_enabled)
        self.format_vtt_checkbox.setEnabled(input_options_enabled)


        # Update button text for Start/Resume
        if is_paused:
             self.start_button.setText("Resume Batch")
             self.start_button.setIcon(IconSet.get_icon(IconSet.ICON_PLAY) if IconSet else QIcon())
             self.start_button.setProperty("primary", "true") # Keep primary style
             self.start_button.style().polish(self.start_button) # Repolish to apply style
        else:
             self.start_button.setText("Start Batch")
             self.start_button.setIcon(IconSet.get_icon(IconSet.ICON_PLAY) if IconSet else QIcon())
             self.start_button.setProperty("primary", "true")
             self.start_button.style().polish(self.start_button)

        # Update status bar text
        if batch_status == BatchStatus.IDLE:
             self.status_label.setText("Ready")
        elif batch_status == BatchStatus.RUNNING:
             self.status_label.setText("Batch Status: Running")
        elif batch_status == BatchStatus.PAUSED:
             self.status_label.setText("Batch Status: Paused")
        elif batch_status == BatchStatus.STOPPING:
             self.status_label.setText("Batch Status: Stopping...")
        elif batch_status == BatchStatus.THROTTLED:
             self.status_label.setText("Batch Status: Throttled (Resource Limited)")
        elif batch_status == BatchStatus.COMPLETED:
             self.status_label.setText("Batch Completed")
        elif batch_status == BatchStatus.FAILED:
             self.status_label.setText("Batch Failed")
        elif batch_status == BatchStatus.CANCELLED:
             self.status_label.setText("Batch Cancelled")
        else:
             self.status_label.setText(f"Batch Status: {batch_status.name.replace('_', ' ').title()}")

        # Show/Hide Clear Completed button
        has_completed_tasks = any(widget.status in [(TaskStatus.COMPLETED if TaskStatus else None), (TaskStatus.FAILED if TaskStatus else None), (TaskStatus.CANCELLED if TaskStatus else None), (TaskStatus.SKIPPED if TaskStatus else None)] for widget in self.task_widgets.values())
        self.clear_completed_button.setVisible(has_completed_tasks)


    def _periodic_ui_update(self):
        """Perform periodic UI updates (e.g., status text, elapsed time)."""
        # This is a fallback for updates not covered by specific signals.
        # For example, updating elapsed time for running tasks.
        # If TaskListItem updates itself based on start/end times, this might not be needed.
        pass # Placeholder for now


    def add_task_to_ui(self, url: str):
        """Add a new TaskListItem widget to the UI for a given URL."""
        if url not in self.task_widgets:
            logger.debug(f"Adding task {url} to UI.")
            task_widget = TaskListItem(url, self.task_list_container)

            # Connect signals from the task widget to slots in the main window
            task_widget.cancel_requested.connect(self.cancel_task_requested.emit)
            task_widget.remove_requested.connect(self.remove_task_requested.emit)
            task_widget.retry_requested.connect(self.retry_task_requested.emit)
            # task_widget.open_output_requested.connect(task_widget._on_open_output_clicked) # Connect directly or via signal?
            # Connected directly in TaskListItem __init__

            self.task_widgets[url] = task_widget
            # Insert the new task at the top of the list (before the stretch)
            self.task_list_container_layout.insertWidget(0, task_widget)

            # Update UI state as tasks are added
            if self.batch_processor and BatchStatus:
                 self._update_ui_state(self.batch_processor.status)


        else:
            logger.debug(f"Task {url} already exists in UI.")


    @pyqtSlot(str)
    def remove_task_from_ui(self, url: str):
        """Remove a TaskListItem widget from the UI for a given URL."""
        if url in self.task_widgets:
            logger.debug(f"Removing task {url} from UI.")
            task_widget = self.task_widgets.pop(url)
            self.task_list_container_layout.removeWidget(task_widget)
            task_widget.deleteLater() # Schedule for deletion

            # If the task was running/pending, this removal should also cancel it in the batch processor
            # The signal remove_task_requested should be connected to the BatchProcessor's remove method

            # Update UI state if the last task was removed
            if not self.task_widgets and self.batch_processor and BatchStatus:
                 self.batch_processor.status = BatchStatus.IDLE # Set batch status to idle if no tasks left
                 self._update_ui_state(BatchStatus.IDLE)
            # Update Clear Completed button visibility
            has_completed_tasks = any(widget.status in [(TaskStatus.COMPLETED if TaskStatus else None), (TaskStatus.FAILED if TaskStatus else None), (TaskStatus.CANCELLED if TaskStatus else None), (TaskStatus.SKIPPED if TaskStatus else None)] for widget in self.task_widgets.values())
            self.clear_completed_button.setVisible(has_completed_tasks)


    def clear_completed_tasks(self):
        """Clear all completed, failed, cancelled, or skipped tasks from the UI."""
        urls_to_remove = [
            url for url, widget in self.task_widgets.items()
            if widget.status in [(TaskStatus.COMPLETED if TaskStatus else None), (TaskStatus.FAILED if TaskStatus else None), (TaskStatus.CANCELLED if TaskStatus else None), (TaskStatus.SKIPPED if TaskStatus else None)]
        ]
        for url in urls_to_remove:
            # Remove from BatchProcessor first if it still exists there
            if self.batch_processor and url in self.batch_processor.tasks:
                 # Call remove_task on AppManager, which will call BatchProcessor.remove_task
                 # and then remove from UI.
                 if self.app_manager:
                      self.app_manager.remove_task(url)
                 else:
                      # Fallback if AppManager is not available
                      if self.batch_processor:
                           self.batch_processor.remove_task(url)
                      self.remove_task_from_ui(url) # Remove from UI directly


            # If BatchProcessor is not available or task already removed, remove from UI directly
            elif url in self.task_widgets:
                 self.remove_task_from_ui(url)


        logger.info(f"Cleared {len(urls_to_remove)} completed tasks from UI.")
        # Hide the button after clearing
        has_completed_tasks_after_clear = any(widget.status in [(TaskStatus.COMPLETED if TaskStatus else None), (TaskStatus.FAILED if TaskStatus else None), (TaskStatus.CANCELLED if TaskStatus else None), (TaskStatus.SKIPPED if TaskStatus else None)] for widget in self.task_widgets.values())
        self.clear_completed_button.setVisible(has_completed_tasks_after_clear)


    def closeEvent(self, event: QCloseEvent):
        """Handle window close event."""
        # Ask for confirmation if batch is running
        if self.batch_processor and BatchStatus and self.batch_processor.status in [BatchStatus.RUNNING, BatchStatus.PAUSED, BatchStatus.THROTTLED, BatchStatus.STOPPING]:
            reply = QMessageBox.question(self, "Confirm Exit",
                                         "A batch is currently in progress. Are you sure you want to exit?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)

            if reply == QMessageBox.StandardButton.Yes:
                # Initiate graceful shutdown of the batch processor
                if self.batch_processor:
                    self.batch_processor.shutdown(wait=False) # Don't wait for shutdown here
                event.accept() # Accept the close event
            else:
                event.ignore() # Ignore the close event
        else:
            # If no batch is running, just accept the close event
            event.accept()

    # --- Slots to show dialogs (called by ApplicationManager) ---

    @pyqtSlot(dict)
    def show_settings_dialog(self, current_settings: Dict[str, Any]):
        """Show the settings dialog."""
        logger.info("Showing settings dialog.")
        # Ensure SettingsDialog class is available
        if 'SettingsDialog' in globals() and SettingsDialog is not None:
             settings_dialog = SettingsDialog(current_settings, self)
             # Connect the dialog's settings_saved signal to a slot in ApplicationManager
             if self.app_manager and hasattr(self.app_manager, '_handle_settings_saved'):
                  settings_dialog.settings_saved.connect(self.app_manager._handle_settings_saved)
             settings_dialog.exec() # Show dialog modally
        else:
             logger.warning("SettingsDialog class not available.")
             QMessageBox.warning(self, "Settings", "Settings dialog is not available.")


    @pyqtSlot()
    def show_about_dialog(self):
        """Show the about dialog."""
        logger.info("Showing about dialog.")
        # Ensure AboutDialog class is available
        if 'AboutDialog' in globals() and AboutDialog is not None:
             about_dialog = AboutDialog(self)
             about_dialog.exec() # Show dialog modally
        else:
             logger.warning("AboutDialog class not available.")
             QMessageBox.warning(self, "About", "About dialog is not available.")


    # ErrorDialog is shown directly by _handle_error_report slot


    @pyqtSlot(dict)
    def show_shortcut_config_dialog(self, current_shortcuts: Dict[ShortcutAction, Tuple[str, bool]]):
        """Show the shortcut configuration dialog."""
        logger.info("Showing shortcut configuration dialog.")
        # Ensure ShortcutConfigDialog class is available
        if 'ShortcutConfigDialog' in globals() and ShortcutConfigDialog is not None:
             shortcut_dialog = ShortcutConfigDialog(current_shortcuts, self)
             # Connect the dialog's shortcuts_saved signal to a slot in ApplicationManager
             if self.app_manager and hasattr(self.app_manager, '_handle_shortcuts_saved'):
                  shortcut_dialog.shortcuts_saved.connect(self.app_manager._handle_shortcuts_saved)
             shortcut_dialog.exec() # Show dialog modally
        else:
             logger.warning("ShortcutConfigDialog class not available.")
             QMessageBox.warning(self, "Shortcuts", "Shortcut configuration dialog is not available.")


    @pyqtSlot()
    def show_help(self):
        """Show help or documentation."""
        logger.info("Showing help.")
        # Open documentation URL or local help file
        help_url = "https://yourwebsite.com/docs" # Replace with actual help URL
        try:
            QDesktopServices.openUrl(QUrl(help_url))
        except Exception as e:
            logger.error(f"Failed to open help URL {help_url}: {e}")
            if self.app_manager and hasattr(self.app_manager, 'error_reporter') and self.app_manager.error_reporter:
                 self.app_manager.error_reporter.report_error("Failed to open help", str(e), ErrorSeverity.WARNING if 'ErrorSeverity' in globals() else None)
            QMessageBox.warning(self, "Help", f"Could not open help documentation.\nTry visiting: {help_url}")

