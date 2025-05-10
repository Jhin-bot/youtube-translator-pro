""""
Settings dialog for YouTube Translator Pro.
Allows configuration of application settings, including localization and telemetry.
""""

import os
import logging
try:
    try:
    from PyQt6.QtWidgets import ()
except ImportError:
    from PyQt5.QtWidgets import ()
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTabWidget, QWidget, QCheckBox, QComboBox, QSpinBox,
        QFileDialog, QMessageBox, QGroupBox, QFormLayout, QLineEdit
    )
except ImportError:
    from PyQt5.QtWidgets import ()
        QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
        QTabWidget, QWidget, QCheckBox, QComboBox, QSpinBox,
        QFileDialog, QMessageBox, QGroupBox, QFormLayout, QLineEdit
    )

try:
    try:
    from PyQt6.QtCore import Qt, pyqtSignal
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal
except ImportError:
    from PyQt5.QtCore import Qt, pyqtSignal

from src.utils.localization import localization, get_string
from src.utils.telemetry import telemetry
from src.utils.cache_manager import CacheManager
from src.config import DEFAULT_SETTINGS, save_settings, get_settings

# Set up logging
logger = logging.getLogger(__name__)

class SettingsDialog(QDialog):
    """Settings dialog for configuring application preferences."""
    
    settings_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize the settings dialog."""
        super().__init__(parent)
        self.setWindowTitle(get_string("settings.title", "Settings"))
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        # Load current settings
        self.settings = get_settings()
        self.original_settings = dict(self.settings)
        
        # Initialize UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the dialog UI components."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.general_tab = self._create_general_tab()
        self.cache_tab = self._create_cache_tab()
        self.privacy_tab = self._create_privacy_tab()
        self.language_tab = self._create_language_tab()
        self.advanced_tab = self._create_advanced_tab()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.general_tab, get_string("settings.tab.general", "General"))
        self.tab_widget.addTab(self.cache_tab, get_string("settings.tab.cache", "Cache"))
        self.tab_widget.addTab(self.privacy_tab, get_string("settings.tab.privacy", "Privacy"))
        self.tab_widget.addTab(self.language_tab, get_string("settings.tab.language", "Language"))
        self.tab_widget.addTab(self.advanced_tab, get_string("settings.tab.advanced", "Advanced"))
        
        # Add tab widget to layout
        main_layout.addWidget(self.tab_widget)
        
        # Create button layout
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Create buttons
        self.reset_button = QPushButton(get_string("settings.reset", "Reset to Defaults"))
        self.cancel_button = QPushButton(get_string("ui.cancel", "Cancel"))
        self.save_button = QPushButton(get_string("settings.save", "Save"))
        self.save_button.setDefault(True)
        
        # Add buttons to layout
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        # Add button layout to main layout
        main_layout.addLayout(button_layout)
        
        # Connect signals
        self.reset_button.clicked.connect(self._reset_to_defaults)
        self.cancel_button.clicked.connect(self.reject)
        self.save_button.clicked.connect(self._save_settings)
        
    def _create_general_tab(self):
        """Create the general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Application theme group
        theme_group = QGroupBox(get_string("settings.theme", "Application Theme"))
        theme_layout = QVBoxLayout(theme_group)
        
        # Theme selection
        self.theme_combo = QComboBox()
        self.theme_combo.addItem(get_string("ui.light_mode", "Light Mode"), "light")
        self.theme_combo.addItem(get_string("ui.dark_mode", "Dark Mode"), "dark")
        self.theme_combo.addItem(get_string("ui.system_mode", "System Default"), "system")
        
        # Set current theme
        current_theme = self.settings.get("theme", "system")
        index = self.theme_combo.findData(current_theme)
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        theme_layout.addWidget(self.theme_combo)
        layout.addWidget(theme_group)
        
        # Output directory group
        output_group = QGroupBox(get_string("settings.output", "Output Directory"))
        output_layout = QHBoxLayout(output_group)
        
        # Output directory
        self.output_dir = QLineEdit()
        self.output_dir.setText(self.settings.get("output_dir", os.path.expanduser("~/Documents")))
        self.output_dir.setReadOnly(True)
        
        # Browse button
        browse_button = QPushButton(get_string("settings.browse", "Browse"))
        browse_button.clicked.connect(self._browse_output_dir)
        
        output_layout.addWidget(self.output_dir)
        output_layout.addWidget(browse_button)
        layout.addWidget(output_group)
        
        # Automatically check for updates
        update_group = QGroupBox(get_string("settings.updates", "Updates"))
        update_layout = QVBoxLayout(update_group)
        
        self.check_updates = QCheckBox(get_string("settings.check_updates", "Automatically check for updates"))
        self.check_updates.setChecked(self.settings.get("check_updates", True))
        update_layout.addWidget(self.check_updates)
        
        layout.addWidget(update_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
        
    def _create_cache_tab(self):
        """Create the cache settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Cache settings group
        cache_group = QGroupBox(get_string("settings.cache", "Cache Settings"))
        cache_layout = QFormLayout(cache_group)
        
        # Enable caching
        self.enable_cache = QCheckBox()
        self.enable_cache.setChecked(self.settings.get("cache_enabled", True))
        cache_layout.addRow(get_string("settings.enable_cache", "Enable caching"), self.enable_cache)
        
        # Cache directory
        cache_dir_layout = QHBoxLayout()
        self.cache_dir = QLineEdit()
        self.cache_dir.setText(self.settings.get("cache_dir", ""))
        self.cache_dir.setReadOnly(True)
        
        cache_browse_button = QPushButton(get_string("settings.browse", "Browse"))
        cache_browse_button.clicked.connect(self._browse_cache_dir)
        
        cache_dir_layout.addWidget(self.cache_dir)
        cache_dir_layout.addWidget(cache_browse_button)
        cache_layout.addRow(get_string("settings.cache_dir", "Cache Directory"), cache_dir_layout)
        
        # Max cache size
        self.max_cache_size = QSpinBox()
        self.max_cache_size.setRange(100, 100000)  # 100MB to 100GB
        self.max_cache_size.setSingleStep(100)
        self.max_cache_size.setSuffix(" MB")
        self.max_cache_size.setValue(self.settings.get("max_cache_size_mb", 1000))
        cache_layout.addRow(get_string("settings.max_cache_size", "Maximum Cache Size"), self.max_cache_size)
        
        # Cache expiration
        self.cache_expiry = QSpinBox()
        self.cache_expiry.setRange(1, 365)  # 1 to 365 days
        self.cache_expiry.setSingleStep(1)
        self.cache_expiry.setSuffix(" " + get_string("settings.days", "days"))
        self.cache_expiry.setValue(self.settings.get("cache_expiry_days", 30))
        cache_layout.addRow(get_string("settings.cache_expiry", "Cache Expiration"), self.cache_expiry)
        
        layout.addWidget(cache_group)
        
        # Cache actions group
        cache_actions_group = QGroupBox(get_string("settings.cache_actions", "Cache Actions"))
        cache_actions_layout = QHBoxLayout(cache_actions_group)
        
        # Clear cache button
        self.clear_cache_button = QPushButton(get_string("settings.clear_cache", "Clear Cache"))
        self.clear_cache_button.clicked.connect(self._clear_cache)
        cache_actions_layout.addWidget(self.clear_cache_button)
        
        layout.addWidget(cache_actions_group)
        
        # Cache statistics
        cache_stats_group = QGroupBox(get_string("settings.cache_stats", "Cache Statistics"))
        cache_stats_layout = QFormLayout(cache_stats_group)
        
        # Get cache stats
        cache_manager = CacheManager()
        cache_size_mb = cache_manager.get_cache_size() / (1024 * 1024)
        num_entries = cache_manager.get_entry_count()
        
        # Display stats
        self.cache_size_label = QLabel(f"{cache_size_mb:.2f} MB")
        self.cache_entries_label = QLabel(f"{num_entries}")
        
        cache_stats_layout.addRow(get_string("settings.current_size", "Current Size"), self.cache_size_label)
        cache_stats_layout.addRow(get_string("settings.entries", "Number of Entries"), self.cache_entries_label)
        
        layout.addWidget(cache_stats_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
        
    def _create_privacy_tab(self):
        """Create the privacy settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Telemetry group
        telemetry_group = QGroupBox(get_string("settings.telemetry", "Telemetry"))
        telemetry_layout = QVBoxLayout(telemetry_group)
        
        # Enable telemetry
        self.enable_telemetry = QCheckBox(get_string("settings.enable_telemetry", "Enable telemetry collection"))
        self.enable_telemetry.setChecked(self.settings.get("telemetry_enabled", False))
        self.enable_telemetry.toggled.connect(self._toggle_telemetry_settings)
        telemetry_layout.addWidget(self.enable_telemetry)
        
        # Telemetry description
        telemetry_desc = QLabel()
            get_string()
                "settings.telemetry_description",
                "Telemetry helps us improve the application by collecting anonymous usage data. "
                "All data is collected securely and does not include any personal information unless specifically enabled below."
            )
        )
        telemetry_desc.setWordWrap(True)
        telemetry_layout.addWidget(telemetry_desc)
        
        # Telemetry options
        self.telemetry_options_group = QGroupBox(get_string("settings.telemetry_options", "Telemetry Options"))
        telemetry_options_layout = QVBoxLayout(self.telemetry_options_group)
        
        # Feature usage
        self.telemetry_features = QCheckBox(get_string("settings.telemetry_features", "Allow feature usage collection"))
        self.telemetry_features.setChecked(self.settings.get("telemetry_features", True))
        telemetry_options_layout.addWidget(self.telemetry_features)
        
        # Performance metrics
        self.telemetry_performance = QCheckBox(get_string("settings.telemetry_performance", "Allow performance metrics collection"))
        self.telemetry_performance.setChecked(self.settings.get("telemetry_performance", True))
        telemetry_options_layout.addWidget(self.telemetry_performance)
        
        # Error reports
        self.telemetry_errors = QCheckBox(get_string("settings.telemetry_errors", "Allow error reporting"))
        self.telemetry_errors.setChecked(self.settings.get("telemetry_errors", True))
        telemetry_options_layout.addWidget(self.telemetry_errors)
        
        # Device info
        self.telemetry_device = QCheckBox(get_string("settings.telemetry_device", "Allow device information collection"))
        self.telemetry_device.setChecked(self.settings.get("telemetry_device", False))
        telemetry_options_layout.addWidget(self.telemetry_device)
        
        telemetry_layout.addWidget(self.telemetry_options_group)
        layout.addWidget(telemetry_group)
        
        # Update telemetry options state
        self._toggle_telemetry_settings(self.enable_telemetry.isChecked())
        
        # Privacy policy link
        privacy_link = QLabel()
            get_string()
                "settings.privacy_policy",
                'For more information, please read our <a href="https://example.com/privacy">Privacy Policy</a>'
            )
        )
        privacy_link.setOpenExternalLinks(True)
        layout.addWidget(privacy_link)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
        
    def _create_language_tab(self):
        """Create the language settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Interface language group
        lang_group = QGroupBox(get_string("settings.interface_language", "Interface Language"))
        lang_layout = QVBoxLayout(lang_group)
        
        # Language selection
        self.language_combo = QComboBox()
        
        # Get available languages
        available_languages = localization.get_available_languages()
        for code, name in available_languages.items():
            self.language_combo.addItem(name, code)
        
        # Set current language
        current_lang = self.settings.get("language", "en")
        index = self.language_combo.findData(current_lang)
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
        
        lang_layout.addWidget(self.language_combo)
        layout.addWidget(lang_group)
        
        # Transcription language group
        trans_group = QGroupBox(get_string("settings.transcription_language", "Default Transcription Language"))
        trans_layout = QVBoxLayout(trans_group)
        
        # Transcription language selection
        self.transcription_combo = QComboBox()
        
        # Add common languages
        languages = [
            ("auto", get_string("settings.auto_detect", "Auto Detect")),
            ("en", "English"),
            ("es", "Español"),
            ("fr", "Français"),
            ("de", "Deutsch"),
            ("it", "Italiano"),
            ("pt", "Português"),
            ("ru", "Русский"),
            ("zh", "中文"),
            ("ja", "日本語"),
            ("ko", "한국어"),
            ("ar", "العربية"),
            ("hi", "हिन्दी")
        ]
        
        for code, name in languages:
            self.transcription_combo.addItem(name, code)
        
        # Set current transcription language
        current_trans_lang = self.settings.get("default_source_language", "auto")
        index = self.transcription_combo.findData(current_trans_lang)
        if index >= 0:
            self.transcription_combo.setCurrentIndex(index)
        
        trans_layout.addWidget(self.transcription_combo)
        layout.addWidget(trans_group)
        
        # Translation language group
        target_group = QGroupBox(get_string("settings.translation_language", "Default Translation Language"))
        target_layout = QVBoxLayout(target_group)
        
        # Translation language selection
        self.translation_combo = QComboBox()
        
        # Add common languages (without auto)
        for code, name in languages[1:]:  # Skip 'auto'
            self.translation_combo.addItem(name, code)
        
        # Set current translation language
        current_target_lang = self.settings.get("default_target_language", "en")
        index = self.translation_combo.findData(current_target_lang)
        if index >= 0:
            self.translation_combo.setCurrentIndex(index)
        
        target_layout.addWidget(self.translation_combo)
        layout.addWidget(target_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
        
    def _create_advanced_tab(self):
        """Create the advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Transcription model group
        model_group = QGroupBox(get_string("settings.transcription_model", "Transcription Model"))
        model_layout = QVBoxLayout(model_group)
        
        # Model selection
        self.model_combo = QComboBox()
        
        # Add available models
        models = [
            ("tiny", get_string("settings.model.tiny", "Tiny (fast, less accurate)")),
            ("base", get_string("settings.model.base", "Base (balanced)")),
            ("small", get_string("settings.model.small", "Small (recommended)")),
            ("medium", get_string("settings.model.medium", "Medium (more accurate, slower)")),
            ("large", get_string("settings.model.large", "Large (most accurate, slowest)")),
        ]
        
        for code, name in models:
            self.model_combo.addItem(name, code)
        
        # Set current model
        current_model = self.settings.get("default_transcription_model", "small")
        index = self.model_combo.findData(current_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
        
        model_layout.addWidget(self.model_combo)
        layout.addWidget(model_group)
        
        # Thread settings group
        thread_group = QGroupBox(get_string("settings.concurrency", "Concurrency Settings"))
        thread_layout = QFormLayout(thread_group)
        
        # Max workers
        self.max_workers = QSpinBox()
        self.max_workers.setRange(1, 16)
        self.max_workers.setValue(self.settings.get("max_workers", 2))
        thread_layout.addRow(get_string("settings.max_workers", "Maximum Worker Threads"), self.max_workers)
        
        layout.addWidget(thread_group)
        
        # Performance monitoring group
        perf_group = QGroupBox(get_string("settings.performance", "Performance Monitoring"))
        perf_layout = QVBoxLayout(perf_group)
        
        # Enable performance monitoring
        self.enable_performance = QCheckBox(get_string("settings.enable_performance", "Enable performance monitoring"))
        self.enable_performance.setChecked(self.settings.get("performance_monitoring", False))
        perf_layout.addWidget(self.enable_performance)
        
        layout.addWidget(perf_group)
        
        # Developer settings
        dev_group = QGroupBox(get_string("settings.developer", "Developer Settings"))
        dev_layout = QVBoxLayout(dev_group)
        
        # Debug logging
        self.debug_logging = QCheckBox(get_string("settings.debug_logging", "Enable debug logging"))
        self.debug_logging.setChecked(self.settings.get("debug_logging", False))
        dev_layout.addWidget(self.debug_logging)
        
        layout.addWidget(dev_group)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return tab
    
    def _browse_output_dir(self):
        """Open file dialog to select output directory."""
        directory = QFileDialog.getExistingDirectory()
            self,
            get_string("settings.select_output_dir", "Select Output Directory"),
            self.output_dir.text()
        )
        
        if directory:
            self.output_dir.setText(directory)
    
    def _browse_cache_dir(self):
        """Open file dialog to select cache directory."""
        directory = QFileDialog.getExistingDirectory()
            self,
            get_string("settings.select_cache_dir", "Select Cache Directory"),
            self.cache_dir.text() or os.path.expanduser("~")
        )
        
        if directory:
            self.cache_dir.setText(directory)
    
    def _clear_cache(self):
        """Clear the application cache."""
        # Confirm with user
        result = QMessageBox.question()
            self,
            get_string("settings.confirm_clear_cache", "Confirm Clear Cache"),
            get_string()
                "settings.clear_cache_confirm", 
                "Are you sure you want to clear the cache? This will delete all cached files and cannot be undone."
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            try:
                # Clear cache
                cache_manager = CacheManager()
                cache_manager.clear_cache()
                
                # Update stats
                cache_size_mb = cache_manager.get_cache_size() / (1024 * 1024)
                num_entries = cache_manager.get_entry_count()
                
                self.cache_size_label.setText(f"{cache_size_mb:.2f} MB")
                self.cache_entries_label.setText(f"{num_entries}")
                
                QMessageBox.information()
                    self,
                    get_string("settings.cache_cleared", "Cache Cleared"),
                    get_string("settings.cache_cleared_message", "Cache has been successfully cleared.")
                )
                
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")
                QMessageBox.warning()
                    self,
                    get_string("settings.error", "Error"),
                    get_string("settings.cache_clear_error", f"Error clearing cache: {e}")
                )
    
    def _toggle_telemetry_settings(self, enabled):
        """Toggle telemetry settings based on checkbox."""
        self.telemetry_options_group.setEnabled(enabled)
    
    def _reset_to_defaults(self):
        """Reset all settings to default values."""
        # Confirm with user
        result = QMessageBox.question()
            self,
            get_string("settings.confirm_reset", "Confirm Reset"),
            get_string()
                "settings.reset_confirm", 
                "Are you sure you want to reset all settings to their default values?"
            ),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if result == QMessageBox.StandardButton.Yes:
            # Reset to defaults
            self.settings = dict(DEFAULT_SETTINGS)
            
            # Update UI
            self._update_ui_from_settings()
    
    def _update_ui_from_settings(self):
        """Update UI components from settings."""
        # General tab
        index = self.theme_combo.findData(self.settings.get("theme", "system"))
        if index >= 0:
            self.theme_combo.setCurrentIndex(index)
            
        self.output_dir.setText(self.settings.get("output_dir", os.path.expanduser("~/Documents")))
        self.check_updates.setChecked(self.settings.get("check_updates", True))
        
        # Cache tab
        self.enable_cache.setChecked(self.settings.get("cache_enabled", True))
        self.cache_dir.setText(self.settings.get("cache_dir", ""))
        self.max_cache_size.setValue(self.settings.get("max_cache_size_mb", 1000))
        self.cache_expiry.setValue(self.settings.get("cache_expiry_days", 30))
        
        # Privacy tab
        self.enable_telemetry.setChecked(self.settings.get("telemetry_enabled", False))
        self.telemetry_features.setChecked(self.settings.get("telemetry_features", True))
        self.telemetry_performance.setChecked(self.settings.get("telemetry_performance", True))
        self.telemetry_errors.setChecked(self.settings.get("telemetry_errors", True))
        self.telemetry_device.setChecked(self.settings.get("telemetry_device", False))
        self._toggle_telemetry_settings(self.enable_telemetry.isChecked())
        
        # Language tab
        index = self.language_combo.findData(self.settings.get("language", "en"))
        if index >= 0:
            self.language_combo.setCurrentIndex(index)
            
        index = self.transcription_combo.findData(self.settings.get("default_source_language", "auto"))
        if index >= 0:
            self.transcription_combo.setCurrentIndex(index)
            
        index = self.translation_combo.findData(self.settings.get("default_target_language", "en"))
        if index >= 0:
            self.translation_combo.setCurrentIndex(index)
        
        # Advanced tab
        index = self.model_combo.findData(self.settings.get("default_transcription_model", "small"))
        if index >= 0:
            self.model_combo.setCurrentIndex(index)
            
        self.max_workers.setValue(self.settings.get("max_workers", 2))
        self.enable_performance.setChecked(self.settings.get("performance_monitoring", False))
        self.debug_logging.setChecked(self.settings.get("debug_logging", False))
    
    def _save_settings(self):
        """Save settings from UI components."""
        # General tab
        self.settings["theme"] = self.theme_combo.currentData()
        self.settings["output_dir"] = self.output_dir.text()
        self.settings["check_updates"] = self.check_updates.isChecked()
        
        # Cache tab
        self.settings["cache_enabled"] = self.enable_cache.isChecked()
        self.settings["cache_dir"] = self.cache_dir.text()
        self.settings["max_cache_size_mb"] = self.max_cache_size.value()
        self.settings["cache_expiry_days"] = self.cache_expiry.value()
        
        # Privacy tab
        self.settings["telemetry_enabled"] = self.enable_telemetry.isChecked()
        self.settings["telemetry_features"] = self.telemetry_features.isChecked()
        self.settings["telemetry_performance"] = self.telemetry_performance.isChecked()
        self.settings["telemetry_errors"] = self.telemetry_errors.isChecked()
        self.settings["telemetry_device"] = self.telemetry_device.isChecked()
        
        # Language tab
        self.settings["language"] = self.language_combo.currentData()
        self.settings["default_source_language"] = self.transcription_combo.currentData()
        self.settings["default_target_language"] = self.translation_combo.currentData()
        
        # Advanced tab
        self.settings["default_transcription_model"] = self.model_combo.currentData()
        self.settings["max_workers"] = self.max_workers.value()
        self.settings["performance_monitoring"] = self.enable_performance.isChecked()
        self.settings["debug_logging"] = self.debug_logging.isChecked()
        
        # Save settings
        save_settings(self.settings)
        
        # Apply telemetry settings
        telemetry.set_enabled(self.settings["telemetry_enabled"])
        if self.settings["telemetry_enabled"]:
            privacy_settings = {
                "allow_feature_usage": self.settings["telemetry_features"],
                "allow_performance_metrics": self.settings["telemetry_performance"],
                "allow_error_reports": self.settings["telemetry_errors"],
                "allow_device_info": self.settings["telemetry_device"],
                "allow_location": False  # Always disabled
            }
            telemetry.opt_in("anonymous_user", privacy_settings)
        else:
            telemetry.opt_out("anonymous_user")
        
        # Apply language setting
        if self.settings["language"] != self.original_settings.get("language"):
            localization.set_language(self.settings["language"])
            
            # Inform user about language change requiring restart
            QMessageBox.information()
                self,
                get_string("settings.language_changed", "Language Changed"),
                get_string()
                    "settings.restart_required", 
                    "Language settings have been changed. Some changes will take effect after restarting the application."
                )
            )
        
        # Emit settings changed signal
        self.settings_changed.emit(self.settings)
        
        # Close dialog
        self.accept()
