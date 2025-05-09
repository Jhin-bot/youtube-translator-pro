""""
Core translation pipeline module that integrates all components of the translator.
""""

import os
import logging
from typing import Dict, Any, Optional, Tuple

from src.utils.youtube_utils import download_youtube_audio, extract_video_id
from src.utils.cache_manager import CacheManager
from src.services.transcription_service import transcribe_audio
from src.services.translation_service import translate_text
from src.utils.error_handling import TranslationError, YouTubeError, TranscriptionError

# Set up logging
logger = logging.getLogger(__name__)

def translate_youtube_video(
    url: str,
    source_language: str = "auto",
    target_language: str = "en",
    cache_manager: Optional[CacheManager] = None,
    output_dir: Optional[str] = None,
    use_cache: bool = True,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """"
    The main pipeline that processes a YouTube video through download, 
    transcription and translation.
    
    Args:
        url: YouTube video URL
        source_language: Source language for transcription
        target_language: Target language for translation
        cache_manager: CacheManager instance for caching
        output_dir: Directory to save output files
        use_cache: Whether to use cached results when available
        progress_callback: Optional callback for progress updates
    
    Returns:
        Dictionary with video info, transcription, and translation
    """"
    try:
        video_id = extract_video_id(url)
        
        # Initialize result dictionary
        result = {
            "video_id": video_id,
            "source_language": source_language,
            "target_language": target_language,
            "url": url
        }
        
        # Set default cache manager if None
        if cache_manager is None:
            cache_manager = CacheManager()
        
        # 1. Download audio (or use cached)
        audio_path = None
        video_info = None
        
        if use_cache:
            audio_path = cache_manager.get_cached_audio(video_id)
        
        if not audio_path:
            logger.info(f"Downloading audio for video {video_id}...")
            if progress_callback:
                progress_callback(0.1, "Downloading audio...")
                
            audio_path, video_info = download_youtube_audio(
                url=url,
                output_dir=output_dir or os.path.join(os.path.expanduser("~"), "youtube_translator"),
                progress_callback=lambda p, m: progress_callback(p * 0.4, m) if progress_callback else None
            )
            
            # Cache the downloaded audio
            if cache_manager.enabled:
                cache_manager.cache_audio(video_id, audio_path)
        else:
            logger.info(f"Using cached audio for video {video_id}")
            # Get video info from cache metadata
            video_info = cache_manager.get_video_info(video_id) or {}
            
            if progress_callback:
                progress_callback(0.4, "Using cached audio...")
        
        # Add video info to result
        result["video_info"] = video_info or {}
        
        # 2. Transcribe audio (or use cached)
        transcription = None
        
        if use_cache:
            transcription = cache_manager.get_cached_transcription(video_id, source_language)
            
        if not transcription:
            logger.info(f"Transcribing audio for video {video_id}...")
            if progress_callback:
                progress_callback(0.5, "Transcribing audio...")
                
            transcription = transcribe_audio(
                audio_file=audio_path,
                language=source_language
            )
            
            # Cache the transcription
            if cache_manager.enabled:
                cache_manager.cache_transcription(video_id, source_language, transcription)
        else:
            logger.info(f"Using cached transcription for video {video_id}")
            if progress_callback:
                progress_callback(0.7, "Using cached transcription...")
        
        # Add transcription to result
        result["transcription"] = transcription
        
        # 3. Translate text (or use cached)
        translation = None
        
        if use_cache:
            translation = cache_manager.get_cached_translation(video_id, source_language, target_language)
            
        if not translation:
            logger.info(f"Translating transcription for video {video_id} from {source_language} to {target_language}...")
            if progress_callback:
                progress_callback(0.8, "Translating text...")
                
            translation = translate_text(
                text=transcription,
                source_lang=source_language,
                target_lang=target_language
            )
            
            # Cache the translation
            if cache_manager.enabled:
                cache_manager.cache_translation(video_id, source_language, target_language, translation)
        else:
            logger.info(f"Using cached translation for video {video_id}")
            if progress_callback:
                progress_callback(0.9, "Using cached translation...")
        
        # Add translation to result
        result["translation"] = translation
        
        if progress_callback:
            progress_callback(1.0, "Translation complete!")
            
        return result
        
    except YouTubeError as e:
        logger.error(f"YouTube error: {e}")
        raise TranslationError(f"Error with YouTube video: {e}")
    except TranscriptionError as e:
        logger.error(f"Transcription error: {e}")
        raise TranslationError(f"Error transcribing audio: {e}")
    except Exception as e:
        logger.error(f"Unexpected error in translation pipeline: {e}")
        raise TranslationError(f"Unexpected error: {e}")
