"""
Integration tests for the full translation pipeline.
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.youtube_utils import download_youtube_audio
from src.utils.cache_manager import CacheManager


class TestTranslationPipeline:
    """Integration tests for the full translation pipeline."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            yield tmpdirname
    
    @pytest.fixture
    def cache_manager(self, temp_dir):
        """Create a cache manager instance for testing."""
        cache_dir = os.path.join(temp_dir, "cache")
        return CacheManager(cache_dir=cache_dir, max_size_mb=10, enabled=True)
    
    @patch('src.utils.youtube_utils.pytube.YouTube')
    @patch('src.services.transcription_service.transcribe_audio')
    @patch('src.services.translation_service.translate_text')
    def test_end_to_end_translation(self, mock_translate, mock_transcribe, mock_youtube, 
                                    temp_dir, cache_manager):
        """Test the full end-to-end translation pipeline."""
        # 1. Set up YouTube download mock
        mock_youtube_instance = MagicMock()
        mock_youtube.return_value = mock_youtube_instance
        
        mock_stream = MagicMock()
        mock_stream.abr = "128kbps"
        mock_youtube_instance.streams.filter.return_value.order_by.return_value.desc.return_value.first.return_value = mock_stream
        
        # Mock YouTube video metadata
        mock_youtube_instance.title = "Test Video"
        mock_youtube_instance.author = "Test Author"
        mock_youtube_instance.length = 60
        mock_youtube_instance.video_id = "dQw4w9WgXcQ"
        
        # Set up test audio file
        test_audio_path = os.path.join(temp_dir, "test_audio.wav")
        with open(test_audio_path, 'wb') as f:
            f.write(b"dummy audio content")
        
        # Mock download method
        with patch('src.utils.youtube_utils.ffmpeg') as mock_ffmpeg:
            # Setup ffmpeg mock chain
            mock_input = MagicMock()
            mock_output = MagicMock()
            mock_ffmpeg.input.return_value = mock_input
            mock_input.output.return_value = mock_output
            mock_output.global_args.return_value = mock_output
            mock_output.run.return_value = (b"", b"")
            
            # Mock the actual download function to return our test file
            with patch('src.core.pipeline.download_youtube_audio', return_value=(test_audio_path, {
                "title": "Test Video",
                "author": "Test Author",
                "duration": 60,
                "video_id": "dQw4w9WgXcQ"
            })):
                # 2. Mock transcription service
                mock_transcribe.return_value = "This is a test transcription."
                
                # 3. Mock translation service
                mock_translate.return_value = "Esto es una transcripción de prueba."
                
                # Execute the full pipeline
                from src.core.pipeline import translate_youtube_video
                
                result = translate_youtube_video(
                    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    source_language="en",
                    target_language="es",
                    cache_manager=cache_manager
                )
                
                # Verify result contains all expected components
                assert "video_info" in result
                assert "transcription" in result
                assert "translation" in result
                assert result["transcription"] == "This is a test transcription."
                assert result["translation"] == "Esto es una transcripción de prueba."
                assert result["video_info"]["title"] == "Test Video"
    
    def test_caching_integration(self, temp_dir, cache_manager):
        """Test that caching works correctly in the pipeline."""
        # Create a test audio file
        test_audio_path = os.path.join(temp_dir, "cached_audio.wav")
        with open(test_audio_path, 'wb') as f:
            f.write(b"test audio data")
        
        # Cache the audio file
        video_id = "test_video_id"
        cache_manager.cache_audio(video_id, test_audio_path)
        
        # Verify it's in the cache
        cached_path = cache_manager.get_cached_audio(video_id)
        assert cached_path is not None
        
        # Now cache a transcription and translation
        transcription = "This is a test transcription."
        cache_manager.cache_transcription(video_id, "en", transcription)
        
        translation = "Esto es una transcripción de prueba."
        cache_manager.cache_translation(video_id, "en", "es", translation)
        
        # Verify retrieving from cache
        cached_transcription = cache_manager.get_cached_transcription(video_id, "en")
        assert cached_transcription == transcription
        
        cached_translation = cache_manager.get_cached_translation(video_id, "en", "es")
        assert cached_translation == translation
        
        # Test pipeline with cached data
        with patch('src.core.pipeline.download_youtube_audio') as mock_download, \
             patch('src.core.pipeline.transcribe_audio') as mock_transcribe, \
             patch('src.core.pipeline.translate_text') as mock_translate:
            
            # These should not be called if caching works
            mock_download.side_effect = Exception("Should not be called")
            mock_transcribe.side_effect = Exception("Should not be called")
            mock_translate.side_effect = Exception("Should not be called")
            
            from src.core.pipeline import translate_youtube_video
            with patch('src.utils.youtube_utils.extract_video_id', return_value=video_id):
                result = translate_youtube_video(
                    url=f"https://www.youtube.com/watch?v={video_id}",
                    source_language="en",
                    target_language="es",
                    cache_manager=cache_manager,
                    use_cache=True
                )
                
                # If caching works, we should get results without calling the mocked functions
                assert result["transcription"] == transcription
                assert result["translation"] == translation
