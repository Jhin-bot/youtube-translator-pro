# Standard library imports
import os
import re
import time
import json
import psutil
import logging
import threading
import traceback
import uuid
import tempfile
import shutil
import signal
import atexit
import weakref
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field
from enum import Enum, auto
# threading.local is a class in the threading module, not a separate module
from typing import List, Dict, Any, Optional, Callable, Union, Tuple, Set
from urllib.parse import urlparse
from heapq import heappush, heappop

# Add requests for HTTP functionality
try:
    import requests
except ImportError:
    # Create a mock requests module
    class MockResponse:
        def __init__(self, status_code=200, json_data=None, text=""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self.text = text
        
        def json(self):
            return self._json_data
    
    class MockRequests:
        def get(self, *args, **kwargs):
            return MockResponse()
        def post(self, *args, **kwargs):
            return MockResponse()
    
    requests = MockRequests()

# Local application imports
# Ensure these imports match your file structure
try:
    from audio_utils import download_audio, convert_to_wav, cleanup_temp_files, RATE_LIMIT, DEFAULT_DOWNLOAD_TIMEOUT, DEFAULT_CONVERSION_TIMEOUT
    AUDIO_UTILS_AVAILABLE = True
except ImportError as e:
    logging.error(f"Could not import audio_utils module: {e}. Audio processing disabled.")
    AUDIO_UTILS_AVAILABLE = False
    # Define mock functions if import fails
    download_audio = lambda *args, **kwargs: (None, "Audio utilities not available.")
    convert_to_wav = lambda *args, **kwargs: (None, "Audio utilities not available.")
    cleanup_temp_files = lambda *args: None
    RATE_LIMIT = {'max_downloads': 1, 'cooldown_period': 0, 'last_download_time': None, 'active_downloads': 0, 'lock': threading.RLock()}
    DEFAULT_DOWNLOAD_TIMEOUT = 600
    DEFAULT_CONVERSION_TIMEOUT = 300


try:
    from transcribe import transcribe, VALID_MODELS, WHISPER_AVAILABLE
except ImportError as e:
    logging.error(f"Could not import transcribe module: {e}. Transcription disabled.")
    WHISPER_AVAILABLE = False
    VALID_MODELS = ["small"] # Provide a default model list
    # Define mock function if import fails
    transcribe = lambda *args, **kwargs: (None, "Transcription utilities not available.")


try:
    from translate import translate, get_available_languages
    TRANSLATE_AVAILABLE = True
    AVAILABLE_LANGUAGES = get_available_languages()
except ImportError as e:
    logging.warning(f"Could not import translate module: {e}. Translation disabled.")
    TRANSLATE_AVAILABLE = False
    AVAILABLE_LANGUAGES = {"None": "None"} # Provide a default language list
    # Define mock function if import fails
    translate = lambda *args, **kwargs: (None, "Translation utilities not available.")


try:
    from srt_export import export_srt, export_json, export_vtt # Import all export functions
    EXPORT_AVAILABLE = True
except ImportError as e:
    logging.error(f"Could not import export module: {e}. Exporting disabled.")
    EXPORT_AVAILABLE = False
    # Define mock functions if import fails
    export_srt = lambda *args, **kwargs: (None, "Export utilities not available.")
    export_json = lambda *args, **kwargs: (None, "Export utilities not available.")
    export_vtt = lambda *args, **kwargs: (None, "Export utilities not available.")


try:
    from cache import CacheManager, CacheType
    CACHE_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Could not import cache module: {e}. Caching disabled.")
    CACHE_AVAILABLE = False
    # Define mock class and enums if import fails
    class CacheManager:
        def __init__(self, *args, **kwargs): pass
        def get(self, key, type): return None
        def set(self, key, type, data): return False
        def delete(self, key, type): pass
        def clear(self): pass
        def clear_unused(self, timeout_seconds): pass
        _initialized = False # Mock attribute
    CacheType = Enum("CacheType", ["TRANSCRIPTION", "TRANSLATION", "AUDIO"])


# Setup logger
logger = logging.getLogger(__name__)

# PyQt imports with fallback mechanism
try:
    # First try PyQt6
    try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal
    logger.info("Using PyQt6 for UI components")
except ImportError:
    try:
        # Then try PyQt5
        from PyQt5.QtCore import QObject, pyqtSignal
        logger.info("Using PyQt5 for UI components")
    except ImportError:
        # If neither PyQt6 nor PyQt5 is available, create mock classes
        logger.warning("Neither PyQt6 nor PyQt5 is available. Creating mock classes.")
        
        # Mock QObject class
        class QObject:
            def __init__(self, *args, **kwargs):
                pass
        
        # Mock Signal class
        class Signal:
            def __init__(self, *args):
                pass
            def connect(self, func):
                pass
            def emit(self, *args):
                pass
        
        # Set up alias
        pyqtSignal = Signal

# Global constants (moved from transcribe for better organization)
DEFAULT_RETRY_COUNT = 3
DEFAULT_RETRY_DELAY = 5  # seconds
DEFAULT_MAX_RETRY_DELAY = 60  # seconds
DEFAULT_TEMP_FILE_MAX_AGE = 24 * 60 * 60  # 24 hours
DEFAULT_LOW_DISK_THRESHOLD = 1024 * 1024 * 1024  # 1 GB
DEFAULT_HIGH_CPU_THRESHOLD = 85  # 85% CPU usage
DEFAULT_HIGH_MEM_THRESHOLD = 85  # 85% memory usage
DEFAULT_TASK_TIMEOUT = 3600  # 1 hour max for a single task
DEFAULT_MIN_DISK_SPACE = 200 * 1024 * 1024 # Minimum 200 MB free space required


# --- Enums ---

class TaskStatus(Enum):
    """Represents the status of a single task in the batch."""
    PENDING = auto()        # Task is waiting to be processed
    VALIDATING = auto()     # Validating URL and checking info
    DOWNLOADING = auto()    # Downloading audio
    CONVERTING = auto()     # Converting audio format
    CACHED = auto()         # Result retrieved from cache
    TRANSCRIBING = auto()   # Performing transcription
    TRANSLATING = auto()    # Performing translation
    EXPORTING = auto()      # Exporting results to file(s)
    COMPLETED = auto()      # Task completed successfully
    FAILED = auto()         # Task failed
    CANCELLED = auto()      # Task was cancelled
    SKIPPED = auto()        # Task was skipped (e.g., invalid URL)
    PAUSED = auto()         # Task is paused (part of batch pause)
    RETRYING = auto()       # Task is being retried


class BatchStatus(Enum):
    """Represents the overall status of the batch processing."""
    IDLE = auto()           # No tasks or processing stopped
    RUNNING = auto()        # Processing is active
    PAUSED = auto()         # Processing is paused
    RESUMING = auto()       # Resuming from paused state
    COMPLETED = auto()      # All tasks completed successfully
    CANCELLED = auto()      # Batch was cancelled by user
    FAILED = auto()         # One or more tasks failed
    THROTTLED = auto()      # Processing is slowed due to resource constraints
    STOPPING = auto()       # Batch is in the process of stopping/cancelling


# --- Data Classes ---

@dataclass
class Task:
    """Represents a single transcription/translation task."""
    url: str
    model: str
    target_lang: Optional[str]
    output_dir: str
    formats: List[str]
    status: TaskStatus = TaskStatus.PENDING
    progress: float = 0.0       # 0.0 to 1.0
    error: Optional[str] = None
    retries: int = 0            # Number of retry attempts
    last_attempt_time: Optional[float] = None # Timestamp of the last attempt start
    start_time: Optional[float] = None    # Timestamp when the task started processing
    end_time: Optional[float] = None      # Timestamp when the task finished
    audio_path: Optional[str] = None      # Path to downloaded/converted audio file
    transcription_result: Optional[Dict[str, Any]] = None # Raw transcription result
    translation_result: Optional[Dict[str, Any]] = None   # Raw translation result
    output_files: Dict[str, str] = field(default_factory=dict) # Dictionary of output format: file path
    temp_files: List[str] = field(default_factory=list) # List of temporary files to clean up
    future: Optional[Future] = None       # Future object for the running task


# --- Batch Processor ---

class BatchProcessor(QObject):
    """Manages a batch of transcription/translation tasks."""

    # Signals to communicate with the ApplicationManager/UI
    task_progress_updated = pyqtSignal(dict) # Emits task URL, status, progress, error, output_dir
    batch_progress_updated = pyqtSignal(dict) # Emits overall batch progress and status
    batch_completion_status = pyqtSignal(dict) # Emits a summary report on batch completion
    resource_warning_occurred = pyqtSignal(dict) # Emits warning type and message
    status_message = pyqtSignal(str) # Emits general status messages (e.g., "Loading model...")


    def __init__(self, cache_manager: Optional[CacheManager] = None, concurrency: int = 2, parent: Optional[QObject] = None):
        """"
        Initialize the Batch Processor.

        Args:
            cache_manager: An optional CacheManager instance.
            concurrency: Maximum number of concurrent tasks.
            parent: The parent QObject.
        """"
        super().__init__(parent)
        self.cache_manager = cache_manager # Store CacheManager instance
        self.concurrency = concurrency
        self.tasks: Dict[str, Task] = {} # Dictionary to store tasks by URL
        self.status = BatchStatus.IDLE
        self._lock = threading.RLock() # Lock for thread-safe access to shared data
        self._executor: Optional[ThreadPoolExecutor] = None
        self._futures: Set[Future] = set() # Set to track active task futures
        self._pause_event = threading.Event() # Event for pausing/resuming the batch
        self._cancel_event = threading.Event() # Event for cancelling the batch
        self._shutdown_event = threading.Event() # Event for application shutdown
        self._processing_thread: Optional[threading.Thread] = None # Thread for managing task execution
        self._task_queue: List[Task] = [] # Priority queue for tasks (using list and heappush/heappop)
        self._temp_files_to_cleanup: List[str] = [] # List of temp files for final cleanup
        self._resource_monitor_timer: Optional[QTimer] = None # Timer for resource monitoring
        self._last_resource_warning_time: Dict[str, float] = {} # Track last warning time per type


        # Register cleanup function to run on program exit
        atexit.register(self._final_cleanup)
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, lambda s, f: self.shutdown(wait=False)) # Handle Ctrl+C
        signal.signal(signal.SIGTERM, lambda s, f: self.shutdown(wait=False)) # Handle termination signal
        if hasattr(signal, 'SIGBREAK'): # Handle Ctrl+Break on Windows
             signal.signal(signal.SIGBREAK, lambda s, f: self.shutdown(wait=False))


        # Start resource monitoring timer
        self._start_resource_monitor()


    def _start_resource_monitor(self):
        """Start a timer to periodically monitor system resources."""
        self._resource_monitor_timer = QTimer(self)
        self._resource_monitor_timer.timeout.connect(self._monitor_resources)
        self._resource_monitor_timer.start(5000) # Check every 5 seconds
        logger.debug("Resource monitor timer started.")


    @pyqtSlot()
    def _monitor_resources(self):
        """Periodically check system resources (CPU, memory, disk) and issue warnings."""
        try:
            # Check disk space in the output directory (or a temporary directory)
            # Use the default output directory from settings if no tasks are running
            check_dir = self.tasks[next(iter(self.tasks))].output_dir if self.tasks else (str(Path.home() / "Downloads")) # Fallback to home dir
            disk_usage = psutil.disk_usage(check_dir)
            free_space_gb = disk_usage.free / (1024**3) # Free space in GB

            if disk_usage.free < DEFAULT_LOW_DISK_THRESHOLD:
                 warning_type = "low_disk_space"
                 message = f"Low disk space detected in {check_dir}. Only {free_space_gb:.2f} GB free."
                 self._issue_resource_warning(warning_type, message, free_space_gb)
                 # Consider pausing batch if space is critically low
                 if disk_usage.free < DEFAULT_MIN_DISK_SPACE and self.status == BatchStatus.RUNNING:
                      logger.critical(f"Critically low disk space ({free_space_gb:.2f} GB). Pausing batch.")
                      self.pause() # Pause the batch automatically
                      self.status_message.emit("Critically low disk space. Batch paused.")
                      self._issue_resource_warning("critical_disk", "Critically low disk space. Batch paused.", free_space_gb)


            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1) # Blocking call, but short interval
            if cpu_percent > DEFAULT_HIGH_CPU_THRESHOLD:
                 warning_type = "high_cpu_usage"
                 message = f"High CPU usage detected: {cpu_percent:.1f}%."
                 self._issue_resource_warning(warning_type, message, cpu_percent)


            # Check memory usage
            mem_usage = psutil.virtual_memory()
            mem_percent = mem_usage.percent
            if mem_percent > DEFAULT_HIGH_MEM_THRESHOLD:
                 warning_type = "high_memory_usage"
                 message = f"High memory usage detected: {mem_percent:.1f}%."
                 self._issue_resource_warning(warning_type, message, mem_percent)


            # Check GPU memory usage (requires nvidia-smi or similar, more complex)
            # Placeholder for GPU monitoring
            # try:
            #     if platform.system() == "Windows":
            #         # Example using wmi (Windows Management Instrumentation)
            #         import wmi
            #         c = wmi.WMI()
            #         gpu_info = c.query("SELECT * FROM Win32_VideoController")
            #         for gpu in gpu_info:
            #             # This is a simplified example, actual GPU memory usage is more complex
            #             # and varies by hardware/driver.
            #             # You might need libraries like pynvml for NVIDIA GPUs.
            #             pass
            #     elif platform.system() == "Linux":
            #         # Example using subprocess with nvidia-smi
            #         # Requires nvidia-smi to be in the PATH
            #         try:
            #             result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,nounits,noheader'], capture_output=True, text=True, check=True)
            #             gpu_lines = result.stdout.strip().split('\n')
            #             for line in gpu_lines:
            #                  used_mb, total_mb = map(int, line.split(','))
            #                  gpu_percent = (used_mb / total_mb) * 100 if total_mb > 0 else 0
            #                  if gpu_percent > GPU_MEMORY_THRESHOLD * 100:
            #                       warning_type = "high_gpu_memory"
            #                       message = f"High GPU memory usage detected: {gpu_percent:.1f}%."
            #                       self._issue_resource_warning(warning_type, message, gpu_percent)
            #         except (FileNotFoundError, subprocess.CalledProcessError):
            #             # nvidia-smi not found or failed
            #             pass # Ignore if nvidia-smi is not available

            # except Exception as e:
            #     logger.warning(f"Failed to monitor GPU resources: {e}")
            #     pass # Ignore if GPU monitoring fails


        except Exception as e:
            logger.error(f"Error during resource monitoring: {e}")


    def _issue_resource_warning(self, warning_type: str, message: str, value: Any):
        """Issue a resource warning, rate-limiting notifications."""
        current_time = time.time()
        # Only issue a warning of the same type if a certain cooldown period has passed
        cooldown = 60 # seconds cooldown for warnings of the same type
        if warning_type not in self._last_resource_warning_time or (current_time - self._last_resource_warning_time[warning_type]) > cooldown:
            logger.warning(f"Resource Warning: {warning_type} - {message}")
            self.resource_warning_occurred.emit({"warning_type": warning_type, "message": message, "value": value})
            self._last_resource_warning_time[warning_type] = current_time


    def add_task(self, url: str, model: str, target_lang: Optional[str], output_dir: str, formats: List[str]):
        """"
        Add a new task to the batch.

        Args:
            url: The YouTube video or playlist URL.
            model: The Whisper model to use (e.g., 'small').
            target_lang: Optional language code for translation (e.g., 'es').
            output_dir: The directory to save output files.
            formats: List of output formats (e.g., ['srt', 'json']).
        """"
        # Basic URL validation
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            logger.warning(f"Skipping invalid URL: {url}")
            # Report this as a skipped task
            skipped_task = Task(url, model, target_lang, output_dir, formats, status=TaskStatus.SKIPPED, error="Invalid URL format.")
            with self._lock:
                 self.tasks[url] = skipped_task
                 self._report_task_progress(skipped_task) # Report skipped status
                 self._report_batch_progress() # Update batch progress
            return

        # Check if task already exists
        with self._lock:
            if url in self.tasks:
                logger.warning(f"Task for URL already exists: {url}. Skipping.")
                # Optionally update parameters if needed, but for now, just skip
                return

            # Create a new task object
            new_task = Task()
                url=url,
                model=model,
                target_lang=target_lang,
                output_dir=output_dir,
                formats=formats,
                status=TaskStatus.PENDING # Initially pending
            )
            self.tasks[url] = new_task
            # Add to the task queue (using URL as the identifier)
            heappush(self._task_queue, (0, time.time(), url)) # Priority 0 (highest), timestamp for tie-breaking

            logger.info(f"Added task for URL: {url}")
            self._report_task_progress(new_task) # Report initial pending status
            self._report_batch_progress() # Update batch progress


    def process_batch(self, urls: Optional[List[str]] = None, model: str = 'small', target_lang: Optional[str] = None, output_dir: Optional[str] = None, formats: Optional[List[str]] = None):
        """"
        Start or resume processing the batch.

        If URLs are provided, they are added as new tasks before processing starts.
        If no URLs are provided, the processor attempts to process existing tasks.
        """"
        with self._lock:
            # Add new tasks if provided
            if urls:
                 logger.info(f"Adding {len(urls)} URLs and starting/resuming batch.")
                 # Use default options if not provided, falling back to settings or hardcoded defaults
                 model = model or (self.parent().settings.get("default_model", "small") if hasattr(self.parent(), 'settings') else "small")
                 target_lang = target_lang or (self.parent().settings.get("default_language", "None") if hasattr(self.parent(), 'settings') else "None")
                 target_lang = target_lang if target_lang != "None" else None # Convert "None" string to actual None
                 output_dir = output_dir or (self.parent().settings.get("output_dir", str(Path.home() / "Downloads" / "YouTubeTranscriber")) if hasattr(self.parent(), 'settings') else str(Path.home() / "Downloads" / "YouTubeTranscriber"))
                 formats = formats or ["srt"] # Default to SRT if not specified


                 for url in urls:
                      self.add_task(url, model, target_lang, output_dir, formats)

            # Start the processing thread if it's not already running'
            if self._processing_thread is None or not self._processing_thread.is_alive():
                logger.info("Starting batch processing thread.")
                self._shutdown_event.clear() # Clear shutdown event
                self._cancel_event.clear() # Clear cancel event
                self._pause_event.clear() # Clear pause event
                self.status = BatchStatus.RUNNING # Set initial status
                self._processing_thread = threading.Thread(target=self._run_batch)
                self._processing_thread.daemon = True # Allow thread to exit with the application
                self._processing_thread.start()
                self._report_batch_progress() # Report initial running status
            elif self.status == BatchStatus.PAUSED:
                 logger.info("Resuming batch processing.")
                 self.resume() # Call resume if paused
            else:
                 logger.debug("Batch processing is already running.")


    def _run_batch(self):
        """The main batch processing loop running in a separate thread."""
        logger.info("Batch processing thread started.")
        # Create ThreadPoolExecutor for concurrent task execution
        self._executor = ThreadPoolExecutor(max_workers=self.concurrency)
        self._futures = set() # Reset futures set

        try:
            while not self._shutdown_event.is_set():
                # Check for pause/cancel requests
                if self._cancel_event.is_set():
                    logger.info("Batch cancellation requested. Stopping.")
                    self.status = BatchStatus.STOPPING
                    self._report_batch_progress()
                    break # Exit processing loop

                if self._pause_event.is_set():
                    logger.debug("Batch paused. Waiting...")
                    self.status = BatchStatus.PAUSED
                    self._report_batch_progress()
                    # Wait until resume is called or shutdown/cancel occurs
                    self._pause_event.wait()
                    if self._shutdown_event.is_set() or self._cancel_event.is_set():
                         continue # Re-check shutdown/cancel after waiting
                    logger.debug("Batch resumed. Continuing.")
                    self.status = BatchStatus.RUNNING # Set status back to running
                    self._report_batch_progress()


                # Submit new tasks to the executor if there are available slots and tasks in queue
                while len(self._futures) < self.concurrency and self._task_queue and not self._pause_event.is_set() and not self._cancel_event.is_set() and not self._shutdown_event.is_set():
                    # Get the next task from the priority queue (lowest priority number first)
                    # The priority queue stores (retry_count, timestamp, url)
                    try:
                         priority, timestamp, url = heappop(self._task_queue)
                         task = self.tasks.get(url)
                         if task is None:
                              logger.warning(f"Task {url} not found in tasks dictionary. Skipping from queue.")
                              continue # Skip if task was removed from tasks

                         # Check if the task is still pending or needs retry
                         if task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                             logger.info(f"Submitting task for processing: {url}")
                             task.status = TaskStatus.RUNNING # Mark as running (temporarily, actual status updated by worker)
                             task.start_time = time.time()
                             task.last_attempt_time = time.time() # Record start of attempt
                             task.error = None # Clear previous error
                             task.progress = 0.0 # Reset progress
                             self._report_task_progress(task) # Report status change

                             # Submit the task to the thread pool
                             future = self._executor.submit(self._process_single_task, task)
                             self._futures.add(future)
                             task.future = future # Store future in task object

                         elif task.status == TaskStatus.PAUSED:
                              # If a paused task somehow ended up in the queue, put it back
                              heappush(self._task_queue, (task.retries, task.last_attempt_time or time.time(), url))
                              logger.debug(f"Putting paused task {url} back into queue.")
                              time.sleep(0.1) # Small sleep to avoid tight loop

                         else:
                             logger.debug(f"Task {url} is not in a state to be processed ({task.status.name}). Skipping from queue.")
                             # Clean up future if it was somehow left over
                             if task.future and not task.future.done():
                                  try:
                                       task.future.cancel() # Attempt to cancel the future
                                  except Exception as e:
                                       logger.warning(f"Failed to cancel future for task {url}: {e}")
                                  self._futures.discard(task.future) # Remove from futures set
                                  task.future = None # Clear future reference


                    except IndexError:
                         # Queue is empty
                         break

                # Check for completed futures and handle results
                for future in as_completed(list(self._futures), timeout=1.0): # Use a timeout to avoid blocking indefinitely
                    with self._lock:
                        self._futures.remove(future) # Remove from active futures

                        # Find the task associated with this future
                        completed_task: Optional[Task] = None
                        for task in self.tasks.values():
                            if task.future == future:
                                completed_task = task
                                break

                        if completed_task:
                            completed_task.future = None # Clear future reference
                            completed_task.end_time = time.time() # Record end time

                            try:
                                # Get the result from the future
                                result_data = future.result() # This will raise exceptions if the worker did

                                # Process the result (success or failure)
                                if result_data and isinstance(result_data, dict) and "status" in result_data:
                                     completed_task.status = TaskStatus[result_data["status"]] if TaskStatus and result_data["status"] in TaskStatus.__members__ else TaskStatus.FAILED # Default to FAILED if status is invalid
                                     completed_task.progress = result_data.get("progress", 1.0) # Should be 1.0 on completion/failure
                                     completed_task.error = result_data.get("error")
                                     completed_task.output_dir = result_data.get("output_dir")
                                     completed_task.output_files = result_data.get("output_files", {})
                                     completed_task.temp_files.extend(result_data.get("temp_files", [])) # Add temp files for cleanup

                                     logger.info(f"Task {completed_task.url} finished with status: {completed_task.status.name}")

                                     # Handle task completion status
                                     if completed_task.status == TaskStatus.COMPLETED:
                                         pass # Task completed successfully

                                     elif completed_task.status == TaskStatus.FAILED:
                                         logger.error(f"Task {completed_task.url} failed: {completed_task.error}")
                                         # Handle retries
                                         if completed_task.retries < (self.parent().settings.get("max_retries", DEFAULT_RETRY_COUNT) if hasattr(self.parent(), 'settings') else DEFAULT_RETRY_COUNT):
                                             completed_task.retries += 1
                                             retry_delay = (self.parent().settings.get("retry_delay", DEFAULT_RETRY_DELAY) if hasattr(self.parent(), 'settings') else DEFAULT_RETRY_DELAY) * (2 ** (completed_task.retries - 1)) # Exponential backoff
                                             retry_delay = min(retry_delay, (self.parent().settings.get("max_retry_delay", DEFAULT_MAX_RETRY_DELAY) if hasattr(self.parent(), 'settings') else DEFAULT_MAX_RETRY_DELAY)) # Cap retry delay
                                             logger.warning(f"Retrying task {completed_task.url} (Attempt {completed_task.retries}/{self.parent().settings.get('max_retries', DEFAULT_RETRY_COUNT) if hasattr(self.parent(), 'settings') else DEFAULT_RETRY_COUNT}) in {retry_delay:.1f} seconds")
                                             completed_task.status = TaskStatus.RETRYING # Mark as retrying
                                             completed_task.last_attempt_time = time.time() + retry_delay # Schedule next attempt
                                             # Add back to the priority queue with updated priority (based on retry count)
                                             heappush(self._task_queue, (completed_task.retries, completed_task.last_attempt_time, completed_task.url))
                                         else:
                                             logger.error(f"Task {completed_task.url} failed after {completed_task.retries} retries.")
                                             # Keep status as FAILED

                                     elif completed_task.status == TaskStatus.CANCELLED:
                                         logger.warning(f"Task {completed_task.url} was cancelled.")
                                         # Clean up temporary files immediately for cancelled tasks
                                         cleanup_temp_files(*completed_task.temp_files)
                                         completed_task.temp_files = [] # Clear temp files list

                                     elif completed_task.status == TaskStatus.SKIPPED:
                                         logger.warning(f"Task {completed_task.url} was skipped: {completed_task.error}")

                                     else:
                                         # Handle unexpected result format
                                         completed_task.status = TaskStatus.FAILED
                                         completed_task.error = "Unexpected result format from worker."
                                         logger.error(f"Task {completed_task.url} failed due to unexpected worker result.")
                                         # No retry for unexpected format errors

                            except Exception as e:
                                # Handle exceptions raised by the worker thread
                                completed_task.status = TaskStatus.FAILED
                                completed_task.error = f"Worker exception: {e}"
                                logger.error(f"Task {completed_task.url} failed with worker exception: {e}", exc_info=True)
                                # No retry for worker exceptions (assume unrecoverable)

                            finally:
                                # Report final task progress
                                self._report_task_progress(completed_task)
                                # Update overall batch progress
                                self._report_batch_progress()

                        else:
                            logger.warning("Completed future does not correspond to any active task.")

                    # Check for shutdown/cancel events again after processing a future
                    if self._shutdown_event.is_set() or self._cancel_event.is_set():
                         break # Exit the inner loop (over futures)


                # If the queue is empty and no futures are active, the batch is finished
                with self._lock:
                    if not self._task_queue and not self._futures and not self._shutdown_event.is_set() and not self._cancel_event.is_set():
                        logger.info("Batch processing finished.")
                        # Determine final batch status
                        if any(task.status == TaskStatus.FAILED for task in self.tasks.values()):
                            self.status = BatchStatus.FAILED
                        elif any(task.status == TaskStatus.CANCELLED for task in self.tasks.values()):
                             self.status = BatchStatus.CANCELLED
                        elif any(task.status == TaskStatus.SKIPPED for task in self.tasks.values()):
                             self.status = BatchStatus.COMPLETED # Consider skipped as part of overall completion
                        else:
                            self.status = BatchStatus.COMPLETED

                        self._report_batch_progress() # Report final status
                        self._report_batch_completion() # Report completion summary
                        break # Exit the main processing loop


                # Small sleep to prevent tight loop when queue is empty but futures are running
                time.sleep(0.1)

        except Exception as e:
            logger.critical(f"Fatal error in batch processing thread: {e}", exc_info=True)
            with self._lock:
                 self.status = BatchStatus.FAILED # Mark batch as failed on fatal error
                 self._report_batch_progress()
                 self._report_batch_completion() # Report completion summary (with failure)

        finally:
            # Shutdown the executor gracefully
            if self._executor:
                self._executor.shutdown(wait=True) # Wait for currently running tasks to finish
                logger.info("ThreadPoolExecutor shut down.")

            # Ensure all tasks are marked as failed or cancelled if shutdown/cancel occurred
            with self._lock:
                 for task in self.tasks.values():
                      if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.VALIDATING, TaskStatus.DOWNLOADING, TaskStatus.CONVERTING, TaskStatus.TRANSCRIBING, TaskStatus.TRANSLATING, TaskStatus.EXPORTING, TaskStatus.RETRYING]:
                           if self._cancel_event.is_set():
                                task.status = TaskStatus.CANCELLED
                                task.error = task.error or "Batch cancelled." # Add error if none exists
                                logger.warning(f"Task {task.url} marked as CANCELLED during shutdown.")
                           elif self._shutdown_event.is_set():
                                task.status = TaskStatus.FAILED # Mark as failed on unexpected shutdown
                                task.error = task.error or "Application shutting down unexpectedly."
                                logger.warning(f"Task {task.url} marked as FAILED during shutdown.")

                           task.progress = 0.0 # Reset progress on cancel/fail
                           task.end_time = time.time() # Set end time
                           self._report_task_progress(task) # Report final status

            logger.info("Batch processing thread finished.")
            self._processing_thread = None # Clear thread reference


    def _process_single_task(self, task: Task) -> Dict[str, Any]:
        """"
        Process a single task (download, transcribe, translate, export).
        This method runs in a worker thread from the ThreadPoolExecutor.
        """"
        logger.info(f"Worker started processing task: {task.url}")
        result_data: Dict[str, Any] = {"url": task.url, "status": TaskStatus.FAILED.name, "progress": 0.0, "error": None, "output_dir": None, "output_files": {}, "temp_files": []}
        temp_files_for_task: List[str] = [] # Track temp files created during this task's execution'

        try:
            # Check for cancellation before starting
            if self._cancel_event.is_set() or self._shutdown_event.is_set():
                 result_data["status"] = TaskStatus.CANCELLED.name
                 result_data["error"] = "Task cancelled before starting."
                 logger.warning(f"Task {task.url} cancelled before starting.")
                 return result_data # Exit worker thread

            # --- Step 1: Download Audio ---
            result_data["status"] = TaskStatus.DOWNLOADING.name
            self._report_task_progress_worker(task.url, TaskStatus.DOWNLOADING, 0.05) # Report initial download progress
            self.status_message.emit(f"Downloading: {task.url}") # Update status bar message

            # Use cache for audio if available
            audio_cache_key = f"audio_{task.url}"
            cached_audio_path = None
            if CACHE_AVAILABLE and self.cache_manager:
                 cached_audio_path = self.cache_manager.get(audio_cache_key, CacheType.AUDIO if CacheType else None)
                 if cached_audio_path and os.path.exists(cached_audio_path):
                      task.audio_path = cached_audio_path
                      logger.info(f"Audio found in cache for {task.url}: {cached_audio_path}")
                      result_data["status"] = TaskStatus.CACHED.name # Indicate cache hit
                      self._report_task_progress_worker(task.url, TaskStatus.CACHED, 0.1) # Report cache hit progress
                 else:
                      cached_audio_path = None # Ensure it's None if not found or invalid'


            if cached_audio_path is None: # Only download if not in cache
                 if not AUDIO_UTILS_AVAILABLE:
                      raise RuntimeError("Audio utilities not available for download.")

                 logger.info(f"Downloading audio for {task.url}...")
                 # Define progress callback for download
                 def download_progress_callback(progress: float, file_path: str):
                      # Map download progress (0-1) to overall task progress (e.g., 5-15%)
                      overall_progress = 0.05 + progress * 0.10
                      self._report_task_progress_worker(task.url, TaskStatus.DOWNLOADING, overall_progress)
                      # Add downloaded file to temp files list if it exists and is temporary
                      if file_path and file_path not in temp_files_for_task and Path(file_path).parent == Path(tempfile.gettempdir()):
                           temp_files_for_task.append(file_path)


                 download_path, download_error = download_audio()
                     task.url,
                     temp_dir=tempfile.gettempdir(), # Use system temp directory for downloads
                     progress_callback=download_progress_callback,
                     stop_event=self._cancel_event if self._cancel_event.is_set else None, # Pass cancel event
                     timeout=DEFAULT_DOWNLOAD_TIMEOUT
                 )

                 if download_error:
                     raise RuntimeError(f"Download failed: {download_error}")
                 if not download_path or not os.path.exists(download_path):
                     raise RuntimeError("Download failed: No file downloaded.")

                 task.audio_path = download_path
                 temp_files_for_task.append(download_path) # Add downloaded file to temp list

                 # Cache the downloaded audio file
                 if CACHE_AVAILABLE and self.cache_manager:
                      try:
                           # Copy the downloaded file to the cache directory
                           cache_file_path = self.cache_manager.set(audio_cache_key, CacheType.AUDIO if CacheType else None, download_path)
                           if cache_file_path:
                                logger.debug(f"Cached audio for {task.url} at {cache_file_path}")
                           else:
                                logger.warning(f"Failed to cache audio for {task.url}.")
                      except Exception as cache_err:
                           logger.warning(f"Error caching audio for {task.url}: {cache_err}")


            # --- Step 2: Convert Audio to WAV (if necessary) ---
            # Whisper requires 16kHz mono WAV. Check if the downloaded file is already in that format.
            # This check requires inspecting the audio file metadata, which can be complex.
            # A simpler approach is to always convert, or use a library that handles this.
            # Assuming convert_to_wav handles format checking internally.

            result_data["status"] = TaskStatus.CONVERTING.name
            self._report_task_progress_worker(task.url, TaskStatus.CONVERTING, 0.15) # Report initial conversion progress
            self.status_message.emit(f"Converting audio: {task.url}")

            if not AUDIO_UTILS_AVAILABLE:
                 raise RuntimeError("Audio utilities not available for conversion.")

            # Define progress callback for conversion
            def convert_progress_callback(progress: float, file_path: str):
                 # Map conversion progress (0-1) to overall task progress (e.g., 15-25%)
                 overall_progress = 0.15 + progress * 0.10
                 self._report_task_progress_worker(task.url, TaskStatus.CONVERTING, overall_progress)
                 # Add converted file to temp files list if it exists and is temporary
                 if file_path and file_path not in temp_files_for_task and Path(file_path).parent == Path(tempfile.gettempdir()):
                      temp_files_for_task.append(file_path)


            wav_audio_path, convert_error = convert_to_wav()
                 task.audio_path,
                 temp_dir=tempfile.gettempdir(), # Use system temp directory for conversion output
                 progress_callback=convert_progress_callback,
                 timeout=DEFAULT_CONVERSION_TIMEOUT
            )

            if convert_error:
                raise RuntimeError(f"Audio conversion failed: {convert_error}")
            if not wav_audio_path or not os.path.exists(wav_audio_path):
                raise RuntimeError("Audio conversion failed: No output file.")

            # The original downloaded file is now temporary if it wasn't from cache'
            if cached_audio_path is None and task.audio_path and os.path.exists(task.audio_path):
                 temp_files_for_task.append(task.audio_path) # Add original download to temp list

            task.audio_path = wav_audio_path # Update task audio path to the WAV file
            temp_files_for_task.append(wav_audio_path) # Add converted file to temp list


            # --- Step 3: Transcribe Audio ---
            result_data["status"] = TaskStatus.TRANSCRIBING.name
            self._report_task_progress_worker(task.url, TaskStatus.TRANSCRIBING, 0.25) # Report initial transcription progress
            self.status_message.emit(f"Transcribing: {task.url}")

            if not WHISPER_AVAILABLE:
                 raise RuntimeError("Whisper library not available for transcription.")

            # Use cache for transcription if available
            transcription_cache_key = f"transcription_{task.url}_{task.model}"
            cached_transcription = None
            if CACHE_AVAILABLE and self.cache_manager:
                 cached_transcription = self.cache_manager.get(transcription_cache_key, CacheType.TRANSCRIPTION if CacheType else None)
                 if cached_transcription:
                      task.transcription_result = cached_transcription
                      logger.info(f"Transcription found in cache for {task.url}")
                      result_data["status"] = TaskStatus.CACHED.name # Indicate cache hit
                      self._report_task_progress_worker(task.url, TaskStatus.CACHED, 0.8) # Report cache hit progress (later stage)
                 else:
                      cached_transcription = None


            if cached_transcription is None: # Only transcribe if not in cache
                 logger.info(f"Transcribing audio for {task.url} using model '{task.model}'...")
                 # Define progress callback for transcription
                 def transcribe_progress_callback(progress: float, status_text: str):
                      # Map transcription progress (0-1) to overall task progress (e.g., 25-80%)
                      overall_progress = 0.25 + progress * 0.55
                      self._report_task_progress_worker(task.url, TaskStatus.TRANSCRIBING, overall_progress, status_text=status_text)


                 transcription_result, transcribe_error = transcribe()
                     task.audio_path,
                     model_name=task.model,
                     progress_callback=transcribe_progress_callback,
                     stop_event=self._cancel_event if self._cancel_event.is_set else None, # Pass cancel event
                     timeout=DEFAULT_TASK_TIMEOUT - (time.time() - task.start_time if task.start_time else 0) # Timeout based on remaining task time
                 )

                 if transcribe_error:
                     raise RuntimeError(f"Transcription failed: {transcribe_error}")
                 if not transcription_result:
                     raise RuntimeError("Transcription failed: No result.")

                 task.transcription_result = transcription_result

                 # Cache the transcription result
                 if CACHE_AVAILABLE and self.cache_manager:
                      try:
                           success = self.cache_manager.set(transcription_cache_key, CacheType.TRANSCRIPTION if CacheType else None, transcription_result)
                           if success:
                                logger.debug(f"Cached transcription for {task.url}")
                           else:
                                logger.warning(f"Failed to cache transcription for {task.url}.")
                      except Exception as cache_err:
                           logger.warning(f"Error caching transcription for {task.url}: {cache_err}")


            # --- Step 4: Translate Transcription (if target_lang is specified) ---
            task.translation_result = None # Reset translation result
            if task.transcription_result and task.target_lang and task.target_lang != "None":
                 result_data["status"] = TaskStatus.TRANSLATING.name
                 self._report_task_progress_worker(task.url, TaskStatus.TRANSLATING, 0.80) # Report initial translation progress
                 self.status_message.emit(f"Translating: {task.url}")

                 if not TRANSLATE_AVAILABLE:
                      raise RuntimeError("Translation utilities not available.")

                 # Use cache for translation if available
                 translation_cache_key = f"translation_{task.url}_{task.model}_{task.target_lang}"
                 cached_translation = None
                 if CACHE_AVAILABLE and self.cache_manager:
                      cached_translation = self.cache_manager.get(translation_cache_key, CacheType.TRANSLATION if CacheType else None)
                      if cached_translation:
                           task.translation_result = cached_translation
                           logger.info(f"Translation found in cache for {task.url}")
                           result_data["status"] = TaskStatus.CACHED.name # Indicate cache hit (if both trans/trans cached)
                           self._report_task_progress_worker(task.url, TaskStatus.CACHED, 0.9) # Report cache hit progress (later stage)
                      else:
                           cached_translation = None


                 if cached_translation is None: # Only translate if not in cache
                      logger.info(f"Translating transcription for {task.url} to '{task.target_lang}'...")
                      # Define progress callback for translation (if translate supports it)
                      def translate_progress_callback(progress: float, status_text: str):
                           # Map translation progress (0-1) to overall task progress (e.g., 80-90%)
                           overall_progress = 0.80 + progress * 0.10
                           self._report_task_progress_worker(task.url, TaskStatus.TRANSLATING, overall_progress, status_text=status_text)


                      translation_result, translate_error = translate()
                          task.transcription_result,
                          target_language=task.target_lang,
                          progress_callback=translate_progress_callback,
                          stop_event=self._cancel_event if self._cancel_event.is_set else None, # Pass cancel event
                          timeout=DEFAULT_TASK_TIMEOUT - (time.time() - task.start_time if task.start_time else 0) # Timeout based on remaining task time
                      )

                      if translate_error:
                          raise RuntimeError(f"Translation failed: {translate_error}")
                      if not translation_result:
                          raise RuntimeError("Translation failed: No result.")

                      task.translation_result = translation_result

                      # Cache the translation result
                      if CACHE_AVAILABLE and self.cache_manager:
                           try:
                                success = self.cache_manager.set(translation_cache_key, CacheType.TRANSLATION if CacheType else None, translation_result)
                                if success:
                                     logger.debug(f"Cached translation for {task.url}")
                                else:
                                     logger.warning(f"Failed to cache translation for {task.url}.")
                           except Exception as cache_err:
                                logger.warning(f"Error caching translation for {task.url}: {cache_err}")


            # --- Step 5: Export Results ---
            result_data["status"] = TaskStatus.EXPORTING.name
            self._report_task_progress_worker(task.url, TaskStatus.EXPORTING, 0.90) # Report initial export progress
            self.status_message.emit(f"Exporting: {task.url}")

            if not EXPORT_AVAILABLE:
                 raise RuntimeError("Export utilities not available.")

            output_files = {}
            export_errors = []

            # Determine the data to export (translated if available, otherwise original transcription)
            data_to_export = task.translation_result if task.translation_result else task.transcription_result

            if not data_to_export:
                 raise RuntimeError("No transcription or translation data to export.")

            # Ensure output directory exists
            os.makedirs(task.output_dir, exist_ok=True)

            # Get video title for filename (basic sanitization)
            video_title = data_to_export.get("title", "transcription").replace(" ", "_").replace("/", "_").replace("\\", "_")[:50] # Sanitize and truncate

            # Export to selected formats
            if "srt" in task.formats:
                 srt_path, srt_error = export_srt(data_to_export, task.output_dir, filename=f"{video_title}.srt")
                 if srt_error:
                      export_errors.append(f"SRT export failed: {srt_error}")
                 elif srt_path:
                      output_files["srt"] = srt_path

            if "json" in task.formats:
                 json_path, json_error = export_json(data_to_export, task.output_dir, filename=f"{video_title}.json")
                 if json_error:
                      export_errors.append(f"JSON export failed: {json_error}")
                 elif json_path:
                      output_files["json"] = json_path

            if "vtt" in task.formats:
                 vtt_path, vtt_error = export_vtt(data_to_export, task.output_dir, filename=f"{video_title}.vtt")
                 if vtt_error:
                      export_errors.append(f"VTT export failed: {vtt_error}")
                 elif vtt_path:
                      output_files["vtt"] = vtt_path


            if export_errors:
                 raise RuntimeError("Export failed: " + "; ".join(export_errors))

            task.output_files = output_files
            task.output_dir = task.output_dir # Ensure output_dir is set in task

            # --- Task Completed Successfully ---
            result_data["status"] = TaskStatus.COMPLETED.name
            result_data["progress"] = 1.0
            result_data["output_dir"] = task.output_dir
            result_data["output_files"] = task.output_files
            logger.info(f"Task {task.url} completed successfully.")

        except Exception as e:
            # Handle any exception during task processing
            error_message = str(e)
            logger.error(f"Task {task.url} failed: {error_message}", exc_info=True)
            result_data["status"] = TaskStatus.FAILED.name
            result_data["error"] = error_message
            result_data["progress"] = 0.0 # Reset progress on failure

        finally:
            # Clean up temporary files specific to this task attempt
            cleanup_temp_files(*temp_files_for_task)
            result_data["temp_files"] = temp_files_for_task # Report temp files for potential final cleanup

            # Return the result data to the main thread
            return result_data


    def _report_task_progress_worker(self, url: str, status: TaskStatus, progress: float, status_text: Optional[str] = None):
        """Helper to report task progress from a worker thread."""
        # This method is called from worker threads. It should emit a signal
        # to update the UI on the main thread.
        # Ensure progress is between 0.0 and 1.0
        progress = max(0.0, min(1.0, progress))

        # Get the current batch progress to include in the update
        batch_progress = self._calculate_overall_progress()

        self.task_progress_updated.emit({)
            "type": "task_progress",
            "url": url,
            "status": status.name,
            "progress": progress,
            "status_text": status_text,
            "batch_progress": batch_progress # Include batch progress
        })


    def _report_batch_progress(self):
        """Calculate and report overall batch progress and status."""
        # This method can be called from any thread, but the signal emission
        # will be queued to the main thread.
        overall_progress = self._calculate_overall_progress()
        with self._lock:
             batch_status_name = self.status.name

        self.batch_progress_updated.emit({)
            "type": "batch_progress",
            "batch_progress": overall_progress,
            "batch_status": batch_status_name
        })


    def _calculate_overall_progress(self) -> float:
        """Calculate the overall progress of the batch."""
        with self._lock:
            if not self.tasks:
                return 0.0 # 0% if no tasks

            total_tasks = len(self.tasks)
            completed_tasks = sum(1 for task in self.tasks.values() if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SKIPPED])
            running_tasks_progress = sum(task.progress for task in self.tasks.values() if task.status in [TaskStatus.RUNNING, TaskStatus.VALIDATING, TaskStatus.DOWNLOADING, TaskStatus.CONVERTING, TaskStatus.TRANSCRIBING, TaskStatus.TRANSLATING, TaskStatus.EXPORTING, TaskStatus.RETRYING])

            # Simple calculation: (completed tasks + sum of running tasks' progress) / total tasks'
            # This assumes each task contributes equally to the overall progress.
            # A more complex approach could weight tasks based on estimated duration.
            overall_progress = (completed_tasks + running_tasks_progress) / total_tasks

            # Ensure progress is between 0.0 and 1.0
            return max(0.0, min(1.0, overall_progress))


    def _report_batch_completion(self):
        """Generate and emit a batch completion report."""
        with self._lock:
            total = len(self.tasks)
            completed = sum(1 for task in self.tasks.values() if task.status == TaskStatus.COMPLETED)
            failed = sum(1 for task in self.tasks.values() if task.status == TaskStatus.FAILED)
            cancelled = sum(1 for task in self.tasks.values() if task.status == TaskStatus.CANCELLED)
            skipped = sum(1 for task in self.tasks.values() if task.status == TaskStatus.SKIPPED)
            batch_status_name = self.status.name

            report = {
                "status": batch_status_name,
                "total": total,
                "completed": completed,
                "failed": failed,
                "cancelled": cancelled,
                "skipped": skipped,
                "tasks": {url: {"status": task.status.name, "error": task.error, "output_dir": task.output_dir, "output_files": task.output_files} for url, task in self.tasks.items()}
            }

        self.batch_completion_status.emit(report)


    @pyqtSlot()
    def pause(self) -> bool:
        """"
        Pause a running batch operation.

        Signals running tasks to pause (if they support it) and prevents new tasks
        from starting until resumed.

        Returns:
            True if pause was initiated, False if no batch is running
        """"
        with self._lock:
            if self.status not in [BatchStatus.RUNNING, BatchStatus.THROTTLED]:
                return False

            logger.info("Pausing batch processing")
            self.status = BatchStatus.PAUSED
            self._pause_event.set() # Set the pause event

            # Signal all running tasks to pause (if they support it)
            # The worker threads check the _pause_event periodically.
            # No need to explicitly signal individual tasks unless they have
            # a specific pause mechanism beyond checking the event.

            self._report_batch_progress() # Report status change

            return True


    @pyqtSlot()
    def resume(self) -> bool:
        """"
        Resume a paused batch operation.

        This will clear the pause event, allowing the processing thread to continue
        and new tasks to be submitted.

        Returns:
            True if resume was initiated, False if no batch is paused
        """"
        with self._lock:
            if self.status != BatchStatus.PAUSED:
                return False

            logger.info("Resuming batch processing")
            self.status = BatchStatus.RESUMING # Indicate resuming state
            self._pause_event.clear() # Clear the pause event

            # The processing thread will automatically pick up where it left off.
            # No need to explicitly resume individual tasks unless they have
            # a specific resume mechanism.

            self.status = BatchStatus.RUNNING # Set status back to running after clearing event
            self._report_batch_progress() # Report status change

            return True


    @pyqtSlot()
    def cancel(self) -> bool:
        """"
        Cancel the current batch operation.

        Signals all running tasks to stop and prevents new tasks from starting.
        Tasks in PENDING or RETRYING status will be marked as CANCELLED.

        Returns:
            True if cancellation was initiated, False otherwise
        """"
        with self._lock:
            if self.status in [BatchStatus.IDLE, BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED, BatchStatus.STOPPING]:
                return False # Cannot cancel if idle, finished, or already stopping

            logger.info("Cancelling batch processing")
            self.status = BatchStatus.STOPPING # Indicate stopping state
            self._cancel_event.set() # Set the cancel event
            self._pause_event.clear() # Clear pause event to allow workers to check cancel event

            # Mark pending/retrying tasks as cancelled immediately
            for task in self.tasks.values():
                 if task.status in [TaskStatus.PENDING, TaskStatus.RETRYING, TaskStatus.PAUSED]:
                      task.status = TaskStatus.CANCELLED
                      task.error = task.error or "Task cancelled by user."
                      task.progress = 0.0 # Reset progress
                      task.end_time = time.time() # Set end time
                      self._report_task_progress(task) # Report status change

            # The processing thread and worker threads will detect the cancel event
            # and terminate gracefully. The _run_batch finally block will mark
            # any still-running tasks as CANCELLED.

            self._report_batch_progress() # Report status change

            return True


    @pyqtSlot(str)
    def cancel_task(self, url: str) -> bool:
        """"
        Cancel a specific task in the batch.

        Args:
            url: The URL of the task to cancel.

        Returns:
            True if the task was found and cancellation was initiated, False otherwise.
        """"
        with self._lock:
            task = self.tasks.get(url)
            if task is None:
                logger.warning(f"Attempted to cancel non-existent task: {url}")
                return False

            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.SKIPPED]:
                 logger.debug(f"Task {url} is already in a terminal state ({task.status.name}). Cannot cancel.")
                 return False # Cannot cancel if already finished

            logger.info(f"Cancelling task: {url}")
            task.status = TaskStatus.CANCELLED # Mark task as cancelled
            task.error = task.error or "Task cancelled by user." # Add error if none exists
            task.progress = 0.0 # Reset progress
            task.end_time = time.time() # Set end time

            # If the task is currently running, signal the worker thread to stop
            if task.future and not task.future.done():
                try:
                    # Attempt to cancel the future (might not work if worker is blocking)
                    cancelled = task.future.cancel()
                    if cancelled:
                         logger.debug(f"Future for task {url} cancelled.")
                    else:
                         logger.warning(f"Could not cancel future for task {url}. Worker might be blocking.")
                except Exception as e:
                    logger.error(f"Error cancelling future for task {url}: {e}")


            # If the task is in the queue (PENDING, RETRYING, PAUSED), remove it
            # Rebuild the queue excluding the cancelled task
            new_task_queue = []
            removed_from_queue = False
            while self._task_queue:
                 priority, timestamp, q_url = heappop(self._task_queue)
                 if q_url == url:
                      removed_from_queue = True
                      logger.debug(f"Task {url} removed from task queue.")
                 else:
                      heappush(new_task_queue, (priority, timestamp, q_url))
            self._task_queue = new_task_queue # Replace the queue

            self._report_task_progress(task) # Report status change
            self._report_batch_progress() # Update batch progress

            return True


    @pyqtSlot(str)
    def remove_task(self, url: str) -> bool:
        """"
        Remove a task from the batch entirely.

        Args:
            url: The URL of the task to remove.

        Returns:
            True if the task was found and removed, False otherwise.
        """"
        with self._lock:
            task = self.tasks.get(url)
            if task is None:
                logger.warning(f"Attempted to remove non-existent task: {url}")
                return False

            # If the task is running, cancel it first
            if task.status in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.VALIDATING, TaskStatus.DOWNLOADING, TaskStatus.CONVERTING, TaskStatus.TRANSCRIBING, TaskStatus.TRANSLATING, TaskStatus.EXPORTING, TaskStatus.RETRYING, TaskStatus.PAUSED]:
                 logger.warning(f"Task {url} is still active ({task.status.name}). Cancelling before removing.")
                 self.cancel_task(url) # Cancel the task

                 # Wait briefly for the worker thread to finish after cancellation
                 if task.future and not task.future.done():
                      try:
                           task.future.result(timeout=1.0) # Wait up to 1 second for result (might raise CancelledError)
                      except Exception:
                           pass # Ignore exceptions during wait


            # Remove from the tasks dictionary
            if url in self.tasks:
                 del self.tasks[url]
                 logger.info(f"Removed task: {url}")

                 # Remove from the task queue if it was there (redundant if cancel_task was called, but safe)
                 new_task_queue = []
                 while self._task_queue:
                      priority, timestamp, q_url = heappop(self._task_queue)
                      if q_url != url:
                           heappush(new_task_queue, (priority, timestamp, q_url))
                 self._task_queue = new_task_queue

                 # Clean up temporary files associated with this task
                 cleanup_temp_files(*task.temp_files)

                 self._report_batch_progress() # Update batch progress

                 return True
            else:
                 return False # Should not happen if task was found initially


    @pyqtSlot(str)
    def retry_task(self, url: str) -> bool:
        """"
        Retry a failed task.

        Args:
            url: The URL of the task to retry.

        Returns:
            True if the task was found and retried, False otherwise.
        """"
        with self._lock:
            task = self.tasks.get(url)
            if task is None:
                logger.warning(f"Attempted to retry non-existent task: {url}")
                return False

            if task.status != TaskStatus.FAILED:
                logger.warning(f"Task {url} is not in FAILED state ({task.status.name}). Cannot retry.")
                return False

            logger.info(f"Retrying task: {url}")
            task.status = TaskStatus.RETRYING # Mark as retrying
            task.error = None # Clear error
            task.progress = 0.0 # Reset progress
            task.retries = 0 # Reset retry count for a manual retry
            task.last_attempt_time = time.time() # Reset last attempt time
            task.audio_path = None # Clear previous audio path (force re-download/convert)
            task.transcription_result = None # Clear previous results
            task.translation_result = None
            task.output_files = {} # Clear previous output files
            cleanup_temp_files(*task.temp_files) # Clean up previous temp files
            task.temp_files = [] # Clear temp files list


            # Add back to the priority queue with reset priority
            heappush(self._task_queue, (task.retries, task.last_attempt_time, task.url))

            self._report_task_progress(task) # Report status change
            self._report_batch_progress() # Update batch progress

            # If the batch is idle, start it to process the retried task
            if self.status == BatchStatus.IDLE:
                 self.process_batch() # Start processing

            return True


    def shutdown(self, wait: bool = True, timeout: Optional[float] = None):
        """"
        Initiate graceful shutdown of the batch processor.

        Args:
            wait: If True, wait for currently running tasks to finish.
            timeout: Maximum time to wait for tasks to finish.
        """"
        with self._lock:
            if self._shutdown_event.is_set():
                 logger.debug("BatchProcessor already shutting down.")
                 return

            logger.info("BatchProcessor shutdown initiated.")
            self.status = BatchStatus.STOPPING # Indicate stopping state
            self._shutdown_event.set() # Set the shutdown event
            self._cancel_event.set() # Also set cancel event to stop workers immediately
            self._pause_event.clear() # Clear pause event to allow workers to check shutdown/cancel

            self._report_batch_progress() # Report status change

        # Wait for the processing thread to finish if requested
        if wait and self._processing_thread and self._processing_thread.is_alive():
             logger.info(f"Waiting for batch processing thread to finish (timeout: {timeout}s)...")
             self._processing_thread.join(timeout=timeout)
             if self._processing_thread.is_alive():
                  logger.warning("Batch processing thread did not finish within timeout.")
             else:
                  logger.info("Batch processing thread finished.")

        # Shutdown the executor (will wait for running tasks if wait=True in shutdown() call)
        if self._executor:
             logger.info("Shutting down ThreadPoolExecutor...")
             self._executor.shutdown(wait=wait, cancel_futures=not wait) # Cancel futures immediately if not waiting
             logger.info("ThreadPoolExecutor shutdown complete.")

        # Stop resource monitor timer
        if self._resource_monitor_timer and self._resource_monitor_timer.isActive():
             self._resource_monitor_timer.stop()
             logger.debug("Resource monitor timer stopped.")


        logger.info("BatchProcessor shutdown process completed.")


    def _final_cleanup(self):
        """Perform final cleanup of temporary files on program exit."""
        logger.info("Performing final temporary file cleanup...")
        with self._lock:
            # Collect all temp files from tasks
            all_temp_files = []
            for task in self.tasks.values():
                 all_temp_files.extend(task.temp_files)

            # Add any other temp files tracked by the processor
            all_temp_files.extend(self._temp_files_to_cleanup)

            # Remove duplicates and clean up
            unique_temp_files = list(set(all_temp_files))
            cleanup_temp_files(*unique_temp_files)

        logger.info("Final temporary file cleanup finished.")


    def get_session_state(self) -> Dict[str, Any]:
        """Get the current state of the batch processor for session saving."""
        with self._lock:
            # Serialize tasks (convert Task objects to dictionaries)
            serializable_tasks = {
                url: {
                    "url": task.url,
                    "model": task.model,
                    "target_lang": task.target_lang,
                    "output_dir": task.output_dir,
                    "formats": task.formats,
                    "status": task.status.name, # Save enum name
                    "progress": task.progress,
                    "error": task.error,
                    "retries": task.retries,
                    "last_attempt_time": task.last_attempt_time,
                    "start_time": task.start_time,
                    "end_time": task.end_time,
                    # Do not save audio_path, transcription_result, translation_result, output_files directly
                    # These should be re-derived or handled by cache/export logic on load.
                    # However, saving output_dir might be useful.
                    "output_dir": task.output_dir,
                    # Save temp_files for cleanup on next startup if crash occurred
                    "temp_files": task.temp_files
                }
                for url, task in self.tasks.items()
            }

            # Serialize the task queue (list of tuples)
            serializable_task_queue = list(self._task_queue)

            state = {
                "tasks": serializable_tasks,
                "status": self.status.name, # Save enum name
                "task_queue": serializable_task_queue,
                "concurrency": self.concurrency, # Save current concurrency
                # Add other relevant state variables here
            }
            logger.debug("BatchProcessor state captured for session saving.")
            return state


    def load_session(self, state: Dict[str, Any]) -> bool:
        """Load the batch processor state from a saved session."""
        if not state:
            logger.info("No batch processor state to load from session.")
            return False

        logger.info("Loading batch processor state from session.")
        with self._lock:
            try:
                # Restore tasks
                restored_tasks_data = state.get("tasks", {})
                self.tasks = {} # Clear current tasks
                for url, task_data in restored_tasks_data.items():
                    try:
                        # Recreate Task objects from dictionary data
                        status_name = task_data.get("status")
                        status = TaskStatus[status_name] if TaskStatus and status_name in TaskStatus.__members__ else TaskStatus.FAILED # Default to FAILED if status is invalid

                        # If the task was running or in progress when saved (due to crash),
                        # mark it as FAILED or PENDING for retry on reload.
                        if status in [TaskStatus.RUNNING, TaskStatus.VALIDATING, TaskStatus.DOWNLOADING, TaskStatus.CONVERTING, TaskStatus.TRANSCRIBING, TaskStatus.TRANSLATING, TaskStatus.EXPORTING, TaskStatus.RETRYING]:
                             logger.warning(f"Task {url} was in progress during last session. Marking as FAILED for retry.")
                             status = TaskStatus.FAILED
                             task_data["error"] = task_data.get("error") or "Task interrupted by unexpected shutdown."
                             # Increment retry count? Or reset for a fresh start? Let's reset for manual retry.'
                             task_data["retries"] = 0


                        restored_task = Task()
                            url=task_data.get("url", url), # Use URL from key as fallback
                            model=task_data.get("model", "small"),
                            target_lang=task_data.get("target_lang"),
                            output_dir=task_data.get("output_dir", str(Path.home() / "Downloads" / "YouTubeTranscriber")),
                            formats=task_data.get("formats", ["srt"]),
                            status=status,
                            progress=task_data.get("progress", 0.0),
                            error=task_data.get("error"),
                            retries=task_data.get("retries", 0),
                            last_attempt_time=task_data.get("last_attempt_time"),
                            start_time=task_data.get("start_time"),
                            end_time=task_data.get("end_time"),
                            # output_dir is already specified above
                            output_files=task_data.get("output_files", {}), # Load output files if saved
                            temp_files=task_data.get("temp_files", []) # Load temp files for cleanup
                        )
                        self.tasks[url] = restored_task

                        # Add tasks that were marked as FAILED (due to crash) or PENDING to the queue for potential retry
                        if restored_task.status in [TaskStatus.PENDING, TaskStatus.FAILED]:
                             heappush(self._task_queue, (restored_task.retries, restored_task.last_attempt_time or time.time(), restored_task.url))


                    except Exception as e:
                        logger.error(f"Failed to restore task {url} from session: {e}. Skipping task.", exc_info=True)
                        # Add a failed task entry to indicate the issue
                        failed_task = Task(url, "unknown", None, "unknown", [], status=TaskStatus.FAILED, error=f"Failed to restore task from session: {e}")
                        self.tasks[url] = failed_task


                # Restore batch status
                status_name = state.get("status", "IDLE")
                self.status = BatchStatus[status_name] if BatchStatus and status_name in BatchStatus.__members__ else BatchStatus.IDLE

                # If the batch was running or stopping when saved, mark as FAILED or IDLE
                if self.status in [BatchStatus.RUNNING, BatchStatus.THROTTLED, BatchStatus.STOPPING, BatchStatus.RESUMING]:
                     logger.warning(f"Batch was in progress ({self.status.name}) during last session. Resetting status to IDLE.")
                     self.status = BatchStatus.IDLE # Reset status to IDLE

                # Restore task queue (if saved, otherwise rebuild from tasks)
                restored_task_queue = state.get("task_queue")
                if restored_task_queue:
                     self._task_queue = restored_task_queue # Use the saved queue
                     logger.debug(f"Restored {len(self._task_queue)} tasks to queue from session.")
                else:
                     # If queue wasn't saved, rebuild it from pending/failed tasks'
                     self._task_queue = []
                     for task in self.tasks.values():
                          if task.status in [TaskStatus.PENDING, TaskStatus.FAILED]:
                               heappush(self._task_queue, (task.retries, task.last_attempt_time or time.time(), task.url))
                     logger.warning(f"Task queue not found in session. Rebuilt queue with {len(self._task_queue)} tasks.")


                # Restore concurrency
                self.concurrency = state.get("concurrency", self.concurrency)


                # Add temp files from loaded tasks to the final cleanup list
                for task in self.tasks.values():
                     self._temp_files_to_cleanup.extend(task.temp_files)
                     task.temp_files = [] # Clear task's temp list after adding to global list'


                logger.info(f"Batch processor state loaded. {len(self.tasks)} tasks restored.")
                return True

            except Exception as e:
                logger.error(f"Failed to load batch processor state from session: {e}", exc_info=True)
                # Clear all tasks and reset state on failure
                self.tasks = {}
                self.status = BatchStatus.IDLE
                self._task_queue = []
                self._futures = set()
                return False


    def _report_task_progress(self, task: Task):
        """Emit task progress signal (called from main thread)."""
        # This method is called from the main thread (e.g., when adding tasks, cancelling).
        # It emits a signal that the UI listens to.
        self.task_progress_updated.emit({)
            "type": "task_progress",
            "url": task.url,
            "status": task.status.name,
            "progress": task.progress,
            "error": task.error,
            "output_dir": task.output_dir,
            "output_files": task.output_files,
            "temp_files": task.temp_files # Include temp files for potential cleanup
        })


# For backward compatibility (optional, can be removed if not needed)
def batch_process(urls, model='small', target_lang=None, concurrency=2, output_dir=None, formats=None):
    """Legacy function for backward compatibility"""
    logger.warning("Using deprecated batch_process function. Use BatchProcessor class directly.")
    processor = BatchProcessor(concurrency=concurrency)
    # This legacy function is blocking, which is not suitable for a GUI application.
    # It should ideally not be used in the final GUI version.
    # Returning a mock result or raising an error is better.
    raise NotImplementedError("Legacy batch_process function is not supported in the GUI application.")

