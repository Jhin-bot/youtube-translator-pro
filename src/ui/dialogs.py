"""
Dialog components for YouTube Translator Pro.
Contains all dialogs used in the application.
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QWidget, QFormLayout, QLineEdit, QSpinBox,
    QCheckBox, QComboBox, QFileDialog, QTextEdit, QGroupBox,
    QDialogButtonBox, QScrollArea
)

from src.ui.styles import StyleManager
from src.config import APP_NAME, APP_VERSION, TRANSCRIPTION_MODELS, TRANSLATION_LANGUAGES

# Logger setup
logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Dialog for application settings."""
    
    def __init__(self, current_settings: Dict[str, Any], parent=None):
        """
        Initialize the settings dialog.
        
        Args:
            current_settings: The current application settings
            parent: The parent widget
        """
        super().__init__(parent)
        self.current_settings = current_settings.copy()
        self.style_manager = StyleManager()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Dialog settings
        self.setWindowTitle(f"{APP_NAME} - Settings")
        self.setMinimumWidth(600)
        self.resize(700, 500)
        
        # Create layout
        main_layout = QVBoxLayout(self)
        
        # Create tabs for different settings categories
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # General tab
        general_tab = QWidget()
        tab_widget.addTab(general_tab, "General")
        self._setup_general_tab(general_tab)
        
        # Transcription tab
        transcription_tab = QWidget()
        tab_widget.addTab(transcription_tab, "Transcription")
        self._setup_transcription_tab(transcription_tab)
        
        # Translation tab
        translation_tab = QWidget()
        tab_widget.addTab(translation_tab, "Translation")
        self._setup_translation_tab(translation_tab)
        
        # Advanced tab
        advanced_tab = QWidget()
        tab_widget.addTab(advanced_tab, "Advanced")
        self._setup_advanced_tab(advanced_tab)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
        # Apply styles
        self.style_manager.apply_styles(self)
    
    def _setup_general_tab(self, tab: QWidget):
        """Set up the general settings tab."""
        layout = QFormLayout(tab)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        current_theme = self.current_settings.get("theme", "dark")
        self.theme_combo.setCurrentText(current_theme.capitalize())
        layout.addRow("Theme:", self.theme_combo)
        
        # Output directory
        output_dir_layout = QHBoxLayout()
        self.output_dir_edit = QLineEdit(self.current_settings.get("output_dir", ""))
        self.output_dir_edit.setReadOnly(True)
        output_dir_layout.addWidget(self.output_dir_edit)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self._browse_output_dir)
        output_dir_layout.addWidget(self.browse_button)
        
        layout.addRow("Output Directory:", output_dir_layout)
        
        # Concurrency setting
        self.concurrency_spin = QSpinBox()
        self.concurrency_spin.setMinimum(1)
        self.concurrency_spin.setMaximum(8)
        self.concurrency_spin.setValue(self.current_settings.get("concurrency", 2))
        layout.addRow("Concurrent Tasks:", self.concurrency_spin)
    
    def _setup_transcription_tab(self, tab: QWidget):
        """Set up the transcription settings tab."""
        layout = QFormLayout(tab)
        
        # Default transcription model
        self.model_combo = QComboBox()
        self.model_combo.addItems([model.capitalize() for model in TRANSCRIPTION_MODELS])
        current_model = self.current_settings.get("default_model", "small")
        self.model_combo.setCurrentText(current_model.capitalize())
        layout.addRow("Default Model:", self.model_combo)
        
        # Cache settings
        self.cache_enabled = QCheckBox("Enable cache")
        self.cache_enabled.setChecked(self.current_settings.get("cache_enabled", True))
        layout.addRow("Cache:", self.cache_enabled)
        
        # Cache size
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setMinimum(100)
        self.cache_size_spin.setMaximum(10000)
        self.cache_size_spin.setSingleStep(100)
        self.cache_size_spin.setSuffix(" MB")
        self.cache_size_spin.setValue(self.current_settings.get("cache_size_mb", 1000))
        layout.addRow("Cache Size:", self.cache_size_spin)
    
    def _setup_translation_tab(self, tab: QWidget):
        """Set up the translation settings tab."""
        layout = QFormLayout(tab)
        
        # Default target language
        self.language_combo = QComboBox()
        for code, name in TRANSLATION_LANGUAGES.items():
            self.language_combo.addItem(name, code)
        
        current_language = self.current_settings.get("default_language", "None")
        index = self.language_combo.findData(current_language)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        layout.addRow("Default Target Language:", self.language_combo)
        
        # Translation engine (placeholder for when multiple engines are supported)
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["Mock (Testing)", "Google Translate API", "DeepL API", "Local Model"])
        layout.addRow("Translation Engine:", self.engine_combo)
        
        # API key (for external translation services)
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter API key for selected translation service")
        layout.addRow("API Key:", self.api_key_edit)
    
    def _setup_advanced_tab(self, tab: QWidget):
        """Set up the advanced settings tab."""
        layout = QVBoxLayout(tab)
        
        # Performance settings
        performance_group = QGroupBox("Performance")
        performance_layout = QFormLayout(performance_group)
        
        # Retry settings
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setMinimum(0)
        self.max_retries_spin.setMaximum(10)
        self.max_retries_spin.setValue(self.current_settings.get("max_retries", 3))
        performance_layout.addRow("Max Retries:", self.max_retries_spin)
        
        self.retry_delay_spin = QSpinBox()
        self.retry_delay_spin.setMinimum(1)
        self.retry_delay_spin.setMaximum(60)
        self.retry_delay_spin.setSuffix(" seconds")
        self.retry_delay_spin.setValue(self.current_settings.get("retry_delay", 5))
        performance_layout.addRow("Initial Retry Delay:", self.retry_delay_spin)
        
        layout.addWidget(performance_group)
        
        # Update settings
        update_group = QGroupBox("Updates")
        update_layout = QFormLayout(update_group)
        
        self.auto_check_updates = QCheckBox("Check for updates automatically")
        self.auto_check_updates.setChecked(
            self.current_settings.get("update_config", {}).get("auto_check", True)
        )
        update_layout.addRow("", self.auto_check_updates)
        
        self.update_interval_spin = QSpinBox()
        self.update_interval_spin.setMinimum(1)
        self.update_interval_spin.setMaximum(168)
        self.update_interval_spin.setSuffix(" hours")
        self.update_interval_spin.setValue(
            self.current_settings.get("update_config", {}).get("check_interval", 24)
        )
        update_layout.addRow("Check Interval:", self.update_interval_spin)
        
        layout.addWidget(update_group)
        
        # Add spacer at the bottom
        layout.addStretch()
    
    def _browse_output_dir(self):
        """Open a file dialog to select the output directory."""
        current_dir = self.output_dir_edit.text() or Path.home()
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            str(current_dir)
        )
        if directory:
            self.output_dir_edit.setText(directory)
    
    def get_settings(self) -> Dict[str, Any]:
        """
        Get the updated settings from the dialog.
        
        Returns:
            Dictionary containing the updated settings
        """
        # Get settings from UI components
        settings = {
            "theme": self.theme_combo.currentText().lower(),
            "output_dir": self.output_dir_edit.text(),
            "concurrency": self.concurrency_spin.value(),
            "default_model": self.model_combo.currentText().lower(),
            "cache_enabled": self.cache_enabled.isChecked(),
            "cache_size_mb": self.cache_size_spin.value(),
            "default_language": self.language_combo.currentData(),
            "max_retries": self.max_retries_spin.value(),
            "retry_delay": self.retry_delay_spin.value(),
            "update_config": {
                "auto_check": self.auto_check_updates.isChecked(),
                "check_interval": self.update_interval_spin.value(),
                # Preserve other update settings
                **self.current_settings.get("update_config", {})
            }
        }
        
        return settings


