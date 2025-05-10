"""
URL input widget for YouTube Translator Pro.
Provides the interface for entering YouTube URLs to process.
"""

import logging
from typing import List
import re

# Set up logging
logger = logging.getLogger(__name__)

try:
    # First try PyQt6
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTextEdit, QGroupBox, QCheckBox
    )
    from PyQt6.QtGui import QClipboard, QKeySequence
    USE_PYQT6 = True
    logger.info("Using PyQt6 for URL input widget")
except ImportError:
    try:
        # Then try PyQt5
        from PyQt5.QtCore import Qt, pyqtSignal
        from PyQt5.QtWidgets import (
            QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
            QTextEdit, QGroupBox, QCheckBox
        )
        from PyQt5.QtGui import QClipboard, QKeySequence
        USE_PYQT6 = False
        logger.info("Using PyQt5 for URL input widget")
    except ImportError:
        # If neither PyQt6 nor PyQt5 is available, create mock classes
        logger.warning("Neither PyQt6 nor PyQt5 is available. Creating mock classes for URL input widget.")
        USE_PYQT6 = False
        
        # Mock implementations for Qt components
        class Qt:
            AlignCenter = 0
            AlignLeft = 0
            AlignRight = 0
            KeyboardModifiers = 0
            ControlModifier = 0
            
        class Signal:
            def __init__(self, *args):
                pass
            def connect(self, func):
                pass
            def emit(self, *args):
                pass
        
        # Alias for signals
        pyqtSignal = lambda *args, **kwargs: Signal()
        
        # Mock widgets
        class QWidget:
            def __init__(self, *args, **kwargs):
                pass
        
        class QVBoxLayout:
            def __init__(self, *args, **kwargs):
                pass
            def addWidget(self, *args, **kwargs):
                pass
            def addLayout(self, *args, **kwargs):
                pass
                
        class QHBoxLayout:
            def __init__(self, *args, **kwargs):
                pass
            def addWidget(self, *args, **kwargs):
                pass
            def addLayout(self, *args, **kwargs):
                pass
                
        class QLabel:
            def __init__(self, *args, **kwargs):
                pass
            
        class QPushButton:
            def __init__(self, *args, **kwargs):
                pass
            def clicked(self):
                return Signal()
            
        class QTextEdit:
            def __init__(self, *args, **kwargs):
                pass
            def setPlainText(self, *args, **kwargs):
                pass
            def toPlainText(self):
                return ""
                
        class QGroupBox:
            def __init__(self, *args, **kwargs):
                pass
            def setLayout(self, *args, **kwargs):
                pass
                
        class QCheckBox:
            def __init__(self, *args, **kwargs):
                pass
            def isChecked(self):
                return False
                
        class QClipboard:
            def __init__(self, *args, **kwargs):
                pass
            def text(self):
                return ""
                
        class QKeySequence:
            def __init__(self, *args, **kwargs):
                pass

from src.ui.styles import StyleManager

# Logger setup
logger = logging.getLogger(__name__)

class UrlInputWidget(QWidget):
    """Widget for entering YouTube URLs to process."""
    
    urls_entered = pyqtSignal(list)
    
    def __init__(self, app_manager, parent=None):
        """
        Initialize the URL input widget.
        
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
        group_box = QGroupBox("YouTube URLs")
        group_layout = QVBoxLayout(group_box)
        
        # Instructions label
        instructions = (
            "Enter YouTube URLs, one per line. You can paste multiple URLs at once. "
            "Only valid YouTube URLs will be processed."
        )
        instructions_label = QLabel(instructions)
        instructions_label.setWordWrap(True)
        group_layout.addWidget(instructions_label)
        
        # URL text edit
        self.url_text_edit = QTextEdit()
        self.url_text_edit.setPlaceholderText("Enter YouTube URLs here...")
        self.url_text_edit.setAcceptRichText(False)
        self.url_text_edit.setMinimumHeight(80)
        group_layout.addWidget(self.url_text_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.paste_button = QPushButton("Paste from Clipboard")
        self.paste_button.clicked.connect(self._paste_from_clipboard)
        button_layout.addWidget(self.paste_button)
        
        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._clear_urls)
        button_layout.addWidget(self.clear_button)
        
        # Add option to batch process all videos
        self.batch_checkbox = QCheckBox("Process all videos in one batch")
        self.batch_checkbox.setChecked(True)
        button_layout.addWidget(self.batch_checkbox)
        
        # Add button layout to group
        group_layout.addLayout(button_layout)
        
        # Add group to main layout
        main_layout.addWidget(group_box)
        
        # Apply styles
        self.style_manager.apply_styles(self)
    
    def _paste_from_clipboard(self):
        """Paste URLs from clipboard."""
        clipboard = self.app_manager.app.clipboard()
        text = clipboard.text()
        
        if text:
            current_text = self.url_text_edit.toPlainText()
            if current_text and not current_text.endswith('\n'):
                current_text += '\n'
            
            self.url_text_edit.setText(current_text + text)
    
    def _clear_urls(self):
        """Clear the URL input field."""
        self.url_text_edit.clear()
    
    def get_urls(self) -> List[str]:
        """
        Get the list of valid YouTube URLs from the input field.
        
        Returns:
            List of valid YouTube URLs
        """
        text = self.url_text_edit.toPlainText()
        lines = text.strip().split('\n')
        
        # Filter out empty lines and validate URLs
        valid_urls = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if self._is_valid_youtube_url(line):
                valid_urls.append(line)
        
        return valid_urls
    
    def _is_valid_youtube_url(self, url: str) -> bool:
        """
        Check if the given URL is a valid YouTube URL.
        
        Args:
            url: The URL to check
            
        Returns:
            True if the URL is a valid YouTube URL, False otherwise
        """
        # Simple pattern matching for YouTube URLs
        patterns = [
            r'^(https?://)?(www\.)?(youtube\.com/watch\?v=[\w-]+)',
            r'^(https?://)?(www\.)?(youtu\.be/[\w-]+)',
            r'^(https?://)?(www\.)?(youtube\.com/shorts/[\w-]+)'
        ]
        
        for pattern in patterns:
            if re.match(pattern, url):
                return True
        
        return False
