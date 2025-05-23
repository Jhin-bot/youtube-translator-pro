""""
Application Manager for YouTube Translator Pro.
Serves as the central coordinator for all application components.
""""

import os
import sys
import logging
import json
import platform
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

try:
    try:
    from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QTimer
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QTimer
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal, QSettings, QTimer

try:
    try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    from PyQt5.QtWidgets import QApplication
except ImportError:
    from PyQt5.QtWidgets import QApplication

# Import configuration and settings
from src.config import load_settings, save_settings, DEFAULT_SETTINGS, VERSION

# Logger setup
logger = logging.getLogger(__name__)

class ApplicationManager(QObject):
    """"
    Central manager for all application features.
    Coordinates UI, processing, settings, and advanced features.
    """"
    # Define signals for communication between components
    error_occurred = pyqtSignal(str, str)
    batch_status_changed = pyqtSignal(object)  # BatchStatus enum
    task_updated = pyqtSignal(dict)
    status_message = pyqtSignal(str)
    overall_progress_updated = pyqtSignal(float)
    batch_completed = pyqtSignal(dict)
    notification_requested = pyqtSignal(str, str, object)  # NotificationType enum
    
    def __init__(self, app: QApplication, splash=None):
        """"
        Initialize the Application Manager.
        
        Args:
            app: The QApplication instance
            splash: Optional splash screen instance
        """"
        super().__init__()
        self.app = app
        self._splash = splash
        
        logger.info("ApplicationManager initializing...")
        
        # Load application settings
        self.settings = load_settings()
        
        # Initialize component managers
        self._initialize_components()
        
        # Connect signals between components
        self._connect_signals()
        
        logger.info("ApplicationManager initialization complete.")
    
    def _initialize_components(self):
        """Initialize all application components."""
        try:
            # Import components dynamically to avoid circular imports
            from src.core.cache_manager import CacheManager
            from src.core.batch_processor import BatchProcessor
            from src.core.session_manager import SessionManager
            from src.core.error_handler import ErrorReporter, CrashHandler
            from src.utils.recent_files import RecentFilesManager
            from src.utils.localization import localization
            from src.utils.telemetry import telemetry
            from src.utils.performance_monitor import monitor as performance_monitor
            
            # Initialize core components
            self.error_reporter = ErrorReporter(parent=self)
            self.session_manager = SessionManager(parent=self)
            self.crash_handler = CrashHandler(session_manager=self.session_manager, parent=self)
            
            # Set global exception handler
            sys.excepthook = self.crash_handler.handle_exception
            
            # Initialize cache manager
            self.cache_manager = CacheManager()
                cache_dir=self.settings.get("cache_dir"),
                max_size_mb=self.settings.get("cache_size_mb", 1000),
                ttl_seconds=self.settings.get("cache_ttl", 60*60*24*30)
            )
            
            # Initialize batch processor
            self.batch_processor = BatchProcessor()
                cache_manager=self.cache_manager,
                concurrency=self.settings.get("concurrency", 2),
                parent=self
            )
            
            # Initialize utility components
            self.recent_files_manager = RecentFilesManager()
                max_files=self.settings.get("max_recent_files", 20),
                parent=self
            )
            
            # Initialize localization
            language = self.settings.get("language", "en")
            localization.set_language(language)
            logger.info(f"Initialized localization with language: {language}")
            
            # Initialize telemetry
            telemetry_enabled = self.settings.get("telemetry_enabled", False)
            telemetry.set_enabled(telemetry_enabled)
            if telemetry_enabled:
                # Setup system information
                sys_info = {
                    "app_version": VERSION,
                    "os": platform.system(),
                    "os_version": platform.version(),
                    "python_version": platform.python_version()
                }
                
                # Allow device info only if explicitly permitted
                if self.settings.get("telemetry_device", False):
                    sys_info.update({)
                        "cpu": platform.processor(),
                        "architecture": platform.machine()
                    })
                
                telemetry.set_system_info(sys_info)
                telemetry.record_app_start()
                logger.info("Telemetry initialized and enabled")
            else:
                logger.info("Telemetry initialized but disabled")
            
            # Initialize performance monitoring
            performance_enabled = self.settings.get("performance_monitoring", False)
            if performance_enabled:
                performance_monitor.enable()
                logger.info("Performance monitoring enabled")
            else:
                logger.info("Performance monitoring disabled")
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize components: {e}", exc_info=True)
            # We'll continue with limited functionality if some components fail'
    
    def _connect_signals(self):
        """Connect signals between components."""
        try:
            # Connect batch processor signals
            if hasattr(self, 'batch_processor'):
                self.batch_processor.progress_updated.connect(self._handle_batch_progress_update)
                self.batch_processor.batch_status_changed.connect(self.batch_status_changed.emit)
                self.batch_processor.batch_completed.connect(self.batch_completed.emit)
                self.batch_processor.task_updated.connect(self.task_updated.emit)
                self.batch_processor.resource_warning.connect(self._handle_resource_warning)
            
            # Connect error reporter signals
            if hasattr(self, 'error_reporter'):
                self.error_reporter.error_reported.connect(self._handle_error_reported)
            
            logger.info("Component signals connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect signals: {e}", exc_info=True)
    
    def run(self):
        """Start the application."""
        try:
            logger.info("Starting application run sequence...")
            # Initialize and show the main window
            from src.ui.main_window import MainWindow
            logger.info("Importing MainWindow successful")
            self.main_window = MainWindow(self)
            logger.info("MainWindow instance created successfully")
            
            # Integrate new features with main window
            logger.info("About to integrate features with main window")
            self._integrate_features_with_main_window()
            logger.info("Features integrated successfully")
            
            # Apply initial style
            logger.info("About to apply initial style")
            self._apply_initial_style()
            logger.info("Initial style applied successfully")
            
            # Restore session if needed
            if hasattr(self, 'session_manager'):
                logger.info("About to restore session")
                self.session_manager.restore_session(self.main_window)
                logger.info("Session restored successfully")
            
            # Hide splash screen if exists
            if self._splash:
                logger.info("About to hide splash screen")
                self._splash.finish(self.main_window)
                logger.info("Splash screen hidden successfully")
            
            # Show main window
            logger.info("About to show main window")
            self.main_window.show()
            logger.info("Main window shown successfully")
            
            # Start application event loop
            logger.info("About to start application event loop (app.exec)")
            return self.app.exec()
        except Exception as e:
            logger.critical(f"Failed to start application: {e}", exc_info=True)
            return 1
            
    def _integrate_features_with_main_window(self):
        """Integrate new features with the main window."""
        try:
            from src.ui.integration_components import FeatureIntegrator
            
            # Create integrator and integrate features
            self.feature_integrator = FeatureIntegrator(self.main_window)
            self.feature_integrator.integrate_all_features()
            
            logger.info("Successfully integrated new features with main window")
        except Exception as e:
            logger.error(f"Failed to integrate features with main window: {e}", exc_info=True)
    
    def _apply_initial_style(self):
        """Apply initial application styling."""
        try:
            from src.ui.styles import StyleManager
            theme = self.settings.get("theme", "dark")
            style_manager = StyleManager()
            style_manager.apply_theme(self.app, theme)
        except Exception as e:
            logger.error(f"Failed to apply initial style: {e}")
    
    def shutdown(self, wait=True, timeout=10.0):
        """"
        Perform graceful application shutdown.
        
        Args:
            wait: If True, wait for background processes to finish
            timeout: Maximum time to wait for processes
        """"
        logger.info("Application shutting down...")
        
        # Save session
        if hasattr(self, 'session_manager'):
            self.session_manager.save_session(self.main_window)
            logger.info("Session saved")
        
        # Stop batch processing
        if hasattr(self, 'batch_processor'):
            # Handle the case where stop might not exist but cancel_batch does
            if hasattr(self.batch_processor, 'stop'):
                self.batch_processor.stop(wait=wait, timeout=timeout)
                logger.info("Batch processor stopped")
            elif hasattr(self.batch_processor, 'cancel_batch'):
                self.batch_processor.cancel_batch()
                logger.info("Batch processor cancelled")
            else:
                logger.warning("Unable to stop batch processor - no stop or cancel_batch method found")
        
        # Record telemetry event for application close
        from src.utils.telemetry import telemetry
        if telemetry.enabled:
            telemetry.record_app_close()
            logger.info("Recorded app close telemetry event")
        
        # Save settings
        save_settings(self.settings)
        logger.info("Settings saved")
        
        logger.info("Application shutdown complete")
    
    # Batch processing methods
    def start_batch(self, urls: List[str]):
        """Start or resume batch processing."""
        if hasattr(self, 'batch_processor'):
            self.batch_processor.start_batch(urls)
    
    def pause_batch(self):
        """Pause batch processing."""
        if hasattr(self, 'batch_processor'):
            self.batch_processor.pause_batch()
    
    def cancel_batch(self):
        """Cancel batch processing."""
        if hasattr(self, 'batch_processor'):
            self.batch_processor.cancel_batch()
    
    def add_task(self, url: str, model: str, target_lang: Optional[str], output_dir: str, formats: List[str]):
        """Add a single task to the batch processor."""
        if hasattr(self, 'batch_processor'):
            self.batch_processor.add_task(url, model, target_lang, output_dir, formats)
    
    # Event handlers
    def _handle_batch_progress_update(self, update: Dict[str, Any]):
        """Handle updates to batch progress and status."""
        if 'progress' in update:
            self.overall_progress_updated.emit(update['progress'])
        if 'status_message' in update:
            self.status_message.emit(update['status_message'])
    
    def _handle_resource_warning(self, warning_data: Dict[str, Any]):
        """Handle resource warning signals."""
        if 'message' in warning_data and 'details' in warning_data:
            self.notification_requested.emit()
                "Resource Warning", 
                warning_data['message'], 
                warning_data.get('type', 'WARNING')
            )
    
    def _handle_error_reported(self, message: str, details: str, severity):
        """Handle errors reported by the ErrorReporter."""
        self.error_occurred.emit(message, details)
    
    # Settings methods
    def save_settings(self, new_settings: Dict[str, Any]):
        """Save application settings and apply them."""
        self.settings.update(new_settings)
        save_settings(self.settings)
        self._apply_settings()
    
    def _apply_settings(self):
        """Apply current settings to application components."""
        try:
            # Update cache manager settings
            if hasattr(self, 'cache_manager'):
                self.cache_manager.set_ttl(self.settings.get("cache_ttl", 60*60*24*30))
                self.cache_manager.set_max_size(self.settings.get("cache_size_mb", 1000))
            
            # Update batch processor settings
            if hasattr(self, 'batch_processor'):
                self.batch_processor.set_concurrency(self.settings.get("concurrency", 2))
            
            # Update recent files manager settings
            if hasattr(self, 'recent_files_manager'):
                self.recent_files_manager.set_max_files(self.settings.get("max_recent_files", 20))
            
            # Update localization settings
            from src.utils.localization import localization
            language = self.settings.get("language", "en")
            if language != localization.current_language:
                localization.set_language(language)
                logger.info(f"Updated localization language to {language}")
            
            # Update telemetry settings
            from src.utils.telemetry import telemetry
            telemetry_enabled = self.settings.get("telemetry_enabled", False)
            telemetry.set_enabled(telemetry_enabled)
            logger.info(f"Updated telemetry enabled status to {telemetry_enabled}")
            
            # Update performance monitoring settings
            from src.utils.performance_monitor import monitor as performance_monitor
            performance_enabled = self.settings.get("performance_monitoring", False)
            if performance_enabled:
                performance_monitor.enable()
            else:
                performance_monitor.disable()
            logger.info(f"Updated performance monitoring enabled status to {performance_enabled}")
            
            logger.info("Settings applied to all components")
        except Exception as e:
            logger.error(f"Failed to apply settings: {e}", exc_info=True)