class AboutDialog(QDialog):
    """Dialog showing information about the application."""
    
    def __init__(self, parent=None):
        """
        Initialize the about dialog.
        
        Args:
            parent: The parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Dialog settings
        self.setWindowTitle(f"About {APP_NAME}")
        self.setFixedSize(500, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # App name and version
        title_label = self.style_manager.create_modern_heading(APP_NAME)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        version_label = QLabel(f"Version {APP_VERSION}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        layout.addSpacing(20)
        
        # Description
        description = (
            "YouTube Translator Pro is an advanced desktop application for transcribing "
            "and translating YouTube videos. It utilizes cutting-edge AI models to provide "
            "high-quality transcriptions and translations in multiple languages."
        )
        desc_label = QLabel(description)
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        layout.addSpacing(20)
        
        # Features
        features_group = QGroupBox("Key Features")
        features_layout = QVBoxLayout(features_group)
        
        features = [
            "High-quality transcription using Whisper AI models",
            "Translation into multiple languages",
            "Batch processing for multiple videos",
            "Export to multiple formats including SRT subtitles",
            "Advanced caching for improved performance"
        ]
        
        for feature in features:
            feature_label = QLabel(f"• {feature}")
            feature_label.setWordWrap(True)
            features_layout.addWidget(feature_label)
        
        layout.addWidget(features_group)
        layout.addSpacing(20)
        
        # Credits
        credits_label = QLabel("© 2025 YouTube Translator Pro Team")
        credits_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(credits_label)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Apply styles
        self.style_manager.apply_styles(self)


class ErrorDialog(QDialog):
    """Dialog for displaying error information."""
    
    def __init__(self, message: str, details: str, parent=None):
        """
        Initialize the error dialog.
        
        Args:
            message: The error message
            details: Detailed error information
            parent: The parent widget
        """
        super().__init__(parent)
        self.style_manager = StyleManager()
        self.message = message
        self.details = details
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Dialog settings
        self.setWindowTitle(f"{APP_NAME} - Error")
        self.resize(600, 400)
        
        # Create layout
        layout = QVBoxLayout(self)
        
        # Error heading
        heading = self.style_manager.create_modern_heading("An Error Occurred")
        layout.addWidget(heading)
        
        # Error message
        message_label = QLabel(self.message)
        message_label.setWordWrap(True)
        message_label.setStyleSheet(f"color: {self.style_manager.colors['error']}; font-weight: bold;")
        layout.addWidget(message_label)
        
        layout.addSpacing(10)
        
        # Error details
        if self.details:
            details_group = QGroupBox("Error Details")
            details_layout = QVBoxLayout(details_group)
            
            details_edit = QTextEdit()
            details_edit.setReadOnly(True)
            details_edit.setText(self.details)
            details_layout.addWidget(details_edit)
            
            layout.addWidget(details_group)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)
        
        # Apply styles
        self.style_manager.apply_styles(self)
