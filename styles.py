"""
Modern styling and theming system for the YouTube Transcriber Pro application.
Provides color schemes, widget styles, icon definitions, animations, and layout constants.
"""

import os
import sys
import platform
from enum import Enum, auto
from typing import Dict, Any, Tuple, List, Optional, NamedTuple

from PyQt6.QtCore import (
    Qt, QSize, QEasingCurve, QPoint, QRect, QPropertyAnimation, QMargins,
    QCoreApplication
)
from PyQt6.QtGui import (
    QColor, QFont, QFontDatabase, QIcon, QPalette, QPixmap, QLinearGradient, QGradient,
    QFontMetrics, QImage
)
from PyQt6.QtWidgets import (
    QApplication, QWidget, QFrame, QPushButton, QLabel, QLineEdit, QComboBox,
    QScrollArea, QScrollBar, QToolTip, QCheckBox, QRadioButton, QProgressBar,
    QSlider, QTabWidget, QTabBar, QToolBar, QMenuBar, QMenu, QListWidget,
    QGraphicsDropShadowEffect, QStyleFactory, QStyle, QSpinBox, QDoubleSpinBox, # Added SpinBox/DoubleSpinBox
    QTextEdit # Added QTextEdit
)
import qtawesome as qta # Import qtawesome for icons

# Setup logger
import logging
logger = logging.getLogger(__name__)


# ==============================================================================
# COLOR SCHEMES
# ==============================================================================

class ColorRole(Enum):
    """Color roles for application theming"""
    PRIMARY = auto()            # Main brand color
    SECONDARY = auto()          # Secondary brand color
    SUCCESS = auto()            # Success/Positive color
    WARNING = auto()            # Warning color
    ERROR = auto()              # Error/Danger color
    INFO = auto()               # Information color

    BACKGROUND = auto()         # Main background color
    BACKGROUND_ALT = auto()     # Alternate background color (e.g., for lists, cards)
    BACKGROUND_HOVER = auto()   # Background color on hover
    BACKGROUND_PRESSED = auto() # Background color when pressed

    FOREGROUND = auto()         # Main text/icon color
    FOREGROUND_DIM = auto()     # Dimmed text/icon color
    FOREGROUND_DISABLED = auto()# Text/icon color for disabled elements

    BORDER = auto()             # Default border color
    BORDER_LIGHT = auto()       # Lighter border color
    BORDER_DARK = auto()        # Darker border color

    SHADOW = auto()             # Shadow color

    HIGHLIGHT = auto()          # Highlight color (e.g., selection background)
    HIGHLIGHTED_TEXT = auto()   # Text color on highlight background

    TOOLTIP_BG = auto()         # Tooltip background color
    TOOLTIP_FG = auto()         # Tooltip foreground color


# Define specific color palettes for dark and light themes
DARK_PALETTE: Dict[ColorRole, QColor] = {
    ColorRole.PRIMARY: QColor("#4A90E2"),       # Blue
    ColorRole.SECONDARY: QColor("#50E3C2"),     # Teal
    ColorRole.SUCCESS: QColor("#7ED321"),       # Green
    ColorRole.WARNING: QColor("#F5A623"),       # Orange
    ColorRole.ERROR: QColor("#D0021B"),         # Red
    ColorRole.INFO: QColor("#4A90E2"),          # Blue (same as primary for info)

    ColorRole.BACKGROUND: QColor("#2C3E50"),    # Dark Slate Blue
    ColorRole.BACKGROUND_ALT: QColor("#34495E"),# Darker Slate Blue
    ColorRole.BACKGROUND_HOVER: QColor("#415A77"), # Hovered background
    ColorRole.BACKGROUND_PRESSED: QColor("#2A3B4C"), # Pressed background

    ColorRole.FOREGROUND: QColor("#ECF0F1"),    # Light Grey (Almost White)
    ColorRole.FOREGROUND_DIM: QColor("#BDC3C7"),# Silver
    ColorRole.FOREGROUND_DISABLED: QColor("#7F8C8D"), # Grey

    ColorRole.BORDER: QColor("#3D566E"),        # Desaturated Blue
    ColorRole.BORDER_LIGHT: QColor("#4A6581"),  # Lighter Border
    ColorRole.BORDER_DARK: QColor("#2B3C4D"),   # Darker Border

    ColorRole.SHADOW: QColor(0, 0, 0, 150),     # Black with opacity (for shadows)

    ColorRole.HIGHLIGHT: QColor("#4A90E2"),     # Blue (same as primary)
    ColorRole.HIGHLIGHTED_TEXT: QColor("#FFFFFF"), # White

    ColorRole.TOOLTIP_BG: QColor("#333333"),    # Dark Grey
    ColorRole.TOOLTIP_FG: QColor("#FFFFFF"),    # White
}

LIGHT_PALETTE: Dict[ColorRole, QColor] = {
    ColorRole.PRIMARY: QColor("#1E88E5"),       # Blue 600
    ColorRole.SECONDARY: QColor("#00BFA5"),     # Teal A700
    ColorRole.SUCCESS: QColor("#64DD17"),       # Light Green A700
    ColorRole.WARNING: QColor("#FFB300"),       # Amber 600
    ColorRole.ERROR: QColor("#E53935"),         # Red 600
    ColorRole.INFO: QColor("#1E88E5"),          # Blue 600 (same as primary)

    ColorRole.BACKGROUND: QColor("#F5F5F5"),    # Grey 100
    ColorRole.BACKGROUND_ALT: QColor("#E0E0E0"),# Grey 300
    ColorRole.BACKGROUND_HOVER: QColor("#D6D6D6"), # Hovered background
    ColorRole.BACKGROUND_PRESSED: QColor("#CDCDCD"), # Pressed background

    ColorRole.FOREGROUND: QColor("#212121"),    # Grey 900 (Dark Grey)
    ColorRole.FOREGROUND_DIM: QColor("#757575"),# Grey 600
    ColorRole.FOREGROUND_DISABLED: QColor("#BDBDBD"), # Grey 400

    ColorRole.BORDER: QColor("#BDBDBD"),        # Grey 400
    ColorRole.BORDER_LIGHT: QColor("#E0E0E0"),  # Grey 300
    ColorRole.BORDER_DARK: QColor("#757575"),   # Grey 600

    ColorRole.SHADOW: QColor(0, 0, 0, 50),      # Black with lower opacity

    ColorRole.HIGHLIGHT: QColor("#1E88E5"),     # Blue 600 (same as primary)
    ColorRole.HIGHLIGHTED_TEXT: QColor("#FFFFFF"), # White

    ColorRole.TOOLTIP_BG: QColor("#424242"),    # Grey 800
    ColorRole.TOOLTIP_FG: QColor("#FFFFFF"),    # White
}

