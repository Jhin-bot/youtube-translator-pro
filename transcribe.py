"""
Transcription module that uses Whisper models to transcribe audio files.
Provides safe and efficient transcription with proper resource management.
"""
import os
import gc
import time
import signal
import tempfile
import threading
import logging
import multiprocessing
import json
import psutil
import atexit
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from multiprocessing import Process, Queue, Event, Value, cpu_count
from contextlib import contextmanager
from functools import lru_cache

# Import whisper conditionally to allow for mock testing
try:
    import whisper
    import numpy as np
    import torch
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Setup logger
logger = logging.getLogger(__name__)

# Transcription settings
DEFAULT_TRANSCRIPTION_TIMEOUT = 1800  # 30 minutes max for transcription
MAX_CACHE_SIZE = 2  # Maximum number of Whisper models to keep loaded in memory

# Define valid Whisper models
VALID_MODELS = ["tiny", "base", "small", "medium", "large"]

# Global tracking of active processes for cleanup
_active_processes = set()
_process_lock = threading.RLock()

# Memory management settings
GPU_MEMORY_THRESHOLD = 0.9  # Trigger cleanup when GPU memory usage exceeds 90%
CPU_MEMORY_THRESHOLD = 0.85  # Trigger cleanup when system memory exceeds 85%

# Register cleanup on exit
@atexit.register
def _cleanup_on_exit():
    """Ensure all processes are terminated on program exit."""
    _terminate_all_processes()
    _clear_model_cache()
    logger.debug("Transcription cleanup complete on exit")


# ===== Process Management =====

def _register_process(process: Process):
    """Add a process to the global tracking set."""
    with _process_lock:
        _active_processes.add(process)

def _unregister_process(process: Process):
    """Remove a process from the global tracking set."""
    with _process_lock:
        _active_processes.discard(process)

def _terminate_all_processes():
    """Terminate all actively tracked processes."""
    logger.info("Terminating all active transcription processes...")
    with _process_lock:
        for process in list(_active_processes): # Iterate over a copy
            if process.is_alive():
                try:
                    logger.debug(f"Terminating process {process.pid} ({process.name})...")
                    process.terminate()
                    # Give it a moment to terminate
                    process.join(timeout=1.0)
                    if process.is_alive():
                         logger.warning(f"Process {process.pid} did not terminate gracefully. Killing.")
                         try:
                              process.kill() # Force kill if terminate fails
                              process.join(timeout=1.0)
                         except Exception as kill_err:
                              logger.error(f"Failed to kill process {process.pid}: {kill_err}")

                    logger.debug(f"Process {process.pid} terminated.")
                except Exception as e:
                    logger.error(f"Error terminating process {process.pid}: {e}")
        _active_processes.clear()
    logger.info("All active transcription processes terminated.")


# ===== Model Loading and Caching =====

