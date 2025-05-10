""""
Integration components for YouTube Translator Pro.
Provides helper methods to integrate new features into the main application.
""""

import os
import logging
import threading
from functools import partial

# Set up logging
logger = logging.getLogger(__name__)

try:
    # First try PyQt6
    try:
    from PyQt6.QtWidgets import ()
except ImportError:
    from PyQt5.QtWidgets import ()
        QToolBar, QMenu, QStatusBar, QLabel,
        QMenuBar, QMainWindow, QMessageBox, QDialog,
        QVBoxLayout
    )
    try:
    from PyQt6.QtGui import QAction, QIcon
except ImportError:
    from PyQt5.QtGui import QAction, QIcon
    try:
    from PyQt6.QtCore import Qt, QSettings, QTimer, pyqtSignal
except ImportError:
    from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSignal
    USE_PYQT6 = True
    logger.info("Using PyQt6 for UI integration components")
except ImportError:
    try:
        # Then try PyQt5
        from PyQt5.QtWidgets import ()
            QToolBar, QMenu, QStatusBar, QLabel,
            QMenuBar, QMainWindow, QMessageBox, QDialog,
            QVBoxLayout
        )
        from PyQt5.QtGui import QAction, QIcon
        from PyQt5.QtCore import Qt, QSettings, QTimer, pyqtSignal
        USE_PYQT6 = False
        logger.info("Using PyQt5 for UI integration components")
    except ImportError:
        # If neither PyQt6 nor PyQt5 is available, create mock classes
        logger.warning("Neither PyQt6 nor PyQt5 is available. Creating mock classes for integration components.")
        USE_PYQT6 = False
        
        # Mock implementations for QtWidgets classes
        class QToolBar:
            def __init__(self, *args, **kwargs): pass
            def addAction(self, *args, **kwargs): pass
            def addSeparator(self, *args, **kwargs): pass
        
        class QMenu:
            def __init__(self, *args, **kwargs): pass
            def addAction(self, *args, **kwargs): pass
            def addSeparator(self, *args, **kwargs): pass
            
        class QStatusBar:
            def __init__(self, *args, **kwargs): pass
            def showMessage(self, *args, **kwargs): pass
            
        class QLabel:
            def __init__(self, *args, **kwargs): pass
            def setText(self, *args, **kwargs): pass
            
        class QMenuBar:
            def __init__(self, *args, **kwargs): pass
            def addMenu(self, *args, **kwargs): pass
            
        class QMainWindow:
            def __init__(self, *args, **kwargs): pass
            def setCentralWidget(self, *args, **kwargs): pass
            
        class QMessageBox:
            def __init__(self, *args, **kwargs): pass
            @staticmethod
            def information(*args, **kwargs): pass
            @staticmethod
            def warning(*args, **kwargs): pass
            @staticmethod
            def critical(*args, **kwargs): pass
            
        class QDialog:
            def __init__(self, *args, **kwargs): pass
            def exec(self, *args, **kwargs): pass
            
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, *args, **kwargs): pass
            
        # Mock implementations for QtGui classes
        class QAction:
            def __init__(self, *args, **kwargs): pass
            def triggered(self): return MockSignal()
            def setEnabled(self, *args, **kwargs): pass
            
        class QIcon:
            def __init__(self, *args, **kwargs): pass
            
        # Mock implementations for QtCore classes
        class Qt:
            AlignCenter = 0
            AlignLeft = 0
            AlignRight = 0
            
        class QSettings:
            def __init__(self, *args, **kwargs): pass
            def setValue(self, *args, **kwargs): pass
            def value(self, *args, **kwargs): return None
            
        class QTimer:
            def __init__(self, *args, **kwargs): pass
            def timeout(self): return MockSignal()
            def start(self, *args, **kwargs): pass
            def stop(self): pass
            
        class MockSignal:
            def __init__(self): pass
            def connect(self, func): pass
            def emit(self, *args): pass
            
        # Alias for pyqtSignal
        pyqtSignal = lambda *args, **kwargs: MockSignal()

from src.utils.localization import localization, get_string
from src.utils.telemetry import telemetry
from src.utils.performance_monitor import monitor, measure_performance
from src.ui.language_selector import LanguageSelector
from src.ui.performance_monitor_widget import PerformanceMonitorWidget
from src.ui.settings_dialog import SettingsDialog
from src.ui.telemetry_consent_dialog import TelemetryConsentDialog
from src.config import get_settings, save_settings, VERSION

# Set up logging
logger = logging.getLogger(__name__)

