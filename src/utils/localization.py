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
        # Use the location relative to this file
        return Path(__file__).parent.parent / "resources" / "localization"
    
    def _load_languages(self) -> None:
        """Load all available language files."""
        loc_dir = self._get_localization_dir()
        
        # Try data directory if resources doesn't exist
        if not loc_dir.exists():
            alt_dir = Path(__file__).parent.parent.parent / "data" / "localization"
            if alt_dir.exists():
                loc_dir = alt_dir
                logger.info(f"Using alternate localization directory: {loc_dir}")
        
        # Create directory if it doesn't exist
        if not loc_dir.exists():
            logger.info(f"Creating localization directory: {loc_dir}")
            loc_dir.mkdir(parents=True, exist_ok=True)
            
            # Create default English language file if it doesn't exist
            self._create_default_language_file(loc_dir)
        
        # Load all language files
        for file_path in loc_dir.glob("*.json"):
            language_code = file_path.stem
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.strings[language_code] = data
                    
                    # Store language name if available
                    lang_name = data.get("language.name", language_code.upper())
                    self.available_languages[language_code] = lang_name
                    
                logger.info(f"Loaded language file: {language_code} ({lang_name})")
            except Exception as e:
                logger.error(f"Error loading language file {file_path}: {e}")
        
        # Make sure default language is available
        if self.default_language not in self.strings:
            logger.warning(f"Default language {self.default_language} not found. Creating it.")
            self._create_default_language_file(loc_dir)
            self.available_languages[self.default_language] = "English"
        
        logger.info(f"Available languages: {', '.join(self.available_languages.keys())}")
    
    def _create_default_language_file(self, loc_dir: Path) -> None:
        """Create the default language file with English strings."""
        english_strings = {
            "app.name": "YouTube Translator Pro",
            "app.description": "A professional tool for downloading, transcribing, and translating YouTube videos",
            
            # Common UI strings
            "ui.download": "Download",
            "ui.transcribe": "Transcribe",
            "ui.translate": "Translate",
            "ui.cancel": "Cancel",
            "ui.settings": "Settings",
            "ui.help": "Help",
            "ui.about": "About",
            "ui.language": "Language",
            "ui.dark_mode": "Dark Mode",
            "ui.light_mode": "Light Mode",
            
            # Main window
            "main.title": "YouTube Translator Pro",
            "main.enter_url": "Enter YouTube URL",
            "main.source_language": "Source Language",
            "main.target_language": "Target Language",
            "main.processing": "Processing...",
            "main.ready": "Ready",
            
            # Video information
            "video.title": "Title",
            "video.author": "Author",
            "video.duration": "Duration",
            "video.views": "Views",
            
            # Messages
            "message.downloading": "Downloading video...",
            "message.transcribing": "Transcribing audio...",
            "message.translating": "Translating text...",
            "message.complete": "Translation complete!",
            "message.error": "An error occurred",
            
            # Errors
            "error.invalid_url": "Invalid YouTube URL",
            "error.download_failed": "Failed to download video",
            "error.transcription_failed": "Failed to transcribe audio",
            "error.translation_failed": "Failed to translate text",
            
            # Settings
            "settings.title": "Settings",
            "settings.cache": "Cache Settings",
            "settings.cache_dir": "Cache Directory",
            "settings.max_cache_size": "Maximum Cache Size (MB)",
            "settings.clear_cache": "Clear Cache",
            "settings.transcription": "Transcription Settings",
            "settings.transcription_model": "Transcription Model",
            "settings.translation": "Translation Settings",
            "settings.translation_model": "Translation Model",
            
            # About
            "about.title": "About YouTube Translator Pro",
            "about.version": "Version",
            "about.description": "YouTube Translator Pro is a powerful tool for downloading, transcribing, and translating YouTube videos.",
            "about.copyright": "© 2025 YouTube Translator Pro",
        }
        
        # Save English strings
        en_file = loc_dir / "en.json"
        with open(en_file, "w", encoding="utf-8") as f:
            json.dump(english_strings, f, ensure_ascii=False, indent=4)
            
        # Add to loaded strings
        self.strings["en"] = english_strings
    
    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.
        
        Args:
            language_code: Language code to set
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code in self.available_languages:
            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
            return True
        else:
            logger.warning(f"Language {language_code} not available, using {self.current_language}")
            return False
    
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
        # Use the location relative to this file
        return Path(__file__).parent.parent / "resources" / "localization"
    
    def _load_languages(self) -> None:
        """Load all available language files."""
        loc_dir = self._get_localization_dir()
        
        # Try data directory if resources doesn't exist
        if not loc_dir.exists():
            alt_dir = Path(__file__).parent.parent.parent / "data" / "localization"
            if alt_dir.exists():
                loc_dir = alt_dir
                logger.info(f"Using alternate localization directory: {loc_dir}")
        
        # Create directory if it doesn't exist
        if not loc_dir.exists():
            logger.info(f"Creating localization directory: {loc_dir}")
            loc_dir.mkdir(parents=True, exist_ok=True)
            
            # Create default English language file if it doesn't exist
            self._create_default_language_file(loc_dir)
        
        # Load all language files
        for file_path in loc_dir.glob("*.json"):
            language_code = file_path.stem
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.strings[language_code] = data
                    
                    # Store language name if available
                    lang_name = data.get("language.name", language_code.upper())
                    self.available_languages[language_code] = lang_name
                    
                logger.info(f"Loaded language file: {language_code} ({lang_name})")
            except Exception as e:
                logger.error(f"Error loading language file {file_path}: {e}")
        
        # Make sure default language is available
        if self.default_language not in self.strings:
            logger.warning(f"Default language {self.default_language} not found. Creating it.")
            self._create_default_language_file(loc_dir)
            self.available_languages[self.default_language] = "English"
        
        logger.info(f"Available languages: {', '.join(self.available_languages.keys())}")
    
    def _create_default_language_file(self, loc_dir: Path) -> None:
        """Create the default language file with English strings."""
        english_strings = {
            "app.name": "YouTube Translator Pro",
            "app.description": "A professional tool for downloading, transcribing, and translating YouTube videos",
            
            # Common UI strings
            "ui.download": "Download",
            "ui.transcribe": "Transcribe",
            "ui.translate": "Translate",
            "ui.cancel": "Cancel",
            "ui.settings": "Settings",
            "ui.help": "Help",
            "ui.about": "About",
            "ui.language": "Language",
            "ui.dark_mode": "Dark Mode",
            "ui.light_mode": "Light Mode",
            
            # Main window
            "main.title": "YouTube Translator Pro",
            "main.enter_url": "Enter YouTube URL",
            "main.source_language": "Source Language",
            "main.target_language": "Target Language",
            "main.processing": "Processing...",
            "main.ready": "Ready",
            
            # Video information
            "video.title": "Title",
            "video.author": "Author",
            "video.duration": "Duration",
            "video.views": "Views",
            
            # Messages
            "message.downloading": "Downloading video...",
            "message.transcribing": "Transcribing audio...",
            "message.translating": "Translating text...",
            "message.complete": "Translation complete!",
            "message.error": "An error occurred",
            
            # Errors
            "error.invalid_url": "Invalid YouTube URL",
            "error.download_failed": "Failed to download video",
            "error.transcription_failed": "Failed to transcribe audio",
            "error.translation_failed": "Failed to translate text",
            
            # Settings
            "settings.title": "Settings",
            "settings.cache": "Cache Settings",
            "settings.cache_dir": "Cache Directory",
            "settings.max_cache_size": "Maximum Cache Size (MB)",
            "settings.clear_cache": "Clear Cache",
            "settings.transcription": "Transcription Settings",
            "settings.transcription_model": "Transcription Model",
            "settings.translation": "Translation Settings",
            "settings.translation_model": "Translation Model",
            
            # About
            "about.title": "About YouTube Translator Pro",
            "about.version": "Version",
            "about.description": "YouTube Translator Pro is a powerful tool for downloading, transcribing, and translating YouTube videos.",
            "about.copyright": "© 2025 YouTube Translator Pro",
        }
        
        # Save English strings
        en_file = loc_dir / "en.json"
        with open(en_file, "w", encoding="utf-8") as f:
            json.dump(english_strings, f, ensure_ascii=False, indent=4)
            
        # Add to loaded strings
        self.strings["en"] = english_strings
    
    def set_language(self, language_code: str) -> bool:
        """
        Set the current language.
        
        Args:
            language_code: Language code to set
            
        Returns:
            True if language was set successfully, False otherwise
        """
        if language_code in self.available_languages:
            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
            return True
        else:
            logger.warning(f"Language {language_code} not available, using {self.current_language}")
            return False
    
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
                self.available_languages.append(language_code)
                
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
        language_names = {
            'en': 'English',
            'fr': 'Français',
            # Add more languages here...
        }
        result = {}
        for code in self.available_languages:
            if code in language_names:
                result[code] = language_names[code]
            else:
                result[code] = code
                
        return result

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
