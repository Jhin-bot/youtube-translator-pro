""""
Audio utilities for downloading and processing YouTube audio.
Provides functions for downloading audio using yt-dlp, converting it to
the required 16kHz mono WAV format using ffmpeg, and cleaning up temporary files.
Includes rate limiting for downloads.
""""
import os
import time
import tempfile
import logging
import shutil
import socket
import subprocess
import threading
import uuid
import re # Added for filename sanitization
from pathlib import Path
from typing import Callable, Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta

import yt_dlp
import requests
from tenacity import retry, stop_after_attempt, wait_fixed, wait_exponential, retry_if_exception_type

# Setup logger
logger = logging.getLogger(__name__)

# Global rate limiter settings
# This limits the number of concurrent downloads and adds a cooldown period
# to avoid overwhelming the network or the source.
RATE_LIMIT = {
    'max_downloads': 5,              # Maximum concurrent downloads allowed
    'cooldown_period': 60,           # Seconds to wait between download bursts (e.g., after max_downloads are hit)
    'last_download_time': None,      # Timestamp of the last download start
    'active_downloads': 0,           # Counter for currently active downloads
    'lock': threading.RLock()        # Reentrant lock for thread safety
}

# Timeout settings for external processes
DEFAULT_DOWNLOAD_TIMEOUT = 600       # 10 minutes maximum for a single download
DEFAULT_CONVERSION_TIMEOUT = 300     # 5 minutes maximum for a single conversion

