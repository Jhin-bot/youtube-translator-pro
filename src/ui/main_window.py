"""
Main window for YouTube Translator Pro.
Provides the primary user interface and interaction points.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

try:
    from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QUrl

try:
    from PyQt6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QProgressBar, QTextEdit, QComboBox,
        QFileDialog, QMessageBox, QTabWidget, QGroupBox, QLineEdit,
        QCheckBox, QToolBar, QStatusBar, QSplitter
    )
except ImportError:
    from PyQt5.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QProgressBar, QTextEdit, QComboBox,
        QFileDialog, QMessageBox, QTabWidget, QGroupBox, QLineEdit,
        QCheckBox, QToolBar, QStatusBar, QSplitter
    )

try:
    from PyQt6.QtGui import QAction, QIcon, QDesktopServices
except ImportError:
    from PyQt5.QtGui import QAction, QIcon, QDesktopServices

from src.ui.styles import StyleManager
from src.ui.dialogs import SettingsDialog, AboutDialog, ErrorDialog
from src.ui.url_input_widget import UrlInputWidget
from src.ui.batch_status_widget import BatchStatusWidget
from src.ui.task_list_widget import TaskListWidget
from src.ui.control_panel_widget import ControlPanelWidget

# Application constants
APP_NAME = "YouTube Translator Pro"
APP_VERSION = "1.0.0"

# Logger setup
logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window for YouTube Translator Pro."""
    
    # Define signals
    output_dir_changed = pyqtSignal(str)
    
    def __init__(self, app_manager):
        """
        Initialize the main window.
        
        Args:
            app_manager: Reference to the ApplicationManager
        """
        super().__init__()
        self.app_manager = app_manager
        self.style_manager = StyleManager()
        
        # Set up UI elements
        self._setup_ui()
        
        # Connect signals from app manager
        self._connect_signals()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Window settings
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1000, 700)
        
        # Create the menu bar and toolbar
        self._create_menu_bar()
        self._create_toolbar()
        self._create_status_bar()
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        main_layout = QVBoxLayout(self.central_widget)
        
        # Create widgets
        self._create_url_input_section(main_layout)
        self._create_batch_status_section(main_layout)
        
        # Create splitter for task list and control panel
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter, 1)
        
        # Add the task list
        self.task_list_widget = TaskListWidget(self.app_manager)
        splitter.addWidget(self.task_list_widget)
        
        # Add the control panel
        self.control_panel = ControlPanelWidget(self.app_manager)
        splitter.addWidget(self.control_panel)
        
        # Set splitter sizes
        splitter.setSizes([600, 400])
        
        # Apply the style
        self.style_manager.apply_styles(self)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        
        # Add actions to file menu
        open_action = QAction("&Open Output Directory", self)
        open_action.triggered.connect(self._open_output_directory)
        file_menu.addAction(open_action)
        
        settings_action = QAction("&Settings", self)
        settings_action.triggered.connect(self._show_settings)
        file_menu.addAction(settings_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Batch menu
        batch_menu = menu_bar.addMenu("&Batch")
        
        start_action = QAction("&Start/Resume Batch", self)
        start_action.triggered.connect(self._start_batch)
        batch_menu.addAction(start_action)
        
        pause_action = QAction("&Pause Batch", self)
        pause_action.triggered.connect(self._pause_batch)
        batch_menu.addAction(pause_action)
        
        cancel_action = QAction("&Cancel Batch", self)
        cancel_action.triggered.connect(self._cancel_batch)
        batch_menu.addAction(cancel_action)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        help_action = QAction("&Help", self)
        help_action.triggered.connect(self._show_help)
        help_menu.addAction(help_action)
    
    def _create_toolbar(self):
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        # Add toolbar actions
        start_action = QAction("Start", self)
        start_action.triggered.connect(self._start_batch)
        toolbar.addAction(start_action)
        
        pause_action = QAction("Pause", self)
        pause_action.triggered.connect(self._pause_batch)
        toolbar.addAction(pause_action)
        
        cancel_action = QAction("Cancel", self)
        cancel_action.triggered.connect(self._cancel_batch)
        toolbar.addAction(cancel_action)
        
        toolbar.addSeparator()
        
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self._show_settings)
        toolbar.addAction(settings_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add status elements
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label, 1)
        
        # Add version label
        version_label = QLabel(f"Version {APP_VERSION}")
        self.status_bar.addPermanentWidget(version_label)
    
    def _create_url_input_section(self, parent_layout):
        """Create the URL input section."""
        self.url_input_widget = UrlInputWidget(self.app_manager)
        parent_layout.addWidget(self.url_input_widget)
    
    def _create_batch_status_section(self, parent_layout):
        """Create the batch status section."""
        self.batch_status_widget = BatchStatusWidget(self.app_manager)
        parent_layout.addWidget(self.batch_status_widget)
    
    def _connect_signals(self):
        """Connect signals from app manager to UI slots."""
        # Connect ApplicationManager signals
        self.app_manager.error_occurred.connect(self._handle_error_report)
        self.app_manager.batch_status_changed.connect(self._handle_batch_status_change)
        self.app_manager.task_updated.connect(self._handle_task_update)
        self.app_manager.status_message.connect(self._handle_status_message)
        self.app_manager.overall_progress_updated.connect(self._handle_progress_update)
        self.app_manager.notification_requested.connect(self._handle_notification)
    
    # Event handlers and slots
    
    @pyqtSlot(str, str)
    def _handle_error_report(self, message, details):
        """Handle error reports from the application manager."""
        logger.error(f"Error: {message} - {details}")
        error_dialog = ErrorDialog(message, details, self)
        error_dialog.exec()
    
    @pyqtSlot(object)
    def _handle_batch_status_change(self, status):
        """Handle batch status changes."""
        self.batch_status_widget.update_status(status)
    
    @pyqtSlot(dict)
    def _handle_task_update(self, task_data):
        """Handle task updates."""
        self.task_list_widget.update_task(task_data)
    
    @pyqtSlot(str)
    def _handle_status_message(self, message):
        """Handle status message updates."""
        self.status_label.setText(message)
    
    @pyqtSlot(float)
    def _handle_progress_update(self, progress):
        """Handle overall progress updates."""
        self.batch_status_widget.update_progress(progress)
    
    @pyqtSlot(str, str, object)
    def _handle_notification(self, title, message, notification_type):
        """Handle notification requests."""
        # This could be extended to show system tray notifications
        priority = QMessageBox.Icon.Information
        if notification_type == 'WARNING':
            priority = QMessageBox.Icon.Warning
        elif notification_type == 'CRITICAL':
            priority = QMessageBox.Icon.Critical
            
        QMessageBox(priority, title, message, QMessageBox.StandardButton.Ok, self).exec()
    
    # Action handlers
    
    def _open_output_directory(self):
        """Open the output directory in the file explorer."""
        output_dir = self.control_panel.get_output_directory()
        try:
            output_path = Path(output_dir)
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(output_path)))
        except Exception as e:
            logger.error(f"Failed to open output directory: {e}")
            QMessageBox.critical(
                self, 
                "Error Opening Directory",
                f"Failed to open output directory:\n{output_dir}\nError: {e}"
            )
    
    def _show_settings(self):
        """Show the settings dialog."""
        dialog = SettingsDialog(self.app_manager.settings, self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.app_manager.save_settings(new_settings)
    
    def _show_about(self):
        """Show the about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()
    
    def _show_help(self):
        """Show help documentation."""
        help_url = "https://www.youtube-translator-pro.com/help"
        QDesktopServices.openUrl(QUrl(help_url))
    
    def _start_batch(self):
        """Start or resume batch processing."""
        urls = self.url_input_widget.get_urls()
        if urls:
            self.app_manager.start_batch(urls)
        else:
            QMessageBox.warning(
                self,
                "No URLs",
                "Please enter at least one YouTube URL to process."
            )
    
    def _pause_batch(self):
        """Pause batch processing."""
        self.app_manager.pause_batch()
    
    def _cancel_batch(self):
        """Cancel batch processing."""
        result = QMessageBox.question(
            self,
            "Cancel Batch",
            "Are you sure you want to cancel all processing?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if result == QMessageBox.StandardButton.Yes:
            self.app_manager.cancel_batch()
    
    # Override closeEvent to handle application shutdown
    def closeEvent(self, event):
        """Handle window close event."""
        # Ask for confirmation if batch processing is active
        if hasattr(self.app_manager, 'batch_processor') and self.app_manager.batch_processor.is_running():
            result = QMessageBox.question(
                self,
                "Confirm Exit",
                "Batch processing is still active. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if result == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Perform graceful shutdown
        logger.info("Main window closing, performing shutdown")
        self.app_manager.shutdown()
        event.accept()