# ==============================================================================
# LAYOUT & DIMENSIONS
# ==============================================================================

class Spacing:
    """Consistent spacing values."""
    XXS = 2
    XS = 4
    S = 8
    M = 12
    L = 16
    XL = 24
    XXL = 32


class Dimensions:
    """Consistent dimension values."""
    BUTTON_HEIGHT = 36
    INPUT_HEIGHT = 36 # For QLineEdit, QComboBox, QSpinBox etc.
    TEXT_EDIT_HEIGHT_SM = 60 # Smaller height for single-line like text edits
    TEXT_EDIT_HEIGHT_MD = 100 # Medium height for multi-line text edits
    TEXT_EDIT_HEIGHT_LG = 150 # Larger height for multi-line text edits

    ICON_SIZE_SMALL = QSize(16, 16)
    ICON_SIZE_MEDIUM = QSize(24, 24)
    ICON_SIZE_LARGE = QSize(32, 32)
    ICON_SIZE_XL = QSize(48, 48)

    BORDER_RADIUS_S = 4 # Small radius
    BORDER_RADIUS_M = 8 # Medium radius
    BORDER_RADIUS_L = 12 # Large radius

    SHADOW_BLUR_RADIUS = 10
    SHADOW_OFFSET = QPoint(0, 2)

    DIALOG_MIN_WIDTH = 400
    DIALOG_MIN_HEIGHT = 300
    MAIN_WINDOW_MIN_WIDTH = 800 # Increased minimum width for better layout
    MAIN_WINDOW_MIN_HEIGHT = 600 # Increased minimum height


# ==============================================================================
# TYPOGRAPHY
# ==============================================================================

class Typography:
    """Manages fonts and text styles."""

    class FontWeight:
        """Standard font weight values."""
        THIN = 100
        EXTRA_LIGHT = 200
        LIGHT = 300
        NORMAL = 400 # Regular
        MEDIUM = 500
        DEMI_BOLD = 600 # Semi-Bold
        BOLD = 700
        EXTRA_BOLD = 800 # Heavy
        BLACK = 900

    # Define font sizes (relative scale)
    FONT_SIZES: Dict[str, int] = {
        "XXS": 8,
        "XS": 10,
        "S": 12,
        "M": 14, # Default size
        "L": 16,
        "XL": 20,
        "XXL": 24,
        "XXXL": 32,
    }

    def __init__(self):
        # Add application-specific fonts here if needed
        # QFontDatabase.addApplicationFont(...)
        pass

    def get_font(self, size_scale: str = "M", weight: Optional[int] = None, monospace: bool = False) -> QFont:
        """
        Get a font with specified size scale, weight, and monospace preference.

        Args:
            size_scale: Key from FONT_SIZES dict (e.g., "M", "L").
            weight: Font weight (e.g., QFont.Weight.Bold). Defaults to QFont.Weight.Normal.
            monospace: If True, return a monospace font.

        Returns:
            QFont object.
        """
        font = QFont("Segoe UI" if platform.system() == "Windows" else "Roboto" if platform.system() == "Linux" else "Helvetica Neue") # Use common system fonts or preferred
        if monospace:
             font = QFont("Courier New" if platform.system() == "Windows" else "Liberation Mono" if platform.system() == "Linux" else "Menlo") # Use common monospace fonts

        font.setPointSize(self.FONT_SIZES.get(size_scale, self.FONT_SIZES["M"])) # Default to Medium size
        font.setWeight(weight if weight is not None else self.FontWeight.NORMAL)

        return font

typography = Typography() # Initialize typography manager


# ==============================================================================
# ICONS
# ==============================================================================

class IconSet:
    """Defines standard application icons using qtawesome."""

    # Application Icon (used for window title bar, taskbar, system tray)
    # Replace with your actual application icon file path or qtawesome name
    APP_ICON = "fa5s.youtube" # Example using Font Awesome YouTube icon
    SPLASH_ICON = "fa5s.youtube" # Example, often the same as APP_ICON

    # General Actions
    ICON_ADD = "fa5s.plus-circle"
    ICON_REMOVE = "fa5s.minus-circle"
    ICON_DELETE = "fa5s.trash-alt" # Added delete icon
    ICON_EDIT = "fa5s.edit"
    ICON_SAVE = "fa5s.save"
    ICON_OPEN = "fa5s.folder-open" # For opening files/directories
    ICON_SETTINGS = "fa5s.cog"
    ICON_SEARCH = "fa5s.search"
    ICON_DOWNLOAD = "fa5s.download"
    ICON_UPLOAD = "fa5s.upload"
    ICON_PLAY = "fa5s.play-circle"
    ICON_PAUSE = "fa5s.pause-circle"
    ICON_STOP = "fa5s.stop-circle"
    ICON_CANCEL = "fa5s.times-circle" # Close/Cancel icon
    ICON_REFRESH = "fa5s.sync-alt" # Refresh/Retry icon
    ICON_INFO = "fa5s.info-circle"
    ICON_WARNING = "fa5s.exclamation-triangle"
    ICON_ERROR = "fa5s.times-circle" # Using cancel icon for error status
    ICON_SUCCESS = "fa5s.check-circle"
    ICON_BROWSE = "fa5s.folder-open" # Same as open
    ICON_CLIPBOARD = "fa5s.clipboard"
    ICON_EXIT = "fa5s.sign-out-alt" # Added exit icon

    # File/Data Types
    ICON_FILE = "fa5s.file"
    ICON_FOLDER = "fa5s.folder"
    ICON_AUDIO = "fa5s.volume-up"
    ICON_VIDEO = "fa5s.video"
    ICON_TEXT = "fa5s.file-alt"
    ICON_SRT = "fa5s.file-alt" # Using text file icon for SRT
    ICON_JSON = "fa5s.file-code" # Using code file icon for JSON
    ICON_VTT = "fa5s.file-alt" # Using text file icon for VTT

    # Status Indicators (used in TaskListItem)
    ICON_STATUS_PENDING = "fa5s.clock"
    ICON_STATUS_RUNNING = "fa5s.circle-notch" # Spinner icon
    ICON_STATUS_COMPLETED = "fa5s.check-circle"
    ICON_STATUS_FAILED = "fa5s.times-circle"
    ICON_STATUS_CANCELLED = "fa5s.times-circle"
    ICON_STATUS_SKIPPED = "fa5s.forward" # Fast forward icon
    ICON_STATUS_PAUSED = "fa5s.pause-circle"
    ICON_STATUS_RETRYING = "fa5s.sync-alt"
    ICON_STATUS_VALIDATING = "fa5s.search"
    ICON_STATUS_DOWNLOADING = "fa5s.download"
    ICON_STATUS_CONVERTING = "fa5s.exchange-alt" # Exchange icon
    ICON_STATUS_TRANSCRIBING = "fa5s.microphone-alt"
    ICON_STATUS_TRANSLATING = "fa5s.language"
    ICON_STATUS_EXPORTING = "fa5s.file-export"
    ICON_STATUS_CACHED = "fa5s.database" # Database/Cache icon


    @staticmethod
    def get_icon(name: str, color: Optional[QColor] = None) -> QIcon:
        """
        Get an icon by name, optionally with a specific color.
        Uses qtawesome for icon rendering.
        """
        try:
            # qtawesome uses color names or hex codes
            color_str = color.name() if color else None
            return qta.icon(name, color=color_str)
        except Exception as e:
            logger.warning(f"Failed to load icon '{name}': {e}. Returning empty icon.")
            return QIcon() # Return empty icon on failure


    @staticmethod
    def get_pixmap(name: str, size: QSize, color: Optional[QColor] = None) -> QPixmap:
        """
        Get an icon as a QPixmap by name, size, and optional color.
        Uses qtawesome for icon rendering.
        """
        try:
            color_str = color.name() if color else None
            return qta.pixmap(name, options=[{'color': color_str}]) if color_str else qta.pixmap(name)
        except Exception as e:
            logger.warning(f"Failed to load pixmap for icon '{name}': {e}. Returning empty pixmap.")
            return QPixmap(size) # Return empty pixmap on failure


