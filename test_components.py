"""
Test script for YouTube Translator Pro UI components.
This script tests the new components we've implemented.
"""

import sys
import os
from pathlib import Path

# Ensure the package's parent directory is in the Python path
package_parent = Path(__file__).parent
if str(package_parent) not in sys.path:
    sys.path.insert(0, str(package_parent))

try:
    try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
except ImportError:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QMessageBox
try:
    try:
    try:
    from PyQt6.QtCore import Qt
except ImportError:
    from PyQt5.QtCore import Qt
except ImportError:
    from PyQt5.QtCore import Qt
except ImportError:
    from PyQt5.QtCore import Qt

# Import our components
from src.utils.localization import localization, get_string
from src.ui.language_selector import LanguageSelector
from src.ui.performance_monitor_widget import PerformanceMonitorWidget
from src.ui.telemetry_consent_dialog import TelemetryConsentDialog
from src.ui.settings_dialog import SettingsDialog
from src.config import load_settings, save_settings

class TestWindow(QMainWindow):
    """Test window for UI components."""
    
    def __init__(self):
        super().__init__()
        
        # Set up window
        self.setWindowTitle("Component Test Window")
        self.setMinimumSize(800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Create layout
        self.layout = QVBoxLayout(self.central_widget)
        
        # Add test buttons
        self.lang_button = QPushButton("Test Language Selector")
        self.lang_button.clicked.connect(self.test_language_selector)
        self.layout.addWidget(self.lang_button)
        
        self.perf_button = QPushButton("Test Performance Monitor")
        self.perf_button.clicked.connect(self.test_performance_monitor)
        self.layout.addWidget(self.perf_button)
        
        self.telemetry_button = QPushButton("Test Telemetry Consent")
        self.telemetry_button.clicked.connect(self.test_telemetry_consent)
        self.layout.addWidget(self.telemetry_button)
        
        self.settings_button = QPushButton("Test Settings Dialog")
        self.settings_button.clicked.connect(self.test_settings_dialog)
        self.layout.addWidget(self.settings_button)
        
        # Initialize components
        self.init_components()
        
    def init_components(self):
        """Initialize components."""
        # Load settings
        self.settings = load_settings()
        
        # Set up localization
        language = self.settings.get("language", "en")
        localization.set_language(language)
        
        # Create language selector
        self.language_selector = LanguageSelector()
        self.language_selector.language_changed.connect(self.on_language_changed)
        self.layout.addWidget(self.language_selector)
        
    def test_language_selector(self):
        """Test the language selector component."""
        try:
            if hasattr(self, 'language_selector'):
                QMessageBox.information(self, "Test", "Language selector already added to the window.")
            else:
                self.language_selector = LanguageSelector()
                self.language_selector.language_changed.connect(self.on_language_changed)
                self.layout.addWidget(self.language_selector)
                QMessageBox.information(self, "Success", "Language selector created successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create language selector: {str(e)}")
    
    def test_performance_monitor(self):
        """Test the performance monitor component."""
        try:
            # Create dialog
            dialog = QMainWindow(self)
            dialog.setWindowTitle("Performance Monitor Test")
            dialog.setMinimumSize(800, 600)
            
            # Create widget
            monitor_widget = PerformanceMonitorWidget(dialog)
            dialog.setCentralWidget(monitor_widget)
            
            # Show dialog
            dialog.show()
            QMessageBox.information(self, "Success", "Performance monitor created successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create performance monitor: {str(e)}")
    
    def test_telemetry_consent(self):
        """Test the telemetry consent dialog."""
        try:
            dialog = TelemetryConsentDialog(self)
            dialog.consent_given.connect(self.on_telemetry_consent)
            result = dialog.exec()
            
            message = "Consent given" if result else "Consent declined"
            QMessageBox.information(self, "Result", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create telemetry consent dialog: {str(e)}")
    
    def test_settings_dialog(self):
        """Test the settings dialog."""
        try:
            dialog = SettingsDialog(self)
            dialog.settings_changed.connect(self.on_settings_changed)
            result = dialog.exec()
            
            message = "Settings saved" if result else "Settings cancelled"
            QMessageBox.information(self, "Result", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create settings dialog: {str(e)}")
    
    def on_language_changed(self, language_code):
        """Handle language change events."""
        # Update settings
        self.settings["language"] = language_code
        save_settings(self.settings)
        
        # Show message
        QMessageBox.information(
            self,
            get_string("language.changed_title", "Language Changed"),
            get_string("language.changed_message", "Some UI elements will update immediately. Others may require a restart.")
        )
    
    def on_telemetry_consent(self, accepted, privacy_settings):
        """Handle telemetry consent response."""
        print(f"Telemetry consent response: {accepted}")
        print(f"Privacy settings: {privacy_settings}")
    
    def on_settings_changed(self, new_settings):
        """Handle settings changed."""
        self.settings = new_settings
        
        # Apply language if changed
        if new_settings.get("language", "en") != self.settings.get("language", "en"):
            localization.set_language(new_settings.get("language", "en"))
            self.language_selector.refresh_text()

def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
