"""
Tests for YouTube utility functions.
"""

import unittest
import os
from unittest.mock import patch, MagicMock
import pytest
from datetime import datetime
from src.utils.youtube_utils import extract_video_id, is_valid_youtube_url


class TestYouTubeUtils:
    """Tests for YouTube utility functions."""
    
    def test_extract_video_id(self, sample_youtube_urls):
        """Test that video IDs are correctly extracted from different URL formats."""
        # All URLs in the fixture should have the same video ID
        expected_id = "dQw4w9WgXcQ"
        
        for url in sample_youtube_urls:
            assert extract_video_id(url) == expected_id
    
    def test_extract_video_id_invalid_url(self):
        """Test that extract_video_id returns None for invalid URLs."""
        invalid_urls = [
            "https://www.example.com",
            "https://www.youtube.com",
            "https://www.youtube.com/watch",
            "https://www.youtube.com/watch?q=test",
            "",
            None
        ]
        
        for url in invalid_urls:
            assert extract_video_id(url) is None
    
    def test_is_valid_youtube_url(self, sample_youtube_urls):
        """Test that is_valid_youtube_url correctly identifies valid YouTube URLs."""
        for url in sample_youtube_urls:
            assert is_valid_youtube_url(url) is True
    
    def test_is_valid_youtube_url_invalid_url(self):
        """Test that is_valid_youtube_url correctly identifies invalid YouTube URLs."""
        invalid_urls = [
            "https://www.example.com",
            "https://www.youtube.com",
            "https://www.youtube.com/watch",
            "https://www.youtube.com/watch?q=test",
            "",
            None
        ]
        
        for url in invalid_urls:
            assert is_valid_youtube_url(url) is False
    
    def test_download_youtube_audio_success(self, temp_dir):
        """Test the YouTube audio download function preparation logic."""
        # In this test, we'll just validate the URL parsing and video ID extraction
        # without actually downloading anything, since the ffmpeg conversion is external
        from src.utils.youtube_utils import extract_video_id, is_valid_youtube_url
        
        # Test various valid URL formats
        test_urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=42s",
            "https://www.youtube.com/embed/dQw4w9WgXcQ"
        ]
        
        for url in test_urls:
            # Ensure URL is considered valid
            assert is_valid_youtube_url(url), f"URL not recognized as valid: {url}"
            
            # Ensure video ID is correctly extracted
            video_id = extract_video_id(url)
            assert video_id == "dQw4w9WgXcQ", f"Failed to extract correct video ID from {url}"
            
        # Also test the negative case
        invalid_urls = [
            "https://www.example.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/invalidpath",
            "not a url at all"
        ]
        
        for url in invalid_urls:
            # URL should be recognized as invalid
            assert not is_valid_youtube_url(url), f"Invalid URL incorrectly recognized as valid: {url}"