# ==============================================================================
# ANIMATIONS
# ==============================================================================

class AnimationPresets:
    """Pre-defined animation configurations."""

    DURATION_XXS = 50
    DURATION_XS = 100
    DURATION_S = 150
    DURATION_M = 250 # Medium duration for general animations
    DURATION_L = 400
    DURATION_XL = 600

    EASE_IN = QEasingCurve.Type.InQuad
    EASE_OUT = QEasingCurve.Type.OutQuad
    EASE_IN_OUT = QEasingCurve.Type.InOutQuad
    LINEAR = QEasingCurve.Type.Linear


    @staticmethod
    def fade_in(widget: QWidget, duration: int = DURATION_M) -> QPropertyAnimation:
        """Create a fade-in animation for a widget."""
        return AnimationPresets._create_fade_animation(widget, 0.0, 1.0, duration)

    @staticmethod
    def fade_out(widget: QWidget, duration: int = DURATION_M) -> QPropertyAnimation:
        """Create a fade-out animation for a widget."""
        return AnimationPresets._create_fade_animation(widget, 1.0, 0.0, duration)

    @staticmethod
    def _create_fade_animation(widget: QWidget, start_value: float, end_value: float, duration: int) -> QPropertyAnimation:
        """Internal helper to create a fade animation."""
        # Create opacity effect if it doesn't exist
        opacity_effect = widget.graphicsEffect()
        if not opacity_effect or not isinstance(opacity_effect, QGraphicsOpacityEffect):
            opacity_effect = QGraphicsOpacityEffect(widget)
            opacity_effect.setOpacity(start_value) # Set initial opacity
            widget.setGraphicsEffect(opacity_effect)
            # Ensure the effect is enabled
            opacity_effect.setEnabled(True)

        # Create animation
        animation = QPropertyAnimation(opacity_effect, b"opacity")
        animation.setDuration(duration)
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(AnimationPresets.EASE_OUT if start_value < end_value else AnimationPresets.EASE_IN)

        # Ensure the widget is visible before fading in and hidden after fading out
        if start_value == 0.0 and end_value == 1.0: # Fade in
             animation.finished.connect(lambda: widget.setVisible(True)) # Ensure visible after
             widget.setVisible(True) # Make visible to start animation
        elif start_value == 1.0 and end_value == 0.0: # Fade out
             animation.finished.connect(lambda: widget.setVisible(False)) # Hide after animation


        return animation


# ==============================================================================
# STYLE MANAGER CLASS
# ==============================================================================

