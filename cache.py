"""
Caching module for YouTube Transcriber Pro.
Provides a CacheManager to store and retrieve transcription, translation,
and audio data to avoid re-processing identical tasks.
"""

import os
import json
import time
import logging
import shutil
import threading
from enum import Enum, auto
from typing import Any, Optional, Dict, List, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import hashlib # Added for generating cache keys

# Local application imports (if any are needed, e.g., for constants)
# try:
#     pass
#     from settings import APP_DATA_DIR # Example
# except ImportError:
#     APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".ytpro_default_app_data")


# Setup logger
logger = logging.getLogger(__name__)

# --- Enums ---

class CacheType(Enum):
    """Represents the type of data stored in the cache."""
    TRANSCRIPTION = auto()  # Raw transcription result (dict)
    TRANSLATION = auto()    # Translated result (dict)
    AUDIO = auto()          # Path to the downloaded/converted audio file


# --- Cache Manager ---

class CacheManager:
    """
    Manages the application cache.
    Stores and retrieves data based on a key and type, with size and time limits.
    """

    def __init__(self, cache_dir: str, max_size_mb: int = 1000, ttl_seconds: int = 60 * 60 * 24 * 30):
        """
        Initialize the Cache Manager.

        Args:
            cache_dir: The root directory for the cache.
            max_size_mb: Maximum size of the cache in megabytes.
            ttl_seconds: Time-to-live for cache entries in seconds.
        """
        self.cache_dir = Path(cache_dir)
        self.max_size_bytes = max_size_mb * 1024 * 1024 # Convert MB to Bytes
        self.ttl_seconds = ttl_seconds
        self._cache_metadata_file = self.cache_dir / "cache_metadata.json"
        self._metadata: Dict[str, Dict[str, Any]] = {} # {cache_key: {path: str, type: str, timestamp: float, size: int}}
        self._lock = threading.RLock() # Lock for thread-safe access to metadata and files
        self._initialized = False

        self._initialize_cache_dir() # Ensure cache directory and metadata are set up


    def _initialize_cache_dir(self):
        """Ensure the cache directory exists and load metadata."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self._load_metadata()
            self._initialized = True
            logger.info(f"CacheManager initialized. Cache directory: {self.cache_dir}, Max size: {self.max_size_bytes / (1024*1024):.1f} MB, TTL: {self.ttl_seconds} s.")
            # Perform initial cleanup on startup
            self.clear_unused(timeout_seconds=self.ttl_seconds)
            self._enforce_size_limit() # Enforce size limit on startup
        except Exception as e:
            logger.critical(f"Failed to initialize CacheManager or cache directory {self.cache_dir}: {e}", exc_info=True)
            self._initialized = False
            self._metadata = {} # Clear metadata if initialization fails


    def _load_metadata(self):
        """Load cache metadata from the JSON file."""
        if self._cache_metadata_file.exists():
            try:
                with self._cache_metadata_file.open('r', encoding='utf-8') as f:
                    self._metadata = json.load(f)
                logger.debug(f"Loaded {len(self._metadata)} cache entries from metadata.")
                # Validate metadata entries (check if files exist)
                keys_to_remove = []
                for key, entry in list(self._metadata.items()):
                     if not Path(entry.get("path", "")).exists():
                          logger.warning(f"Cache entry file not found: {entry.get('path')}. Removing metadata entry for {key}.")
                          keys_to_remove.append(key)
                for key in keys_to_remove:
                     del self._metadata[key]

                if keys_to_remove:
                     self._save_metadata() # Save updated metadata after removing invalid entries

            except (json.JSONDecodeError, Exception) as e:
                logger.error(f"Failed to load cache metadata from {self._cache_metadata_file}: {e}. Starting with empty metadata.", exc_info=True)
                self._metadata = {} # Reset metadata on load error


    def _save_metadata(self):
        """Save current cache metadata to the JSON file."""
        if not self._initialized:
             logger.warning("CacheManager not initialized. Skipping metadata save.")
             return

        try:
            with self._cache_metadata_file.open('w', encoding='utf-8') as f:
                json.dump(self._metadata, f, indent=2)
            logger.debug(f"Saved {len(self._metadata)} cache entries to metadata.")
        except Exception as e:
            logger.error(f"Failed to save cache metadata to {self._cache_metadata_file}: {e}", exc_info=True)


    def _generate_key(self, base_key: str, cache_type: CacheType) -> str:
        """Generate a unique cache key based on base key and type."""
        # Use a hash to create a fixed-size key, ensuring uniqueness based on input
        combined_key = f"{cache_type.name}_{base_key}"
        return hashlib.sha256(combined_key.encode('utf-8')).hexdigest()


    def get(self, base_key: str, cache_type: CacheType) -> Optional[Any]:
        """
        Retrieve data from the cache.

        Args:
            base_key: The base key for the cache entry (e.g., YouTube URL).
            cache_type: The type of data to retrieve.

        Returns:
            The cached data, or None if not found, expired, or invalid.
        """
        if not self._initialized:
             logger.debug("CacheManager not initialized. Get operation skipped.")
             return None

        cache_key = self._generate_key(base_key, cache_type)

        with self._lock:
            entry = self._metadata.get(cache_key)
            if not entry:
                logger.debug(f"Cache miss for key: {cache_key}")
                return None

            file_path = Path(entry.get("path", ""))
            timestamp = entry.get("timestamp", 0)
            entry_type = entry.get("type")

            # Check if the file exists and the type matches
            if not file_path.exists() or entry_type != cache_type.name:
                logger.warning(f"Cache entry mismatch or file not found for key {cache_key}. Removing invalid entry.")
                self._delete_entry(cache_key) # Remove invalid entry
                return None

            # Check TTL
            current_time = time.time()
            if current_time - timestamp > self.ttl_seconds:
                logger.debug(f"Cache entry expired for key: {cache_key}. Removing.")
                self._delete_entry(cache_key) # Remove expired entry
                return None

            logger.debug(f"Cache hit for key: {cache_key}")

            # Return data based on type
            try:
                if cache_type == CacheType.AUDIO:
                    # For audio, return the file path
                    return str(file_path)
                else:
                    # For transcription/translation, load from JSON file
                    with file_path.open('r', encoding='utf-8') as f:
                        data = json.load(f)
                    return data
            except Exception as e:
                logger.error(f"Failed to retrieve data from cache file {file_path} for key {cache_key}: {e}", exc_info=True)
                self._delete_entry(cache_key) # Remove corrupted entry
                return None


    def set(self, base_key: str, cache_type: CacheType, data: Any) -> Optional[str]:
        """
        Store data in the cache.

        Args:
            base_key: The base key for the cache entry (e.g., YouTube URL).
            cache_type: The type of data to store.
            data: The data to store (audio file path or transcription/translation dict).

        Returns:
            The path to the cached file if successful, None otherwise.
        """
        if not self._initialized:
             logger.debug("CacheManager not initialized. Set operation skipped.")
             return None

        cache_key = self._generate_key(base_key, cache_type)
        file_path = self.cache_dir / f"{cache_key}.cache" # Use a generic .cache extension

        with self._lock:
            try:
                # Store data based on type
                if cache_type == CacheType.AUDIO:
                    # For audio, copy the file to the cache directory
                    if not isinstance(data, str) or not Path(data).exists():
                         logger.warning(f"Invalid data provided for audio cache: {data}")
                         return None
                    shutil.copy2(data, file_path) # Use copy2 to preserve metadata
                else:
                    # For transcription/translation, save as JSON
                    with file_path.open('w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2)

                # Get file size
                file_size = file_path.stat().st_size

                # Update metadata
                self._metadata[cache_key] = {
                    "path": str(file_path),
                    "type": cache_type.name,
                    "timestamp": time.time(),
                    "size": file_size
                }

                self._save_metadata() # Save updated metadata

                # Enforce size limit after adding a new entry
                self._enforce_size_limit()

                logger.debug(f"Cached entry for key: {cache_key}, type: {cache_type.name}, size: {file_size} bytes.")
                return str(file_path) # Return the path to the cached file

            except Exception as e:
                logger.error(f"Failed to store data in cache for key {cache_key}: {e}", exc_info=True)
                # Clean up the partially created file if it exists
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as cleanup_err:
                        logger.warning(f"Failed to clean up partial cache file {file_path}: {cleanup_err}")
                # Remove metadata entry if it was added
                if cache_key in self._metadata:
                     del self._metadata[cache_key]
                     self._save_metadata() # Save metadata after removal
                return None


    def delete(self, base_key: str, cache_type: Optional[CacheType] = None):
        """
        Delete an entry or entries from the cache.

        Args:
            base_key: The base key for the cache entry(s).
            cache_type: Optional. If specified, delete only the entry of this type.
                        If None, delete all entries with this base key across all types.
        """
        if not self._initialized:
             logger.debug("CacheManager not initialized. Delete operation skipped.")
             return

        with self._lock:
            keys_to_delete = []
            if cache_type:
                 # Delete a specific type for the base key
                 cache_key = self._generate_key(base_key, cache_type)
                 if cache_key in self._metadata:
                      keys_to_delete.append(cache_key)
            else:
                 # Delete all types for the base key (find all keys starting with hash of base_key)
                 # This requires iterating through metadata, which might be slow for a large cache.
                 # A better approach for deleting by base_key across types might require
                 # a different metadata structure (e.g., nested dict {base_key: {type: metadata}}).
                 # For now, let's regenerate keys for all known types and check existence.
                 # Assuming we know all possible CacheTypes.
                 all_cache_types = list(CacheType)
                 for c_type in all_cache_types:
                      cache_key = self._generate_key(base_key, c_type)
                      if cache_key in self._metadata:
                           keys_to_delete.append(cache_key)


            for key in keys_to_delete:
                 self._delete_entry(key) # Delete the actual file and metadata entry

            if keys_to_delete:
                 self._save_metadata() # Save metadata after deletions
                 logger.debug(f"Deleted {len(keys_to_delete)} cache entries for base key: {base_key}.")


    def _delete_entry(self, cache_key: str):
        """Internal method to delete a single cache entry (file and metadata)."""
        entry = self._metadata.get(cache_key)
        if entry:
            file_path = Path(entry.get("path", ""))
            if file_path.exists():
                try:
                    file_path.unlink() # Delete the file
                    logger.debug(f"Deleted cache file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to delete cache file {file_path}: {e}", exc_info=True)
            # Remove from metadata regardless of file deletion success
            del self._metadata[cache_key]
            logger.debug(f"Removed metadata for cache key: {cache_key}")


    def clear(self):
        """Clear the entire cache (all files and metadata)."""
        if not self._initialized:
             logger.debug("CacheManager not initialized. Clear operation skipped.")
             return

        logger.info("Clearing entire cache...")
        with self._lock:
            # Delete all files listed in metadata
            for entry in self._metadata.values():
                file_path = Path(entry.get("path", ""))
                if file_path.exists():
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.error(f"Failed to delete cache file during clear {file_path}: {e}", exc_info=True)

            # Clear metadata
            self._metadata = {}
            self._save_metadata() # Save empty metadata

        logger.info("Cache cleared.")


    def clear_unused(self, timeout_seconds: Optional[int] = None):
        """
        Clear cache entries older than the specified timeout (defaults to TTL).

        Args:
            timeout_seconds: The age threshold in seconds. Defaults to self.ttl_seconds.
        """
        if not self._initialized:
             logger.debug("CacheManager not initialized. Clear unused operation skipped.")
             return

        threshold_seconds = timeout_seconds if timeout_seconds is not None else self.ttl_seconds
        if threshold_seconds <= 0:
             logger.debug("Clear unused timeout is zero or negative. Skipping.")
             return

        logger.info(f"Clearing cache entries older than {threshold_seconds} seconds...")
        current_time = time.time()
        keys_to_delete = []

        with self._lock:
            for key, entry in self._metadata.items():
                timestamp = entry.get("timestamp", 0)
                if current_time - timestamp > threshold_seconds:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                self._delete_entry(key)

            if keys_to_delete:
                self._save_metadata() # Save metadata after deletions
                logger.info(f"Cleared {len(keys_to_delete)} unused cache entries.")
            else:
                logger.debug("No unused cache entries found to clear.")


    def _enforce_size_limit(self):
        """Enforce the maximum cache size limit by removing oldest entries."""
        if not self._initialized or self.max_size_bytes <= 0:
             logger.debug("CacheManager not initialized or size limit disabled. Size enforcement skipped.")
             return

        current_size = sum(entry.get("size", 0) for entry in self._metadata.values())
        logger.debug(f"Current cache size: {current_size / (1024*1024):.1f} MB / {self.max_size_bytes / (1024*1024):.1f} MB")

        if current_size > self.max_size_bytes:
            logger.warning(f"Cache size exceeds limit ({current_size / (1024*1024):.1f} MB > {self.max_size_bytes / (1024*1024):.1f} MB). Enforcing limit.")

            # Get entries sorted by timestamp (oldest first)
            # Sort metadata entries by timestamp
            sorted_entries = sorted(
                self._metadata.items(),
                key=lambda item: item[1].get("timestamp", 0)
            )

            # Remove oldest entries until size is within limit
            keys_to_delete = []
            for key, entry in sorted_entries:
                if current_size <= self.max_size_bytes:
                    break # Stop removing once within limit

                keys_to_delete.append(key)
                current_size -= entry.get("size", 0) # Subtract size of removed entry

            for key in keys_to_delete:
                self._delete_entry(key)

            if keys_to_delete:
                self._save_metadata() # Save metadata after deletions
                logger.info(f"Removed {len(keys_to_delete)} oldest entries to enforce size limit.")
                logger.debug(f"New cache size: {sum(entry.get('size', 0) for entry in self._metadata.values()) / (1024*1024):.1f} MB.")
            else:
                 logger.warning("Could not reduce cache size below limit by removing oldest entries.")


    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics."""
        with self._lock:
             total_size_bytes = sum(entry.get("size", 0) for entry in self._metadata.values())
             entry_count = len(self._metadata)
             return {
                 "initialized": self._initialized,
                 "cache_dir": str(self.cache_dir),
                 "max_size_mb": self.max_size_bytes / (1024*1024),
                 "ttl_seconds": self.ttl_seconds,
                 "total_size_bytes": total_size_bytes,
                 "total_size_mb": total_size_bytes / (1024*1024),
                 "entry_count": entry_count,
                 "metadata_file": str(self._cache_metadata_file)
             }


# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     # Create a temporary directory for testing the cache
#     test_cache_dir = Path(tempfile.mkdtemp(prefix="ytpro_cache_test_"))
#     logger.info(f"Using temporary cache directory: {test_cache_dir}")

#     # Create a mock CacheManager instance
#     cache_manager = CacheManager(cache_dir=str(test_cache_dir), max_size_mb=10, ttl_seconds=5) # 10 MB limit, 5s TTL

#     # Test caching transcription
#     transcription_data = {"title": "Test Video", "segments": [{"text": "hello", "start": 0, "end": 1}]}
#     base_key_transcription = "https://www.youtube.com/watch?v=test_video_transcription"
#     if cache_manager.set(base_key_transcription, CacheType.TRANSCRIPTION, transcription_data):
#          logger.info("Transcription data cached successfully.")
#     else:
#          logger.error("Failed to cache transcription data.")

#     # Test retrieving transcription
#     retrieved_transcription = cache_manager.get(base_key_transcription, CacheType.TRANSCRIPTION)
#     if retrieved_transcription:
#          logger.info(f"Retrieved transcription data: {retrieved_transcription}")
#          assert retrieved_transcription == transcription_data
#     else:
#          logger.warning("Failed to retrieve transcription data from cache.")


#     # Test caching audio (create a dummy audio file)
#     dummy_audio_path = test_cache_dir / "dummy_audio.wav"
#     with open(dummy_audio_path, 'wb') as f:
#          f.write(b"This is dummy audio data." * 100) # Create a small file
#     base_key_audio = "https://www.youtube.com/watch?v=test_video_audio"
#     cached_audio_path = cache_manager.set(base_key_audio, CacheType.AUDIO, str(dummy_audio_path))
#     if cached_audio_path:
#          logger.info(f"Audio file cached successfully at: {cached_audio_path}")
#          assert Path(cached_audio_path).exists()
#     else:
#          logger.error("Failed to cache audio file.")

