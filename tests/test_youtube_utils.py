"""
Tests for YouTube utility functions.
"""

import pytest
from unittest.mock import patch, MagicMock

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
    
    @patch('src.utils.youtube_utils.pytube.YouTube')
    def test_download_youtube_audio_success(self, mock_youtube, temp_dir):
        """Test that download_youtube_audio successfully downloads audio."""
        from src.utils.youtube_utils import download_youtube_audio
        
        # Create mock YouTube object
        mock_youtube_instance = MagicMock()
        mock_youtube.return_value = mock_youtube_instance
        
        # Configure mock
        mock_stream = MagicMock()
        mock_stream.abr = "128kbps"
        mock_stream.mime_type = "audio/mp4"
        mock_youtube_instance.streams.filter.return_value.order_by.return_value.desc.return_value.first.return_value = mock_stream
        mock_youtube_instance.title = "Test Video"
        mock_youtube_instance.author = "Test Author"
        mock_youtube_instance.length = 60
        mock_youtube_instance.thumbnail_url = "https://example.com/thumbnail.jpg"
        mock_youtube_instance.video_id = "dQw4w9WgXcQ"
        mock_youtube_instance.publish_date = None
        mock_youtube_instance.views = 1000
        
        # Mock download method
        mock_stream.download.return_value = f"{temp_dir}/test_video.mp4"
        
        # Mock ffmpeg
        with patch('src.utils.youtube_utils.ffmpeg') as mock_ffmpeg:
            mock_ffmpeg.input.return_value.output.return_value.global_args.return_value.global_args.return_value.run.return_value = None
            
            # Call function
            with patch('src.utils.youtube_utils.tempfile.mkdtemp', return_value=temp_dir):
                result = download_youtube_audio(
                    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    output_dir=temp_dir,
                    format="wav",
                    sample_rate=16000
                )
            
            # Assertions
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[1], dict)
            assert result[1]["title"] == "Test Video"
            assert result[1]["video_id"] == "dQw4w9WgXcQ"