class StyleManager:
    """
    Manages the application's visual style, themes, and provides style helpers.
    """

    def __init__(self, is_dark_theme: bool = True):
        """
        Initialize the Style Manager.

        Args:
            is_dark_theme: True for dark theme, False for light theme.
        """
        self._is_dark_theme = is_dark_theme
        self._current_palette = DARK_PALETTE if is_dark_theme else LIGHT_PALETTE
        self._app_stylesheet = "" # Store the generated stylesheet

        self._generate_stylesheet() # Generate initial stylesheet


    def set_theme(self, theme_name: str):
        """Set the application theme ('dark' or 'light')."""
        is_dark = theme_name.lower() == "dark"
        if self._is_dark_theme != is_dark:
            self._is_dark_theme = is_dark
            self._current_palette = DARK_PALETTE if self._is_dark_theme else LIGHT_PALETTE
            self._generate_stylesheet() # Regenerate stylesheet
            # Apply the new stylesheet to the application instance if available
            app = QCoreApplication.instance()
            if isinstance(app, QApplication):
                 self.apply_global_style(app, theme_name)
            logger.info(f"Theme set to: {theme_name}")


    def get_color(self, role: ColorRole) -> QColor:
        """Get the color for a specific role in the current theme."""
        return self._current_palette.get(role, QColor(Qt.GlobalColor.black)) # Default to black if role not found


    def _generate_stylesheet(self):
        """Generate the QSS stylesheet based on the current palette and constants."""
        # This is where you define the look and feel of your widgets using QSS.
        # Use the colors from self._current_palette and constants from Spacing/Dimensions.

        palette = self._current_palette
        fg_color = palette[ColorRole.FOREGROUND].name()
        bg_color = palette[ColorRole.BACKGROUND].name()
        alt_bg_color = palette[ColorRole.BACKGROUND_ALT].name()
        primary_color = palette[ColorRole.PRIMARY].name()
        secondary_color = palette[ColorRole.SECONDARY].name()
        border_color = palette[ColorRole.BORDER].name()
        error_color = palette[ColorRole.ERROR].name()
        success_color = palette[ColorRole.SUCCESS].name()
        warning_color = palette[ColorRole.WARNING].name()
        disabled_fg_color = palette[ColorRole.FOREGROUND_DISABLED].name()
        disabled_bg_color = palette[ColorRole.BACKGROUND].name() # Use background for disabled bg
        highlight_color = palette[ColorRole.HIGHLIGHT].name()
        highlighted_text_color = palette[ColorRole.HIGHLIGHTED_TEXT].name()
        border_radius_s = Dimensions.BORDER_RADIUS_S
        border_radius_m = Dimensions.BORDER_RADIUS_M
        border_radius_l = Dimensions.BORDER_RADIUS_L
        spacing_s = Spacing.S
        spacing_m = Spacing.M
        spacing_l = Spacing.L


        stylesheet = f"""
        /* General Styles */
        QWidget {{
            color: {fg_color};
            background-color: {bg_color};
            font-family: "{typography.get_font().family()}";
            font-size: {typography.FONT_SIZES['M']}pt;
        }}

        QMainWindow {{
            background-color: {bg_color};
        }}

        QFrame {{
            border: none;
        }}

        /* Headings */
        QLabel#heading {{ /* Assuming objectName is set to 'heading' */
            font-size: {typography.FONT_SIZES['XL']}pt;
            font-weight: {typography.FontWeight.BOLD};
            margin-bottom: {Spacing.M}px;
        }}
         QLabel#subheading {{ /* Assuming objectName is set to 'subheading' */
            font-size: {typography.FONT_SIZES['L']}pt;
            font-weight: {typography.FontWeight.BOLD};
            margin-bottom: {Spacing.S}px;
        }}


        /* Buttons */
        QPushButton {{
            background-color: {primary_color};
            color: {highlighted_text_color}; /* Use highlighted text color for button text */
            border: none;
            padding: {Spacing.S}px {Spacing.M}px;
            border-radius: {border_radius_s}px;
            min-height: {Dimensions.BUTTON_HEIGHT - 2*Spacing.S}px; /* Account for padding */
        }}
        QPushButton:hover {{
            background-color: {palette[ColorRole.BACKGROUND_HOVER].name()}; /* Use a background hover color */
        }}
        QPushButton:pressed {{
            background-color: {palette[ColorRole.BACKGROUND_PRESSED].name()}; /* Use a background pressed color */
        }}
        QPushButton:disabled {{
            background-color: {palette[ColorRole.BACKGROUND_ALT].name()}; /* Use alt background for disabled */
            color: {disabled_fg_color};
        }}

        /* Flat Buttons (e.g., icon buttons) */
        QPushButton[is_flat="true"] {{ /* Assuming dynamic property 'is_flat' */
            background-color: transparent;
            border: none;
            padding: {Spacing.XS}px; /* Smaller padding for icon buttons */
        }}
         QPushButton[is_flat="true"]:hover {{
            background-color: {palette[ColorRole.BACKGROUND_HOVER].name()};
         }}
         QPushButton[is_flat="true"]:pressed {{
            background-color: {palette[ColorRole.BACKGROUND_PRESSED].name()};
         }}
         QPushButton[is_flat="true"]:disabled {{
            background-color: transparent;
            color: {disabled_fg_color};
         }}


        /* Primary Buttons (default style) */
        QPushButton[is_primary="true"] {{ /* Assuming dynamic property 'is_primary' */
            background-color: {primary_color};
            color: {highlighted_text_color};
        }}
         QPushButton[is_primary="true"]:hover {{
            background-color: {palette[ColorRole.PRIMARY].darker(120).name()}; /* Slightly darker primary on hover */
         }}
         QPushButton[is_primary="true"]:pressed {{
            background-color: {palette[ColorRole.PRIMARY].darker(150).name()}; /* Even darker on pressed */
         }}
         QPushButton[is_primary="true"]:disabled {{
            background-color: {palette[ColorRole.BACKGROUND_ALT].name()};
            color: {disabled_fg_color};
         }}


        /* Danger Buttons (e.g., Cancel, Delete) */
        QPushButton[is_danger="true"] {{ /* Assuming dynamic property 'is_danger' */
            background-color: {error_color};
            color: {highlighted_text_color};
        }}
        QPushButton[is_danger="true"]:hover {{
            background-color: {palette[ColorRole.ERROR].darker(120).name()};
        }}
        QPushButton[is_danger="true"]:pressed {{
            background-color: {palette[ColorRole.ERROR].darker(150).name()};
        }}
        QPushButton[is_danger="true"]:disabled {{
            background-color: {palette[ColorRole.BACKGROUND_ALT].name()};
            color: {disabled_fg_color};
        }}


        /* Input Fields (QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox) */
        QLineEdit, QTextEdit, QComboBox, QAbstractSpinBox {{
            background-color: {alt_bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius_s}px;
            padding: {Spacing.XS}px;
            selection-background-color: {highlight_color};
            selection-color: {highlighted_text_color};
            min-height: {Dimensions.INPUT_HEIGHT - 2*Spacing.XS - 2}px; /* Account for padding and border */
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QAbstractSpinBox:focus {{
            border-color: {primary_color};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QAbstractSpinBox:disabled {{
             background-color: {bg_color};
             color: {disabled_fg_color};
             border-color: {palette[ColorRole.BORDER_LIGHT].name()};
        }}

        QTextEdit {{
             min-height: {Dimensions.TEXT_EDIT_HEIGHT_MD}px; /* Default height for multiline */
        }}


        QComboBox::drop-down {{
            border: none;
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px; /* Adjust width as needed */
        }}
        QComboBox::down-arrow {{
            image: url(data:image/png;base64,...); /* Placeholder for down arrow icon */
            /* You would typically use a themed SVG or font icon here */
        }}

        QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
            border: 1px solid {border_color};
            background-color: {alt_bg_color};
            border-radius: {border_radius_s / 2}px; /* Smaller radius for spinbox buttons */
            width: 16px; /* Adjust width */
            padding: 0px; /* No padding */
        }}
        QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{
            background-color: {palette[ColorRole.BACKGROUND_HOVER].name()};
        }}
        QAbstractSpinBox::up-button:pressed, QAbstractSpinBox::down-button:pressed {{
            background-color: {palette[ColorRole.BACKGROUND_PRESSED].name()};
        }}
        QAbstractSpinBox::up-arrow {{
             image: url(data:image/png;base64,...); /* Placeholder for up arrow icon */
        }}
         QAbstractSpinBox::down-arrow {{
             image: url(data:image/png;base64,...); /* Placeholder for down arrow icon */
         }}


        /* Checkboxes and Radio Buttons */
        QCheckBox, QRadioButton {{
            spacing: {Spacing.XS}px;
            color: {fg_color};
        }}
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 16px;
            height: 16px;
        }}
        QCheckBox::indicator:unchecked {{
             image: url(data:image/png;base64,...); /* Placeholder for unchecked checkbox */
        }}
        QCheckBox::indicator:checked {{
             image: url(data:image/png;base64,...); /* Placeholder for checked checkbox */
        }}
        QRadioButton::indicator:unchecked {{
             image: url(data:image/png;base64,...); /* Placeholder for unchecked radio */
        }}
        QRadioButton::indicator:checked {{
             image: url(data:image/png;base64,...); /* Placeholder for checked radio */
        }}
        QCheckBox:disabled, QRadioButton:disabled {{
             color: {disabled_fg_color};
        }}
        QCheckBox::indicator:disabled, QRadioButton::indicator:disabled {{
             opacity: 0.5; /* Dim indicator when disabled */
        }}


        /* Progress Bar */
        QProgressBar {{
            border: 1px solid {border_color};
            border-radius: {border_radius_s}px;
            text-align: center;
            background-color: {alt_bg_color};
            color: {fg_color}; /* Text color */
        }}
        QProgressBar::chunk {{
            background-color: {primary_color};
            border-radius: {border_radius_s - 1}px; /* Slightly smaller radius than container */
        }}

        /* Progress Bar for Error State */
        QProgressBar[is_error="true"]::chunk {{ /* Assuming dynamic property 'is_error' */
             background-color: {error_color};
        }}

        /* Progress Bar for Success State */
        QProgressBar[is_success="true"]::chunk {{ /* Assuming dynamic property 'is_success' */
             background-color: {success_color};
        }}


        /* Scroll Area */
        QScrollArea {{
            border: 1px solid {border_color};
            border-radius: {border_radius_s}px;
        }}

        /* Scroll Bar */
        QScrollBar:vertical, QScrollBar:horizontal {{
            border: none;
            background: {alt_bg_color};
            width: 12px; /* Adjust width for vertical */
            height: 12px; /* Adjust height for horizontal */
            margin: {border_radius_s}px; /* Margin to create rounded corners */
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {palette[ColorRole.FOREGROUND_DIM].name()}; /* Handle color */
            border-radius: {border_radius_s / 2}px;
            min-width: 20px; /* Minimum size for handle */
            min-height: 20px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            border: none;
            background: none;
        }}
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
        QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
            background: none;
        }}


        /* Tab Widget */
        QTabWidget::pane {{
            border: 1px solid {border_color};
            border-top-left-radius: 0px;
            border-top-right-radius: 0px;
            border-bottom-left-radius: {border_radius_s}px;
            border-bottom-right-radius: {border_radius_s}px;
            margin-top: -1px; /* Overlap with tab bar border */
        }}
        QTabBar::tab {{
            background: {alt_bg_color};
            border: 1px solid {border_color};
            border-bottom: none; /* No bottom border */
            border-top-left-radius: {border_radius_s}px;
            border-top-right-radius: {border_radius_s}px;
            padding: {Spacing.S}px {Spacing.M}px;
            margin-right: 1px; /* Space between tabs */
        }}
        QTabBar::tab:selected {{
            background: {bg_color}; /* Use main background for selected tab */
            border-bottom: 1px solid {bg_color}; /* Hide bottom border with background color */
        }}
        QTabBar::tab:hover {{
            background: {palette[ColorRole.BACKGROUND_HOVER].name()};
        }}


        /* Card Style (for QFrame or QWidget used as cards) */
        QFrame[is_card="true"], QWidget[is_card="true"] {{ /* Assuming dynamic property 'is_card' */
            background-color: {alt_bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius_m}px;
            padding: {Spacing.M}px;
            /* Add shadow effect via code */
        }}

        /* Task List Item Style (inherits from card) */
        QFrame[is_task_item="true"] {{ /* Assuming dynamic property 'is_task_item' */
            background-color: {bg_color}; /* Use main background for list items */
            border: 1px solid {palette[ColorRole.BORDER_LIGHT].name()}; /* Lighter border */
            border-radius: {border_radius_s}px; /* Smaller radius */
            padding: {Spacing.S}px; /* Smaller padding */
            margin-bottom: {Spacing.XS}px; /* Space between items */
        }}
         QFrame[is_task_item="true"]:hover {{
            background-color: {palette[ColorRole.BACKGROUND_HOVER].name()};
         }}


        /* Status Bar */
        QStatusBar {{
            background-color: {alt_bg_color};
            border-top: 1px solid {border_color};
            font-size: {typography.FONT_SIZES['S']}pt;
        }}
        QStatusBar QLabel {{
            padding: 0 {Spacing.S}px; /* Padding for labels in status bar */
        }}


        /* Menu Bar and Menus */
        QMenuBar {{
            background-color: {bg_color};
            color: {fg_color};
            border-bottom: 1px solid {border_color};
        }}
        QMenuBar::item {{
            padding: {Spacing.XS}px {Spacing.S}px;
            background: transparent;
        }}
        QMenuBar::item:selected {{
            background: {highlight_color};
            color: {highlighted_text_color};
        }}
        QMenu {{
            background-color: {bg_color};
            color: {fg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius_s}px;
            padding: {Spacing.XS}px;
        }}
        QMenu::item {{
            padding: {Spacing.XS}px {Spacing.M}px;
            margin: 1px 0; /* Space between items */
            border-radius: {border_radius_s / 2}px; /* Smaller radius for menu items */
        }}
        QMenu::item:selected {{
            background: {highlight_color};
            color: {highlighted_text_color};
        }}
        QMenu::separator {{
            height: 1px;
            background: {border_color};
            margin: {Spacing.XS}px 0;
        }}


        /* Tooltip */
        QToolTip {{
            color: {palette[ColorRole.TOOLTIP_FG].name()};
            background-color: {palette[ColorRole.TOOLTIP_BG].name()};
            border: 1px solid {palette[ColorRole.BORDER_DARK].name()};
            border-radius: {border_radius_s}px;
            padding: {Spacing.S}px;
            opacity: 230; /* Semi-transparent */
        }}


        /* Table Widget (e.g., for Shortcut Config Dialog) */
        QTableWidget {{
            gridline-color: {border_color};
            background-color: {bg_color};
            border: 1px solid {border_color};
            border-radius: {border_radius_s}px;
            selection-background-color: {highlight_color};
            selection-color: {highlighted_text_color};
        }}
        QTableWidget QHeaderView::section {{
            background-color: {alt_bg_color};
            color: {fg_color};
            padding: {Spacing.S}px;
            border: 1px solid {border_color};
            border-left: none;
            border-top: none;
        }}
         QTableWidget QHeaderView::section:first {{
            border-left: 1px solid {border_color};
         }}

        QTableWidget::item {{
            padding: {Spacing.XS}px;
        }}
        QTableWidget::item:selected {{
            background-color: {highlight_color};
            color: {highlighted_text_color};
        }}


        /* Add more specific styles as needed for other widgets */

        """
        self._app_stylesheet = stylesheet
        logger.debug("Generated QSS stylesheet.")


    def get_app_stylesheet(self, theme_name: Optional[str] = None) -> str:
        """
        Get the generated QSS stylesheet for the current or specified theme.
        If theme_name is provided, regenerates the stylesheet for that theme first.
        """
        if theme_name and theme_name.lower() != ("dark" if self._is_dark_theme else "light"):
             self.set_theme(theme_name) # Regenerate for the specified theme

        return self._app_stylesheet


    def apply_global_style(self, app: QApplication, theme_name: str):
        """
        Apply global styling (stylesheet and palette) to the entire application.

        Args:
            app: QApplication instance.
            theme_name: The name of the theme to apply ('dark' or 'light').
        """
        self.set_theme(theme_name) # Set theme and regenerate stylesheet

        # Apply stylesheet
        app.setStyleSheet(self._app_stylesheet)

        # Apply QPalette (can help with native dialogs and consistency)
        palette = QPalette()
        current_palette_colors = self._current_palette
        palette.setColor(QPalette.ColorRole.Window, current_palette_colors[ColorRole.BACKGROUND])
        palette.setColor(QPalette.ColorRole.WindowText, current_palette_colors[ColorRole.FOREGROUND])
        palette.setColor(QPalette.ColorRole.Base, current_palette_colors[ColorRole.BACKGROUND_ALT])
        palette.setColor(QPalette.ColorRole.AlternateBase, current_palette_colors[ColorRole.BACKGROUND])
        palette.setColor(QPalette.ColorRole.ToolTipBase, current_palette_colors[ColorRole.TOOLTIP_BG])
        palette.setColor(QPalette.ColorRole.ToolTipText, current_palette_colors[ColorRole.TOOLTIP_FG])
        palette.setColor(QPalette.ColorRole.Text, current_palette_colors[ColorRole.FOREGROUND])
        palette.setColor(QPalette.ColorRole.Button, current_palette_colors[ColorRole.BACKGROUND_ALT])
        palette.setColor(QPalette.ColorRole.ButtonText, current_palette_colors[ColorRole.FOREGROUND])
        palette.setColor(QPalette.ColorRole.BrightText, current_palette_colors[ColorRole.PRIMARY]) # Example
        palette.setColor(QPalette.ColorRole.Link, current_palette_colors[ColorRole.PRIMARY])
        palette.setColor(QPalette.ColorRole.Highlight, current_palette_colors[ColorRole.HIGHLIGHT])
        palette.setColor(QPalette.ColorRole.HighlightedText, current_palette_colors[ColorRole.HIGHLIGHTED_TEXT])
        palette.setColor(QPalette.ColorRole.DisabledText, current_palette_colors[ColorRole.FOREGROUND_DISABLED])
        palette.setColor(QPalette.ColorRole.DisabledButtonBase, current_palette_colors[ColorRole.BACKGROUND_ALT]) # Use alt background for disabled buttons
        palette.setColor(QPalette.ColorRole.DisabledWindowText, current_palette_colors[ColorRole.FOREGROUND_DISABLED])
        palette.setColor(QPalette.ColorGroup.Active, QPalette.ColorRole.Text, current_palette_colors[ColorRole.FOREGROUND])
        palette.setColor(QPalette.ColorGroup.Inactive, QPalette.ColorRole.Text, current_palette_colors[ColorRole.FOREGROUND_DIM])
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, current_palette_colors[ColorRole.FOREGROUND_DISABLED])


        app.setPalette(palette)

        # Set fusion style for consistent look across platforms
        app.setStyle(QStyleFactory.create("Fusion"))
        logger.info("Global palette and Fusion style applied.")


    # --- Widget Styling Helpers ---

    def create_modern_button(self, text: str, parent: Optional[QWidget] = None, is_primary: bool = False, is_danger: bool = False, is_flat: bool = False, icon: Optional[QIcon] = None, icon_size: Optional[QSize] = None) -> QPushButton:
        """Create a QPushButton with modern styling."""
        button = QPushButton(text, parent)
        button.setFont(typography.get_font("M", typography.FontWeight.MEDIUM)) # Medium weight font

        # Set dynamic properties for QSS styling
        button.setProperty("is_primary", is_primary)
        button.setProperty("is_danger", is_danger)
        button.setProperty("is_flat", is_flat)

        # Set icon if provided
        if icon:
             button.setIcon(icon)
             button.setIconSize(icon_size if icon_size else Dimensions.ICON_SIZE_MEDIUM)

        # Apply base button style (handled by QSS based on properties)
        # button.setStyleSheet(self.get_button_style(is_primary, is_danger, is_flat)) # QSS is more efficient

        # Add shadow effect if not flat (optional, can be resource intensive)
        # if not is_flat:
        #      self.create_shadow_effect(button)

        return button

    def create_modern_heading(self, text: str, parent: Optional[QWidget] = None, is_subheading: bool = False) -> QLabel:
        """Create a QLabel with heading styling."""
        label = QLabel(text, parent)
        # Set objectName for QSS styling
        label.setObjectName("subheading" if is_subheading else "heading")
        # Font is set by QSS based on objectName
        # label.setFont(typography.get_font("XL" if not is_subheading else "L", typography.FontWeight.BOLD))
        return label


    def create_card_widget(self, parent: Optional[QWidget] = None) -> QFrame:
        """Create a QFrame with card styling."""
        frame = QFrame(parent)
        frame.setProperty("is_card", True) # Set dynamic property for QSS
        # Apply card style (handled by QSS)
        # self.apply_card_style(frame)
        # Add shadow effect (optional)
        # self.create_shadow_effect(frame)
        return frame


    def apply_card_style(self, widget: QWidget):
        """Apply card styling to an existing widget."""
        widget.setProperty("is_card", True)
        # Trigger style re-computation
        widget.style().polish(widget)
        # Add shadow effect (optional)
        # self.create_shadow_effect(widget)


    def apply_scrollable_style(self, widget: QWidget):
        """Apply scrollable area styling to an existing widget (e.g., QScrollArea)."""
        # QSS handles QScrollArea and QScrollBar styling directly
        # No need for a dynamic property here unless specific variations are needed.
        # widget.setStyleSheet(widget.styleSheet() + self.get_scrollable_style()) # Append QSS if needed


    def apply_task_item_style(self, widget: QWidget):
        """Apply task list item styling to an existing widget (e.g., QFrame)."""
        widget.setProperty("is_task_item", True) # Set dynamic property for QSS
        # Trigger style re-computation
        widget.style().polish(widget)


    def create_status_indicator(self, status_type: Enum, parent: Optional[QWidget] = None) -> QLabel:
        """
        Create a QLabel with an icon representing a status.

        Args:
            status_type: An Enum member representing the status (e.g., TaskStatus.COMPLETED).
            parent: The parent widget.

        Returns:
            QLabel with status icon.
        """
        label = QLabel(parent)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setFixedSize(Dimensions.ICON_SIZE_MEDIUM) # Fixed size for status icon

        # Set initial icon and color based on status type
        self.update_status_indicator(label, status_type)

        # Add a method to update the status dynamically
        def update_status(self, new_status_type: Enum):
             self.update_status_indicator(label, new_status_type)

        # Attach the update method to the label object
        label.update_status = update_status.__get__(self, label.__class__)

        return label


    def update_status_indicator(self, label: QLabel, status_type: Enum):
        """Update the icon and color of a status indicator label."""
        icon_name = ""
        icon_color = self.get_color(ColorRole.FOREGROUND_DIM) # Default dimmed color

        # Map status types to icons and colors
        if status_type == getattr(TaskStatus, 'PENDING', None):
             icon_name = IconSet.ICON_STATUS_PENDING
             icon_color = self.get_color(ColorRole.FOREGROUND_DIM)
        elif status_type == getattr(TaskStatus, 'RUNNING', None):
             icon_name = IconSet.ICON_STATUS_RUNNING
             icon_color = self.get_color(ColorRole.PRIMARY)
             # Optionally add a spinning animation via QPropertyAnimation or QSS
             # QSS example: animation: spin 2s linear infinite; @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        elif status_type == getattr(TaskStatus, 'COMPLETED', None):
             icon_name = IconSet.ICON_STATUS_COMPLETED
             icon_color = self.get_color(ColorRole.SUCCESS)
        elif status_type == getattr(TaskStatus, 'FAILED', None):
             icon_name = IconSet.ICON_STATUS_FAILED
             icon_color = self.get_color(ColorRole.ERROR)
        elif status_type == getattr(TaskStatus, 'CANCELLED', None):
             icon_name = IconSet.ICON_STATUS_CANCELLED
             icon_color = self.get_color(ColorRole.WARNING) # Use warning color for cancelled
        elif status_type == getattr(TaskStatus, 'SKIPPED', None):
             icon_name = IconSet.ICON_STATUS_SKIPPED
             icon_color = self.get_color(ColorRole.FOREGROUND_DIM) # Dimmed for skipped
        elif status_type == getattr(TaskStatus, 'PAUSED', None):
             icon_name = IconSet.ICON_STATUS_PAUSED
             icon_color = self.get_color(ColorRole.INFO) # Use info color for paused
        elif status_type == getattr(TaskStatus, 'RETRYING', None):
             icon_name = IconSet.ICON_STATUS_RETRYING
             icon_color = self.get_color(ColorRole.WARNING) # Warning color for retrying
        elif status_type == getattr(TaskStatus, 'VALIDATING', None):
             icon_name = IconSet.ICON_STATUS_VALIDATING
             icon_color = self.get_color(ColorRole.PRIMARY)
        elif status_type == getattr(TaskStatus, 'DOWNLOADING', None):
             icon_name = IconSet.ICON_STATUS_DOWNLOADING
             icon_color = self.get_color(ColorRole.PRIMARY)
        elif status_type == getattr(TaskStatus, 'CONVERTING', None):
             icon_name = IconSet.ICON_STATUS_CONVERTING
             icon_color = self.get_color(ColorRole.PRIMARY)
        elif status_type == getattr(TaskStatus, 'TRANSCRIBING', None):
             icon_name = IconSet.ICON_STATUS_TRANSCRIBING
             icon_color = self.get_color(ColorRole.PRIMARY)
        elif status_type == getattr(TaskStatus, 'TRANSLATING', None):
             icon_name = IconSet.ICON_STATUS_TRANSLATING
             icon_color = self.get_color(ColorRole.PRIMARY)
        elif status_type == getattr(TaskStatus, 'EXPORTING', None):
             icon_name = IconSet.ICON_STATUS_EXPORTING
             icon_color = self.get_color(ColorRole.PRIMARY)
        elif status_type == getattr(TaskStatus, 'CACHED', None):
             icon_name = IconSet.ICON_STATUS_CACHED
             icon_color = self.get_color(ColorRole.INFO) # Info color for cache hit


        # Use qtawesome to get the pixmap
        pixmap = IconSet.get_pixmap(icon_name, Dimensions.ICON_SIZE_MEDIUM, icon_color)
        label.setPixmap(pixmap)

        # Add spinning animation for running status using QPropertyAnimation
        # This needs to be managed carefully to avoid multiple animations on the same object.
        # A simpler approach is often pure QSS animation if possible.
        # If using QPropertyAnimation, store the animation object and stop/start it.
        if status_type == getattr(TaskStatus, 'RUNNING', None):
             # Check if a spinning animation already exists
             if not hasattr(label, '_spinning_animation') or label._spinning_animation is None:
                  # Create a graphics effect for rotation (QGraphicsRotation is in QtWidgets)
                  # Or, use QPropertyAnimation on the 'rotation' property if the widget supports it.
                  # QLabel doesn't have a 'rotation' property directly.
                  # A simpler way is to use QSS animation if the icon is part of the stylesheet.
                  # If the icon is set via setPixmap, QSS animation on the QLabel won't rotate the pixmap.
                  # For setPixmap, you'd need to manually update the pixmap with rotation in a timer,
                  # or use a QGraphicsScene/View, or rely on QSS if the icon is background/content.

                  # Let's stick to QSS animation on the label itself, assuming the icon is
                  # part of the label's visual representation that QSS can animate (less common for setPixmap).
                  # Or, if TaskListItem uses a custom paint method, it could draw the rotated icon.

                  # Alternative: Use QMovie for a simple loading spinner GIF (less flexible)

                  # Let's add a placeholder for a QPropertyAnimation approach, though QSS is preferred.
                  # Requires a QGraphicsRotation effect or similar.
                  # For simplicity, let's just rely on the icon change for now and maybe add QSS animation later.
                  pass # Placeholder for animation


        else:
             # Stop any running animation if status is not RUNNING
             if hasattr(label, '_spinning_animation') and label._spinning_animation is not None:
                  label._spinning_animation.stop()
                  label._spinning_animation = None # Clear reference


    # --- Shadow Effect Helper ---

    def create_shadow_effect(self, widget: QWidget, blur_radius: int = Dimensions.SHADOW_BLUR_RADIUS, offset: QPoint = Dimensions.SHADOW_OFFSET, color: Optional[QColor] = None) -> QGraphicsDropShadowEffect:
        """Create and apply a drop shadow effect to a widget."""
        if not color:
             color = self.get_color(ColorRole.SHADOW)

        shadow_effect = QGraphicsDropShadowEffect(widget)
        shadow_effect.setBlurRadius(blur_radius)
        shadow_effect.setOffset(offset)
        shadow_effect.setColor(color)

        widget.setGraphicsEffect(shadow_effect)
        return shadow_effect


    # --- QSS Snippets (can be used to build the main stylesheet) ---

    def get_button_style(self, is_primary: bool, is_danger: bool, is_flat: bool) -> str:
        """Get QSS snippet for a button based on properties."""
        # This method is less used now that QSS properties handle variations
        base_style = f"""
        QPushButton {{
            border: none;
            padding: {Spacing.S}px {Spacing.M}px;
            border-radius: {Dimensions.BORDER_RADIUS_S}px;
            min-height: {Dimensions.BUTTON_HEIGHT - 2*Spacing.S}px;
        }}
        QPushButton:hover {{
            background-color: {self.get_color(ColorRole.BACKGROUND_HOVER).name()};
        }}
        QPushButton:pressed {{
            background-color: {self.get_color(ColorRole.BACKGROUND_PRESSED).name()};
        }}
        QPushButton:disabled {{
            background-color: {self.get_color(ColorRole.BACKGROUND_ALT).name()};
            color: {self.get_color(ColorRole.FOREGROUND_DISABLED).name()};
        }}
        """

        if is_flat:
             return base_style + f"""
             QPushButton {{
                 background-color: transparent;
                 padding: {Spacing.XS}px;
             }}
             """
        elif is_danger:
             return base_style + f"""
             QPushButton {{
                 background-color: {self.get_color(ColorRole.ERROR).name()};
                 color: {self.get_color(ColorRole.HIGHLIGHTED_TEXT).name()};
             }}
             QPushButton:hover {{
                 background-color: {self.get_color(ColorRole.ERROR).darker(120).name()};
             }}
             QPushButton:pressed {{
                 background-color: {self.get_color(ColorRole.ERROR).darker(150).name()};
             }}
             """
        elif is_primary:
             return base_style + f"""
             QPushButton {{
                 background-color: {self.get_color(ColorRole.PRIMARY).name()};
                 color: {self.get_color(ColorRole.HIGHLIGHTED_TEXT).name()};
             }}
             QPushButton:hover {{
                 background-color: {self.get_color(ColorRole.PRIMARY).darker(120).name()};
             }}
             QPushButton:pressed {{
                 background-color: {self.get_color(ColorRole.PRIMARY).darker(150).name()};
             }}
             """
        else: # Default secondary style
             return base_style + f"""
             QPushButton {{
                 background-color: {self.get_color(ColorRole.SECONDARY).name()};
                 color: {self.get_color(ColorRole.HIGHLIGHTED_TEXT).name()};
             }}
             QPushButton:hover {{
                 background-color: {self.get_color(ColorRole.SECONDARY).darker(120).name()};
             }}
             QPushButton:pressed {{
                 background-color: {self.get_color(ColorRole.SECONDARY).darker(150).name()};
             }}
             """

    # Add other QSS snippet methods as needed (e.g., get_input_style, get_card_style)


