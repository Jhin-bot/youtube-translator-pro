"""
Control panel widget for YouTube Translator Pro.
Provides controls for configuring transcription and translation options.
"""

import logging
from typing import List, Optional
from pathlib import Path

try:
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal

try:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QGroupBox, QFormLayout, QLineEdit, QFileDialog,
        QCheckBox, QListWidget, QListWidgetItem
    )
except ImportError:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QComboBox, QGroupBox, QFormLayout, QLineEdit, QFileDialog,
        QCheckBox, QListWidget, QListWidgetItem
    )

from src.ui.styles import StyleManager
from src.config import TRANSCRIPTION_MODELS, TRANSLATION_LANGUAGES

# Logger setup
logger = logging.getLogger(__name__)

class ControlPanelWidget(QWidget):
    """Widget for configuring transcription and translation options."""
    
    output_dir_changed = pyqtSignal(str)
    
    def __init__(self, app_manager, parent=None):
        """
        Initialize the control panel widget.
        
        Args:
            app_manager: Reference to the ApplicationManager
            parent: The parent widget
        """
        super().__init__(parent)
        self.app_manager = app_manager
        self.style_manager = StyleManager()
        self.settings = self.app_manager.settings
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Transcription options
        self._create_transcription_options(main_layout)
        
        # Translation options
        self._create_translation_options(main_layout)
        
        # Output options
        self._create_output_options(main_layout)
        
        # Add spacer at the bottom
        main_layout.addStretch()
        
        # Apply styles
        self.style_manager.apply_styles(self)
    
    def _create_transcription_options(self, parent_layout):
        """
        Create transcription options group.
        
        Args:
            parent_layout: The parent layout to add the group to
        """
        group = QGroupBox("Transcription Options")
        layout = QFormLayout(group)
        
        # Model selection
        self.model_combo = QComboBox()
        for model in TRANSCRIPTION_MODELS:
            self.model_combo.addItem(model.capitalize(), model)
        
        # Set default from settings
        default_model = self.settings.get("default_model", "small")
        index = self.model_combo.findData(default_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        layout.addRow("Model:", self.model_combo)
        
        # Add transcription options group to parent layout
        parent_layout.addWidget(group)
    
    def _create_translation_options(self, parent_layout):
        """
        Create translation options group.
        
        Args:
            parent_layout: The parent layout to add the group to
        """
        group = QGroupBox("Translation Options")
        layout = QFormLayout(group)
        
        # Target language selection
        self.language_combo = QComboBox()
        for code, name in TRANSLATION_LANGUAGES.items():
            self.language_combo.addItem(name, code)
        
        # Set default from settings
        default_language = self.settings.get("default_language", "None")
        index = self.language_combo.findData(default_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        layout.addRow("Target Language:", self.language_combo)
        
        # Add translation options group to parent layout
        parent_layout.addWidget(group)
    
    def _create_output_options(self, parent_layout):
        """
        Create output options group.
        
        Args:
            parent_layout: The parent layout to add the group to
        """
        group = QGroupBox("Output Options")
        layout = QVBoxLayout(group)
        
        # Output directory
        dir_layout = QFormLayout()
        
        # Directory selector
        dir_select_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.settings.get("output_dir", ""))
        self.output_dir_edit.setReadOnly(True)
        dir_select_layout.addWidget(self.output_dir_edit)
        
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_output_dir)
        dir_select_layout.addWidget(browse_button)
        
        dir_layout.addRow("Output Directory:", dir_select_layout)
        layout.addLayout(dir_layout)
        
        # Output formats
        format_label = QLabel("Output Formats:")
        layout.addWidget(format_label)
        
        # Format selection list
        self.format_list = QListWidget()
        self.format_list.setMaximumHeight(100)
        
        # Add available formats
        formats = [
            ("SRT", "SubRip subtitle format", True),
            ("TXT", "Plain text transcript", False),
            ("VTT", "WebVTT subtitle format", False),
            ("JSON", "JSON transcript data", False),
            ("CSV", "CSV transcript data", False)
        ]
        
        for format_id, description, default in formats:
            item = QListWidgetItem(f"{format_id} - {description}")
            item.setData(Qt.ItemDataRole.UserRole, format_id.lower())
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            item.setCheckState(Qt.CheckState.Checked if default else Qt.CheckState.Unchecked)
            self.format_list.addItem(item)
        
        layout.addWidget(self.format_list)
        
        # Auto-open output checkbox
        self.auto_open_checkbox = QCheckBox("Automatically open output when complete")
        self.auto_open_checkbox.setChecked(True)
        layout.addWidget(self.auto_open_checkbox)
        
        # Add output options group to parent layout
        parent_layout.addWidget(group)
    
    def _browse_output_dir(self):
        """Open a file dialog to select the output directory."""
        current_dir = self.output_dir_edit.text() or str(Path.home())
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            current_dir
        )
        if directory:
            self.output_dir_edit.setText(directory)
            self.output_dir_changed.emit(directory)
    
    def get_model(self) -> str:
        """
        Get the selected transcription model.
        
        Returns:
            The selected model name
        """
        return self.model_combo.currentData()
    
    def get_target_language(self) -> str:
        """
        Get the selected target language.
        
        Returns:
            The selected language code
        """
        return self.language_combo.currentData()
    
    def get_output_directory(self) -> str:
        """
        Get the selected output directory.
        
        Returns:
            The output directory path
        """
        return self.output_dir_edit.text() or self.settings.get("output_dir", "")
    
    def get_output_formats(self) -> List[str]:
        """
        Get the selected output formats.
        
        Returns:
            List of selected format codes
        """
        formats = []
        for i in range(self.format_list.count()):
            item = self.format_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                formats.append(item.data(Qt.ItemDataRole.UserRole))
        return formats
    
    def is_auto_open_enabled(self) -> bool:
        """
        Check if auto-open output is enabled.
        
        Returns:
            True if auto-open is enabled, False otherwise
        """
        return self.auto_open_checkbox.isChecked()
