"""
Advanced caching system for YouTube Translator Pro.

Provides intelligent caching of downloaded videos, transcriptions, and translations
to improve performance and reduce redundant processing.
"""

import os
import json
import time
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Union, List, Tuple
from datetime import datetime, timedelta

from src.config import CACHE_DIR, setup_logging
from src.utils.error_handling import try_except_decorator, ResourceError

# Initialize logger
logger = setup_logging()


class CacheManager:
    """
    Manages application-wide caching for videos, transcriptions, and translations.
    Implements intelligent cache eviction policies and size management.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        """Implement singleton pattern for cache manager."""
        if cls._instance is None:
            cls._instance = super(CacheManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, cache_dir: Union[str, Path] = CACHE_DIR, max_size_mb: int = 1000, 
                 ttl_days: int = 30, enabled: bool = True):
        """Initialize the cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            max_size_mb: Maximum cache size in megabytes
            ttl_days: Time-to-live for cache entries in days
            enabled: Whether caching is enabled
        """
        # Skip initialization if already initialized (singleton pattern)
        if self._initialized:
            return
            
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024  # Convert MB to bytes
        self.ttl_seconds = ttl_days * 24 * 60 * 60  # Convert days to seconds
        self.enabled = enabled
        
        # Define subdirectories
        self.audio_cache_dir = self.cache_dir / "audio"
        self.transcription_cache_dir = self.cache_dir / "transcriptions"
        self.translation_cache_dir = self.cache_dir / "translations"
        self.metadata_cache_dir = self.cache_dir / "metadata"
        
        # Ensure cache directories exist
        self._ensure_cache_dirs()
        
        # Initialize cache index
        self.index_file = self.cache_dir / "cache_index.json"
        self.cache_index = self._load_cache_index()
        
        # Perform initial cleanup
        self._cleanup_cache()
        
        self._initialized = True
        logger.info(f"Cache manager initialized with max size {max_size_mb}MB and TTL {ttl_days} days")
    
    def _ensure_cache_dirs(self) -> None:
        """Ensure all cache directories exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.audio_cache_dir.mkdir(exist_ok=True)
        self.transcription_cache_dir.mkdir(exist_ok=True)
        self.translation_cache_dir.mkdir(exist_ok=True)
        self.metadata_cache_dir.mkdir(exist_ok=True)
    
    def _load_cache_index(self) -> Dict[str, Any]:
        """Load the cache index from disk."""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)
                logger.info(f"Loaded cache index with {len(index.get('entries', {}))} entries")
                return index
            except Exception as e:
                logger.error(f"Failed to load cache index: {e}")
                # If index is corrupt, create a new one
                return self._create_new_index()
        else:
            return self._create_new_index()
    
    def _create_new_index(self) -> Dict[str, Any]:
        """Create a new cache index."""
        return {
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "last_cleaned": datetime.now().isoformat(),
            "entries": {},
            "stats": {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "size_bytes": 0
            }
        }
    
    def _save_cache_index(self) -> None:
        """Save the cache index to disk."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_index, f, indent=2)
            logger.debug("Cache index saved")
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    @try_except_decorator
    def get_cached_audio(self, video_id: str) -> Optional[str]:
        """
        Get cached audio file path for a video ID.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to cached audio file if it exists, None otherwise
        """
        if not self.enabled:
            return None
            
        cache_key = f"audio:{video_id}"
        cache_entry = self.cache_index.get("entries", {}).get(cache_key)
        
        if cache_entry and self._is_entry_valid(cache_entry):
            # Check if file exists
            file_path = Path(cache_entry["file_path"])
            if file_path.exists():
                # Update access time
                cache_entry["last_accessed"] = datetime.now().isoformat()
                self.cache_index["stats"]["hits"] += 1
                self._save_cache_index()
                logger.info(f"Cache hit for audio of video {video_id}")
                return str(file_path)
        
        # Cache miss
        self.cache_index["stats"]["misses"] += 1
        self._save_cache_index()
        logger.info(f"Cache miss for audio of video {video_id}")
        return None
    
    @try_except_decorator
    def cache_audio(self, video_id: str, audio_file: Union[str, Path], 
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Cache an audio file for a video ID.
        
        Args:
            video_id: YouTube video ID
            audio_file: Path to the audio file to cache
            metadata: Optional metadata to store with the cache entry
            
        Returns:
            Path to the cached audio file
        """
        if not self.enabled:
            return str(audio_file)
            
        # Ensure source file exists
        src_path = Path(audio_file)
        if not src_path.exists():
            raise ResourceError(f"Audio file not found: {audio_file}")
        
        # Generate cache key and destination path
        cache_key = f"audio:{video_id}"
        extension = src_path.suffix
        dest_filename = f"{video_id}{extension}"
        dest_path = self.audio_cache_dir / dest_filename
        
        # Copy file to cache
        try:
            shutil.copy2(src_path, dest_path)
        except Exception as e:
            logger.error(f"Failed to copy audio file to cache: {e}")
            return str(audio_file)
        
        # Create or update cache entry
        file_size = dest_path.stat().st_size
        cache_entry = {
            "key": cache_key,
            "file_path": str(dest_path),
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "size_bytes": file_size,
            "metadata": metadata or {}
        }
        
        # Update cache index
        self.cache_index["entries"][cache_key] = cache_entry
        self.cache_index["stats"]["size_bytes"] += file_size
        self._save_cache_index()
        
        # Check if cache exceeds max size and clean up if necessary
        if self.cache_index["stats"]["size_bytes"] > self.max_size_bytes:
            self._cleanup_cache()
        
        logger.info(f"Cached audio file for video {video_id}: {dest_path}")
        return str(dest_path)
    
    @try_except_decorator
    def get_cached_transcription(self, video_id: str, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Get cached transcription for a video ID and model.
        
        Args:
            video_id: YouTube video ID
            model_name: Transcription model name
            
        Returns:
            Transcription data if it exists, None otherwise
        """
        if not self.enabled:
            return None
            
        cache_key = f"transcription:{video_id}:{model_name}"
        cache_entry = self.cache_index.get("entries", {}).get(cache_key)
        
        if cache_entry and self._is_entry_valid(cache_entry):
            # Check if file exists
            file_path = Path(cache_entry["file_path"])
            if file_path.exists():
                try:
                    # Load transcription data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        transcription = json.load(f)
                    
                    # Update access time
                    cache_entry["last_accessed"] = datetime.now().isoformat()
                    self.cache_index["stats"]["hits"] += 1
                    self._save_cache_index()
                    logger.info(f"Cache hit for transcription of video {video_id} with model {model_name}")
                    return transcription
                except Exception as e:
                    logger.error(f"Failed to load cached transcription: {e}")
        
        # Cache miss
        self.cache_index["stats"]["misses"] += 1
        self._save_cache_index()
        logger.info(f"Cache miss for transcription of video {video_id} with model {model_name}")
        return None
    
    @try_except_decorator
    def cache_transcription(self, video_id: str, model_name: str, 
                            transcription_data: Dict[str, Any]) -> None:
        """
        Cache transcription data for a video ID and model.
        
        Args:
            video_id: YouTube video ID
            model_name: Transcription model name
            transcription_data: Transcription data to cache
        """
        if not self.enabled:
            return
            
        # Generate cache key and destination path
        cache_key = f"transcription:{video_id}:{model_name}"
        dest_filename = f"{video_id}_{model_name}.json"
        dest_path = self.transcription_cache_dir / dest_filename
        
        # Save transcription data to file
        try:
            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(transcription_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save transcription data to cache: {e}")
            return
        
        # Create or update cache entry
        file_size = dest_path.stat().st_size
        cache_entry = {
            "key": cache_key,
            "file_path": str(dest_path),
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "size_bytes": file_size,
            "metadata": {
                "video_id": video_id,
                "model_name": model_name
            }
        }
        
        # Update cache index
        self.cache_index["entries"][cache_key] = cache_entry
        self.cache_index["stats"]["size_bytes"] += file_size
        self._save_cache_index()
        
        # Check if cache exceeds max size and clean up if necessary
        if self.cache_index["stats"]["size_bytes"] > self.max_size_bytes:
            self._cleanup_cache()
        
        logger.info(f"Cached transcription for video {video_id} with model {model_name}")
    
    @try_except_decorator
    def get_cached_translation(self, video_id: str, source_lang: str, 
                               target_lang: str) -> Optional[Dict[str, Any]]:
        """
        Get cached translation for a video ID and language pair.
        
        Args:
            video_id: YouTube video ID
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translation data if it exists, None otherwise
        """
        if not self.enabled:
            return None
            
        cache_key = f"translation:{video_id}:{source_lang}:{target_lang}"
        cache_entry = self.cache_index.get("entries", {}).get(cache_key)
        
        if cache_entry and self._is_entry_valid(cache_entry):
            # Check if file exists
            file_path = Path(cache_entry["file_path"])
            if file_path.exists():
                try:
                    # Load translation data
                    with open(file_path, 'r', encoding='utf-8') as f:
                        translation = json.load(f)
                    
                    # Update access time
                    cache_entry["last_accessed"] = datetime.now().isoformat()
                    self.cache_index["stats"]["hits"] += 1
                    self._save_cache_index()
                    logger.info(f"Cache hit for translation of video {video_id} from {source_lang} to {target_lang}")
                    return translation
                except Exception as e:
                    logger.error(f"Failed to load cached translation: {e}")
        
        # Cache miss
        self.cache_index["stats"]["misses"] += 1
        self._save_cache_index()
        logger.info(f"Cache miss for translation of video {video_id} from {source_lang} to {target_lang}")
        return None
    
    @try_except_decorator
    def cache_translation(self, video_id: str, source_lang: str, target_lang: str,
                          translation_data: Dict[str, Any]) -> None:
        """
        Cache translation data for a video ID and language pair.
        
        Args:
            video_id: YouTube video ID
            source_lang: Source language code
            target_lang: Target language code
            translation_data: Translation data to cache
        """
        if not self.enabled:
            return
            
        # Generate cache key and destination path
        cache_key = f"translation:{video_id}:{source_lang}:{target_lang}"
        dest_filename = f"{video_id}_{source_lang}_{target_lang}.json"
        dest_path = self.translation_cache_dir / dest_filename
        
        # Save translation data to file
        try:
            with open(dest_path, 'w', encoding='utf-8') as f:
                json.dump(translation_data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save translation data to cache: {e}")
            return
        
        # Create or update cache entry
        file_size = dest_path.stat().st_size
        cache_entry = {
            "key": cache_key,
            "file_path": str(dest_path),
            "created_at": datetime.now().isoformat(),
            "last_accessed": datetime.now().isoformat(),
            "size_bytes": file_size,
            "metadata": {
                "video_id": video_id,
                "source_lang": source_lang,
                "target_lang": target_lang
            }
        }
        
        # Update cache index
        self.cache_index["entries"][cache_key] = cache_entry
        self.cache_index["stats"]["size_bytes"] += file_size
        self._save_cache_index()
        
        # Check if cache exceeds max size and clean up if necessary
        if self.cache_index["stats"]["size_bytes"] > self.max_size_bytes:
            self._cleanup_cache()
        
        logger.info(f"Cached translation for video {video_id} from {source_lang} to {target_lang}")
    
    def _is_entry_valid(self, entry: Dict[str, Any]) -> bool:
        """Check if a cache entry is still valid (not expired)."""
        try:
            created_at = datetime.fromisoformat(entry["created_at"])
            expiration_time = created_at + timedelta(seconds=self.ttl_seconds)
            return datetime.now() < expiration_time
        except Exception as e:
            logger.error(f"Error checking cache entry validity: {e}")
            return False
    
    def _cleanup_cache(self) -> None:
        """
        Clean up the cache by removing expired entries and
        applying eviction policy if cache exceeds maximum size.
        """
        if not self.enabled:
            return
            
        logger.info("Starting cache cleanup")
        
        # Remove expired entries
        expired_keys = []
        for key, entry in list(self.cache_index.get("entries", {}).items()):
            if not self._is_entry_valid(entry):
                expired_keys.append(key)
                
        # Remove expired entries from cache
        for key in expired_keys:
            self._remove_cache_entry(key)
            
        # If cache still exceeds max size, apply LRU eviction policy
        if self.cache_index["stats"]["size_bytes"] > self.max_size_bytes:
            self._apply_eviction_policy()
            
        # Update last_cleaned timestamp
        self.cache_index["last_cleaned"] = datetime.now().isoformat()
        self._save_cache_index()
        
        logger.info(f"Cache cleanup completed. Removed {len(expired_keys)} expired entries.")
    
    def _remove_cache_entry(self, cache_key: str) -> None:
        """Remove a cache entry and its associated file."""
        entry = self.cache_index["entries"].get(cache_key)
        if not entry:
            return
            
        # Remove file
        file_path = Path(entry["file_path"])
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.error(f"Failed to delete cache file {file_path}: {e}")
        
        # Update stats
        self.cache_index["stats"]["size_bytes"] -= entry.get("size_bytes", 0)
        self.cache_index["stats"]["evictions"] += 1
        
        # Remove entry from index
        del self.cache_index["entries"][cache_key]
        
        logger.debug(f"Removed cache entry: {cache_key}")
    
    def _apply_eviction_policy(self) -> None:
        """
        Apply Least Recently Used (LRU) cache eviction policy.
        Removes least recently used entries until cache size is below max size.
        """
        # Sort entries by last_accessed time
        entries = list(self.cache_index["entries"].items())
        entries.sort(key=lambda x: x[1].get("last_accessed", ""))
        
        # Remove entries until we're under the size limit
        for key, _ in entries:
            self._remove_cache_entry(key)
            
            # Check if we're now under the limit
            if self.cache_index["stats"]["size_bytes"] <= self.max_size_bytes:
                break
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.cache_index["stats"].copy()
        stats["entry_count"] = len(self.cache_index.get("entries", {}))
        stats["size_mb"] = round(stats["size_bytes"] / (1024 * 1024), 2)
        return stats
    
    def clear_cache(self) -> None:
        """Clear the entire cache."""
        if not self.enabled:
            return
            
        logger.info("Clearing cache")
        
        # Remove all cache entries
        for key in list(self.cache_index.get("entries", {}).keys()):
            self._remove_cache_entry(key)
        
        # Reset stats
        self.cache_index["stats"] = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "size_bytes": 0
        }
        
        self._save_cache_index()
        logger.info("Cache cleared")
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable caching."""
        self.enabled = enabled
        logger.info(f"Caching {'enabled' if enabled else 'disabled'}")
    
    def set_max_size(self, max_size_mb: int) -> None:
        """Set maximum cache size in megabytes."""
        self.max_size_bytes = max_size_mb * 1024 * 1024
        logger.info(f"Cache max size set to {max_size_mb}MB")
        
        # Clean up if necessary
        if self.cache_index["stats"]["size_bytes"] > self.max_size_bytes:
            self._cleanup_cache()
    
    def set_ttl(self, ttl_days: int) -> None:
        """Set time-to-live for cache entries in days."""
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        logger.info(f"Cache TTL set to {ttl_days} days")
        
        # Clean up to apply new TTL
        self._cleanup_cache()


# Create a function to get the singleton instance
def get_cache_manager() -> CacheManager:
    """Get the singleton instance of the cache manager."""
    from src.config import load_settings
    
    # Load settings
    settings = load_settings()
    
    # Initialize with settings
    return CacheManager(
        cache_dir=settings.get("cache_dir", CACHE_DIR),
        max_size_mb=settings.get("cache_size_mb", 1000),
        ttl_days=settings.get("cache_ttl", 30) // (24 * 60 * 60),  # Convert seconds to days
        enabled=settings.get("cache_enabled", True)
    )