#     # Test retrieving audio
#     retrieved_audio_path = cache_manager.get(base_key_audio, CacheType.AUDIO)
#     if retrieved_audio_path:
#          logger.info(f"Retrieved audio path: {retrieved_audio_path}")
#          assert Path(retrieved_audio_path).exists()
#     else:
#          logger.warning("Failed to retrieve audio path from cache.")

#     # Test TTL (wait for cache entry to expire)
#     # logger.info("Waiting 6 seconds to test TTL...")
#     # time.sleep(6)
#     # expired_transcription = cache_manager.get(base_key_transcription, CacheType.TRANSCRIPTION)
#     # if expired_transcription is None:
#     #      logger.info("Transcription cache entry expired as expected.")
#     # else:
#     #      logger.error("Transcription cache entry did NOT expire.")

#     # Test size limit (add more data than the limit)
#     logger.info("Adding data to test size limit...")
#     for i in range(20):
#          dummy_data = {"data": f"This is some dummy data entry number {i}." * 500} # Create data larger than 10 MB total
#          base_key_dummy = f"dummy_key_{i}"
#          cache_manager.set(base_key_dummy, CacheType.TRANSCRIPTION, dummy_data)
#          logger.debug(f"Added dummy entry {i}. Current cache stats: {cache_manager.get_cache_stats()}")

#     # Check cache stats after adding many entries
#     final_stats = cache_manager.get_cache_stats()
#     logger.info(f"Final cache stats after size limit test: {final_stats}")
#     assert final_stats["total_size_bytes"] <= cache_manager.max_size_bytes

#     # Test clearing cache
#     # cache_manager.clear()
#     # logger.info(f"Cache stats after clearing: {cache_manager.get_cache_stats()}")
#     # assert cache_manager.get_cache_stats()["entry_count"] == 0

#     # Clean up temporary directory
#     # try:
    pass
#     #     shutil.rmtree(test_cache_dir)
#     #     logger.info(f"Cleaned up temporary cache directory: {test_cache_dir}")
#     # except Exception as e:
#     #     logger.error(f"Failed to clean up temporary cache directory {test_cache_dir}: {e}")