# Initialize global style manager (default to dark theme)
style_manager = StyleManager(is_dark_theme=True)

# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     app = QApplication(sys.argv)

#     # Apply global style
#     style_manager.apply_global_style(app, "dark") # Or "light"

#     # Create some widgets to demonstrate styling
#     window = QMainWindow()
#     window.setWindowTitle("Style Demo")
#     window.setGeometry(100, 100, 600, 400)

#     central_widget = QWidget()
#     window.setCentralWidget(central_widget)
#     layout = QVBoxLayout(central_widget)
#     layout.setContentsMargins(Spacing.L, Spacing.L, Spacing.L, Spacing.L)
#     layout.setSpacing(Spacing.M)

#     # Headings
#     heading1 = style_manager.create_modern_heading("Main Application Heading")
#     heading2 = style_manager.create_modern_heading("Sub Heading", is_subheading=True)
#     layout.addWidget(heading1)
#     layout.addWidget(heading2)

#     # Buttons
#     button_layout = QHBoxLayout()
#     btn_primary = style_manager.create_modern_button("Primary Button", is_primary=True)
#     btn_secondary = style_manager.create_modern_button("Secondary Button") # Default
#     btn_danger = style_manager.create_modern_button("Danger Button", is_danger=True)
#     btn_flat = style_manager.create_modern_button("Flat Button", is_flat=True, icon=IconSet.get_icon(IconSet.ICON_SETTINGS))
#     button_layout.addWidget(btn_primary)
#     button_layout.addWidget(btn_secondary)
#     button_layout.addWidget(btn_danger)
#     button_layout.addWidget(btn_flat)
#     layout.addLayout(button_layout)