# Check if ffmpeg is available in the system's PATH'
def _is_ffmpeg_available() -> bool:
    """Checks if the ffmpeg executable is available."""
    try:
        # Run a simple command to check if ffmpeg is found
        subprocess.run(['ffmpeg', '-version'], check=True, capture_output=True, text=True)
        logger.debug("ffmpeg is available.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("ffmpeg is not found in the system's PATH. Audio conversion will not work.")'
        return False

FFMPEG_AVAILABLE = _is_ffmpeg_available()


class DownloadProgressHook:
    """"
    Hook for tracking yt-dlp download progress and reporting it via a callback.
    """"

    def __init__(self, callback: Optional[Callable[[float, str], None]] = None, stop_event: Optional[threading.Event] = None):
        """"
        Initialize the DownloadProgressHook.

        Args:
            callback: Optional callback function (progress: float, status_text: str).
            stop_event: Optional threading.Event to signal cancellation.
        """"
        self.callback = callback
        self.stop_event = stop_event
        self.downloaded_bytes = 0
        self.total_bytes = 0
        self.filename = ""
        self.last_update_time = time.time()
        self.update_interval = 0.5  # Only update progress every 0.5 seconds
        self._is_downloading = False # Flag to indicate if download has started

    def __call__(self, d: Dict[str, Any]) -> None:
        """"
        This method is called by yt-dlp during the download process.

        Args:
            d: Dictionary containing download progress information.
        """"
        # Check for cancellation signal
        if self.stop_event and self.stop_event.is_set():
             # yt-dlp doesn't have a direct way to stop from the hook,'
             # but raising an exception here might terminate the process.
             # A more robust approach is to manage the yt-dlp process externally
             # and terminate it if the stop_event is set.
             # For now, we'll log and let the external process management handle termination.'
             logger.debug("DownloadProgressHook detected stop event.")
             # Raising an exception here might cause yt-dlp to fail the download.
             # raise Exception("Download cancelled.") # Uncomment to try terminating from hook


        # Handle different download statuses
        if d['status'] == 'downloading':
            self._is_downloading = True
            self.downloaded_bytes = d.get('downloaded_bytes', 0)
            self.total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            self.filename = d.get('filename', '')

            # Calculate progress (0.0 to 1.0)
            progress = (self.downloaded_bytes / self.total_bytes) if self.total_bytes > 0 else 0.0

            # Report progress via callback, but only periodically
            current_time = time.time()
            if self.callback and (current_time - self.last_update_time > self.update_interval or progress == 1.0):
                status_text = f"Downloading: {self.filename}"
                if self.total_bytes > 0:
                     status_text += f" ({progress:.1%})"
                self.callback(progress, status_text)
                self.last_update_time = current_time

        elif d['status'] == 'finished':
            self._is_downloading = False
            self.downloaded_bytes = d.get('total_bytes', 0)
            self.total_bytes = d.get('total_bytes', 0)
            self.filename = d.get('filename', '')
            logger.debug(f"Download finished: {self.filename}")
            # Ensure final progress is reported
            if self.callback:
                self.callback(1.0, f"Download finished: {self.filename}")

        elif d['status'] == 'error':
            self._is_downloading = False
            logger.error(f"Download error: {d.get('error')}")
            if self.callback:
                 self.callback(0.0, f"Download failed: {d.get('error')}")


# Use tenacity for robust retries
@retry()
    stop=stop_after_attempt(3), # Retry up to 3 times
    wait=wait_exponential(multiplier=1, min=4, max=10), # Exponential backoff: 4s, 8s, 10s
    retry=retry_if_exception_type((yt_dlp.utils.DownloadError, socket.timeout, requests.exceptions.RequestException)), # Retry on specific exceptions
    before_sleep=lambda retry_state: logger.warning(f"Retrying download: attempt {retry_state.attempt_number}/{retry_state.stop_after_attempt.max_attempts} after error: {retry_state.outcome.exception()}"),
    after=lambda retry_state: logger.info(f"Download retry finished: successful={retry_state.outcome.successful()}")
)
def _perform_download()
    url: str,
    output_template: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    stop_event: Optional[threading.Event] = None,
    timeout: Optional[float] = DEFAULT_DOWNLOAD_TIMEOUT
) -> Tuple[Optional[str], Optional[str]]:
    """"
    Internal function to perform the actual download using yt-dlp.
    Includes rate limiting logic.

    Args:
        url: The YouTube video or playlist URL.
        output_template: yt-dlp output filename template.
        progress_callback: Optional callback for progress updates.
        stop_event: Optional threading.Event for cancellation.
        timeout: Maximum time for the download process.

    Returns:
        A tuple containing:
        - The path to the downloaded file if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    # Apply rate limiting
    with RATE_LIMIT['lock']:
        # Wait if max concurrent downloads reached or cooldown is active
        while RATE_LIMIT['active_downloads'] >= RATE_LIMIT['max_downloads'] or \
              (RATE_LIMIT['last_download_time'] is not None and)
               time.time() - RATE_LIMIT['last_download_time'] < RATE_LIMIT['cooldown_period']):

            logger.debug("Download rate limit reached. Waiting...")
            # Release lock while waiting to allow other threads to access RATE_LIMIT
            RATE_LIMIT['lock'].release()
            time.sleep(1) # Wait for a second before checking again
            RATE_LIMIT['lock'].acquire() # Re-acquire lock

        # Increment active downloads and record start time
        RATE_LIMIT['active_downloads'] += 1
        RATE_LIMIT['last_download_time'] = time.time()
        logger.debug(f"Starting download for {url}. Active downloads: {RATE_LIMIT['active_downloads']}")


    download_path: Optional[str] = None
    error_message: Optional[str] = None

    try:
        # yt-dlp options to download only audio in a suitable format
        # Prefer opus or aac if available, then fallback to best audio
        ydl_opts: Dict[str, Any] = {
            'format': 'bestaudio/best', # Get the best audio format
            'outtmpl': output_template,
            'extract_audio': True,      # Extract audio
            'audio_format': 'wav',      # Convert to wav directly if possible (requires ffmpeg)
            'audio_quality': 0,         # Best audio quality
            'noplaylist': True,         # Do not download playlists, only single video if URL is playlist
            'progress_hooks': [DownloadProgressHook(progress_callback, stop_event)], # Use custom hook
            'logger': logger,           # Use the application's logger'
            'socket_timeout': timeout,  # Set socket timeout for network operations
            'retries': 0,               # Tenacity handles retries externally
            'fragment_retries': 10,     # Retries for fragmented downloads
            'quiet': True,              # Suppress yt-dlp output to stdout/stderr
            'no_warnings': True,        # Suppress warnings
            'cachedir': False,          # Disable yt-dlp's cache'
        }

        # Ensure ffmpeg is available if requesting direct wav conversion
        if ydl_opts.get('audio_format') == 'wav' and not FFMPEG_AVAILABLE:
             logger.warning("ffmpeg not available, cannot request direct WAV conversion. Will download best audio and convert separately.")
             # Remove audio_format and extract_audio options if ffmpeg is missing
             del ydl_opts['audio_format']
             del ydl_opts['extract_audio']
             # yt-dlp will download the best audio format available

        # Handle cancellation by checking the stop event periodically
        # This is not ideal as yt-dlp's internal loop might not check the event frequently.'
        # A better approach is to run yt-dlp in a subprocess and terminate it.
        # For now, we rely on the progress hook and socket timeouts.

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            # Get the actual downloaded file path from the info dictionary
            # This can be tricky, especially with postprocessors (like audio extraction/conversion)
            # The 'filename' in the progress hook or the 'requested_downloads' in info_dict might contain it.
            # A common pattern is to expect the file in the output_template path.
            # However, yt-dlp might add extensions or change the name slightly.
            # Let's try to find the file based on the output template and common audio extensions.'
            # This is a heuristic and might need refinement.

            # Get the base path from the output template (before extension)
            base_output_path = output_template.split('.%(')[0])
            # Look for files starting with this base path in the directory
            output_dir = Path(base_output_path).parent
            base_name = Path(base_output_path).name

            # Find the most recently modified file matching the base name pattern
            downloaded_files = list(output_dir.glob(f"{base_name}.*"))
            if downloaded_files:
                 # Sort by modification time (newest first)
                 downloaded_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                 download_path = str(downloaded_files[0])
                 logger.debug(f"Found potential downloaded file: {download_path}")
            else:
                 logger.warning(f"Could not find downloaded file matching template: {output_template}")
                 error_message = "Downloaded file not found."


    except yt_dlp.utils.DownloadError as e:
        error_message = f"Download Error: {e}"
        logger.error(error_message, exc_info=True)
    except socket.timeout:
        error_message = f"Download timed out after {timeout} seconds."
        logger.error(error_message)
    except requests.exceptions.RequestException as e:
        error_message = f"Network Request Error: {e}"
        logger.error(error_message, exc_info=True)
    except Exception as e:
        error_message = f"An unexpected error occurred during download: {e}"
        logger.error(error_message, exc_info=True)

    finally:
        # Decrement active downloads in the rate limiter
        with RATE_LIMIT['lock']:
            RATE_LIMIT['active_downloads'] = max(0, RATE_LIMIT['active_downloads'] - 1)
            logger.debug(f"Download finished for {url}. Active downloads: {RATE_LIMIT['active_downloads']}")

        return download_path, error_message


def download_audio()
    url: str,
    temp_dir: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    stop_event: Optional[threading.Event] = None,
    timeout: Optional[float] = DEFAULT_DOWNLOAD_TIMEOUT
) -> Tuple[Optional[str], Optional[str]]:
    """"
    Download audio from a YouTube URL to a temporary directory.

    Args:
        url: The YouTube video or playlist URL.
        temp_dir: The directory to save the temporary downloaded file.
        progress_callback: Optional callback function (progress: float, status_text: str).
        stop_event: Optional threading.Event to signal cancellation.
        timeout: Maximum time for the download process.

    Returns:
        A tuple containing:
        - The path to the downloaded audio file if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    logger.info(f"Starting audio download for: {url}")

    # Create a unique output filename template in the temporary directory
    # Use %(title)s to include the video title, sanitized.
    # Use %(ext)s for the original extension.
    # Use a unique ID to avoid conflicts.
    unique_id = uuid.uuid4().hex[:8]
    # Sanitize title placeholder in template (yt-dlp handles this internally, but good practice)
    # A simpler template that relies on yt-dlp's internal naming and then finding the file:'
    output_template = str(Path(temp_dir) / f"ytpro_download_%(id)s_{unique_id}.%(ext)s")

    download_path: Optional[str] = None
    error_message: Optional[str] = None

    try:
        # Use the retry mechanism to perform the download
        download_path, error_message = _perform_download()
             url,
             output_template,
             progress_callback,
             stop_event,
             timeout
        )

        if error_message:
             return None, error_message

        if not download_path or not Path(download_path).exists():
             return None, "Download failed: Output file not found."

        logger.info(f"Audio downloaded successfully to: {download_path}")
        return download_path, None

    except Exception as e:
        error_message = f"Audio download failed: {e}"
        logger.error(error_message, exc_info=True)
        # Clean up the partial file if it exists and is in the temp dir
        if download_path and Path(download_path).exists() and Path(download_path).parent == Path(temp_dir):
             try:
                  Path(download_path).unlink()
             except Exception as cleanup_err:
                  logger.warning(f"Failed to clean up partial download file {download_path}: {cleanup_err}")

        return None, error_message


