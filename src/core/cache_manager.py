"""
Cache Manager for YouTube Translator Pro.
Handles caching of downloaded videos, transcriptions, and translations.
"""

import os
import json
import time
import logging
import shutil
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
import hashlib

from PyQt6.QtCore import QObject, pyqtSignal

# Logger setup
logger = logging.getLogger(__name__)

class CacheManager(QObject):
    """
    Manages caching of downloaded videos, transcriptions, and translations.
    Implements LRU (Least Recently Used) policy for cache eviction.
    """
    
    cache_cleared = pyqtSignal()
    cache_updated = pyqtSignal(str, str)  # (cache_type, item_id)
    
    def __init__(self, cache_dir: Optional[str] = None, max_size_mb: int = 1000, 
                 ttl_seconds: int = 60*60*24*30, parent=None):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory where cache files are stored
            max_size_mb: Maximum size of the cache in megabytes
            ttl_seconds: Time-to-live for cached items in seconds
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # Set default cache directory if not provided
        if cache_dir is None:
            home_dir = str(Path.home())
            cache_dir = os.path.join(home_dir, ".youtube_translator_pro", "cache")
            
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Set up cache subdirectories
        self.cache_dir = cache_dir
        self.audio_cache_dir = os.path.join(cache_dir, "audio")
        self.transcription_cache_dir = os.path.join(cache_dir, "transcriptions")
        self.translation_cache_dir = os.path.join(cache_dir, "translations")
        self.thumbnail_cache_dir = os.path.join(cache_dir, "thumbnails")
        
        # Create subdirectories
        os.makedirs(self.audio_cache_dir, exist_ok=True)
        os.makedirs(self.transcription_cache_dir, exist_ok=True)
        os.makedirs(self.translation_cache_dir, exist_ok=True)
        os.makedirs(self.thumbnail_cache_dir, exist_ok=True)
        
        # Cache settings
        self.max_size_mb = max_size_mb
        self.ttl_seconds = ttl_seconds
        
        # Initialize access tracking
        self.access_log_file = os.path.join(cache_dir, "access_log.json")
        self.access_log = self._load_access_log()
        
        logger.info(f"Cache initialized with max size {max_size_mb}MB and TTL {ttl_seconds} seconds")
        
    def _load_access_log(self) -> Dict[str, Any]:
        """
        Load the access log from disk.
        
        Returns:
            Dictionary with access timestamps for cached items.
        """
        if os.path.exists(self.access_log_file):
            try:
                with open(self.access_log_file, 'r', encoding='utf-8') as f:
                    access_log = json.load(f)
                logger.debug(f"Loaded access log with {len(access_log)} entries")
                return access_log
            except Exception as e:
                logger.error(f"Failed to load access log: {e}")
                
        # Return empty log if file doesn't exist or loading failed
        return {"audio": {}, "transcriptions": {}, "translations": {}, "thumbnails": {}}
    
    def _save_access_log(self) -> None:
        """Save the access log to disk."""
        try:
            with open(self.access_log_file, 'w', encoding='utf-8') as f:
                json.dump(self.access_log, f)
            logger.debug("Access log saved successfully")
        except Exception as e:
            logger.error(f"Failed to save access log: {e}")
    
    def _update_access_time(self, cache_type: str, item_id: str) -> None:
        """
        Update the access time for a cached item.
        
        Args:
            cache_type: Type of cached item (audio, transcription, translation, thumbnail)
            item_id: ID of the cached item
        """
        if cache_type not in self.access_log:
            self.access_log[cache_type] = {}
            
        self.access_log[cache_type][item_id] = time.time()
        self._save_access_log()
    
    def _get_cache_size(self) -> float:
        """
        Calculate the total size of the cache in megabytes.
        
        Returns:
            Cache size in megabytes.
        """
        total_size = 0
        
        # Calculate size of audio cache
        for filename in os.listdir(self.audio_cache_dir):
            file_path = os.path.join(self.audio_cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        # Calculate size of transcription cache
        for filename in os.listdir(self.transcription_cache_dir):
            file_path = os.path.join(self.transcription_cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        # Calculate size of translation cache
        for filename in os.listdir(self.translation_cache_dir):
            file_path = os.path.join(self.translation_cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        # Calculate size of thumbnail cache
        for filename in os.listdir(self.thumbnail_cache_dir):
            file_path = os.path.join(self.thumbnail_cache_dir, filename)
            if os.path.isfile(file_path):
                total_size += os.path.getsize(file_path)
        
        # Convert to megabytes
        return total_size / (1024 * 1024)
    
    def _ensure_cache_size(self) -> None:
        """
        Ensure the cache size doesn't exceed the maximum size.
        Removes least recently used items if needed.
        """
        current_size = self._get_cache_size()
        
        if current_size <= self.max_size_mb:
            return
        
        logger.info(f"Cache size ({current_size:.2f} MB) exceeds maximum ({self.max_size_mb} MB). Cleaning up...")
        
        # Get all cached items with their access times
        items = []
        
        # Add audio items
        for item_id, access_time in self.access_log.get("audio", {}).items():
            file_path = os.path.join(self.audio_cache_dir, f"{item_id}.mp3")
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                items.append(("audio", item_id, access_time, size, file_path))
        
        # Add transcription items
        for item_id, access_time in self.access_log.get("transcriptions", {}).items():
            file_path = os.path.join(self.transcription_cache_dir, f"{item_id}.json")
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                items.append(("transcriptions", item_id, access_time, size, file_path))
        
        # Add translation items
        for item_id, access_time in self.access_log.get("translations", {}).items():
            file_path = os.path.join(self.translation_cache_dir, f"{item_id}.json")
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                items.append(("translations", item_id, access_time, size, file_path))
        
        # Add thumbnail items
        for item_id, access_time in self.access_log.get("thumbnails", {}).items():
            file_path = os.path.join(self.thumbnail_cache_dir, f"{item_id}.jpg")
            if os.path.exists(file_path):
                size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                items.append(("thumbnails", item_id, access_time, size, file_path))
        
        # Sort by access time (oldest first)
        items.sort(key=lambda x: x[2])
        
        # Remove items until cache size is below maximum
        removed_size = 0
        removed_count = 0
        
        for cache_type, item_id, access_time, size, file_path in items:
            if current_size - removed_size <= self.max_size_mb * 0.9:  # Keep removing until we're 10% below max
                break
                
            try:
                # Remove the file
                os.remove(file_path)
                
                # Update tracking
                if item_id in self.access_log.get(cache_type, {}):
                    del self.access_log[cache_type][item_id]
                
                removed_size += size
                removed_count += 1
                
                logger.debug(f"Removed cached item: {cache_type}/{item_id} ({size:.2f} MB)")
            except Exception as e:
                logger.error(f"Failed to remove cached item {file_path}: {e}")
        
        # Save updated access log
        self._save_access_log()
        
        logger.info(f"Cache cleanup complete. Removed {removed_count} items ({removed_size:.2f} MB)")
        
        # Emit signal
        self.cache_cleared.emit()
    
    def _clear_expired_items(self) -> None:
        """Remove items that have exceeded their TTL."""
        current_time = time.time()
        expired_count = 0
        
        for cache_type in self.access_log:
            expired_items = []
            
            for item_id, access_time in self.access_log[cache_type].items():
                if current_time - access_time > self.ttl_seconds:
                    expired_items.append(item_id)
            
            for item_id in expired_items:
                # Determine file path based on cache type
                if cache_type == "audio":
                    file_path = os.path.join(self.audio_cache_dir, f"{item_id}.mp3")
                elif cache_type == "transcriptions":
                    file_path = os.path.join(self.transcription_cache_dir, f"{item_id}.json")
                elif cache_type == "translations":
                    file_path = os.path.join(self.translation_cache_dir, f"{item_id}.json")
                elif cache_type == "thumbnails":
                    file_path = os.path.join(self.thumbnail_cache_dir, f"{item_id}.jpg")
                else:
                    continue
                
                # Remove file if it exists
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        expired_count += 1
                        logger.debug(f"Removed expired item: {cache_type}/{item_id}")
                    except Exception as e:
                        logger.error(f"Failed to remove expired item {file_path}: {e}")
                
                # Remove from access log
                del self.access_log[cache_type][item_id]
        
        # Save updated access log
        if expired_count > 0:
            self._save_access_log()
            logger.info(f"Removed {expired_count} expired items from cache")
            
            # Emit signal
            self.cache_cleared.emit()
    
    def clear_unused(self, keep_days: int) -> None:
        """
        Clear items that haven't been accessed in the specified number of days.
        
        Args:
            keep_days: Number of days to keep items. Items not accessed in this period will be removed.
        """
        current_time = time.time()
        unused_seconds = keep_days * 24 * 60 * 60
        unused_count = 0
        
        for cache_type in self.access_log:
            unused_items = []
            
            for item_id, access_time in self.access_log[cache_type].items():
                if current_time - access_time > unused_seconds:
                    unused_items.append(item_id)
            
            for item_id in unused_items:
                # Determine file path based on cache type
                if cache_type == "audio":
                    file_path = os.path.join(self.audio_cache_dir, f"{item_id}.mp3")
                elif cache_type == "transcriptions":
                    file_path = os.path.join(self.transcription_cache_dir, f"{item_id}.json")
                elif cache_type == "translations":
                    file_path = os.path.join(self.translation_cache_dir, f"{item_id}.json")
                elif cache_type == "thumbnails":
                    file_path = os.path.join(self.thumbnail_cache_dir, f"{item_id}.jpg")
                else:
                    continue
                
                # Remove file if it exists
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        unused_count += 1
                        logger.debug(f"Removed unused item: {cache_type}/{item_id}")
                    except Exception as e:
                        logger.error(f"Failed to remove unused item {file_path}: {e}")
                
                # Remove from access log
                del self.access_log[cache_type][item_id]
        
        # Save updated access log
        if unused_count > 0:
            self._save_access_log()
            logger.info(f"Removed {unused_count} unused items from cache")
            
            # Emit signal
            self.cache_cleared.emit()
    
    def cache_audio(self, video_id: str, audio_data: bytes) -> str:
        """
        Cache audio data for a video.
        
        Args:
            video_id: YouTube video ID
            audio_data: Audio data as bytes
            
        Returns:
            Path to the cached audio file
        """
        # Generate cache file path
        cache_file = os.path.join(self.audio_cache_dir, f"{video_id}.mp3")
        
        # Save audio data
        with open(cache_file, 'wb') as f:
            f.write(audio_data)
        
        # Update access log
        self._update_access_time("audio", video_id)
        
        # Ensure cache doesn't exceed max size
        self._ensure_cache_size()
        
        # Clear expired items
        self._clear_expired_items()
        
        # Emit signal
        self.cache_updated.emit("audio", video_id)
        
        logger.info(f"Cached audio for video {video_id}")
        return cache_file
    
    def get_cached_audio(self, video_id: str) -> Optional[str]:
        """
        Get the path to cached audio for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to the cached audio file or None if not cached
        """
        cache_file = os.path.join(self.audio_cache_dir, f"{video_id}.mp3")
        
        if os.path.exists(cache_file):
            # Update access log
            self._update_access_time("audio", video_id)
            
            logger.debug(f"Using cached audio for video {video_id}")
            return cache_file
        
        return None
    
    def cache_transcription(self, video_id: str, model: str, transcription_data: Dict) -> str:
        """
        Cache transcription data for a video.
        
        Args:
            video_id: YouTube video ID
            model: Transcription model used
            transcription_data: Transcription data as dictionary
            
        Returns:
            Path to the cached transcription file
        """
        # Generate cache ID (video_id + model)
        cache_id = f"{video_id}_{model}"
        
        # Generate cache file path
        cache_file = os.path.join(self.transcription_cache_dir, f"{cache_id}.json")
        
        # Save transcription data
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(transcription_data, f, ensure_ascii=False, indent=2)
        
        # Update access log
        self._update_access_time("transcriptions", cache_id)
        
        # Ensure cache doesn't exceed max size
        self._ensure_cache_size()
        
        # Emit signal
        self.cache_updated.emit("transcriptions", cache_id)
        
        logger.info(f"Cached transcription for video {video_id} with model {model}")
        return cache_file
    
    def get_cached_transcription(self, video_id: str, model: str) -> Optional[Dict]:
        """
        Get cached transcription data for a video.
        
        Args:
            video_id: YouTube video ID
            model: Transcription model
            
        Returns:
            Transcription data as dictionary or None if not cached
        """
        # Generate cache ID
        cache_id = f"{video_id}_{model}"
        
        # Generate cache file path
        cache_file = os.path.join(self.transcription_cache_dir, f"{cache_id}.json")
        
        if os.path.exists(cache_file):
            try:
                # Load transcription data
                with open(cache_file, 'r', encoding='utf-8') as f:
                    transcription_data = json.load(f)
                
                # Update access log
                self._update_access_time("transcriptions", cache_id)
                
                logger.debug(f"Using cached transcription for video {video_id} with model {model}")
                return transcription_data
            except Exception as e:
                logger.error(f"Failed to load cached transcription: {e}")
        
        return None
    
    def cache_translation(self, video_id: str, source_lang: str, target_lang: str, 
                          translation_data: Dict) -> str:
        """
        Cache translation data for a video.
        
        Args:
            video_id: YouTube video ID
            source_lang: Source language code
            target_lang: Target language code
            translation_data: Translation data as dictionary
            
        Returns:
            Path to the cached translation file
        """
        # Generate cache ID
        cache_id = f"{video_id}_{source_lang}_{target_lang}"
        
        # Generate cache file path
        cache_file = os.path.join(self.translation_cache_dir, f"{cache_id}.json")
        
        # Save translation data
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(translation_data, f, ensure_ascii=False, indent=2)
        
        # Update access log
        self._update_access_time("translations", cache_id)
        
        # Ensure cache doesn't exceed max size
        self._ensure_cache_size()
        
        # Emit signal
        self.cache_updated.emit("translations", cache_id)
        
        logger.info(f"Cached translation for video {video_id} from {source_lang} to {target_lang}")
        return cache_file
    
    def get_cached_translation(self, video_id: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Get cached translation data for a video.
        
        Args:
            video_id: YouTube video ID
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translation data as dictionary or None if not cached
        """
        # Generate cache ID
        cache_id = f"{video_id}_{source_lang}_{target_lang}"
        
        # Generate cache file path
        cache_file = os.path.join(self.translation_cache_dir, f"{cache_id}.json")
        
        if os.path.exists(cache_file):
            try:
                # Load translation data
                with open(cache_file, 'r', encoding='utf-8') as f:
                    translation_data = json.load(f)
                
                # Update access log
                self._update_access_time("translations", cache_id)
                
                logger.debug(f"Using cached translation for video {video_id} from {source_lang} to {target_lang}")
                return translation_data
            except Exception as e:
                logger.error(f"Failed to load cached translation: {e}")
        
        return None
    
    def cache_thumbnail(self, video_id: str, thumbnail_data: bytes) -> str:
        """
        Cache thumbnail data for a video.
        
        Args:
            video_id: YouTube video ID
            thumbnail_data: Thumbnail data as bytes
            
        Returns:
            Path to the cached thumbnail file
        """
        # Generate cache file path
        cache_file = os.path.join(self.thumbnail_cache_dir, f"{video_id}.jpg")
        
        # Save thumbnail data
        with open(cache_file, 'wb') as f:
            f.write(thumbnail_data)
        
        # Update access log
        self._update_access_time("thumbnails", video_id)
        
        # Ensure cache doesn't exceed max size
        self._ensure_cache_size()
        
        # Emit signal
        self.cache_updated.emit("thumbnails", video_id)
        
        logger.info(f"Cached thumbnail for video {video_id}")
        return cache_file
    
    def get_cached_thumbnail(self, video_id: str) -> Optional[str]:
        """
        Get the path to cached thumbnail for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to the cached thumbnail file or None if not cached
        """
        cache_file = os.path.join(self.thumbnail_cache_dir, f"{video_id}.jpg")
        
        if os.path.exists(cache_file):
            # Update access log
            self._update_access_time("thumbnails", video_id)
            
            logger.debug(f"Using cached thumbnail for video {video_id}")
            return cache_file
        
        return None
    
    def clear_all(self) -> None:
        """Clear all cached items."""
        try:
            # Clear audio cache
            for filename in os.listdir(self.audio_cache_dir):
                file_path = os.path.join(self.audio_cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Clear transcription cache
            for filename in os.listdir(self.transcription_cache_dir):
                file_path = os.path.join(self.transcription_cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Clear translation cache
            for filename in os.listdir(self.translation_cache_dir):
                file_path = os.path.join(self.translation_cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Clear thumbnail cache
            for filename in os.listdir(self.thumbnail_cache_dir):
                file_path = os.path.join(self.thumbnail_cache_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Reset access log
            self.access_log = {"audio": {}, "transcriptions": {}, "translations": {}, "thumbnails": {}}
            self._save_access_log()
            
            logger.info("All cache cleared")
            
            # Emit signal
            self.cache_cleared.emit()
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        # Calculate sizes
        audio_size = sum(os.path.getsize(os.path.join(self.audio_cache_dir, f)) 
                         for f in os.listdir(self.audio_cache_dir) 
                         if os.path.isfile(os.path.join(self.audio_cache_dir, f)))
        
        transcription_size = sum(os.path.getsize(os.path.join(self.transcription_cache_dir, f)) 
                                for f in os.listdir(self.transcription_cache_dir) 
                                if os.path.isfile(os.path.join(self.transcription_cache_dir, f)))
        
        translation_size = sum(os.path.getsize(os.path.join(self.translation_cache_dir, f)) 
                              for f in os.listdir(self.translation_cache_dir) 
                              if os.path.isfile(os.path.join(self.translation_cache_dir, f)))
        
        thumbnail_size = sum(os.path.getsize(os.path.join(self.thumbnail_cache_dir, f)) 
                            for f in os.listdir(self.thumbnail_cache_dir) 
                            if os.path.isfile(os.path.join(self.thumbnail_cache_dir, f)))
        
        # Count items
        audio_count = len(os.listdir(self.audio_cache_dir))
        transcription_count = len(os.listdir(self.transcription_cache_dir))
        translation_count = len(os.listdir(self.translation_cache_dir))
        thumbnail_count = len(os.listdir(self.thumbnail_cache_dir))
        
        # Calculate total
        total_size = audio_size + transcription_size + translation_size + thumbnail_size
        total_count = audio_count + transcription_count + translation_count + thumbnail_count
        
        # Return stats
        return {
            "total_size_bytes": total_size,
            "total_size_mb": total_size / (1024 * 1024),
            "total_items": total_count,
            "audio": {
                "size_bytes": audio_size,
                "size_mb": audio_size / (1024 * 1024),
                "count": audio_count
            },
            "transcriptions": {
                "size_bytes": transcription_size,
                "size_mb": transcription_size / (1024 * 1024),
                "count": transcription_count
            },
            "translations": {
                "size_bytes": translation_size,
                "size_mb": translation_size / (1024 * 1024),
                "count": translation_count
            },
            "thumbnails": {
                "size_bytes": thumbnail_size,
                "size_mb": thumbnail_size / (1024 * 1024),
                "count": thumbnail_count
            },
            "max_size_mb": self.max_size_mb,
            "ttl_seconds": self.ttl_seconds,
            "ttl_days": self.ttl_seconds / (60 * 60 * 24)
        }
    
    def set_max_size(self, max_size_mb: int) -> None:
        """
        Set the maximum cache size.
        
        Args:
            max_size_mb: Maximum size in megabytes
        """
        if max_size_mb < 100:
            logger.warning(f"Cache size too small, setting to minimum 100MB instead of {max_size_mb}MB")
            max_size_mb = 100
            
        self.max_size_mb = max_size_mb
        logger.info(f"Cache max size set to {max_size_mb}MB")
        
        # Ensure cache size is within limits
        self._ensure_cache_size()
    
    def set_ttl(self, ttl_seconds: int) -> None:
        """
        Set the cache time-to-live.
        
        Args:
            ttl_seconds: Time-to-live in seconds
        """
        if ttl_seconds < 3600:  # At least 1 hour
            logger.warning(f"TTL too short, setting to minimum 1 hour instead of {ttl_seconds}s")
            ttl_seconds = 3600
            
        self.ttl_seconds = ttl_seconds
        logger.info(f"Cache TTL set to {ttl_seconds}s ({ttl_seconds / (60 * 60 * 24):.1f} days)")
        
        # Clear expired items
        self._clear_expired_items()
        
    def stop(self) -> None:
        """Clean up resources before stopping."""
        # Save access log
        self._save_access_log()
        logger.info("Cache manager stopped")