#     # Inputs
#     input_layout = QFormLayout()
#     line_edit = QLineEdit()
#     line_edit.setPlaceholderText("Enter text...")
#     combo_box = QComboBox()
#     combo_box.addItems(["Option 1", "Option 2", "Option 3"])
#     spin_box = QSpinBox()
#     spin_box.setRange(0, 100)
#     double_spin_box = QDoubleSpinBox()
#     double_spin_box.setRange(0.0, 10.0)
#     text_edit = QTextEdit()
#     text_edit.setPlaceholderText("Enter multi-line text...")
#     text_edit.setFixedHeight(Dimensions.TEXT_EDIT_HEIGHT_SM) # Example fixed height

#     input_layout.addRow("Line Edit:", line_edit)
#     input_layout.addRow("Combo Box:", combo_box)
#     input_layout.addRow("Spin Box:", spin_box)
#     input_layout.addRow("Double Spin Box:", double_spin_box)
#     input_layout.addRow("Text Edit:", text_edit)
#     layout.addLayout(input_layout)


#     # Checkboxes and Radio Buttons
#     checkbox_layout = QHBoxLayout()
#     checkbox1 = QCheckBox("Option A")
#     checkbox2 = QCheckBox("Option B")
#     radio1 = QRadioButton("Choice X")
#     radio2 = QRadioButton("Choice Y")
#     checkbox_layout.addWidget(checkbox1)
#     checkbox_layout.addWidget(checkbox2)
#     checkbox_layout.addWidget(radio1)
#     checkbox_layout.addWidget(radio2)
#     layout.addLayout(checkbox_layout)