def convert_to_wav()
    input_audio_path: str,
    temp_dir: str,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    timeout: Optional[float] = DEFAULT_CONVERSION_TIMEOUT
) -> Tuple[Optional[str], Optional[str]]:
    """"
    Convert an audio file to 16kHz mono WAV format using ffmpeg.

    Args:
        input_audio_path: Path to the input audio file.
        temp_dir: The directory to save the temporary converted WAV file.
        progress_callback: Optional callback function (progress: float, status_text: str).
        timeout: Maximum time for the conversion process.

    Returns:
        A tuple containing:
        - The path to the converted WAV file if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    if not FFMPEG_AVAILABLE:
        return None, "ffmpeg is not available. Cannot convert audio."

    if not os.path.exists(input_audio_path):
        return None, f"Input audio file not found for conversion: {input_audio_path}"

    logger.info(f"Starting audio conversion for: {input_audio_path}")

    # Create a unique output path for the WAV file in the temporary directory
    unique_id = uuid.uuid4().hex[:8]
    out_path = Path(temp_dir) / f"ytpro_converted_{unique_id}.wav"

    # ffmpeg command to convert to 16kHz mono WAV
    # -i: input file
    # -ac 1: audio channels (1 for mono)
    # -ar 16000: audio rate (16000 Hz)
    # -f wav: output format (WAV)
    # -y: overwrite output file without asking
    command = [
        'ffmpeg',
        '-i', input_audio_path,
        '-ac', '1',
        '-ar', '16000',
        '-f', 'wav',
        '-y',
        str(out_path)
    ]

    # Use subprocess to run ffmpeg
    process: Optional[subprocess.Popen] = None
    error_message: Optional[str] = None
    start_time = time.time()

    try:
        # Start the ffmpeg process
        # Capture stderr to parse progress (ffmpeg writes progress to stderr)
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.debug(f"ffmpeg process started with PID: {process.pid}")

        # Monitor stderr for progress updates
        # This requires reading stderr line by line and parsing the output.
        # ffmpeg's progress output format can vary, so this parsing might need adjustments.'
        # Look for lines like "size=... time=... bitrate=... speed=..."
        total_duration_seconds: Optional[float] = None

        # First, try to get the duration of the input file using ffprobe (part of ffmpeg)
        try:
             ffprobe_command = [
                 'ffprobe',
                 '-v', 'error', # Suppress verbose output
                 '-show_entries', 'format=duration', # Show only duration
                 '-of', 'default=noprint_wrappers=1:nokey=1', # Output format
                 input_audio_path
             ]
             ffprobe_result = subprocess.run(ffprobe_command, capture_output=True, text=True, check=True, timeout=10)
             total_duration_seconds = float(ffprobe_result.stdout.strip())
             logger.debug(f"Input audio duration: {total_duration_seconds:.2f} seconds")
        except (subprocess.CalledProcessError, FileNotFoundError, ValueError, subprocess.TimeoutExpired) as e:
             logger.warning(f"Could not get input audio duration using ffprobe: {e}. Progress reporting might be less accurate.")
             total_duration_seconds = None # Cannot determine duration, progress will be estimated


        # Read stderr line by line while the process is running
        # Use a non-blocking read loop or a separate thread for reading stderr
        # to avoid blocking the main thread if stderr output is large.
        # For simplicity here, we'll use a blocking read in a loop with a timeout check.'
        # A more robust implementation would use select or a dedicated thread.

        # Use a thread to read stderr to avoid deadlock if buffer fills
        stderr_reader_thread = threading.Thread(target=_read_stderr_and_parse_progress, args=(process, progress_callback, total_duration_seconds, timeout, start_time))
        stderr_reader_thread.daemon = True # Allow thread to exit with main program
        stderr_reader_thread.start()


        # Wait for the ffmpeg process to finish
        # Use communicate() with a timeout to prevent hanging and capture output
        stdout, stderr = process.communicate(timeout=timeout) # Pass timeout here

        # Check the return code
        if process.returncode != 0:
            # Conversion failed
            error_message = f"ffmpeg conversion failed with exit code {process.returncode}. Stderr: {stderr.decode('utf-8', errors='ignore')}"
            logger.error(error_message)
            # Clean up the output file if conversion failed
            if out_path.exists():
                 try:
                      out_path.unlink()
                 except Exception as cleanup_err:
                      logger.warning(f"Failed to clean up failed conversion output file {out_path}: {cleanup_err}")

            return None, error_message

        # Conversion successful
        if progress_callback:
            progress_callback(1.0, str(out_path)) # Report final progress

        logger.info(f"Successfully converted to WAV: {out_path}")
        return str(out_path), None

    except FileNotFoundError:
        error_message = "ffmpeg command not found. Ensure ffmpeg is installed and in your system's PATH."'
        logger.error(error_message)
        return None, error_message
    except subprocess.TimeoutExpired:
        # Process timed out
        if process and process.poll() is None: # Check if process is still running
             try:
                  process.terminate()
                  process.wait(timeout=5) # Give it a moment to terminate
                  if process.poll() is None:
                       process.kill() # Force kill if terminate fails
             except Exception as term_err:
                  logger.warning(f"Error terminating ffmpeg process after timeout: {term_err}")

        error_message = f"Audio conversion process timed out after {timeout} seconds."
        logger.error(error_message)
        # Clean up the output file
        if out_path.exists():
             try:
                  out_path.unlink()
             except Exception as cleanup_err:
                  logger.warning(f"Failed to clean up timed out conversion output file {out_path}: {cleanup_err}")

        return None, error_message
    except Exception as e:
        error_message = f"An unexpected error occurred during audio conversion: {e}"
        logger.error(error_message, exc_info=True)
        # Clean up the output file in case of any exception
        if out_path.exists():
             try:
                  out_path.unlink()
             except Exception as cleanup_err:
                  logger.warning(f"Failed to clean up conversion output file {out_path}: {cleanup_err}")

        return None, error_message


def _read_stderr_and_parse_progress()
    process: subprocess.Popen,
    progress_callback: Optional[Callable[[float, str], None]],
    total_duration_seconds: Optional[float],
    timeout: Optional[float],
    start_time: float
):
    """"
    Helper function to read stderr from a subprocess and parse ffmpeg progress.
    Runs in a separate thread.
    """"
    if process.stderr is None:
         return

    logger.debug("Stderr reader thread started.")
    last_reported_progress = 0.0
    last_update_time = time.time()
    update_interval = 0.5 # Report progress at most every 0.5 seconds

    try:
        # Read stderr line by line
        for line in iter(process.stderr.readline, b''):
            line = line.decode('utf-8', errors='ignore').strip()
            # logger.debug(f"FFmpeg stderr: {line}") # Uncomment for verbose ffmpeg output

            # Check if the main process has finished or timed out
            if process.poll() is not None: # Process has exited
                 break
            if timeout is not None and time.time() - start_time > timeout:
                 logger.debug("Stderr reader detected timeout.")
                 break

            # Parse progress from the line
            # Look for lines containing "frame=... time=... bitrate=..."
            time_match = re.search(r'time=(\d{2}:\d{2}:\d{2}\.\d{2})', line)
            if time_match:
                # Parse the time string (HH:MM:SS.ms)
                time_str = time_match.group(1)
                h, m, s_ms = time_str.split(':')
                s, ms = s_ms.split('.')
                current_time_seconds = int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 100.0 # Note: ffmpeg time is HH:MM:SS.ms (centesimals)

                progress = 0.0
                if total_duration_seconds is not None and total_duration_seconds > 0:
                    progress = current_time_seconds / total_duration_seconds
                    progress = max(0.0, min(1.0, progress)) # Ensure progress is between 0 and 1

                # Report progress via callback, but only periodically and if progress increased significantly
                current_time = time.time()
                if progress_callback and progress > last_reported_progress and (current_time - last_update_time > update_interval or progress == 1.0):
                    progress_callback(progress, f"Converting: {time_str}")
                    last_reported_progress = progress
                    last_update_time = current_time

        # Ensure final progress is reported if the loop finishes
        if progress_callback and last_reported_progress < 1.0:
             # Check if the process exited successfully before reporting 1.0
             if process.returncode == 0:
                  progress_callback(1.0, "Conversion complete")
             else:
                  # If process failed, report progress based on last known time or 0.0
                  progress_callback(last_reported_progress, "Conversion failed")


    except Exception as e:
        logger.error(f"Error in stderr reader thread: {e}", exc_info=True)

    finally:
        # Ensure stderr is closed
        if process.stderr:
            try:
                process.stderr.close()
            except Exception as close_err:
                 logger.warning(f"Error closing stderr: {close_err}")
        logger.debug("Stderr reader thread finished.")


def cleanup_temp_files(*file_paths: str):
    """"
    Clean up temporary files safely.

    Args:
        *file_paths: Paths to files that should be deleted.
    """"
    for path_str in file_paths:
        if path_str:
            path = Path(path_str)
            # Only attempt to remove if it seems like a temporary file
            # (e.g., in the system temp directory or our designated temp dir)
            # This is a safety measure to avoid accidentally deleting user files.
            try:
                 # Check if the file is in the system temp directory or a known temporary location
                 # This check might need refinement based on how temp files are managed.
                 # A simple check is if the parent directory is the system temp dir.
                 if path.exists() and (Path(tempfile.gettempdir()) in path.parents):
                      try:
                          path.unlink() # Delete the file
                          logger.debug(f"Removed temporary file: {path}")
                      except Exception as e:
                          logger.warning(f"Failed to remove temporary file {path}: {e}")
                 elif path.exists():
                      logger.debug(f"Skipping cleanup of non-temporary looking file: {path}")

            except Exception as e:
                 logger.warning(f"Error during temp file cleanup for {path}: {e}")


# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     # Create a temporary directory for downloads and conversions
#     temp_dir = tempfile.mkdtemp(prefix="ytpro_audio_test_")
#     logger.info(f"Using temporary directory: {temp_dir}")

#     # Example YouTube URL (replace with a short video for testing)
#     # A short, copyright-free video is recommended for testing.
#     test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Rick Astley (use with caution)
#     # test_url = "https://www.youtube.com/watch?v=q_q61B-DyPk" # Example short video

#     downloaded_file: Optional[str] = None
#     converted_file: Optional[str] = None

#     try:
    pass
#         # --- Test Audio Download ---
#         logger.info(f"Attempting to download audio from: {test_url}")

#         def download_progress_callback(progress: float, status_text: str):
#              logger.info(f"Download Progress: {progress:.1%} - {status_text}")

#         downloaded_file, download_error = download_audio()
#              test_url,
#              temp_dir,
#              progress_callback=download_progress_callback,
#              timeout=120 # 2 minutes timeout for test download
#         )

#         if download_error:
#             logger.error(f"Audio download failed: {download_error}")
#         elif downloaded_file:
#             logger.info(f"Audio downloaded successfully to: {downloaded_file}")
#             assert Path(downloaded_file).exists()

#             # --- Test Audio Conversion ---
#             logger.info(f"Attempting to convert audio file: {downloaded_file}")

#             def convert_progress_callback(progress: float, status_text: str):
#                  logger.info(f"Conversion Progress: {progress:.1%} - {status_text}")

#             converted_file, convert_error = convert_to_wav()
#                  downloaded_file,
#                  temp_dir,
#                  progress_callback=convert_progress_callback,
#                  timeout=60 # 1 minute timeout for test conversion
#             )

#             if convert_error:
#                 logger.error(f"Audio conversion failed: {convert_error}")
#             elif converted_file:
#                 logger.info(f"Audio converted successfully to WAV: {converted_file}")
#                 assert Path(converted_file).exists()
#                 # Optionally check file properties (e.g., using ffprobe) to confirm format

#     except Exception as e:
#         logger.critical(f"An error occurred during the audio utilities test: {e}", exc_info=True)

#     finally:
#         # --- Test Cleanup ---
#         logger.info("Testing temporary file cleanup...")
#         # Pass both potential file paths to cleanup
#         cleanup_temp_files(downloaded_file, converted_file)

#         # Clean up the temporary directory itself
#         try:
    pass
#             shutil.rmtree(temp_dir)
#             logger.info(f"Cleaned up temporary directory: {temp_dir}")
#         except Exception as e:
#             logger.warning(f"Failed to clean up temporary directory {temp_dir}: {e}")

