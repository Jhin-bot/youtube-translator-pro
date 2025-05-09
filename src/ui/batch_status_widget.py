"""
Batch status widget for YouTube Translator Pro.
Displays the current status and progress of batch processing.
"""

import logging
from typing import Optional

try:
    from PyQt6.QtCore import Qt, pyqtSlot
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSlot

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QProgressBar, QGroupBox
    )
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QProgressBar, QGroupBox
    )

from src.ui.styles import StyleManager

# Logger setup
logger = logging.getLogger(__name__)

class BatchStatusWidget(QWidget):
    """Widget for displaying batch processing status and progress."""
    
    def __init__(self, app_manager, parent=None):
        """
        Initialize the batch status widget.
        
        Args:
            app_manager: Reference to the ApplicationManager
            parent: The parent widget
        """
        super().__init__(parent)
        self.app_manager = app_manager
        self.style_manager = StyleManager()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create group box
        group_box = QGroupBox("Batch Status")
        group_layout = QVBoxLayout(group_box)
        
        # Status and controls
        status_layout = QHBoxLayout()
        
        # Status label
        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Control buttons
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self._start_batch)
        status_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self._pause_batch)
        self.pause_button.setEnabled(False)
        status_layout.addWidget(self.pause_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._cancel_batch)
        self.cancel_button.setEnabled(False)
        status_layout.addWidget(self.cancel_button)
        
        group_layout.addLayout(status_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p% (%v/%m)")
        self.progress_bar.setTextVisible(True)
        group_layout.addWidget(self.progress_bar)
        
        # Status message
        self.message_label = QLabel("Ready to process videos.")
        self.message_label.setWordWrap(True)
        group_layout.addWidget(self.message_label)
        
        # Add group to main layout
        main_layout.addWidget(group_box)
        
        # Apply styles
        self.style_manager.apply_styles(self)
    
    @pyqtSlot(object)
    def update_status(self, status):
        """
        Update the batch status display.
        
        Args:
            status: The new batch status
        """
        # Convert status enum to string
        status_text = str(status).split('.')[-1] if hasattr(status, 'name') else str(status)
        
        # Update status label
        self.status_label.setText(status_text)
        
        # Update button states based on status
        is_idle = status_text == "IDLE"
        is_running = status_text == "RUNNING"
        is_paused = status_text == "PAUSED"
        
        self.start_button.setEnabled(is_idle or is_paused)
        self.pause_button.setEnabled(is_running)
        self.cancel_button.setEnabled(is_running or is_paused)
        
        # Update status color
        if is_idle:
            self.status_label.setStyleSheet("font-weight: bold;")
        elif is_running:
            self.status_label.setStyleSheet(f"font-weight: bold; color: {self.style_manager.colors['accent']};")
        elif is_paused:
            self.status_label.setStyleSheet(f"font-weight: bold; color: {self.style_manager.colors['warning']};")
        else:
            self.status_label.setStyleSheet("font-weight: bold;")
    
    @pyqtSlot(float)
    def update_progress(self, progress: float):
        """
        Update the progress bar.
        
        Args:
            progress: The progress value (0.0 to 1.0)
        """
        # Convert to percentage (0-100)
        percentage = int(progress * 100)
        self.progress_bar.setValue(percentage)
    
    @pyqtSlot(str)
    def update_message(self, message: str):
        """
        Update the status message.
        
        Args:
            message: The new status message
        """
        self.message_label.setText(message)
    
    def _start_batch(self):
        """Start or resume batch processing."""
        # Forward to the url input widget to get URLs and start processing
        from src.ui.url_input_widget import UrlInputWidget
        
        # Find the URL input widget
        url_input = self.parent().findChild(UrlInputWidget)
        if url_input:
            urls = url_input.get_urls()
            if urls:
                self.app_manager.start_batch(urls)
            else:
                self.update_message("No valid YouTube URLs found. Please enter at least one URL.")
        else:
            self.app_manager.start_batch([])
    
    def _pause_batch(self):
        """Pause batch processing."""
        self.app_manager.pause_batch()
    
    def _cancel_batch(self):
        """Cancel batch processing."""
        self.app_manager.cancel_batch()
