"""
Batch processor for YouTube Translator Pro.
Manages the processing of multiple YouTube videos in a queue.
"""

import os
import time
import logging
import threading
import queue
from enum import Enum, auto
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

from src.config import DEFAULT_SETTINGS
from src.utils.youtube_utils import download_youtube_audio
from src.services.transcription_service import transcribe
from src.services.translation_service import TranslationService, TranslationEngine

# Logger setup
logger = logging.getLogger(__name__)

# Batch status enumeration
class BatchStatus(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    RESUMING = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    FAILED = auto()
    THROTTLED = auto()
    STOPPING = auto()

# Task status enumeration
class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    SKIPPED = auto()
    PAUSED = auto()
    RETRYING = auto()
    VALIDATING = auto()
    DOWNLOADING = auto()
    CONVERTING = auto()
    TRANSCRIBING = auto()
    TRANSLATING = auto()
    EXPORTING = auto()

class BatchProcessor(QObject):
    """
    Processor for batch operations on YouTube videos.
    Handles the queue of tasks and their execution.
    """
    
    # Signals
    batch_status_changed = pyqtSignal(object)  # BatchStatus enum
    task_updated = pyqtSignal(dict)  # Task data dictionary
    batch_completed = pyqtSignal(dict)  # Batch completion report
    progress_updated = pyqtSignal(dict)  # Progress update dictionary
    resource_warning = pyqtSignal(dict)  # Resource warning dictionary
    
    def __init__(self, cache_manager=None, concurrency: int = 2, parent=None):
        """
        Initialize the batch processor.
        
        Args:
            cache_manager: Optional cache manager for caching results
            concurrency: Maximum number of concurrent tasks to run
            parent: Parent QObject
        """
        super().__init__(parent)
        self.cache_manager = cache_manager
        self.concurrency = concurrency
        
        # Task management
        self.task_queue = queue.Queue()
        self.active_tasks = {}  # URL -> task_data
        self.completed_tasks = {}  # URL -> task_data
        self.status = BatchStatus.IDLE
        
        # Worker threads
        self.worker_threads = []
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "total_duration": 0,
            "start_time": None,
            "end_time": None
        }
        
        # Translation service
        self.translation_service = TranslationService()
        
        logger.info("BatchProcessor initialized")
    
    def start_batch(self, urls: List[str]):
        """
        Start or resume processing a batch of YouTube URLs.
        
        Args:
            urls: List of YouTube URLs to process
        """
        if self.status == BatchStatus.PAUSED:
            logger.info("Resuming paused batch")
            self.status = BatchStatus.RESUMING
            self.batch_status_changed.emit(self.status)
            self.pause_event.set()  # Clear the pause
            return
        
        if self.status == BatchStatus.RUNNING:
            logger.info("Batch already running, adding URLs to queue")
            for url in urls:
                self._add_url_to_queue(url)
            return
        
        logger.info(f"Starting new batch with {len(urls)} URLs")
        
        # Reset state
        self.stop_event.clear()
        self.pause_event.clear()
        
        # Reset statistics
        self.stats["total_tasks"] = 0
        self.stats["completed_tasks"] = 0
        self.stats["failed_tasks"] = 0
        self.stats["cancelled_tasks"] = 0
        self.stats["total_duration"] = 0
        self.stats["start_time"] = time.time()
        self.stats["end_time"] = None
        
        # Add URLs to queue
        for url in urls:
            self._add_url_to_queue(url)
        
        # Start worker threads
        self._start_worker_threads()
        
        # Update status
        self.status = BatchStatus.RUNNING
        self.batch_status_changed.emit(self.status)
        self.pause_event.set()  # Ensure not paused
        
        # Start progress updates
        self._start_progress_updates()
    
    def pause_batch(self):
        """Pause the current batch processing."""
        if self.status == BatchStatus.RUNNING:
            logger.info("Pausing batch")
            self.status = BatchStatus.PAUSED
            self.batch_status_changed.emit(self.status)
            self.pause_event.clear()  # Signal pause
    
    def cancel_batch(self):
        """Cancel the current batch processing."""
        if self.status in [BatchStatus.RUNNING, BatchStatus.PAUSED]:
            logger.info("Cancelling batch")
            self.status = BatchStatus.STOPPING
            self.batch_status_changed.emit(self.status)
            self.stop_event.set()  # Signal stop
            self.pause_event.set()  # Clear any pause
            
            # Clear the queue
            while not self.task_queue.empty():
                try:
                    task = self.task_queue.get_nowait()
                    url = task.get("url")
                    if url:
                        task["status"] = TaskStatus.CANCELLED.name
                        self.completed_tasks[url] = task
                        self.task_updated.emit(task)
                        self.stats["cancelled_tasks"] += 1
                except queue.Empty:
                    break
    
    def add_task(self, url: str, model: str, target_lang: Optional[str], output_dir: str, formats: List[str]):
        """
        Add a single task with specific parameters.
        
        Args:
            url: YouTube URL
            model: Transcription model name
            target_lang: Target language code for translation (None for no translation)
            output_dir: Output directory for results
            formats: List of output formats
        """
        task = {
            "url": url,
            "model": model,
            "target_lang": target_lang,
            "output_dir": output_dir,
            "formats": formats,
            "status": TaskStatus.PENDING.name,
            "progress": 0.0,
            "added_time": time.time(),
            "start_time": None,
            "end_time": None,
            "title": "Validating...",
            "error": None,
            "output_files": []
        }
        
        # Check if task already exists
        if url in self.active_tasks or url in self.completed_tasks:
            logger.warning(f"Task for URL {url} already exists, skipping")
            return
        
        # Add to queue
        self.task_queue.put(task)
        self.active_tasks[url] = task
        self.stats["total_tasks"] += 1
        
        # Update UI
        self.task_updated.emit(task)
        
        # Start batch if not already running
        if self.status == BatchStatus.IDLE:
            self.start_batch([])
    
    def cancel_task(self, url: str):
        """
        Cancel a specific task.
        
        Args:
            url: URL of the task to cancel
        """
        if url in self.active_tasks:
            task = self.active_tasks[url]
            task["status"] = TaskStatus.CANCELLED.name
            self.completed_tasks[url] = task
            del self.active_tasks[url]
            self.task_updated.emit(task)
            self.stats["cancelled_tasks"] += 1
    
    def remove_task(self, url: str):
        """
        Remove a task from tracking.
        
        Args:
            url: URL of the task to remove
        """
        if url in self.active_tasks:
            del self.active_tasks[url]
        
        if url in self.completed_tasks:
            del self.completed_tasks[url]
    
    def retry_task(self, url: str):
        """
        Retry a failed or cancelled task.
        
        Args:
            url: URL of the task to retry
        """
        if url in self.completed_tasks:
            task = self.completed_tasks[url].copy()
            task["status"] = TaskStatus.PENDING.name
            task["progress"] = 0.0
            task["error"] = None
            task["added_time"] = time.time()
            task["start_time"] = None
            task["end_time"] = None
            task["output_files"] = []
            
            # Remove from completed tasks
            del self.completed_tasks[url]
            
            # Add back to queue
            self.task_queue.put(task)
            self.active_tasks[url] = task
            
            # Update UI
            self.task_updated.emit(task)
            
            # Start batch if not already running
            if self.status == BatchStatus.IDLE:
                self.start_batch([])
    
    def is_running(self) -> bool:
        """Check if batch processing is currently running."""
        return self.status in [BatchStatus.RUNNING, BatchStatus.RESUMING, BatchStatus.STOPPING]
    
    def set_concurrency(self, concurrency: int):
        """Set the maximum number of concurrent tasks."""
        self.concurrency = max(1, concurrency)
        # Adjust worker threads if already running
        if self.is_running():
            self._adjust_worker_threads()
    
    def load_session(self, session_data: Dict[str, Any]):
        """Load batch processor state from session data."""
        try:
            logger.info("Loading batch processor state from session data")
            
            # Restore tasks
            active_tasks = session_data.get("active_tasks", {})
            completed_tasks = session_data.get("completed_tasks", {})
            
            # Add pending tasks back to queue
            for url, task in active_tasks.items():
                if task.get("status") in [TaskStatus.PENDING.name, TaskStatus.PAUSED.name]:
                    self.task_queue.put(task)
                    self.active_tasks[url] = task
                    self.task_updated.emit(task)
            
            # Add completed tasks to tracking
            for url, task in completed_tasks.items():
                self.completed_tasks[url] = task
                self.task_updated.emit(task)
            
            # Restore statistics
            self.stats = session_data.get("stats", self.stats)
            
            logger.info(f"Loaded {len(self.active_tasks)} active tasks and {len(self.completed_tasks)} completed tasks")
            
        except Exception as e:
            logger.error(f"Error loading batch processor session: {e}")
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get batch processor state for session saving."""
        return {
            "active_tasks": self.active_tasks.copy(),
            "completed_tasks": self.completed_tasks.copy(),
            "stats": self.stats.copy()
        }
    
    def cancel_all(self, wait: bool = True, timeout: Optional[float] = 10.0):
        """Cancel all tasks and stop batch processing."""
        self.cancel_batch()
        
        if wait and self.worker_threads:
            logger.info(f"Waiting for worker threads to complete (timeout: {timeout} seconds)")
            start_time = time.time()
            
            while any(thread.is_alive() for thread in self.worker_threads):
                if timeout and time.time() - start_time > timeout:
                    logger.warning("Timeout waiting for worker threads to complete")
                    break
                time.sleep(0.1)
            
            # Final cleanup
            self.status = BatchStatus.IDLE
            self.batch_status_changed.emit(self.status)
    
    # Private methods
    
    def _add_url_to_queue(self, url: str):
        """Add a URL to the processing queue with default settings."""
        # Skip if already in queue or completed
        if url in self.active_tasks or url in self.completed_tasks:
            logger.debug(f"URL {url} already in queue or completed, skipping")
            return
        
        # Create task with default settings
        settings = getattr(self.parent(), 'settings', DEFAULT_SETTINGS)
        
        task = {
            "url": url,
            "model": settings.get("default_model", "small"),
            "target_lang": settings.get("default_language", "None"),
            "output_dir": settings.get("output_dir", str(Path.home() / "Downloads")),
            "formats": ["srt"],  # Default format
            "status": TaskStatus.PENDING.name,
            "progress": 0.0,
            "added_time": time.time(),
            "start_time": None,
            "end_time": None,
            "title": "Validating...",
            "error": None,
            "output_files": []
        }
        
        # Add to queue and tracking
        self.task_queue.put(task)
        self.active_tasks[url] = task
        self.stats["total_tasks"] += 1
        
        # Update UI
        self.task_updated.emit(task)
        
        logger.debug(f"Added URL {url} to queue")
    
    def _start_worker_threads(self):
        """Start worker threads for processing tasks."""
        # Stop existing threads if any
        if self.worker_threads:
            self.stop_event.set()
            for thread in self.worker_threads:
                if thread.is_alive():
                    thread.join(1.0)
            self.worker_threads = []
            self.stop_event.clear()
        
        # Create new worker threads
        for i in range(self.concurrency):
            thread = threading.Thread(
                target=self._worker_thread,
                name=f"worker-{i}",
                daemon=True
            )
            self.worker_threads.append(thread)
            thread.start()
        
        logger.info(f"Started {len(self.worker_threads)} worker threads")
    
    def _adjust_worker_threads(self):
        """Adjust the number of worker threads based on concurrency setting."""
        current_workers = len([thread for thread in self.worker_threads if thread.is_alive()])
        
        if current_workers < self.concurrency:
            # Add more workers
            for i in range(current_workers, self.concurrency):
                thread = threading.Thread(
                    target=self._worker_thread,
                    name=f"worker-{i}",
                    daemon=True
                )
                self.worker_threads.append(thread)
                thread.start()
                logger.debug(f"Added worker thread {thread.name}")
        
        # If we have too many workers, they'll exit naturally when the stop_event is set
        # We don't need to forcibly terminate them
    
    def _start_progress_updates(self):
        """Start a thread to periodically send progress updates."""
        def update_thread():
            while not self.stop_event.is_set():
                if self.status == BatchStatus.RUNNING:
                    self._send_progress_update()
                time.sleep(0.5)  # Update twice per second
        
        thread = threading.Thread(target=update_thread, name="progress-updater", daemon=True)
        thread.start()
    
    def _send_progress_update(self):
        """Send a progress update signal."""
        total_tasks = self.stats["total_tasks"]
        completed_tasks = self.stats["completed_tasks"]
        
        if total_tasks == 0:
            progress = 0.0
        else:
            # Factor in progress of active tasks
            active_progress = sum(task.get("progress", 0.0) for task in self.active_tasks.values())
            active_count = len(self.active_tasks)
            
            # Calculate overall progress
            progress = (completed_tasks + active_progress) / total_tasks
        
        # Send update
        self.progress_updated.emit({
            "progress": progress,
            "completed": completed_tasks,
            "total": total_tasks,
            "status_message": f"Processing {len(self.active_tasks)} tasks, {completed_tasks}/{total_tasks} completed"
        })
    
    def _worker_thread(self):
        """Worker thread function for processing tasks."""
        logger.debug(f"Worker thread {threading.current_thread().name} started")
        
        while not self.stop_event.is_set():
            # Wait for pause to be cleared
            self.pause_event.wait()
            if self.stop_event.is_set():
                break
            
            try:
                # Get task from queue with timeout
                try:
                    task = self.task_queue.get(timeout=1.0)
                except queue.Empty:
                    # Check if all tasks completed
                    if not self.active_tasks and self.status == BatchStatus.RUNNING:
                        self._handle_batch_completion()
                    continue
                
                # Process task
                url = task.get("url")
                if not url:
                    logger.warning("Task missing URL, skipping")
                    continue
                
                # Mark task as running
                task["status"] = TaskStatus.RUNNING.name
                task["start_time"] = time.time()
                self.task_updated.emit(task)
                
                # Process the task
                self._process_task(task)
                
                # Task queue item completion
                self.task_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
        
        logger.debug(f"Worker thread {threading.current_thread().name} stopped")
    
    def _process_task(self, task: Dict[str, Any]):
        """Process a single task."""
        url = task.get("url")
        if not url:
            return
        
        try:
            # Validate YouTube URL
            task["status"] = TaskStatus.VALIDATING.name
            self._update_task_progress(task, 0.05, "Validating YouTube URL...")
            
            # Download YouTube audio
            task["status"] = TaskStatus.DOWNLOADING.name
            self._update_task_progress(task, 0.1, "Downloading audio...")
            
            audio_path, video_info = download_youtube_audio(
                url,
                output_dir=task.get("output_dir"),
                progress_callback=lambda p, m: self._update_task_progress(task, 0.1 + p * 0.2, m)
            )
            
            # Update task with video info
            task["title"] = video_info.get("title", "Unknown video")
            task["duration"] = video_info.get("duration", 0)
            self.task_updated.emit(task)
            
            # Convert audio if needed
            task["status"] = TaskStatus.CONVERTING.name
            self._update_task_progress(task, 0.3, "Preparing audio...")
            
            # Transcribe audio
            task["status"] = TaskStatus.TRANSCRIBING.name
            self._update_task_progress(task, 0.4, "Transcribing audio...")
            
            transcription_result, error = transcribe(
                audio_path,
                model_name=task.get("model", "small"),
                progress_callback=lambda p, m: self._update_task_progress(task, 0.4 + p * 0.4, m),
                stop_event=self.stop_event
            )
            
            if not transcription_result or error:
                raise RuntimeError(f"Transcription failed: {error}")
            
            # Translate if requested
            target_lang = task.get("target_lang")
            if target_lang and target_lang != "None":
                task["status"] = TaskStatus.TRANSLATING.name
                self._update_task_progress(task, 0.8, f"Translating to {target_lang}...")
                
                translation_result, error = self.translation_service.translate(
                    transcription_result,
                    target_lang,
                    progress_callback=lambda p, m: self._update_task_progress(task, 0.8 + p * 0.1, m),
                    stop_event=self.stop_event
                )
                
                if translation_result:
                    transcription_result = translation_result
                if error:
                    logger.warning(f"Translation warning: {error}")
            
            # Export results
            task["status"] = TaskStatus.EXPORTING.name
            self._update_task_progress(task, 0.9, "Exporting results...")
            
            output_files = self._export_results(
                transcription_result,
                task.get("output_dir"),
                task.get("formats", ["srt"]),
                video_info
            )
            
            task["output_files"] = output_files
            
            # Mark task as completed
            task["status"] = TaskStatus.COMPLETED.name
            task["progress"] = 1.0
            task["end_time"] = time.time()
            self.stats["completed_tasks"] += 1
            
            if task.get("duration"):
                self.stats["total_duration"] += task["duration"]
            
            # Move from active to completed
            del self.active_tasks[url]
            self.completed_tasks[url] = task
            
            # Update UI
            self.task_updated.emit(task)
            logger.info(f"Task completed: {url} - {task['title']}")
            
        except Exception as e:
            logger.error(f"Error processing task {url}: {e}")
            
            # Mark task as failed
            task["status"] = TaskStatus.FAILED.name
            task["error"] = str(e)
            task["end_time"] = time.time()
            self.stats["failed_tasks"] += 1
            
            # Move from active to completed
            del self.active_tasks[url]
            self.completed_tasks[url] = task
            
            # Update UI
            self.task_updated.emit(task)
    
    def _update_task_progress(self, task: Dict[str, Any], progress: float, message: str):
        """Update task progress and emit task_updated signal."""
        if self.stop_event.is_set():
            raise InterruptedError("Task cancelled")
        
        if self.pause_event.is_set() == False:  # If paused
            task["status"] = TaskStatus.PAUSED.name
            self.task_updated.emit(task)
            self.pause_event.wait()  # Wait for pause to be cleared
            task["status"] = TaskStatus.RUNNING.name
        
        task["progress"] = progress
        task["status_message"] = message
        self.task_updated.emit(task)
    
    def _export_results(self, transcription_result, output_dir: str, formats: List[str], video_info: Dict[str, Any]) -> List[str]:
        """Export transcription results to specified formats."""
        from src.utils.export_utils import export_transcription
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate base filename from video title
        title = video_info.get("title", "unknown")
        safe_title = "_".join(title.split())
        safe_title = "".join(c for c in safe_title if c.isalnum() or c in "_-")
        
        output_files = []
        
        for format_name in formats:
            try:
                output_file = export_transcription(
                    transcription_result,
                    output_path,
                    format_name,
                    safe_title,
                    video_info
                )
                if output_file:
                    output_files.append(str(output_file))
            except Exception as e:
                logger.error(f"Error exporting to {format_name}: {e}")
        
        return output_files
    
    def _handle_batch_completion(self):
        """Handle batch completion."""
        if self.status != BatchStatus.RUNNING:
            return
        
        logger.info("Batch processing completed")
        
        # Update stats
        self.stats["end_time"] = time.time()
        
        # Create completion report
        report = {
            "total_tasks": self.stats["total_tasks"],
            "completed_tasks": self.stats["completed_tasks"],
            "failed_tasks": self.stats["failed_tasks"],
            "cancelled_tasks": self.stats["cancelled_tasks"],
            "total_duration": self.stats["total_duration"],
            "processing_time": self.stats["end_time"] - self.stats["start_time"] if self.stats["start_time"] else 0
        }
        
        # Update status
        self.status = BatchStatus.COMPLETED
        self.batch_status_changed.emit(self.status)
        
        # Emit completion report
        self.batch_completed.emit(report)
"""
Stop method for BatchProcessor class.
This is a temporary file that will be used to add the missing stop method.
"""

def stop(self, wait: bool = True, timeout: float = 10.0):
    """Stop batch processing (alias for cancel_batch that accepts wait and timeout params)."""
    logger.info(f"Stopping batch processor with wait={wait}, timeout={timeout}")
    
    # Call the existing cancel_batch method
    self.cancel_batch()
    
    # If wait is requested, wait for threads to exit
    if wait and self.worker_threads:
        # Set appropriate timeouts
        thread_timeout = timeout / len(self.worker_threads) if len(self.worker_threads) > 0 else timeout
        
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=thread_timeout)
                
        # Clear thread list after waiting
        self.worker_threads = []
    
    return