class FeatureIntegrator:
    """Helper class to integrate new features into the main window."""
    
    def __init__(self, main_window):
        """"
        Initialize the feature integrator.
        
        Args:
            main_window: The main application window
        """"
        self.main_window = main_window
        self.settings = get_settings()
        
        # Initialize components
        self.language_selector = None
        self.performance_dialog = None
        
        # Load telemetry consent status
        self.check_telemetry_consent()
        
    def integrate_all_features(self):
        """Integrate all new features into the application."""
        # Add language selector to status bar
        self.integrate_language_selector()
        
        # Add performance monitoring
        self.setup_performance_monitoring()
        
        # Add settings menu items
        self.integrate_settings_menu()
        
        # Apply current language
        self.apply_language_settings()
        
    def check_telemetry_consent(self):
        """Check if telemetry consent has been requested."""
        # Check if this is the first run or if consent hasn't been asked'
        if self.settings.get("telemetry_consent_shown", False):
            # Consent has already been requested, apply saved settings
            telemetry.set_enabled(self.settings.get("telemetry_enabled", False))
            
            if self.settings.get("telemetry_enabled", False):
                # Set privacy settings
                privacy_settings = {
                    "allow_feature_usage": self.settings.get("telemetry_features", True),
                    "allow_performance_metrics": self.settings.get("telemetry_performance", True),
                    "allow_error_reports": self.settings.get("telemetry_errors", True),
                    "allow_device_info": self.settings.get("telemetry_device", False),
                    "allow_location": False  # Always disabled
                }
                telemetry.opt_in("anonymous_user", privacy_settings)
                logger.info("Telemetry enabled with saved settings")
            else:
                telemetry.opt_out("anonymous_user")
                logger.info("Telemetry disabled based on saved settings")
        else:
            # This is the first run or consent wasn't asked before'
            # Schedule consent dialog to be shown after the main window is displayed
            QTimer.singleShot(1000, self.show_telemetry_consent_dialog)
    
    def show_telemetry_consent_dialog(self):
        """Show the telemetry consent dialog."""
        dialog = TelemetryConsentDialog(self.main_window)
        dialog.consent_given.connect(self.on_telemetry_consent)
        dialog.exec()
        
        # Mark as shown regardless of the decision
        self.settings["telemetry_consent_shown"] = True
        save_settings(self.settings)
    
    def on_telemetry_consent(self, accepted, privacy_settings):
        """"
        Handle telemetry consent response.
        
        Args:
            accepted: Whether consent was given
            privacy_settings: Selected privacy settings
        """"
        # Update settings
        self.settings["telemetry_enabled"] = accepted
        
        if accepted:
            self.settings["telemetry_features"] = privacy_settings.get("allow_feature_usage", True)
            self.settings["telemetry_performance"] = privacy_settings.get("allow_performance_metrics", True)
            self.settings["telemetry_errors"] = privacy_settings.get("allow_error_reports", True)
            self.settings["telemetry_device"] = privacy_settings.get("allow_device_info", False)
            
            # Record feature usage for the consent itself
            telemetry.record_feature_usage("telemetry_consent", {"accepted": True})
        
        # Save settings
        save_settings(self.settings)
    
    def integrate_language_selector(self):
        """Add language selector to the application."""
        # Create language selector
        self.language_selector = LanguageSelector(self.main_window)
        
        # Connect signal
        self.language_selector.language_changed.connect(self.on_language_changed)
        
        # Add to status bar if it exists
        status_bar = self.main_window.statusBar()
        if status_bar:
            status_bar.addPermanentWidget(self.language_selector)
            logger.info("Added language selector to status bar")
        else:
            logger.warning("Status bar not found, language selector not added")
    
    def on_language_changed(self, language_code):
        """"
        Handle language change.
        
        Args:
            language_code: New language code
        """"
        # Update settings
        self.settings["language"] = language_code
        save_settings(self.settings)
        
        # Apply language to UI
        self.apply_language_settings()
        
        # Record feature usage
        if telemetry.enabled:
            telemetry.record_feature_usage("language_change", {"language": language_code})
        
        # Show message to user
        QMessageBox.information()
            self.main_window,
            get_string("language.changed_title", "Language Changed"),
            get_string("language.changed_message", "Some UI elements will update immediately. Others may require a restart.")
        )
    
    def apply_language_settings(self):
        """Apply current language settings to the UI."""
        # Get current language
        current_lang = self.settings.get("language", "en")
        
        # Set language in localization manager
        localization.set_language(current_lang)
        
        # Update window title
        self.main_window.setWindowTitle(get_string("app.name", "YouTube Translator Pro"))
        
        # Update status bar message
        status_bar = self.main_window.statusBar()
        if status_bar:
            status_bar.showMessage(get_string("app.ready", "Ready"))
            
        # Refresh language selector text
        if self.language_selector:
            self.language_selector.refresh_text()
            
        # Record language setting in telemetry
        if telemetry.enabled:
            telemetry.record_feature_usage("language_applied", {"language": current_lang})
            
        logger.info(f"Applied language settings: {current_lang}")
    
    def setup_performance_monitoring(self):
        """Set up performance monitoring."""
        # Check if performance monitoring is enabled
        if self.settings.get("performance_monitoring", False):
            logger.info("Performance monitoring enabled")
            
            # Create shortcut to view performance dialog
            self.create_performance_shortcut()
        else:
            logger.info("Performance monitoring disabled")
    
    def create_performance_shortcut(self):
        """Create a shortcut to view performance monitoring dialog."""
        # Add to help menu if it exists
        menu_bar = self.main_window.menuBar()
        if menu_bar:
            # Look for existing help menu
            help_menu = None
            for action in menu_bar.actions():
                if action.text() == get_string("ui.help", "Help"):
                    help_menu = action.menu()
                    break
            
            # Create help menu if it doesn't exist'
            if not help_menu:
                help_menu = menu_bar.addMenu(get_string("ui.help", "Help"))
            
            # Add performance action
            performance_action = QAction()
                get_string("ui.performance", "Performance Monitor"), 
                self.main_window
            )
            performance_action.triggered.connect(self.show_performance_dialog)
            help_menu.addAction(performance_action)
            
            logger.info("Added performance monitor shortcut to help menu")
    
    def show_performance_dialog(self):
        """Show the performance monitoring dialog."""
        # Create dialog if it doesn't exist'
        if not self.performance_dialog:
            self.performance_dialog = QDialog(self.main_window)
            self.performance_dialog.setWindowTitle(get_string("performance.title", "Performance Monitor"))
            self.performance_dialog.setMinimumWidth(800)
            self.performance_dialog.setMinimumHeight(600)
            
            # Create layout
            layout = QVBoxLayout(self.performance_dialog)
            
            # Add performance widget
            performance_widget = PerformanceMonitorWidget(self.performance_dialog)
            layout.addWidget(performance_widget)
            
            # Store reference to widget for language updates
            self.performance_dialog.performance_widget = performance_widget
        
        # Show dialog
        self.performance_dialog.show()
        self.performance_dialog.raise_()
        
        # Record feature usage
        if telemetry.enabled:
            telemetry.record_feature_usage("view_performance_monitor")
    
    def integrate_settings_menu(self):
        """Add settings menu to the application."""
        # Add to menu bar if it exists
        menu_bar = self.main_window.menuBar()
        if menu_bar:
            # Create settings action
            settings_action = QAction()
                get_string("ui.settings", "Settings"), 
                self.main_window
            )
            settings_action.triggered.connect(self.show_settings_dialog)
            
            # Look for existing file menu
            file_menu = None
            for action in menu_bar.actions():
                if action.text() == get_string("ui.file", "File"):
                    file_menu = action.menu()
                    break
            
            # Create file menu if it doesn't exist'
            if not file_menu:
                file_menu = menu_bar.addMenu(get_string("ui.file", "File"))
            
            # Add settings action (before exit if it exists)
            exit_action = None
            for action in file_menu.actions():
                if action.text() == get_string("ui.exit", "Exit"):
                    exit_action = action
                    break
            
            if exit_action:
                file_menu.insertAction(exit_action, settings_action)
                file_menu.insertSeparator(exit_action)
            else:
                file_menu.addAction(settings_action)
            
            logger.info("Added settings to file menu")
    
    def show_settings_dialog(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.main_window)
        dialog.settings_changed.connect(self.on_settings_changed)
        
        if dialog.exec():
            logger.info("Settings saved")
        else:
            logger.info("Settings dialog cancelled")
        
        # Record feature usage
        if telemetry.enabled:
            telemetry.record_feature_usage("view_settings")
    
    def on_settings_changed(self, new_settings):
        """"
        Handle settings changed.
        
        Args:
            new_settings: New settings dictionary
        """"
        # Store old values for comparison
        old_lang = self.settings.get("language", "en")
        old_performance = self.settings.get("performance_monitoring", False)
        
        # Update settings
        self.settings = new_settings
        
        # Check for language change
        if new_settings.get("language", "en") != old_lang:
            self.apply_language_settings()
        
        # Check for performance monitoring change
        if new_settings.get("performance_monitoring", False) != old_performance:
            if new_settings.get("performance_monitoring", False):
                self.create_performance_shortcut()
            else:
                # TODO: Remove performance shortcut if possible
                pass
