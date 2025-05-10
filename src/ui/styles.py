"""
Style manager for YouTube Translator Pro.
Provides consistent styling and theming across the application.
"""

import logging

# PyQt imports with fallbacks
try:
    # First try PyQt6
    from PyQt6.QtCore import Qt
    from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton
    from PyQt6.QtGui import QPalette, QColor, QFont
    USE_PYQT6 = True
    logger = logging.getLogger(__name__)
    logger.info("Using PyQt6 for styles")
except ImportError:
    try:
        # Then try PyQt5
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton
        from PyQt5.QtGui import QPalette, QColor, QFont
        USE_PYQT6 = False
        logger = logging.getLogger(__name__)
        logger.info("Using PyQt5 for styles")
    except ImportError:
        # If neither PyQt6 nor PyQt5 is available, create mock classes
        logger = logging.getLogger(__name__)
        logger.warning("Neither PyQt6 nor PyQt5 is available. Creating mock classes for styles.")
        USE_PYQT6 = False
        
        # Mock implementations for Qt components
        class Qt:
            AlignCenter = 0
            AlignLeft = 0
            AlignRight = 0
            black = 0
            white = 0
            darkGray = 0
            gray = 0
            lightGray = 0
            red = 0
            green = 0
            blue = 0
            cyan = 0
            magenta = 0
            yellow = 0
            darkRed = 0
            darkGreen = 0
            darkBlue = 0
        
        # Mock widgets
        class QApplication:
            @staticmethod
            def palette():
                return QPalette()
            @staticmethod
            def setPalette(palette):
                pass
                
        class QWidget:
            def __init__(self, *args, **kwargs):
                pass
            def setStyleSheet(self, *args, **kwargs):
                pass
                
        class QLabel:
            def __init__(self, *args, **kwargs):
                pass
            def setStyleSheet(self, *args, **kwargs):
                pass
                
        class QPushButton:
            def __init__(self, *args, **kwargs):
                pass
            def setStyleSheet(self, *args, **kwargs):
                pass
                
        class QPalette:
            def __init__(self, *args, **kwargs):
                self.Window = 0
                self.WindowText = 1
                self.Base = 2
                self.AlternateBase = 3
                self.ToolTipBase = 4
                self.ToolTipText = 5
                self.Text = 6
                self.Button = 7
                self.ButtonText = 8
                self.BrightText = 9
                self.Link = 10
                self.Highlight = 11
                self.HighlightedText = 12
            def setColor(self, *args, **kwargs):
                pass
                
        class QColor:
            def __init__(self, *args, **kwargs):
                pass
                
        class QFont:
            def __init__(self, *args, **kwargs):
                pass
            def setPointSize(self, *args, **kwargs):
                pass

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
        
        # Apply global stylesheet
        app.setStyleSheet(self._get_stylesheet())
        
        logger.info(f"Applied {theme} theme to application")
    
    def _apply_dark_theme(self, app: QApplication):
        """Apply dark theme to the application."""
        # Set dark palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors["bg_primary"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors["bg_secondary"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors["bg_secondary"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(self.colors["accent"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.colors["text_primary"]))
        
        app.setPalette(palette)
    
    def _apply_light_theme(self, app: QApplication):
        """Apply light theme to the application."""
        # Set light palette
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors["bg_primary"]))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(self.colors["bg_secondary"]))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(self.colors["bg_tertiary"]))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors["bg_secondary"]))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors["text_primary"]))
        palette.setColor(QPalette.ColorRole.Link, QColor(self.colors["accent"]))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors["accent"]))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(self.colors["text_primary"]))
        
        app.setPalette(palette)
    
    def _get_stylesheet(self):
        """Get the global stylesheet for the application."""
        return f"""
        QWidget {{
            background-color: {self.colors["bg_primary"]};
            color: {self.colors["text_primary"]};
        }}
        
        QLabel {{
            color: {self.colors["text_primary"]};
            background-color: transparent;
        }}
        
        QPushButton {{
            background-color: {self.colors["bg_secondary"]};
            color: {self.colors["text_primary"]};
            border: 1px solid {self.colors["border"]};
            border-radius: 4px;
            padding: 5px 10px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors["bg_tertiary"]};
            border: 1px solid {self.colors["accent"]};
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors["accent"]};
            color: white;
        }}
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox {{
            background-color: {self.colors["bg_tertiary"]};
            color: {self.colors["text_primary"]};
            border: 1px solid {self.colors["border"]};
            border-radius: 4px;
            padding: 5px;
        }}
        
        QProgressBar {{
            background-color: {self.colors["bg_tertiary"]};
            border: 1px solid {self.colors["border"]};
            border-radius: 4px;
            text-align: center;
        }}
        
        QProgressBar::chunk {{
            background-color: {self.colors["accent"]};
            width: 10px;
            margin: 0.5px;
        }}
        
        QTabWidget::pane {{
            border: 1px solid {self.colors["border"]};
            background-color: {self.colors["bg_secondary"]};
        }}
        
        QTabBar::tab {{
            background-color: {self.colors["bg_primary"]};
            color: {self.colors["text_secondary"]};
            border: 1px solid {self.colors["border"]};
            border-bottom: none;
            padding: 5px 10px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.colors["bg_secondary"]};
            color: {self.colors["text_primary"]};
            border: 1px solid {self.colors["accent"]};
            border-bottom: none;
        }}
        
        QMenuBar {{
            background-color: {self.colors["bg_primary"]};
        }}
        
        QMenuBar::item {{
            background-color: transparent;
            padding: 4px 10px;
        }}
        
        QMenuBar::item:selected {{
            background-color: {self.colors["accent"]};
            color: white;
        }}
        
        QStatusBar {{
            background-color: {self.colors["bg_secondary"]};
            color: {self.colors["text_secondary"]};
        }}
        """
    
    def apply_styles(self, widget: QWidget):
        """
        Apply styles to a specific widget.
        
        Args:
            widget: The widget to style
        """
        # Apply specific widget styles if needed
        widget.setStyleSheet(self._get_stylesheet())
    
    def create_modern_heading(self, text: str, parent=None):
        """
        Create a styled heading label.
        
        Args:
            text: The heading text
            parent: The parent widget
            
        Returns:
            A styled QLabel for use as a heading
        """
        label = QLabel(text, parent)
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        label.setFont(font)
        label.setStyleSheet(f"color: {self.colors['accent']}; background-color: transparent;")
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
        button = QPushButton(text, parent)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['success']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['success']};
                opacity: 0.8;
            }}
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
        button = QPushButton(text, parent)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['warning']};
                color: black;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['warning']};
                opacity: 0.8;
            }}
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
        button = QPushButton(text, parent)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.colors['error']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {self.colors['error']};
                opacity: 0.8;
            }}
        """)
        return button
