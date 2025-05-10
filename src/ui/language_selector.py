""""
Language selector widget for YouTube Translator Pro.
Provides a dropdown for selecting the application language.
""""

import logging
try:
    try:
    from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
except ImportError:
    from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget
except ImportError:
    from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

try:
    try:
    from PyQt6.QtCore import pyqtSignal
except ImportError:
    from PyQt5.QtCore import pyqtSignal
except ImportError:
    from PyQt5.QtCore import pyqtSignal

from src.utils.localization import localization, get_string

# Set up logging
logger = logging.getLogger(__name__)

class LanguageSelector(QWidget):
    """Widget for selecting the application language."""
    
    language_changed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the language selector widget."""
        super().__init__(parent)
        
        # Set up layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label = QLabel(get_string("ui.language", "Language"))
        layout.addWidget(self.label)
        
        # Create combo box
        self.combo = QComboBox()
        self._populate_languages()
        layout.addWidget(self.combo)
        
        # Connect signals
        self.combo.currentIndexChanged.connect(self._on_language_changed)
        
    def _populate_languages(self):
        """Populate the language combo box."""
        # Get available languages
        languages = localization.get_available_languages()
        
        # Add languages to combo box
        for code, name in languages.items():
            self.combo.addItem(name, code)
        
        # Set current language
        current_language = localization.current_language
        index = self.combo.findData(current_language)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            
    def _on_language_changed(self, index):
        """Handle language selection change."""
        if index < 0:
            return
            
        # Get selected language code
        language_code = self.combo.itemData(index)
        
        # Set language if different from current
        if language_code != localization.current_language:
            logger.info(f"Changing language to {language_code}")
            
            # Update localization
            localization.set_language(language_code)
            
            # Emit signal
            self.language_changed.emit(language_code)
            
    def refresh_text(self):
        """Refresh text after language change."""
        self.label.setText(get_string("ui.language", "Language"))
