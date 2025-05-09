"""
Right-to-Left (RTL) support utilities for YouTube Translator Pro.
Provides helper functions and classes for handling RTL languages.
"""

import logging
from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtCore import Qt, QLocale
from PyQt6.QtGui import QFontDatabase

from src.utils.localization import localization, get_string

# Set up logging
logger = logging.getLogger(__name__)

# List of RTL language codes
RTL_LANGUAGES = ["ar", "he", "fa", "ur"]

def is_rtl_language(language_code: str) -> bool:
    """
    Check if the language is a right-to-left language.
    
    Args:
        language_code: Language code to check
        
    Returns:
        True if the language is RTL, False otherwise
    """
    # Check if language is in known RTL languages
    if language_code in RTL_LANGUAGES:
        return True
    
    # Check if language direction is specified in localization data
    try:
        direction = get_string("language.direction", "ltr")
        return direction.lower() == "rtl"
    except:
        return False

def apply_rtl_to_application(app: QApplication, language_code: str) -> None:
    """
    Apply RTL layout to the entire application if needed.
    
    Args:
        app: QApplication instance
        language_code: Current language code
    """
    if is_rtl_language(language_code):
        logger.info(f"Applying RTL layout for language: {language_code}")
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Load and set appropriate fonts for RTL
        _load_rtl_fonts()
    else:
        logger.info(f"Applying LTR layout for language: {language_code}")
        app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

def apply_rtl_to_widget(widget: QWidget, language_code: str) -> None:
    """
    Apply RTL layout to a specific widget if needed.
    
    Args:
        widget: Widget to apply RTL layout to
        language_code: Current language code
    """
    if is_rtl_language(language_code):
        widget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    else:
        widget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)

def _load_rtl_fonts() -> None:
    """Load fonts suitable for RTL languages."""
    try:
        # Load system fonts that support Arabic and Hebrew
        # This ensures proper rendering of RTL text
        database = QFontDatabase()
        families = database.families()
        
        rtl_fonts = []
        preferred_fonts = ["Arial", "Tahoma", "Times New Roman", "Segoe UI"]
        
        # Find fonts that support Arabic script
        for family in families:
            for font in preferred_fonts:
                if font.lower() in family.lower():
                    rtl_fonts.append(family)
                    break
        
        if rtl_fonts:
            logger.info(f"Found suitable RTL fonts: {', '.join(rtl_fonts[:3])}")
        else:
            logger.warning("No suitable RTL fonts found, using system defaults")
    except Exception as e:
        logger.error(f"Error loading RTL fonts: {e}")
        
class RTLMixin:
    """
    Mixin class for RTL support in widgets.
    Add this to widget classes that need special RTL handling.
    """
    
    def update_layout_direction(self, language_code=None):
        """
        Update the layout direction based on current language.
        
        Args:
            language_code: Language code to use, defaults to current language
        """
        if not language_code:
            language_code = localization.current_language
            
        if is_rtl_language(language_code):
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self._on_rtl_applied()
        else:
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self._on_ltr_applied()
    
    def _on_rtl_applied(self):
        """
        Override this method for special RTL handling.
        Called when RTL layout is applied.
        """
        pass
    
    def _on_ltr_applied(self):
        """
        Override this method for special LTR handling.
        Called when LTR layout is applied.
        """
        pass