# Use lru_cache to keep recently used models in memory
@lru_cache(maxsize=MAX_CACHE_SIZE)
def _load_whisper_model(model_name: str, device: str) -> whisper.Whisper:
    """
    Load a Whisper model, caching recent ones.

    Args:
        model_name: The name of the model to load.
        device: The device to load the model onto ('cpu' or 'cuda').

    Returns:
        The loaded Whisper model object.

    Raises:
        RuntimeError: If Whisper is not available or model loading fails.
    """
    if not WHISPER_AVAILABLE:
        raise RuntimeError("Whisper library is not available.")

    logger.info(f"Loading Whisper model '{model_name}' on '{device}'...")
    try:
        # Check available memory before loading large models
        if device == 'cuda' and torch.cuda.is_available():
             # Check GPU memory
             torch.cuda.empty_cache() # Clear cache before checking
             gpu_memory_info = torch.cuda.mem_get_info() # returns (free, total)
             free_gpu_memory_gb = gpu_memory_info[0] / (1024**3)
             total_gpu_memory_gb = gpu_memory_info[1] / (1024**3)
             logger.debug(f"GPU memory: {free_gpu_memory_gb:.2f} GB free / {total_gpu_memory_gb:.2f} GB total")

             # Estimate model size (these are rough estimates, actual size varies)
             model_sizes_gb = {
                 "tiny": 0.074, # ~74 MB
                 "base": 0.148, # ~148 MB
                 "small": 0.498, # ~498 MB
                 "medium": 1.53, # ~1.53 GB
                 "large": 3.07 # ~3.07 GB
             }
             estimated_model_size_gb = model_sizes_gb.get(model_name, 0)

             # Allow some buffer for other processes/overhead
             required_free_gpu_memory_gb = estimated_model_size_gb * 1.2 # Require 20% buffer

             if free_gpu_memory_gb < required_free_gpu_memory_gb:
                  raise RuntimeError(f"Insufficient GPU memory to load model '{model_name}'. Requires ~{required_free_gpu_memory_gb:.2f} GB free, but only {free_gpu_memory_gb:.2f} GB available.")

        elif device == 'cpu':
             # Check system RAM
             mem_info = psutil.virtual_memory()
             free_ram_gb = mem_info.available / (1024**3)
             total_ram_gb = mem_info.total / (1024**3)
             logger.debug(f"System RAM: {free_ram_gb:.2f} GB free / {total_ram_gb:.2f} GB total")

             # CPU models also require significant RAM, especially larger ones
             # These estimates are very rough and depend on implementation details
             cpu_model_sizes_gb = {
                 "tiny": 0.2,
                 "base": 0.5,
                 "small": 1.5,
                 "medium": 4.0,
                 "large": 8.0 # Large models on CPU can use a lot of RAM
             }
             estimated_model_size_gb = cpu_model_sizes_gb.get(model_name, 0)
             required_free_ram_gb = estimated_model_size_gb * 1.5 # Require 50% buffer

             if free_ram_gb < required_free_ram_gb:
                  raise RuntimeError(f"Insufficient system RAM to load model '{model_name}' on CPU. Requires ~{required_free_ram_gb:.2f} GB free, but only {free_ram_gb:.2f} GB available.")


        # Load the model
        model = whisper.load_model(model_name, device=device)
        logger.info(f"Whisper model '{model_name}' loaded successfully.")
        return model

    except RuntimeError as re:
         # Re-raise specific runtime errors (like insufficient memory)
         raise re
    except Exception as e:
        logger.error(f"Failed to load Whisper model '{model_name}': {e}", exc_info=True)
        raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}")


def _clear_model_cache():
    """Clear the LRU cache for Whisper models."""
    logger.info("Clearing Whisper model cache...")
    _load_whisper_model.cache_clear()
    # Also attempt to release memory
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    logger.info("Whisper model cache cleared.")


# ===== Worker Process Function =====

