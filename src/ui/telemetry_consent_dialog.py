"""
Telemetry consent dialog for YouTube Translator Pro.
Requests user permission for collecting anonymous usage data.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QGroupBox, QDialogButtonBox, QTextBrowser
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.localization import get_string
from src.utils.telemetry import telemetry

# Set up logging
logger = logging.getLogger(__name__)

class TelemetryConsentDialog(QDialog):
    """Dialog for requesting user consent for telemetry collection."""
    
    consent_given = pyqtSignal(bool, dict)
    
    def __init__(self, parent=None):
        """Initialize the telemetry consent dialog."""
        super().__init__(parent)
        self.setWindowTitle(get_string("telemetry.consent_title", "Data Collection Consent"))
        self.setMinimumWidth(600)
        self.setMinimumHeight(450)
        
        # Initialize UI
        self._init_ui()
        
    def _init_ui(self):
        """Initialize the dialog UI components."""
        # Create main layout
        main_layout = QVBoxLayout(self)
        
        # Create header
        header_label = QLabel(get_string(
            "telemetry.header",
            "Help Improve YouTube Translator Pro"
        ))
        header_font = header_label.font()
        header_font.setBold(True)
        header_font.setPointSize(header_font.pointSize() + 2)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)
        
        # Create description
        description = QTextBrowser()
        description.setOpenExternalLinks(True)
        description.setHtml(get_string(
            "telemetry.description",
            """
            <p>We're committed to creating the best possible experience for our users. 
            To help us improve, we'd like to collect anonymous usage data.</p>
            
            <p><b>This is completely optional.</b> YouTube Translator Pro works perfectly whether you choose 
            to share this data or not.</p>
            
            <p>If you opt in, we'll collect:</p>
            <ul>
                <li>Which features you use most frequently</li>
                <li>Performance metrics to help us optimize the application</li>
                <li>Error reports to help us fix bugs</li>
            </ul>
            
            <p>We <b>never</b> collect:</p>
            <ul>
                <li>Personal information (name, email, etc.)</li>
                <li>Video content, transcriptions, or translations</li>
                <li>YouTube account information</li>
                <li>Files from your computer</li>
            </ul>
            
            <p>You can change your mind at any time in the application settings.</p>
            
            <p>For more information, please read our <a href="https://example.com/privacy">Privacy Policy</a>.</p>
            """
        ))
        main_layout.addWidget(description)
        
        # Create options group
        options_group = QGroupBox(get_string("telemetry.options", "Data Collection Options"))
        options_layout = QVBoxLayout(options_group)
        
        # Create options
        self.collect_features = QCheckBox(get_string(
            "telemetry.collect_features",
            "Allow collection of feature usage data"
        ))
        self.collect_features.setChecked(True)
        options_layout.addWidget(self.collect_features)
        
        self.collect_performance = QCheckBox(get_string(
            "telemetry.collect_performance",
            "Allow collection of performance metrics"
        ))
        self.collect_performance.setChecked(True)
        options_layout.addWidget(self.collect_performance)
        
        self.collect_errors = QCheckBox(get_string(
            "telemetry.collect_errors",
            "Allow collection of error reports"
        ))
        self.collect_errors.setChecked(True)
        options_layout.addWidget(self.collect_errors)
        
        self.collect_device = QCheckBox(get_string(
            "telemetry.collect_device",
            "Allow collection of device information (OS version, CPU, RAM)"
        ))
        self.collect_device.setChecked(False)
        options_layout.addWidget(self.collect_device)
        
        main_layout.addWidget(options_group)
        
        # Create buttons
        buttons = QDialogButtonBox()
        
        self.decline_button = buttons.addButton(
            get_string("telemetry.decline", "No, Thanks"), 
            QDialogButtonBox.ButtonRole.RejectRole
        )
        
        self.accept_button = buttons.addButton(
            get_string("telemetry.accept", "Yes, I'll Help"), 
            QDialogButtonBox.ButtonRole.AcceptRole
        )
        
        # Set accept button as default
        self.accept_button.setDefault(True)
        
        # Connect buttons
        self.decline_button.clicked.connect(self._on_decline)
        self.accept_button.clicked.connect(self._on_accept)
        
        main_layout.addWidget(buttons)
        
    def _on_accept(self):
        """Handle accept button click."""
        # Update telemetry settings
        privacy_settings = {
            "allow_feature_usage": self.collect_features.isChecked(),
            "allow_performance_metrics": self.collect_performance.isChecked(),
            "allow_error_reports": self.collect_errors.isChecked(),
            "allow_device_info": self.collect_device.isChecked(),
            "allow_location": False  # Always disabled
        }
        
        # Enable telemetry
        telemetry.set_enabled(True)
        telemetry.opt_in("anonymous_user", privacy_settings)
        
        logger.info("User opted into telemetry collection")
        logger.debug(f"Telemetry privacy settings: {privacy_settings}")
        
        # Emit signal
        self.consent_given.emit(True, privacy_settings)
        
        # Close dialog
        self.accept()
        
    def _on_decline(self):
        """Handle decline button click."""
        # Disable telemetry
        telemetry.set_enabled(False)
        telemetry.opt_out("anonymous_user")
        
        logger.info("User declined telemetry collection")
        
        # Emit signal
        self.consent_given.emit(False, {})
        
        # Close dialog
        self.reject()
