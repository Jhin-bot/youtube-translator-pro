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

try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal

# Logger setup
logger = logging.getLogger(__name__)

class CacheManager(QObject):
    """Cache manager for YouTube Translator Pro."""
    
    # Signals
    cache_cleared = pyqtSignal()
    cache_updated = pyqtSignal(str, str)
    
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
            
        # Create cache directory if it doesn't exist'
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
    
    def _load_access_log(self) -> Dict[str, Dict[str, float]]:
        """
        Load the access log from disk.
        
        Returns:
            Dictionary mapping cache types to item IDs and access times
        """
        if os.path.exists(self.access_log_file):
            try:
                with open(self.access_log_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading access log: {e}")
        
        # Create a new access log
        return {
            "audio": {},
            "transcription": {},
            "translation": {},
            "thumbnail": {}
        }
    
    def _save_access_log(self) -> None:
        """Save the access log to disk."""
        try:
            with open(self.access_log_file, 'w') as f:
                json.dump(self.access_log, f)
        except Exception as e:
            logger.error(f"Error saving access log: {e}")
    
    def _update_access_time(self, cache_type: str, item_id: str) -> None:
        """
        Update the access time for a cached item.
        
        Args:
            cache_type: Type of cache (audio, transcription, translation, thumbnail)
            item_id: ID of the cached item
        """
        if cache_type not in self.access_log:
            self.access_log[cache_type] = {}
            
        self.access_log[cache_type][item_id] = time.time()
        self._save_access_log()
    
    def _get_cache_size(self) -> float:
        """
        Get the total size of the cache in megabytes.
        
        Returns:
            Total cache size in megabytes
        """
        total_size = 0
        
        for root, _, files in os.walk(self.cache_dir):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    total_size += os.path.getsize(file_path)
        
        return total_size / (1024 * 1024)  # Convert bytes to MB
    
    def _ensure_cache_size(self) -> None:
        """
        Ensure the cache size doesn't exceed the maximum size.
        Removes least recently used items if needed.
        """
        current_size = self._get_cache_size()
        
        if current_size <= self.max_size_mb:
            return
            
        logger.info(f"Cache size ({current_size:.2f}MB) exceeds maximum ({self.max_size_mb}MB). Cleaning up...")
        
        # Collect all items and their access times
        all_items = []
        
        for cache_type, items in self.access_log.items():
            for item_id, access_time in items.items():
                cache_dir = getattr(self, f"{cache_type}_cache_dir")
                file_path = os.path.join(cache_dir, item_id)
                
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Size in MB
                    all_items.append((cache_type, item_id, access_time, file_path, file_size))
        
        # Sort by access time (oldest first)
        all_items.sort(key=lambda x: x[2])
        
        # Delete items until we're under the limit
        deleted_size = 0
        deleted_count = 0
        
        for cache_type, item_id, _, file_path, file_size in all_items:
            if current_size - deleted_size <= self.max_size_mb * 0.9:  # Aim for 90% of max size
                break
                
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    
                # Update tracking
                deleted_size += file_size
                deleted_count += 1
                
                # Remove from access log
                if item_id in self.access_log[cache_type]:
                    del self.access_log[cache_type][item_id]
                    
            except Exception as e:
                logger.error(f"Error removing cached item {file_path}: {e}")
        
        self._save_access_log()
        logger.info(f"Removed {deleted_count} cached items ({deleted_size:.2f}MB)")
    
    def _clear_expired_items(self) -> None:
        """Remove items that have exceeded their TTL."""
        current_time = time.time()
        expired_count = 0
        
        for cache_type, items in self.access_log.items():
            to_remove = []
            
            for item_id, access_time in items.items():
                if current_time - access_time > self.ttl_seconds:
                    cache_dir = getattr(self, f"{cache_type}_cache_dir")
                    file_path = os.path.join(cache_dir, item_id)
                    
                    if os.path.exists(file_path):
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                
                            expired_count += 1
                        except Exception as e:
                            logger.error(f"Error removing expired item {file_path}: {e}")
                    
                    to_remove.append(item_id)
            
            # Remove expired items from access log
            for item_id in to_remove:
                del self.access_log[cache_type][item_id]
        
        if expired_count > 0:
            self._save_access_log()
            logger.info(f"Removed {expired_count} expired items from cache")
    
    def clear_unused(self, keep_days: int) -> int:
        """
        Clear items that haven't been accessed in the specified number of days.
        
        Args:
            keep_days: Number of days to keep items (remove older items)
            
        Returns:
            Number of items removed
        """
        current_time = time.time()
        keep_seconds = keep_days * 24 * 60 * 60
        removed_count = 0
        
        for cache_type, items in self.access_log.items():
            to_remove = []
            
            for item_id, access_time in items.items():
                if current_time - access_time > keep_seconds:
                    cache_dir = getattr(self, f"{cache_type}_cache_dir")
                    file_path = os.path.join(cache_dir, item_id)
                    
                    if os.path.exists(file_path):
                        try:
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                            elif os.path.isdir(file_path):
                                shutil.rmtree(file_path)
                                
                            removed_count += 1
                        except Exception as e:
                            logger.error(f"Error removing unused item {file_path}: {e}")
                    
                    to_remove.append(item_id)
            
            # Remove unused items from access log
            for item_id in to_remove:
                del self.access_log[cache_type][item_id]
        
        if removed_count > 0:
            self._save_access_log()
            logger.info(f"Removed {removed_count} unused items from cache")
            self.cache_cleared.emit()
            
        return removed_count
    
    def cache_audio(self, video_id: str, audio_data: bytes) -> str:
        """
        Cache audio data for a video.
        
        Args:
            video_id: YouTube video ID
            audio_data: Raw audio data bytes
            
        Returns:
            Path to the cached audio file
        """
        # Ensure cache size is within limits
        self._ensure_cache_size()
        
        # Create file path
        file_path = os.path.join(self.audio_cache_dir, video_id + ".mp3")
        
        # Write audio data
        try:
            with open(file_path, 'wb') as f:
                f.write(audio_data)
                
            # Update access log
            self._update_access_time("audio", video_id + ".mp3")
            
            # Emit signal
            self.cache_updated.emit("audio", video_id)
            
            logger.info(f"Cached audio for video: {video_id}")
            return file_path
        except Exception as e:
            logger.error(f"Error caching audio for video {video_id}: {e}")
            return ""
    
    def get_cached_audio(self, video_id: str) -> Optional[str]:
        """
        Get the cached audio file path for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to the cached audio file, or None if not found
        """
        file_path = os.path.join(self.audio_cache_dir, video_id + ".mp3")
        
        if os.path.exists(file_path):
            # Update access log
            self._update_access_time("audio", video_id + ".mp3")
            
            return file_path
        
        return None
    
    def cache_transcription(self, video_id: str, model: str, transcription_data: Dict) -> str:
        """
        Cache transcription data for a video.
        
        Args:
            video_id: YouTube video ID
            model: Transcription model used
            transcription_data: Transcription data
            
        Returns:
            Path to the cached transcription file
        """
        # Ensure cache size is within limits
        self._ensure_cache_size()
        
        # Create a safe filename with the model included
        safe_model = model.replace("/", "-").replace("\\", "-")
        file_name = f"{video_id}_{safe_model}.json"
        file_path = os.path.join(self.transcription_cache_dir, file_name)
        
        # Write transcription data
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(transcription_data, f, ensure_ascii=False, indent=2)
                
            # Update access log
            self._update_access_time("transcription", file_name)
            
            # Emit signal
            self.cache_updated.emit("transcription", video_id)
            
            logger.info(f"Cached transcription for video: {video_id} (model: {model})")
            return file_path
        except Exception as e:
            logger.error(f"Error caching transcription for video {video_id}: {e}")
            return ""
    
    def get_cached_transcription(self, video_id: str, model: str) -> Optional[Dict]:
        """
        Get the cached transcription data for a video.
        
        Args:
            video_id: YouTube video ID
            model: Transcription model used
            
        Returns:
            Transcription data, or None if not found
        """
        # Create a safe filename with the model included
        safe_model = model.replace("/", "-").replace("\\", "-")
        file_name = f"{video_id}_{safe_model}.json"
        file_path = os.path.join(self.transcription_cache_dir, file_name)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update access log
                self._update_access_time("transcription", file_name)
                
                return data
            except Exception as e:
                logger.error(f"Error loading cached transcription for video {video_id}: {e}")
                
        return None
    
    def cache_translation(self, video_id: str, source_lang: str, target_lang: str, 
                          translation_data: Dict) -> str:
        """
        Cache translation data for a video.
        
        Args:
            video_id: YouTube video ID
            source_lang: Source language code
            target_lang: Target language code
            translation_data: Translation data
            
        Returns:
            Path to the cached translation file
        """
        # Ensure cache size is within limits
        self._ensure_cache_size()
        
        # Create a safe filename with language info
        file_name = f"{video_id}_{source_lang}_to_{target_lang}.json"
        file_path = os.path.join(self.translation_cache_dir, file_name)
        
        # Write translation data
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(translation_data, f, ensure_ascii=False, indent=2)
                
            # Update access log
            self._update_access_time("translation", file_name)
            
            # Emit signal
            self.cache_updated.emit("translation", video_id)
            
            logger.info(f"Cached translation for video: {video_id} ({source_lang} to {target_lang})")
            return file_path
        except Exception as e:
            logger.error(f"Error caching translation for video {video_id}: {e}")
            return ""
    
    def get_cached_translation(self, video_id: str, source_lang: str, target_lang: str) -> Optional[Dict]:
        """
        Get the cached translation data for a video.
        
        Args:
            video_id: YouTube video ID
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            Translation data, or None if not found
        """
        # Create a safe filename with language info
        file_name = f"{video_id}_{source_lang}_to_{target_lang}.json"
        file_path = os.path.join(self.translation_cache_dir, file_name)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Update access log
                self._update_access_time("translation", file_name)
                
                return data
            except Exception as e:
                logger.error(f"Error loading cached translation for video {video_id}: {e}")
                
        return None
    
    def cache_thumbnail(self, video_id: str, thumbnail_data: bytes) -> str:
        """
        Cache thumbnail image for a video.
        
        Args:
            video_id: YouTube video ID
            thumbnail_data: Raw thumbnail image data bytes
            
        Returns:
            Path to the cached thumbnail file
        """
        # Ensure cache size is within limits
        self._ensure_cache_size()
        
        # Create file path
        file_path = os.path.join(self.thumbnail_cache_dir, video_id + ".jpg")
        
        # Write thumbnail data
        try:
            with open(file_path, 'wb') as f:
                f.write(thumbnail_data)
                
            # Update access log
            self._update_access_time("thumbnail", video_id + ".jpg")
            
            # Emit signal
            self.cache_updated.emit("thumbnail", video_id)
            
            logger.info(f"Cached thumbnail for video: {video_id}")
            return file_path
        except Exception as e:
            logger.error(f"Error caching thumbnail for video {video_id}: {e}")
            return ""
    
    def get_cached_thumbnail(self, video_id: str) -> Optional[str]:
        """
        Get the cached thumbnail file path for a video.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Path to the cached thumbnail file, or None if not found
        """
        file_path = os.path.join(self.thumbnail_cache_dir, video_id + ".jpg")
        
        if os.path.exists(file_path):
            # Update access log
            self._update_access_time("thumbnail", video_id + ".jpg")
            
            return file_path
        
        return None
    
    def clear_all(self) -> None:
        """Clear all cached items."""
        try:
            # Remove all files in cache directories
            for directory in [self.audio_cache_dir, self.transcription_cache_dir, 
                             self.translation_cache_dir, self.thumbnail_cache_dir]:
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        logger.error(f"Error removing cached item {file_path}: {e}")
            
            # Reset access log
            self.access_log = {
                "audio": {},
                "transcription": {},
                "translation": {},
                "thumbnail": {}
            }
            self._save_access_log()
            
            # Emit signal
            self.cache_cleared.emit()
            
            logger.info("Cache cleared")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the cache.
        
        Returns:
            Dictionary with cache statistics
        """
        stats = {
            "total_size_mb": self._get_cache_size(),
            "max_size_mb": self.max_size_mb,
            "ttl_days": self.ttl_seconds / (60*60*24),
            "categories": {}
        }
        
        # Count items and get size for each category
        categories = [
            ("audio", self.audio_cache_dir),
            ("transcription", self.transcription_cache_dir),
            ("translation", self.translation_cache_dir),
            ("thumbnail", self.thumbnail_cache_dir)
        ]
        
        for category, directory in categories:
            category_stats = {
                "count": 0,
                "size_mb": 0,
                "oldest_days": 0,
                "newest_days": 0
            }
            
            # Get file count and size
            if os.path.exists(directory):
                files = os.listdir(directory)
                category_stats["count"] = len(files)
                
                # Calculate size
                size = 0
                for filename in files:
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        size += os.path.getsize(file_path)
                
                category_stats["size_mb"] = size / (1024 * 1024)
                
                # Get age information
                current_time = time.time()
                access_times = []
                
                for item_id in self.access_log.get(category, {}):
                    access_time = self.access_log[category][item_id]
                    access_times.append(access_time)
                
                if access_times:
                    oldest = min(access_times)
                    newest = max(access_times)
                    
                    category_stats["oldest_days"] = (current_time - oldest) / (60*60*24)
                    category_stats["newest_days"] = (current_time - newest) / (60*60*24)
            
            stats["categories"][category] = category_stats
        
        return stats
    
    def set_max_size(self, max_size_mb: int) -> None:
        """
        Set the maximum size of the cache.
        
        Args:
            max_size_mb: Maximum size in megabytes
        """
        if max_size_mb < 100:
            max_size_mb = 100  # Minimum 100MB
            
        self.max_size_mb = max_size_mb
        logger.info(f"Cache max size set to {max_size_mb}MB")
        
        # Ensure cache is within new limits
        self._ensure_cache_size()
    
    def set_ttl(self, ttl_seconds: int) -> None:
        """
        Set the time-to-live for cached items.
        
        Args:
            ttl_seconds: Time-to-live in seconds
        """
        if ttl_seconds < 60 * 60:  # Minimum 1 hour
            ttl_seconds = 60 * 60
            
        self.ttl_seconds = ttl_seconds
        logger.info(f"Cache TTL set to {ttl_seconds} seconds")
        
        # Clear expired items
        self._clear_expired_items()
    
    def stop(self) -> None:
        """Clean up resources before stopping."""
        # Save access log
        self._save_access_log()
        logger.info("Cache manager stopped")
