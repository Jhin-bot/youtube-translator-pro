"""
Localization utilities for YouTube Translator Pro.
Supports multiple languages and dynamic language switching.
"""

import os
import json
import logging
import locale
import platform
from typing import Dict, Any, Optional, List
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class LocalizationManager:
    """
    Manages localization of strings throughout the application.
    Supports dynamic language switching and fallback to default language.
    """
    
    def __init__(self, default_language: str = "en", auto_detect: bool = True):
        """
        Initialize the localization manager.
        
        Args:
            default_language: Default language code
            auto_detect: Whether to auto-detect system language
        """
        self.default_language = default_language
        self.current_language = default_language
        self.strings: Dict[str, Dict[str, str]] = {}
        self.available_languages = {}
        
        # Load available languages
        self._load_languages()
        
        # Auto-detect system language if requested
        if auto_detect:
            detected_lang = self.detect_system_language()
            if detected_lang and detected_lang in self.available_languages:
                self.current_language = detected_lang
                logger.info(f"Auto-detected language: {detected_lang}")
            else:
                logger.info(f"Could not auto-detect supported language, using default: {default_language}")
    
    def _get_localization_dir(self) -> Path:
        """Get the localization directory path."""
        # Try to find localization directory
        base_path = Path(__file__).parent.parent.parent  # Go up to project root
        loc_dir = base_path / "localization"
        
        # Create directory if it doesn't exist
        if not loc_dir.exists():
            loc_dir.mkdir(parents=True)
            logger.info(f"Created localization directory: {loc_dir}")
            
            # Create default language file
            self._create_default_language_file(loc_dir)
        
        return loc_dir
    
    def _load_languages(self) -> None:
        """Load all available language files."""
        loc_dir = self._get_localization_dir()
        
        # Load all language files
        for file_path in loc_dir.glob("*.json"):
            lang_code = file_path.stem
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.strings[lang_code] = json.load(f)
                
                # Add to available languages
                self.available_languages[lang_code] = self.get_language_name(lang_code)
                logger.info(f"Loaded language: {lang_code} ({len(self.strings[lang_code])} strings)")
            except Exception as e:
                logger.error(f"Error loading language file {file_path}: {e}")
        
        # Make sure default language exists
        if self.default_language not in self.strings:
            logger.warning(f"Default language '{self.default_language}' not found, creating it")
            self._create_default_language_file(loc_dir)
    
    def _create_default_language_file(self, loc_dir: Path) -> None:
        """Create the default language file with English strings."""
        default_strings = {
            "app.name": "YouTube Translator Pro",
            "app.description": "Transcribe and translate YouTube videos",
            "menu.file": "File",
            "menu.edit": "Edit",
            "menu.help": "Help",
            "menu.file.open": "Open",
            "menu.file.save": "Save",
            "menu.file.exit": "Exit",
            "menu.edit.settings": "Settings",
            "menu.help.about": "About",
            "button.start": "Start",
            "button.pause": "Pause",
            "button.cancel": "Cancel",
            "button.settings": "Settings",
            "settings.title": "Settings",
            "settings.general": "General",
            "settings.transcription": "Transcription",
            "settings.translation": "Translation",
            "settings.output": "Output",
            "settings.save": "Save",
            "settings.cancel": "Cancel",
            "about.title": "About",
            "about.version": "Version",
            "about.license": "License",
            "about.author": "Author",
            "status.ready": "Ready",
            "status.working": "Working...",
            "status.completed": "Completed",
            "status.failed": "Failed",
            "error.title": "Error",
            "error.generic": "An error occurred",
            "error.network": "Network error",
            "error.invalid_url": "Invalid URL",
            "url.placeholder": "Enter YouTube URL(s) here",
            "url.button.paste": "Paste",
            "url.button.clear": "Clear",
            "language.english": "English",
            "language.spanish": "Spanish",
            "language.french": "French",
            "language.german": "German",
            "language.italian": "Italian",
            "language.portuguese": "Portuguese",
            "language.russian": "Russian",
            "language.japanese": "Japanese",
            "language.chinese": "Chinese",
            "language.korean": "Korean",
            "language.arabic": "Arabic",
            "performance.title": "Performance Monitor",
            "telemetry.title": "Telemetry Consent",
            "telemetry.message": "Would you like to help improve the application by sending anonymous usage data?",
            "telemetry.accept": "Accept",
            "telemetry.decline": "Decline"
        }
        
        self.strings[self.default_language] = default_strings
        self.available_languages[self.default_language] = "English"
        
        try:
            default_file = loc_dir / f"{self.default_language}.json"
            with open(default_file, "w", encoding="utf-8") as f:
                json.dump(default_strings, f, ensure_ascii=False, indent=4)
            logger.info(f"Created default language file: {default_file}")
        except Exception as e:
            logger.error(f"Error creating default language file: {e}")
    
    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.
        
        Args:
            language_code: Language code to set
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code not in self.strings:
            logger.warning(f"Language '{language_code}' not available")
            return False
        
        self.current_language = language_code
        logger.info(f"Language set to: {language_code}")
        return True
    
    def get_string(self, key: str, default: Optional[str] = None) -> str:
        """
        Get a localized string by key.
        
        Args:
            key: String identifier key
            default: Default value if key not found
            
        Returns:
            Localized string or default/key if not found
        """
        # Try current language
        if self.current_language in self.strings and key in self.strings[self.current_language]:
            return self.strings[self.current_language][key]
        
        # Try default language
        if self.default_language in self.strings and key in self.strings[self.default_language]:
            logger.debug(f"String '{key}' not found in {self.current_language}, using {self.default_language}")
            return self.strings[self.default_language][key]
        
        # Return default or key
        logger.debug(f"String '{key}' not found in any language")
        return default if default is not None else key
    
    def add_string(self, language_code: str, key: str, value: str) -> None:
        """
        Add or update a string for a specific language.
        
        Args:
            language_code: Language code
            key: String identifier key
            value: String value
        """
        if language_code not in self.strings:
            self.strings[language_code] = {}
            if language_code not in self.available_languages:
                self.available_languages[language_code] = language_code.upper()
                
        self.strings[language_code][key] = value
        
        # Save to file
        self._save_language_file(language_code)
    
    def _save_language_file(self, language_code: str) -> None:
        """Save a language file to disk."""
        if language_code not in self.strings:
            logger.error(f"Cannot save language {language_code}: not in strings dictionary")
            return
            
        loc_dir = self._get_localization_dir()
        file_path = loc_dir / f"{language_code}.json"
        
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.strings[language_code], f, ensure_ascii=False, indent=4)
            logger.info(f"Saved language file: {language_code}")
        except Exception as e:
            logger.error(f"Error saving language file {file_path}: {e}")
    
    def get_available_languages(self) -> Dict[str, str]:
        """
        Get a dictionary of available languages with their native names.
        
        Returns:
            Dictionary mapping language codes to their native names
        """
        return self.available_languages
    
    def get_language_name(self, language_code: str) -> str:
        """Get the native name of a language from its code."""
        # This is a simple mapping, could be expanded or loaded from a file
        language_names = {
            "en": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "it": "Italiano",
            "pt": "Português",
            "ru": "Русский",
            "ja": "日本語",
            "zh": "中文",
            "ko": "한국어",
            "ar": "العربية"
        }
        
        return language_names.get(language_code, language_code.upper())
        
    def detect_system_language(self) -> Optional[str]:
        """
        Detect the system language and return the corresponding language code.
        
        Returns:
            Language code (e.g., 'en', 'fr') or None if detection fails
        """
        try:
            # Get system locale
            if platform.system() == 'Windows':
                import ctypes
                windll = ctypes.windll.kernel32
                system_locale = locale.windows_locale[windll.GetUserDefaultUILanguage()]
            else:
                system_locale = locale.getdefaultlocale()[0]
                
            # Extract language code (first part before '_')
            if system_locale and '_' in system_locale:
                lang_code = system_locale.split('_')[0].lower()
                logger.info(f"Detected system language code: {lang_code}")
                return lang_code
            elif system_locale:
                logger.info(f"Detected system language code: {system_locale.lower()}")
                return system_locale.lower()
                
        except Exception as e:
            logger.warning(f"Failed to detect system language: {e}")
            
        return None

    def get_language_names(self) -> Dict[str, str]:
        """
        Get a dictionary of language names for all available languages.
        
        Returns:
            Dictionary mapping language codes to their native names
        """
        return {code: self.get_language_name(code) for code in self.available_languages}


# Create a global instance for use throughout the application
localization = LocalizationManager()

# Helper function for easier access
def get_string(key: str, default: Optional[str] = None) -> str:
    """
    Get a localized string by key.
    
    Args:
        key: String identifier key
        default: Default value if key not found
        
    Returns:
        Localized string
    """
    return localization.get_string(key, default)
