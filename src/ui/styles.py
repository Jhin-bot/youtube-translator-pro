"""
Style manager for YouTube Translator Pro.
Provides consistent styling and theming across the application.
"""

import logging
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtGui import QPalette, QColor

# Logger setup
logger = logging.getLogger(__name__)

class StyleManager:
    """
    Manages application styling and themes.
    Provides consistent styling across the application.
    """
    
    # Color schemes
    DARK_THEME = {
        "bg_primary": "#2D2D30",
        "bg_secondary": "#252526",
        "bg_tertiary": "#1E1E1E",
        "text_primary": "#FFFFFF",
        "text_secondary": "#CCCCCC",
        "accent": "#007ACC",
        "accent_hover": "#1C97EA",
        "success": "#6A9955",
        "warning": "#FFCC00",
        "error": "#F14C4C",
        "border": "#3F3F46"
    }
    
    LIGHT_THEME = {
        "bg_primary": "#F5F5F5",
        "bg_secondary": "#EAEAEA",
        "bg_tertiary": "#FFFFFF",
        "text_primary": "#1E1E1E",
        "text_secondary": "#424242",
        "accent": "#0078D7",
        "accent_hover": "#106EBE",
        "success": "#107C10",
        "warning": "#D83B01",
        "error": "#E81123",
        "border": "#C8C8C8"
    }
    
    def __init__(self, theme="dark"):
        """
        Initialize the style manager.
        
        Args:
            theme: The initial theme ("dark" or "light")
        """
        self.current_theme = theme
        self.colors = self.DARK_THEME if theme == "dark" else self.LIGHT_THEME
    
    def apply_theme(self, app: QApplication, theme="dark"):
        """
        Apply a theme to the entire application.
        
        Args:
            app: The QApplication instance
            theme: The theme to apply ("dark" or "light")
        """
        self.current_theme = theme
        self.colors = self.DARK_THEME if theme == "dark" else self.LIGHT_THEME
        
        if theme == "dark":
            self._apply_dark_theme(app)
        else:
            self._apply_light_theme(app)
        
        # Apply stylesheet for more detailed styling
        app.setStyleSheet(self._get_stylesheet())
        
        logger.info(f"Applied {theme} theme to application")
    
    def _apply_dark_theme(self, app: QApplication):
        """Apply dark theme to the application."""
        palette = QPalette()
        
        # Set window/widget background colors
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors["bg_primary"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors["bg_secondary"]))
        
        # Set text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(self.colors["text_secondary"]))
        
        # Set button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors["bg_primary"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors["text_primary"]))
        
        # Set highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.colors["text_primary"]))
        
        # Set tooltip colors
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.colors["text_primary"]))
        
        # Apply the palette
        app.setPalette(palette)
    
    def _apply_light_theme(self, app: QApplication):
        """Apply light theme to the application."""
        palette = QPalette()
        
        # Set window/widget background colors
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors["bg_primary"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors["bg_secondary"]))
        
        # Set text colors
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(self.colors["text_secondary"]))
        
        # Set button colors
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors["bg_primary"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors["text_primary"]))
        
        # Set highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.colors["text_primary"]))
        
        # Set tooltip colors
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.colors["text_primary"]))
        
        # Apply the palette
        app.setPalette(palette)
    
    def _get_stylesheet(self):
        """Get the global stylesheet for the application."""
        return f"""
            /* QMainWindow styles */
            QMainWindow {{
                background-color: {self.colors["bg_tertiary"]};
            }}
            
            /* QWidget styles */
            QWidget {{
                background-color: {self.colors["bg_primary"]};
                color: {self.colors["text_primary"]};
            }}
            
            /* QLabel styles */
            QLabel {{
                color: {self.colors["text_primary"]};
            }}
            
            /* QPushButton styles */
            QPushButton {{
                background-color: {self.colors["accent"]};
                color: {self.colors["text_primary"]};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors["accent_hover"]};
            }}
            
            QPushButton:disabled {{
                background-color: {self.colors["bg_secondary"]};
                color: {self.colors["text_secondary"]};
            }}
            
            /* QLineEdit styles */
            QLineEdit {{
                background-color: {self.colors["bg_secondary"]};
                color: {self.colors["text_primary"]};
                border: 1px solid {self.colors["border"]};
                padding: 6px;
                border-radius: 4px;
            }}
            
            /* QTextEdit styles */
            QTextEdit {{
                background-color: {self.colors["bg_secondary"]};
                color: {self.colors["text_primary"]};
                border: 1px solid {self.colors["border"]};
                padding: 6px;
                border-radius: 4px;
            }}
            
            /* QComboBox styles */
            QComboBox {{
                background-color: {self.colors["bg_secondary"]};
                color: {self.colors["text_primary"]};
                border: 1px solid {self.colors["border"]};
                padding: 6px;
                border-radius: 4px;
            }}
            
            /* QProgressBar styles */
            QProgressBar {{
                background-color: {self.colors["bg_secondary"]};
                color: {self.colors["text_primary"]};
                border: 1px solid {self.colors["border"]};
                border-radius: 4px;
                text-align: center;
            }}
            
            QProgressBar::chunk {{
                background-color: {self.colors["accent"]};
                border-radius: 4px;
            }}
            
            /* QTabWidget styles */
            QTabWidget::pane {{
                border: 1px solid {self.colors["border"]};
                border-radius: 4px;
            }}
            
            QTabBar::tab {{
                background-color: {self.colors["bg_secondary"]};
                color: {self.colors["text_primary"]};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors["accent"]};
            }}
            
            /* QStatusBar styles */
            QStatusBar {{
                background-color: {self.colors["bg_tertiary"]};
                color: {self.colors["text_secondary"]};
            }}
            
            /* QGroupBox styles */
            QGroupBox {{
                border: 1px solid {self.colors["border"]};
                border-radius: 4px;
                margin-top: 16px;
                padding-top: 16px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                background-color: {self.colors["bg_primary"]};
                color: {self.colors["text_primary"]};
            }}
        """
    
    def apply_styles(self, widget: QWidget):
        """
        Apply styles to a specific widget.
        
        Args:
            widget: The widget to style
        """
        # No additional styling needed here as the global stylesheet handles it
        pass
    
    def create_modern_heading(self, text: str, parent=None):
        """
        Create a styled heading label.
        
        Args:
            text: The heading text
            parent: The parent widget
            
        Returns:
            A styled QLabel for use as a heading
        """
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtGui import QFont
        
        label = QLabel(text, parent)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(f"color: {self.colors['accent']}; margin-bottom: 10px;")
        
        return label
    
    def create_success_button(self, text: str, parent=None):
        """
        Create a styled success button.
        
        Args:
            text: The button text
            parent: The parent widget
            
        Returns:
            A styled QPushButton with success styling
        """
        from PyQt6.QtWidgets import QPushButton
        
        button = QPushButton(text, parent)
        button.setStyleSheet(f"""
            background-color: {self.colors['success']};
            color: {self.colors['text_primary']};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        """)
        
        return button
    
    def create_warning_button(self, text: str, parent=None):
        """
        Create a styled warning button.
        
        Args:
            text: The button text
            parent: The parent widget
            
        Returns:
            A styled QPushButton with warning styling
        """
        from PyQt6.QtWidgets import QPushButton
        
        button = QPushButton(text, parent)
        button.setStyleSheet(f"""
            background-color: {self.colors['warning']};
            color: {self.colors['text_primary']};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        """)
        
        return button
    
    def create_error_button(self, text: str, parent=None):
        """
        Create a styled error button.
        
        Args:
            text: The button text
            parent: The parent widget
            
        Returns:
            A styled QPushButton with error styling
        """
        from PyQt6.QtWidgets import QPushButton
        
        button = QPushButton(text, parent)
        button.setStyleSheet(f"""
            background-color: {self.colors['error']};
            color: {self.colors['text_primary']};
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
        """)
        
        return button
