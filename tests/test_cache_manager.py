"""
Tests for the CacheManager component.
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta
import pytest
from unittest.mock import patch, MagicMock

from src.utils.cache_manager import CacheManager


class TestCacheManager:
    """Tests for the CacheManager class."""
    
    def test_cache_manager_singleton(self, temp_cache_dir):
        """Test that CacheManager implements the singleton pattern."""
        cache_manager1 = CacheManager(cache_dir=temp_cache_dir)
        cache_manager2 = CacheManager(cache_dir=temp_cache_dir)
        
        # Both instances should be the same object
        assert cache_manager1 is cache_manager2
    
    def test_cache_manager_initialization(self, temp_cache_dir):
        """Test that CacheManager initializes correctly."""
        cache_manager = CacheManager(
            cache_dir=temp_cache_dir,
            max_size_mb=100,
            ttl_days=1,
            enabled=True
        )
        
        # Check that directories were created
        cache_dir = Path(temp_cache_dir)
        assert cache_dir.exists()
        assert (cache_dir / "audio").exists()
        assert (cache_dir / "transcriptions").exists()
        assert (cache_dir / "translations").exists()
        assert (cache_dir / "metadata").exists()
        
        # Check that cache index was created
        assert (cache_dir / "cache_index.json").exists()
        
        # Check settings were applied
        assert cache_manager.max_size_bytes == 100 * 1024 * 1024  # 100MB
        assert cache_manager.ttl_seconds == 1 * 24 * 60 * 60  # 1 day
        assert cache_manager.enabled is True
    
    def test_cache_audio(self, temp_cache_dir, tmp_path):
        """Test caching audio files."""
        # Create a test audio file
        test_audio = tmp_path / "test_audio.wav"
        test_audio.write_bytes(b"test audio data")
        
        # Initialize cache manager
        cache_manager = CacheManager(cache_dir=temp_cache_dir, enabled=True)
        
        # Cache the audio file
        video_id = "test_video_id"
        cached_path = cache_manager.cache_audio(
            video_id=video_id,
            audio_file=str(test_audio),
            metadata={"title": "Test Video"}
        )
        
        # Check that the file was cached
        assert Path(cached_path).exists()
        
        # Check that the entry was added to the cache index
        cache_key = f"audio:{video_id}"
        assert cache_key in cache_manager.cache_index["entries"]
        
        # Check that the entry has the correct metadata
        entry = cache_manager.cache_index["entries"][cache_key]
        assert entry["metadata"]["title"] == "Test Video"
    
    def test_get_cached_audio(self, temp_cache_dir, tmp_path):
        """Test retrieving cached audio files."""
        # Create a test audio file
        test_audio = tmp_path / "test_audio.wav"
        test_audio.write_bytes(b"test audio data")
        
        # Initialize cache manager
        cache_manager = CacheManager(cache_dir=temp_cache_dir, enabled=True)
        
        # Cache the audio file
        video_id = "test_video_id"
        cached_path = cache_manager.cache_audio(
            video_id=video_id,
            audio_file=str(test_audio),
            metadata={"title": "Test Video"}
        )
        
        # Retrieve the cached file
        retrieved_path = cache_manager.get_cached_audio(video_id)
        
        # Check that the correct path was returned
        assert retrieved_path == cached_path
        
        # Check that a hit was recorded in the stats
        assert cache_manager.cache_index["stats"]["hits"] == 1
    
    def test_cache_miss(self, temp_cache_dir):
        """Test behavior when cache is missed."""
        # Initialize cache manager
        cache_manager = CacheManager(cache_dir=temp_cache_dir, enabled=True)
        
        # Try to retrieve a non-existent cache entry
        result = cache_manager.get_cached_audio("non_existent_video")
        
        # Check that None was returned
        assert result is None
        
        # Check that a miss was recorded in the stats
        assert cache_manager.cache_index["stats"]["misses"] == 1
    
    def test_cache_disabled(self, temp_cache_dir, tmp_path):
        """Test behavior when cache is disabled."""
        # Create a test audio file
        test_audio = tmp_path / "test_audio.wav"
        test_audio.write_bytes(b"test audio data")
        
        # Initialize cache manager with caching disabled
        cache_manager = CacheManager(cache_dir=temp_cache_dir, enabled=False)
        
        # Try to cache a file
        video_id = "test_video_id"
        cached_path = cache_manager.cache_audio(
            video_id=video_id,
            audio_file=str(test_audio)
        )
        
        # Check that the original path was returned
        assert cached_path == str(test_audio)
        
        # Try to retrieve from cache
        result = cache_manager.get_cached_audio(video_id)
        
        # Check that None was returned
        assert result is None
    
    def test_cache_expiration(self, temp_cache_dir, tmp_path):
        """Test that cache entries expire correctly."""
        # Create a test audio file
        test_audio = tmp_path / "test_audio.wav"
        test_audio.write_bytes(b"test audio data")
        
        # Initialize cache manager with a short TTL
        cache_manager = CacheManager(
            cache_dir=temp_cache_dir,
            ttl_days=0.0001,  # Very short TTL (~9 seconds)
            enabled=True
        )
        
        # Cache the audio file
        video_id = "test_video_id"
        cache_manager.cache_audio(
            video_id=video_id,
            audio_file=str(test_audio)
        )
        
        # Wait for the cache entry to expire
        time.sleep(10)
        
        # Try to retrieve the cached file
        result = cache_manager.get_cached_audio(video_id)
        
        # Check that None was returned
        assert result is None
    
    def test_cache_cleanup(self, temp_cache_dir, tmp_path):
        """Test that cache cleanup works correctly."""
        # Create test audio files - Make them 2MB each to ensure we clearly exceed limits
        test_files = []
        for i in range(5):
            test_file = tmp_path / f"test_audio_{i}.wav"
            # Create a 2MB file (2 * 1024 * 1024 bytes)
            with open(test_file, 'wb') as f:
                f.write(b"0" * 2 * 1024 * 1024)
            test_files.append(test_file)
        
        # Initialize cache manager with a small max size - make it 5MB to allow 2 files at most
        cache_manager = CacheManager(
            cache_dir=temp_cache_dir,
            max_size_mb=5,  # Only 5MB max (2 files max)
            enabled=True
        )
        
        # First, add the "oldest" files with explicit timestamps
        for i in range(3):  # Add 3 files = 6MB total
            cache_manager.cache_audio(
                video_id=f"test_video_{i}",
                audio_file=str(test_files[i])
            )
            # Set access time to be progressively older for earlier files
            key = f"audio:test_video_{i}"
            older_time = datetime.now() - timedelta(hours=10-i)  # Make a bigger difference
            cache_manager.cache_index["entries"][key]["last_accessed"] = older_time.isoformat()
        
        # Save the modified timestamps
        cache_manager._save_cache_index()
        
        # Check total size - should be around 6MB (3 files * 2MB)
        print(f"Cache size after initial files: {cache_manager.cache_index['stats']['size_bytes']/1024/1024:.2f}MB")
        
        # Force a cleanup to apply the eviction policy
        cache_manager._cleanup_cache()
        
        # Now the cache should contain at most 2 files (5MB max, each file is 2MB)
        # The oldest ones should have been evicted (test_video_0 definitely)
        assert "audio:test_video_0" not in cache_manager.cache_index["entries"]
        
        # At least one of the more recent ones should still be there
        assert "audio:test_video_2" in cache_manager.cache_index["entries"]
        
        # The cache should not exceed max size after cleanup
        current_size = cache_manager.cache_index["stats"]["size_bytes"]
        assert current_size <= cache_manager.max_size_bytes
        
        # We should have at most 2 files in the cache now (each 2MB, max 5MB)
        assert len(cache_manager.cache_index["entries"]) <= 2
    
    def test_clear_cache(self, temp_cache_dir, tmp_path):
        """Test clearing the entire cache."""
        # Create a test audio file
        test_audio = tmp_path / "test_audio.wav"
        test_audio.write_bytes(b"test audio data")
        
        # Initialize cache manager
        cache_manager = CacheManager(cache_dir=temp_cache_dir, enabled=True)
        
        # Cache the audio file
        video_id = "test_video_id"
        cache_manager.cache_audio(
            video_id=video_id,
            audio_file=str(test_audio)
        )
        
        # Clear the cache
        cache_manager.clear_cache()
        
        # Check that the cache is empty
        assert len(cache_manager.cache_index["entries"]) == 0
        assert cache_manager.cache_index["stats"]["size_bytes"] == 0
        
        # Try to retrieve the cached file
        result = cache_manager.get_cached_audio(video_id)
        
        # Check that None was returned
        assert result is None
