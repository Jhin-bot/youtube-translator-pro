"""
YouTube utility functions for downloading and extracting information from YouTube videos.

Provides functionality for:
- Validating YouTube URLs (with support for all URL formats)
- Downloading audio from YouTube videos
- Extracting video metadata
- Managing YouTube API interactions
"""

import os
import re
import time
import logging
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Union, List, Callable
from urllib.parse import parse_qs, urlparse

import pytube
import ffmpeg
from pytube.exceptions import RegexMatchError, VideoUnavailable

from src.config import setup_logging
from src.utils.error_handling import YoutubeError, try_except_decorator

# Initialize logger
logger = setup_logging()

def download_youtube_audio(
    url: str,
    output_dir: Union[str, Path],
    format: str = "wav",
    sample_rate: int = 16000,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Download audio from a YouTube video and convert to the specified format.
    
    Args:
        url: YouTube URL
        output_dir: Directory to save temporary files
        format: Audio format (wav, mp3, etc.)
        sample_rate: Sample rate for the output audio (Hz)
        progress_callback: Optional callback function for progress updates
        
    Returns:
        Tuple containing:
        - Path to the downloaded audio file
        - Dictionary with video information (title, duration, etc.)
    """
    try:
        # Validate if output directory exists
        output_path = Path(output_dir)
        if not output_path.exists():
            output_path.mkdir(parents=True, exist_ok=True)
        
        # Check if pytube is available, otherwise show error
        try:
            from pytube import YouTube
            import pytube.exceptions
        except ImportError:
            logger.error("pytube not installed - required for YouTube downloads")
            raise ImportError("pytube library is required for YouTube downloads. Install with: pip install pytube")
        
        # Import audio processing libraries
        try:
            import ffmpeg
        except ImportError:
            logger.error("ffmpeg-python not installed - required for audio processing")
            raise ImportError("ffmpeg-python library is required for audio processing. Install with: pip install ffmpeg-python")
        
        # Create a temp directory for processing
        temp_dir = tempfile.mkdtemp(dir=output_path if output_path.exists() else None)
        temp_path = Path(temp_dir)
        
        # Report progress
        if progress_callback:
            progress_callback(0.1, "Fetching video information...")
        
        # Initialize YouTube object and get video info
        try:
            yt = YouTube(url, on_progress_callback=lambda stream, chunk, bytes_remaining: _report_download_progress(
                stream, chunk, bytes_remaining, progress_callback
            ))
            
            video_info = {
                "title": yt.title,
                "author": yt.author,
                "duration": yt.length,  # Duration in seconds
                "thumbnail_url": yt.thumbnail_url,
                "video_id": yt.video_id,
                "publish_date": yt.publish_date.isoformat() if yt.publish_date else None,
                "views": yt.views,
                "url": url
            }
            
            logger.info(f"Found video: {yt.title} ({yt.length}s)")
            
        except pytube.exceptions.RegexMatchError:
            logger.error(f"Invalid YouTube URL: {url}")
            raise ValueError(f"Invalid YouTube URL: {url}")
            
        except pytube.exceptions.VideoUnavailable:
            logger.error(f"Video unavailable: {url}")
            raise ValueError(f"Video unavailable: {url}")
            
        except Exception as e:
            logger.error(f"Error fetching video information: {e}")
            raise RuntimeError(f"Error fetching video information: {e}")
        
        # Report progress
        if progress_callback:
            progress_callback(0.2, "Finding audio stream...")
        
        # Get the audio stream
        try:
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            
            if not audio_stream:
                logger.error(f"No audio stream found for video: {url}")
                raise ValueError(f"No audio stream found for video: {url}")
                
            logger.info(f"Selected audio stream: {audio_stream.abr} {audio_stream.mime_type}")
            
        except Exception as e:
            logger.error(f"Error getting audio stream: {e}")
            raise RuntimeError(f"Error getting audio stream: {e}")
        
        # Report progress
        if progress_callback:
            progress_callback(0.3, "Downloading audio...")
        
        # Download the audio stream
        try:
            # Download to temp directory
            downloaded_file = audio_stream.download(output_path=temp_dir)
            downloaded_path = Path(downloaded_file)
            
            logger.info(f"Downloaded audio to: {downloaded_file}")
            
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            raise RuntimeError(f"Error downloading audio: {e}")
        
        # Report progress
        if progress_callback:
            progress_callback(0.7, "Converting audio format...")
        
        # Convert to WAV with the specified sample rate
        try:
            # Prepare output filename
            output_filename = f"{downloaded_path.stem}.{format}"
            output_file = temp_path / output_filename

            try:
                # Use ffmpeg to convert
                (
                    ffmpeg
                    .input(str(downloaded_path))
                    .output(str(output_file), format=format, acodec='pcm_s16le' if format == 'wav' else 'libmp3lame',
                           ar=sample_rate, ac=1)
                    .global_args('-y')  # Overwrite if exists
                    .global_args('-loglevel', 'error')
                    .run(capture_stdout=True, capture_stderr=True)
                )
                
                logger.info(f"Converted audio to: {output_file}")
                
            except ffmpeg.Error as e:
                logger.error(f"FFmpeg error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")
                raise RuntimeError(f"FFmpeg error: {e.stderr.decode() if hasattr(e, 'stderr') else str(e)}")
            
            # Delete the original downloaded file if conversion successful
            if downloaded_path.exists():
                try:
                    downloaded_path.unlink()
                except Exception as e:
                    # Just log this error but don't fail the whole process
                    logger.warning(f"Could not delete temporary file {downloaded_path}: {e}")
                    # Continue processing anyway
            
        except Exception as e:
            logger.error(f"Error converting audio: {e}")
            raise RuntimeError(f"Error converting audio: {e}")
        
        # Report progress
        if progress_callback:
            progress_callback(1.0, "Audio download and conversion complete")
        
        return str(output_file), video_info
        
    except Exception as e:
        logger.error(f"Error in download_youtube_audio: {e}")
        raise


def _report_download_progress(stream, chunk, bytes_remaining, progress_callback: Optional[Callable[[float, str], None]] = None):
    """
    Progress callback for YouTube downloads.
    
    Args:
        stream: The stream being downloaded
        chunk: The chunk being downloaded
        bytes_remaining: Number of bytes remaining
        progress_callback: User progress callback function
    """
    if not progress_callback:
        return
    
    # Calculate download progress
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage = bytes_downloaded / total_size if total_size > 0 else 0
    
    # Map the download progress (0-1) to the 0.3-0.7 range in our overall process
    mapped_progress = 0.3 + (percentage * 0.4)
    
    # Format message
    if total_size > 1024 * 1024:
        total_mb = total_size / (1024 * 1024)
        downloaded_mb = bytes_downloaded / (1024 * 1024)
        message = f"Downloading: {downloaded_mb:.1f} MB / {total_mb:.1f} MB ({percentage:.1%})"
    else:
        total_kb = total_size / 1024
        downloaded_kb = bytes_downloaded / 1024
        message = f"Downloading: {downloaded_kb:.1f} KB / {total_kb:.1f} KB ({percentage:.1%})"
    
    # Call the progress callback
    progress_callback(mapped_progress, message)


@try_except_decorator
def extract_video_id(url: str) -> Optional[str]:
    """
    Extract the YouTube video ID from a URL.
    
    Supports all YouTube URL formats including:
    - Standard watch URLs: https://www.youtube.com/watch?v=VIDEO_ID
    - Short URLs: https://youtu.be/VIDEO_ID
    - Embed URLs: https://www.youtube.com/embed/VIDEO_ID
    - Shortened URLs with additional parameters
    - Mobile app URLs
    - URLs with timestamps and playlists
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID if found, None otherwise
        
    Raises:
        YoutubeError: If URL parsing fails unexpectedly
    """
    try:
        if not url:
            return None
        
        # Method 1: Parse the URL and extract from query parameters
        parsed_url = urlparse(url)
        
        # youtu.be URLs
        if parsed_url.netloc == 'youtu.be':
            return parsed_url.path.lstrip('/')
        
        # youtube.com URLs with video ID in query string
        if parsed_url.netloc in ('youtube.com', 'www.youtube.com', 'm.youtube.com'):
            if parsed_url.path == '/watch':
                # Standard watch URL
                query_params = parse_qs(parsed_url.query)
                if 'v' in query_params:
                    return query_params['v'][0]
            
            elif '/embed/' in parsed_url.path or '/v/' in parsed_url.path:
                # Embed URL
                return parsed_url.path.split('/')[-1]
            
            elif '/shorts/' in parsed_url.path:
                # Shorts URL
                return parsed_url.path.split('/')[-1]
        
        # Method 2: Fallback to regex for any remaining formats
        youtube_regex = r'(?:youtube\.com/(?:[^/]+/.+/|(?:v|e(?:mbed)?)/|.*[?&]v=)|youtu\.be/)([^"&?/ ]{11})'
        match = re.search(youtube_regex, url)
        
        if match:
            return match.group(1)
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting video ID from {url}: {str(e)}")
        raise YoutubeError(f"Failed to extract video ID from URL: {str(e)}", {"url": url})


def is_valid_youtube_url(url: str) -> bool:
    """
    Check if the given URL is a valid YouTube URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a valid YouTube URL, False otherwise
    """
    return extract_video_id(url) is not None
