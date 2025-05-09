"""
Application Manager for YouTube Translator Pro.
Serves as the central coordinator for all application components.
"""

import os
import sys
import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal, QSettings, QTimer
from PyQt6.QtWidgets import QApplication

# Import configuration and settings
from src.config import load_settings, save_settings, DEFAULT_SETTINGS

# Logger setup
logger = logging.getLogger(__name__)

class ApplicationManager(QObject):
    """
    Central manager for all application features.
    Coordinates UI, processing, settings, and advanced features.
    """
    # Define signals for communication between components
    error_occurred = pyqtSignal(str, str)
    batch_status_changed = pyqtSignal(object)  # BatchStatus enum
    task_updated = pyqtSignal(dict)
    status_message = pyqtSignal(str)
    overall_progress_updated = pyqtSignal(float)
    batch_completed = pyqtSignal(dict)
    notification_requested = pyqtSignal(str, str, object)  # NotificationType enum
    
    def __init__(self, app: QApplication, splash=None):
        """
        Initialize the Application Manager.
        
        Args:
            app: The QApplication instance
            splash: Optional splash screen instance
        """
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
            
            # Initialize core components
            self.error_reporter = ErrorReporter(parent=self)
            self.session_manager = SessionManager(parent=self)
            self.crash_handler = CrashHandler(session_manager=self.session_manager, parent=self)
            
            # Set global exception handler
            sys.excepthook = self.crash_handler.handle_exception
            
            # Initialize cache manager
            self.cache_manager = CacheManager(
                cache_dir=self.settings.get("cache_dir"),
                max_size_mb=self.settings.get("cache_size_mb", 1000),
                ttl_seconds=self.settings.get("cache_ttl", 60*60*24*30)
            )
            
            # Initialize batch processor
            self.batch_processor = BatchProcessor(
                cache_manager=self.cache_manager,
                concurrency=self.settings.get("concurrency", 2),
                parent=self
            )
            
            # Initialize utility components
            self.recent_files_manager = RecentFilesManager(
                max_files=self.settings.get("max_recent_files", 20),
                parent=self
            )
            
            logger.info("All components initialized successfully")
        except Exception as e:
            logger.critical(f"Failed to initialize components: {e}", exc_info=True)
            # We'll continue with limited functionality if some components fail
    
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
            # Initialize and show the main window
            from src.ui.main_window import MainWindow
            self.main_window = MainWindow(self)
            
            # Apply initial style
            self._apply_initial_style()
            
            # Restore session if needed
            if hasattr(self, 'session_manager'):
                self.session_manager.restore_session(self.main_window)
            
            # Hide splash screen if exists
            if self._splash:
                self._splash.finish(self.main_window)
            
            # Show main window
            self.main_window.show()
            
            # Start application event loop
            return self.app.exec()
        except Exception as e:
            logger.critical(f"Failed to start application: {e}", exc_info=True)
            return 1
    
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
        """
        Perform graceful application shutdown.
        
        Args:
            wait: If True, wait for background processes to finish
            timeout: Maximum time to wait for processes
        """
        logger.info("Application shutdown initiated...")
        
        # Save current session
        if hasattr(self, 'session_manager') and hasattr(self, 'main_window'):
            self.session_manager.save_session(self.main_window)
        
        # Stop batch processor
        if hasattr(self, 'batch_processor'):
            self.batch_processor.cancel_all(wait=wait, timeout=timeout)
        
        # Clear caches
        if hasattr(self, 'cache_manager'):
            self.cache_manager.clear_unused(0)
        
        # Save settings
        save_settings(self.settings)
        
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
            self.notification_requested.emit(
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
        if hasattr(self, 'batch_processor'):
            self.batch_processor.set_concurrency(self.settings.get("concurrency", 2))
        
        if hasattr(self, 'cache_manager'):
            self.cache_manager.set_max_size(self.settings.get("cache_size_mb", 1000))
            self.cache_manager.set_ttl(self.settings.get("cache_ttl", 60*60*24*30))
        
        # Apply theme if changed
        theme = self.settings.get("theme", "dark")
        try:
            from src.ui.styles import StyleManager
            style_manager = StyleManager()
            style_manager.apply_theme(self.app, theme)
        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