def _transcribe_worker(
    audio_path: str,
    model_name: str,
    device: str,
    result_queue: Queue,
    progress_queue: Queue,
    stop_event: Event,
    language: Optional[str] = None, # Source language for transcription
    task: str = "transcribe" # 'transcribe' or 'translate' (though translation is handled separately now)
):
    """
    Worker process function to perform transcription or translation.

    Args:
        audio_path: Path to the audio file.
        model_name: Name of the Whisper model to use.
        device: Device to run inference on ('cpu' or 'cuda').
        result_queue: Queue to put the transcription result.
        progress_queue: Queue to report progress.
        stop_event: Event to signal process termination.
        language: Optional source language code for transcription.
        task: Task to perform ('transcribe' or 'translate'). Note: Translation is now handled in batch.py, this worker only transcribes.
    """
    # Ensure the process is registered for cleanup
    current_process = multiprocessing.current_process()
    _register_process(current_process)
    current_process.name = f"transcribe-worker-{model_name}-{os.getpid()}" # Set process name

    logger.debug(f"Transcription worker started (PID: {os.getpid()}) for {audio_path} using model '{model_name}' on '{device}'.")

    try:
        # Register signal handlers for graceful termination
        def handle_term_signal(signum, frame):
            logger.debug(f"Worker {os.getpid()} received termination signal: {signum}")
            stop_event.set() # Signal the main thread to stop
            # Note: This signal handler runs in the main thread of the worker process.
            # It sets the event, which the transcription loop should check.

        # Use default signal handler for SIGINT (Ctrl+C) - might cause issues if not handled
        # signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, handle_term_signal)
        if hasattr(signal, 'SIGBREAK'):  # Windows specific
            signal.signal(signal.SIGBREAK, handle_term_signal)


        # Report starting
        progress_queue.put({"type": "status", "message": "Loading model..."})
        progress_queue.put({"type": "progress", "value": 0.05}) # Report initial progress


        # Load the model (will use LRU cache)
        model = _load_whisper_model(model_name, device)

        # Report model loaded
        progress_queue.put({"type": "status", "message": "Model loaded."})
        progress_queue.put({"type": "progress", "value": 0.1}) # Report progress after loading


        # Perform transcription
        logger.info(f"Starting transcription of {audio_path}...")
        progress_queue.put({"type": "status", "message": "Transcribing..."})

        # Whisper's transcribe method has a progress callback argument
        # The callback receives (progress, status_text)
        def whisper_progress_callback(progress: float, status_text: str):
             # Map Whisper's progress (0-1) to a range within the worker's progress (e.g., 10-95%)
             overall_progress = 0.10 + progress * 0.85
             progress_queue.put({"type": "progress", "value": overall_progress})
             progress_queue.put({"type": "status", "message": f"Transcribing: {status_text}"})
             # Check stop event frequently within the callback if Whisper supports it
             if stop_event.is_set():
                  logger.debug(f"Worker {os.getpid()} detected stop event during transcription.")
                  # Raising an exception here might stop the Whisper process
                  raise KeyboardInterrupt # Use KeyboardInterrupt as a common way to stop loops


        # Use the 'transcribe' task for Whisper, even if the overall task is translation.
        # The translation step is handled separately in batch.py after transcription.
        # The 'language' argument in whisper.transcribe is for the *source* language detection/hinting.
        # If language is None, Whisper attempts to detect it.
        transcription_options = {
            "task": "transcribe",
            "language": language, # Use provided language hint or None for auto-detect
            "fp16": (device == "cuda") # Use FP16 on GPU if available
        }

        # Add progress callback if Whisper version supports it
        # Check if the transcribe method has a progress_callback parameter
        import inspect
        if 'progress_callback' in inspect.signature(model.transcribe).parameters:
             transcription_options['progress_callback'] = whisper_progress_callback
        else:
             logger.warning("Whisper version does not support progress callback. Progress updates will be less granular.")


        # Check stop event before starting transcription
        if stop_event.is_set():
             logger.warning(f"Worker {os.getpid()} detected stop event before transcription.")
             result_queue.put({"status": "CANCELLED", "error": "Task cancelled."})
             return # Exit worker thread


        # Perform the transcription
        result = model.transcribe(audio_path, **transcription_options)

        # Check stop event after transcription finishes (in case it was set during the process)
        if stop_event.is_set():
             logger.warning(f"Worker {os.getpid()} detected stop event after transcription finished.")
             result_queue.put({"status": "CANCELLED", "error": "Task cancelled."})
             return # Exit worker thread


        logger.info(f"Transcription completed for {audio_path}.")
        progress_queue.put({"type": "progress", "value": 0.95}) # Report near completion


        # Prepare result data
        transcription_result = {
            "text": result.get("text"),
            "segments": result.get("segments"),
            "language": result.get("language"), # Detected or specified language
            # Add other relevant information from the result if needed
        }

        result_queue.put({"status": "TRANSCRIBED", "result": transcription_result}) # Report success

    except KeyboardInterrupt:
        # Handle cancellation via stop_event and KeyboardInterrupt
        logger.warning(f"Worker {os.getpid()} transcription cancelled.")
        result_queue.put({"status": "CANCELLED", "error": "Transcription cancelled."})

    except RuntimeError as re:
         # Handle specific runtime errors like insufficient memory
         logger.error(f"Worker {os.getpid()} RuntimeError: {re}", exc_info=True)
         result_queue.put({"status": "FAILED", "error": str(re)})

    except Exception as e:
        # Handle any other exceptions
        error_message = f"Transcription worker error: {e}"
        logger.error(f"Worker {os.getpid()} exception: {error_message}", exc_info=True)
        result_queue.put({"status": "FAILED", "error": error_message})

    finally:
        # Ensure the process is unregistered
        _unregister_process(current_process)
        logger.debug(f"Transcription worker finished (PID: {os.getpid()}).")


# ===== Main Transcription Function (called by BatchProcessor) =====

