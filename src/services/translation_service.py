""""
Translation service for YouTube Translator Pro.
Handles the translation of transcription results into different languages.
""""

import time
import logging
import threading
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum, auto

# Import configuration
from src.config import TRANSLATION_LANGUAGES, DEFAULT_TRANSLATION_TIMEOUT

# Setup logger
logger = logging.getLogger(__name__)

class TranslationEngine(Enum):
    """Available translation engines."""
    MOCK = auto()       # Mock engine for testing/development
    GOOGLE = auto()     # Google Translate API
    DEEPL = auto()      # DeepL API
    LOCAL = auto()      # Local translation model


class TranslationService:
    """"
    Service for translating transcription results.
    Supports multiple translation engines and provides a unified interface.
    """"
    
    def __init__(self, engine: TranslationEngine = TranslationEngine.MOCK, api_key: Optional[str] = None):
        """"
        Initialize the translation service.
        
        Args:
            engine: The translation engine to use
            api_key: Optional API key for the selected engine
        """"
        self.engine = engine
        self.api_key = api_key
        self._initialize_engine()
        logger.info(f"Translation service initialized with {engine.name} engine")
    
    def _initialize_engine(self):
        """Initialize the selected translation engine."""
        if self.engine == TranslationEngine.MOCK:
            self.translator = MockTranslator()
        elif self.engine == TranslationEngine.GOOGLE:
            self.translator = GoogleTranslator(api_key=self.api_key)
        elif self.engine == TranslationEngine.DEEPL:
            self.translator = DeepLTranslator(api_key=self.api_key)
        elif self.engine == TranslationEngine.LOCAL:
            self.translator = LocalModelTranslator()
        else:
            logger.warning(f"Unsupported translation engine: {self.engine}. Falling back to mock translator.")
            self.translator = MockTranslator()
    
    def get_available_languages(self) -> Dict[str, str]:
        """"
        Get the available translation languages.
        
        Returns:
            Dictionary mapping language codes to language names
        """"
        return TRANSLATION_LANGUAGES.copy()
    
    def translate(
        self,
        transcription_result: Dict[str, Any],
        target_language: str,
        progress_callback: Optional[Callable[[float, str], None]] = None,
        stop_event: Optional[threading.Event] = None,
        timeout: Optional[float] = DEFAULT_TRANSLATION_TIMEOUT
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """"
        Translate a transcription result into a target language.
        
        Args:
            transcription_result: The transcription result dictionary to translate
            target_language: The target language code
            progress_callback: Optional callback function for progress updates
            stop_event: Optional event to signal cancellation
            timeout: Maximum time in seconds to wait for translation
            
        Returns:
            A tuple containing:
            - The translated transcription result dictionary if successful, None otherwise
            - An error message string if failed, None otherwise
        """"
        if not transcription_result or "segments" not in transcription_result:
            return None, "Invalid transcription result provided for translation."
        
        if not target_language or target_language == "None":
            logger.debug("No target language specified or 'None' selected. Skipping translation.")
            return transcription_result, None
        
        if target_language not in TRANSLATION_LANGUAGES:
            return None, f"Target language '{target_language}' is not supported."
        
        logger.info(f"Starting translation to '{target_language}' using {self.engine.name} engine")
        
        # Create a default stop event if none provided
        internal_stop_event = None
        if stop_event is None:
            internal_stop_event = threading.Event()
            stop_event = internal_stop_event
        
        start_time = time.time()
        
        # Extract the segments to translate
        segments = transcription_result.get("segments", [])
        total_segments = len(segments)
        
        if total_segments == 0:
            return None, "No segments found in transcription result."
        
        # Report initial progress
        if progress_callback:
            progress_callback(0.0, f"Starting translation to {TRANSLATION_LANGUAGES[target_language]}")
        
        # Process each segment
        translated_segments = []
        error_message = None
        
        for i, segment in enumerate(segments):
            # Check for stop event or timeout
            if stop_event.is_set():
                return None, "Translation cancelled."
            
            if timeout and (time.time() - start_time > timeout):
                return None, f"Translation timeout after {timeout} seconds."
            
            # Report progress
            progress = i / total_segments
            if progress_callback:
                progress_callback(progress, f"Translating segment {i+1}/{total_segments}")
            
            try:
                # Extract text to translate
                text = segment.get("text", "")
                
                # Translate the text
                translated_text, error = self.translator.translate_text(
                    text, 
                    target_language,
                    stop_event=stop_event
                )
                
                if error:
                    logger.warning(f"Error translating segment {i}: {error}")
                    error_message = f"Error translating segment {i}: {error}"
                    # Continue with next segment
                
                # Create a new segment with translated text
                translated_segment = segment.copy()
                translated_segment["text"] = translated_text or text  # Fall back to original if translation failed
                translated_segments.append(translated_segment)
                
            except Exception as e:
                logger.error(f"Exception translating segment {i}: {e}")
                # Create a copy with original text as fallback
                translated_segment = segment.copy()
                translated_segments.append(translated_segment)
                error_message = f"Error during translation: {e}"
        
        # Create the translated result
        translated_result = transcription_result.copy()
        translated_result["segments"] = translated_segments
        
        # Add metadata about translation
        if "metadata" not in translated_result:
            translated_result["metadata"] = {}
        translated_result["metadata"]["translated"] = True
        translated_result["metadata"]["target_language"] = target_language
        translated_result["metadata"]["translation_engine"] = self.engine.name
        
        # Report completion
        if progress_callback:
            progress_callback(1.0, "Translation complete")
        
        logger.info(f"Translation to {target_language} completed in {time.time() - start_time:.2f} seconds")
        
        return translated_result, error_message


# ===== Translator Implementations =====

class BaseTranslator:
    """Base translator interface."""
    
    def translate_text(
        self, 
        text: str, 
        target_language: str,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """"
        Translate text to the target language.
        
        Args:
            text: The text to translate
            target_language: The target language code
            stop_event: Optional event to signal cancellation
            
        Returns:
            A tuple containing:
            - The translated text if successful, None otherwise
            - An error message string if failed, None otherwise
        """"
        raise NotImplementedError("Subclasses must implement translate_text")


class MockTranslator(BaseTranslator):
    """Mock translator for testing and development."""
    
    def translate_text(
        self, 
        text: str, 
        target_language: str,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Mock translation that adds a language tag."""
        logger.debug(f"Mock translating to {target_language}: {text[:50]}...")
        
        if stop_event and stop_event.is_set():
            return None, "Translation cancelled."
        
        # Simulate processing time
        time.sleep(0.05)
        
        # Simple mock translation - just append language indicator
        translated_text = f"{text} [Translated to {target_language}]"
        
        return translated_text, None


class GoogleTranslator(BaseTranslator):
    """Google Translate API implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key."""
        self.api_key = api_key
        
        # Check if google-cloud-translate is available
        try:
            from google.cloud import translate_v2 as translate
            self.translate_client = translate.Client(api_key=api_key) if api_key else None
            self.google_translate_available = True
        except ImportError:
            self.google_translate_available = False
            logger.warning("Google Cloud Translate library not available.")
    
    def translate_text(
        self, 
        text: str, 
        target_language: str,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate using Google Translate API."""
        if not self.google_translate_available:
            return None, "Google Translate library not available."
        
        if not self.translate_client:
            return None, "Google Translate API key not configured."
        
        try:
            # Call the Google Translate API
            result = self.translate_client.translate(
                text,
                target_language=target_language
            )
            
            # Extract the translated text from the response
            translated_text = result.get('translatedText', text)
            
            return translated_text, None
            
        except Exception as e:
            logger.error(f"Google Translate API error: {e}")
            return None, f"Translation error: {e}"


class DeepLTranslator(BaseTranslator):
    """DeepL API implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with optional API key."""
        self.api_key = api_key
        
        try:
            import deepl
            self.deepl_client = deepl.Translator(api_key) if api_key else None
            self.deepl_available = True
        except ImportError:
            self.deepl_available = False
            logger.warning("DeepL library not available.")
    
    def translate_text(
        self, 
        text: str, 
        target_language: str,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate using DeepL API."""
        if not self.deepl_available:
            return None, "DeepL library not available."
        
        if not self.deepl_client:
            return None, "DeepL API key not configured."
        
        try:
            # Map target language codes to DeepL format if needed
            deepl_target_language = target_language.upper()
            if len(target_language) == 2:
                # Convert ISO 639-1 codes to DeepL format
                # This mapping may need to be expanded based on DeepL's supported languages'
                mapping = {
                    "en": "EN-US",  # Default to US English
                    "de": "DE",
                    "fr": "FR",
                    # Add more mappings as needed
                }
                deepl_target_language = mapping.get(target_language, f"{target_language.upper()}")
            
            # Call DeepL API
            result = self.deepl_client.translate_text(
                text,
                target_lang=deepl_target_language
            )
            
            return result.text, None
            
        except Exception as e:
            logger.error(f"DeepL API error: {e}")
            return None, f"Translation error: {e}"


class LocalModelTranslator(BaseTranslator):
    """Local machine learning model for translation."""
    
    def __init__(self):
        """Initialize the local model (placeholder)."""
        self.model = None
        self.local_translation_available = False
        logger.warning("Local translation model not implemented yet.")
    
    def translate_text(
        self, 
        text: str, 
        target_language: str,
        stop_event: Optional[threading.Event] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """Translate using a local model (placeholder)."""
        return None, "Local translation model not implemented."