#     # Progress Bar
#     progress_bar = QProgressBar()
#     progress_bar.setValue(50)
#     layout.addWidget(progress_bar)

#     # Card Example
#     card_frame = style_manager.create_card_widget()
#     card_layout = QVBoxLayout(card_frame)
#     card_layout.addWidget(QLabel("This is a card with some content."))
#     layout.addWidget(card_frame)


#     # Status Indicator Example (requires TaskStatus enum)
#     # Assuming TaskStatus is available globally or imported
#     # if 'TaskStatus' in globals():
#     #      status_label_pending = style_manager.create_status_indicator(TaskStatus.PENDING)
#     #      status_label_running = style_manager.create_status_indicator(TaskStatus.RUNNING)
#     #      status_label_completed = style_manager.create_status_indicator(TaskStatus.COMPLETED)
#     #      status_label_failed = style_manager.create_status_indicator(TaskStatus.FAILED)
#     #      status_layout = QHBoxLayout()
#     #      status_layout.addWidget(QLabel("Status Indicators:"))
#     #      status_layout.addWidget(status_label_pending)
#     #      status_layout.addWidget(status_label_running)
#     #      status_layout.addWidget(status_label_completed)
#     #      status_layout.addWidget(status_label_failed)
#     #      layout.addLayout(status_layout)


#     layout.addStretch(1) # Push everything to the top

#     window.show()
#     sys.exit(app.exec())