def transcribe(
    audio_path: str,
    model_name: str = 'small',
    language: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    stop_event: Optional[Event] = None,
    timeout: Optional[float] = DEFAULT_TRANSCRIPTION_TIMEOUT
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Transcribe an audio file using a Whisper model in a separate process.

    Args:
        audio_path: Path to the input audio file (expected to be 16kHz mono WAV).
        model_name: The name of the Whisper model to use.
        language: Optional source language code (e.g., 'en', 'es'). If None, Whisper detects.
        progress_callback: Optional callback function (progress: float, status_text: str).
        stop_event: Optional multiprocessing.Event to signal cancellation.
        timeout: Maximum time in seconds to wait for the transcription process.

    Returns:
        A tuple containing:
        - The transcription result dictionary if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """
    if not WHISPER_AVAILABLE:
        return None, "Whisper library is not available. Please install it (e.g., pip install whisper)."

    if not os.path.exists(audio_path):
        return None, f"Audio file not found: {audio_path}"

    if model_name not in VALID_MODELS:
        return None, f"Invalid Whisper model name: {model_name}. Valid models are: {', '.join(VALID_MODELS)}"

    # Determine the device to use (GPU if available and supported, otherwise CPU)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.debug(f"Using device: {device}")

    # Create queues for result and progress
    result_queue: Queue = Queue()
    progress_queue: Queue = Queue()
    # Create stop event if not provided
    if stop_event is None:
         stop_event = Event()

    # Create and start the worker process
    worker_process = Process(
        target=_transcribe_worker,
        args=(audio_path, model_name, device, result_queue, progress_queue, stop_event, language)
    )
    _register_process(worker_process) # Register the process for cleanup

    worker_process.start()
    logger.debug(f"Transcription worker process started with PID: {worker_process.pid}")

    transcription_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    worker_status = "RUNNING" # Track worker status internally

    start_time = time.time()

    try:
        # Monitor queues for updates and results
        while worker_process.is_alive() and not stop_event.is_set():
            # Check for timeout
            if timeout is not None and time.time() - start_time > timeout:
                logger.warning(f"Transcription process timed out after {timeout} seconds.")
                error_message = "Transcription timed out."
                worker_status = "FAILED"
                stop_event.set() # Signal the worker to stop
                break

            # Check progress queue
            while not progress_queue.empty():
                try:
                    update = progress_queue.get_nowait()
                    if update["type"] == "progress" and progress_callback:
                        # Pass progress to the main progress callback
                        # The progress value from the worker is already mapped (0.0 to 1.0)
                        progress_callback(update["value"], update.get("status_text", "Transcribing..."))
                    elif update["type"] == "status" and progress_callback:
                         # Pass status text to the main progress callback
                         progress_callback(update.get("value", 0.0), update.get("message", "Transcribing..."))

                except Exception as e:
                    logger.warning(f"Error getting from progress queue: {e}")


            # Check result queue (non-blocking)
            if not result_queue.empty():
                try:
                    result_data = result_queue.get_nowait()
                    worker_status = result_data.get("status", "FAILED")
                    if worker_status == "TRANSCRIBED":
                        transcription_result = result_data.get("result")
                        logger.debug("Received transcription result from worker.")
                    else: # FAILED or CANCELLED
                        error_message = result_data.get("error", "Unknown worker error.")
                        logger.error(f"Worker reported status {worker_status}: {error_message}")

                    # Exit the monitoring loop once a result is received
                    break

                except Exception as e:
                    logger.error(f"Error getting from result queue: {e}")
                    error_message = f"Error receiving result from worker: {e}"
                    worker_status = "FAILED"
                    break # Exit loop on error


            # Small sleep to prevent tight loop
            time.sleep(0.05)

        # If the loop finished because the process exited without putting a result
        if worker_process.is_alive() and stop_event.is_set() and worker_status == "RUNNING":
             # Process was signaled to stop but didn't put a result yet
             error_message = error_message or "Transcription cancelled."
             worker_status = "CANCELLED"
             logger.debug("Worker process loop exited due to stop event.")
        elif worker_process.exitcode is not None and worker_status == "RUNNING":
             # Process exited unexpectedly
             error_message = error_message or f"Transcription process exited unexpectedly with code {worker_process.exitcode}."
             worker_status = "FAILED"
             logger.error(f"Worker process exited unexpectedly: {worker_process.exitcode}")


    except Exception as e:
        logger.critical(f"Fatal error in main transcription thread: {e}", exc_info=True)
        error_message = f"Fatal error in transcription process management: {e}"
        worker_status = "FAILED"

    finally:
        # Ensure the worker process is terminated and cleaned up
        if worker_process.is_alive():
            logger.warning(f"Terminating transcription worker process {worker_process.pid}...")
            try:
                worker_process.terminate()
                worker_process.join(timeout=5.0) # Give it a few seconds to terminate
                if worker_process.is_alive():
                     logger.error(f"Worker process {worker_process.pid} did not terminate gracefully. Killing.")
                     worker_process.kill()
                     worker_process.join(timeout=1.0)
            except Exception as term_err:
                logger.error(f"Error terminating worker process {worker_process.pid}: {term_err}")

        _unregister_process(worker_process) # Unregister the process

        logger.debug("Transcription process management finished.")

        # Return the result and error message
        return transcription_result, error_message

# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     # Create a dummy audio file for testing
#     dummy_audio_path = Path(tempfile.gettempdir()) / "dummy_audio_test.wav"
#     try:
#          # Create a simple WAV header and some silent data
#          # This is a minimal valid 16kHz mono WAV file
#          import wave
#          sample_rate = 16000
#          channels = 1
#          sample_width = 2 # 16 bits
#          duration_seconds = 5
#          n_frames = sample_rate * duration_seconds

#          with wave.open(str(dummy_audio_path), 'wb') as wf:
#              wf.setnchannels(channels)
#              wf.setsampwidth(sample_width)
#              wf.setframerate(sample_rate)
#              # Write silent frames (16-bit signed integer, 0 is silence)
#              wf.writeframes(b'\\x00\\x00' * n_frames)

#          logger.info(f"Created dummy audio file: {dummy_audio_path}")

#          # --- Test Transcription ---
#          logger.info("Starting transcription test...")

#          def test_progress_callback(progress: float, status_text: str):
#              logger.info(f"Transcription Progress: {progress:.1%} - {status_text}")

#          # Test with a small model
#          # Ensure you have the 'small' model downloaded or Whisper can download it
#          # whisper.load_model("small") # Pre-load if needed

#          # Create a stop event for potential cancellation testing
#          test_stop_event = Event()

#          # You can uncomment this block to test cancellation after a few seconds
#          # def cancel_after_delay(delay):
#          #      time.sleep(delay)
#          #      logger.warning("Signaling transcription stop event!")
#          #      test_stop_event.set()
#          # cancel_thread = threading.Thread(target=cancel_after_delay, args=(5,)) # Cancel after 5 seconds
#          # cancel_thread.daemon = True
#          # cancel_thread.start()


#          transcription_result, error = transcribe(
#              str(dummy_audio_path),
#              model_name="tiny", # Use a smaller model for faster testing
#              language="en", # Hint language
#              progress_callback=test_progress_callback,
#              stop_event=test_stop_event,
#              timeout=30 # 30 seconds timeout for test
#          )

#          if error:
#              logger.error(f"Transcription failed: {error}")
#          elif transcription_result:
#              logger.info("Transcription successful!")
#              logger.info(f"Detected Language: {transcription_result.get('language')}")
#              logger.info(f"Transcription Text: {transcription_result.get('text')}")
#              # logger.info(f"Segments: {transcription_result.get('segments')}")
#          else:
#               logger.warning("Transcription finished with no result and no error.")


#     except ImportError:
#          logger.error("PyDub or PyAudio not installed. Cannot create dummy WAV file.")
#     except Exception as e:
#          logger.critical(f"An error occurred during the transcription test: {e}", exc_info=True)

#     finally:
#         # Clean up the dummy audio file
#         if dummy_audio_path.exists():
#             try:
#                 dummy_audio_path.unlink()
#                 logger.info(f"Cleaned up dummy audio file: {dummy_audio_path}")
#             except Exception as e:
#                 logger.warning(f"Failed to clean up dummy audio file {dummy_audio_path}: {e}")

#         # Ensure all worker processes are terminated
#         _terminate_all_processes()
#         _clear_model_cache()
