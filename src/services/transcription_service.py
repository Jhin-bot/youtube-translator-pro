""""
Transcription service for YouTube Translator Pro.
Handles the transcription of audio files using Whisper models.
""""

import os
import gc
import time
import signal
import logging
import multiprocessing
import psutil
import atexit
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from multiprocessing import Process, Queue, Event, Value
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

# Import configuration
from src.config import DEFAULT_TRANSCRIPTION_TIMEOUT, TRANSCRIPTION_MODELS

# Setup logger
logger = logging.getLogger(__name__)

# Global tracking of active processes for cleanup
_active_processes = set()
_process_lock = multiprocessing.RLock()

# Memory management settings
GPU_MEMORY_THRESHOLD = 0.9  # Trigger cleanup when GPU memory usage exceeds 90%
CPU_MEMORY_THRESHOLD = 0.85  # Trigger cleanup when system memory exceeds 85%
MAX_CACHE_SIZE = 2  # Maximum number of Whisper models to keep loaded in memory

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
        for process in list(_active_processes):  # Iterate over a copy
            if process.is_alive():
                try:
                    logger.debug(f"Terminating process {process.pid} ({process.name})...")
                    process.terminate()
                    # Give it a moment to terminate
                    process.join(timeout=1.0)
                    if process.is_alive():
                        logger.warning(f"Process {process.pid} did not terminate gracefully. Killing.")
                        try:
                            process.kill()  # Force kill if terminate fails
                            process.join(timeout=1.0)
                        except Exception as kill_err:
                            logger.error(f"Failed to kill process {process.pid}: {kill_err}")

                    logger.debug(f"Process {process.pid} terminated.")
                except Exception as e:
                    logger.error(f"Error terminating process {process.pid}: {e}")
        _active_processes.clear()
    logger.info("All active transcription processes terminated.")


# ===== Model Loading and Caching =====

@lru_cache(maxsize=MAX_CACHE_SIZE)
def _load_whisper_model(model_name: str, device: str) -> "whisper.Whisper":
    """"
    Load a Whisper model, caching recent ones.

    Args:
        model_name: The name of the model to load.
        device: The device to load the model onto ('cpu' or 'cuda').

    Returns:
        The loaded Whisper model object.

    Raises:
        RuntimeError: If Whisper is not available or model loading fails.
    """"
    if not WHISPER_AVAILABLE:
        raise RuntimeError("Whisper library is not available.")

    logger.info(f"Loading Whisper model '{model_name}' on '{device}'...")
    try:
        # Check available memory before loading large models
        if device == 'cuda' and torch.cuda.is_available():
            # Check GPU memory
            torch.cuda.empty_cache()  # Clear cache before checking
            gpu_memory_info = torch.cuda.mem_get_info()  # returns (free, total)
            free_gpu_memory_gb = gpu_memory_info[0] / (1024**3)
            total_gpu_memory_gb = gpu_memory_info[1] / (1024**3)
            logger.debug(f"GPU memory: {free_gpu_memory_gb:.2f} GB free / {total_gpu_memory_gb:.2f} GB total")

            # Estimate model size (rough estimates)
            model_sizes_gb = {
                "tiny": 0.074,  # ~74 MB
                "base": 0.148,  # ~148 MB
                "small": 0.498,  # ~498 MB
                "medium": 1.53,  # ~1.53 GB
                "large": 3.07  # ~3.07 GB
            }
            estimated_model_size_gb = model_sizes_gb.get(model_name, 0)

            # Allow buffer for overhead
            required_free_gpu_memory_gb = estimated_model_size_gb * 1.2  # Require 20% buffer

            if free_gpu_memory_gb < required_free_gpu_memory_gb:
                raise RuntimeError(f"Insufficient GPU memory to load model '{model_name}'. Requires ~{required_free_gpu_memory_gb:.2f} GB free, but only {free_gpu_memory_gb:.2f} GB available.")

        elif device == 'cpu':
            # Check system RAM
            mem_info = psutil.virtual_memory()
            free_ram_gb = mem_info.available / (1024**3)
            total_ram_gb = mem_info.total / (1024**3)
            logger.debug(f"System RAM: {free_ram_gb:.2f} GB free / {total_ram_gb:.2f} GB total")

            # CPU models also require significant RAM
            cpu_model_sizes_gb = {
                "tiny": 0.2,
                "base": 0.5,
                "small": 1.5,
                "medium": 4.0,
                "large": 8.0
            }
            estimated_model_size_gb = cpu_model_sizes_gb.get(model_name, 0)
            required_free_ram_gb = estimated_model_size_gb * 1.5  # Require 50% buffer

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
    language: Optional[str] = None
):
    """"
    Worker process function to perform transcription.
    
    Args:
        audio_path: Path to the audio file to transcribe.
        model_name: Name of the Whisper model to use.
        device: Device to run the model on ('cpu' or 'cuda').
        result_queue: Queue to put the results into.
        progress_queue: Queue to report progress.
        stop_event: Event to signal cancellation.
        language: Optional language code for transcription.
    """"
    try:
        logger.info(f"Transcription worker started for {audio_path} with model {model_name}")
        progress_queue.put((0.0, "Loading model..."))
        
        # Determine device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Using device: {device}")
        
        # Load the Whisper model
        model = _load_whisper_model(model_name, device)
        progress_queue.put((0.1, "Model loaded successfully"))
        
        if stop_event.is_set():
            result_queue.put((None, "Transcription cancelled before processing"))
            return
        
        # Load audio file
        progress_queue.put((0.2, "Loading audio..."))
        try:
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            progress_queue.put((0.3, "Audio loaded successfully"))
        except Exception as e:
            error_msg = f"Failed to load audio file: {e}"
            logger.error(error_msg)
            result_queue.put((None, error_msg))
            return
        
        if stop_event.is_set():
            result_queue.put((None, "Transcription cancelled after loading audio"))
            return
        
        # Process audio with Whisper
        progress_queue.put((0.4, "Transcribing..."))
        
        # Prepare transcription options
        options = {}
        if language:
            options["language"] = language
        
        # Perform transcription
        try:
            result = model.transcribe(
                audio, 
                **options
            )
            progress_queue.put((0.9, "Transcription complete, processing results..."))
        except Exception as e:
            error_msg = f"Transcription failed: {e}"
            logger.error(error_msg, exc_info=True)
            result_queue.put((None, error_msg))
            return
        
        if stop_event.is_set():
            result_queue.put((None, "Transcription cancelled after processing"))
            return
        
        # Send success result
        progress_queue.put((1.0, "Transcription complete"))
        result_queue.put((result, None))
        logger.info(f"Transcription worker completed for {audio_path}")
        
    except Exception as e:
        error_msg = f"Unexpected error in transcription worker: {e}"
        logger.error(error_msg, exc_info=True)
        result_queue.put((None, error_msg))


# ===== Main Transcription Function =====

def transcribe(
    audio_path: str,
    model_name: str = 'small',
    language: Optional[str] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
    stop_event: Optional[Event] = None,
    timeout: Optional[float] = DEFAULT_TRANSCRIPTION_TIMEOUT
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """"
    Transcribe an audio file using a Whisper model in a separate process.
    
    Args:
        audio_path: Path to the input audio file.
        model_name: The name of the Whisper model to use.
        language: Optional source language code.
        progress_callback: Optional callback function for progress updates.
        stop_event: Optional Event to signal cancellation.
        timeout: Maximum time in seconds to wait for transcription.
        
    Returns:
        A tuple containing:
        - The transcription result dictionary if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    if not os.path.exists(audio_path):
        return None, f"Audio file not found: {audio_path}"
    
    if model_name not in TRANSCRIPTION_MODELS:
        return None, f"Invalid model name: {model_name}. Valid models are: {', '.join(TRANSCRIPTION_MODELS)}"
    
    # Create our own stop_event if none provided
    internal_stop_event = None
    if stop_event is None:
        internal_stop_event = Event()
        stop_event = internal_stop_event
    
    # Determine device for transcription
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Create queues for communication
    result_queue = Queue()
    progress_queue = Queue()
    
    # Create and start the worker process
    worker = Process(
        target=_transcribe_worker,
        args=(audio_path, model_name, device, result_queue, progress_queue, stop_event, language),
        name=f"transcribe-{os.path.basename(audio_path)}"
    )
    
    # Register the process for cleanup
    _register_process(worker)
    
    try:
        worker.start()
        logger.info(f"Started transcription process (PID: {worker.pid}) for {audio_path}")
        
        start_time = time.time()
        result = None
        error = None
        completed = False
        
        # Monitor progress and check for completion
        while not completed and (timeout is None or time.time() - start_time < timeout):
            if worker.is_alive():
                # Check for progress updates
                try:
                    while not progress_queue.empty():
                        progress, status_text = progress_queue.get(block=False)
                        if progress_callback:
                            progress_callback(progress, status_text)
                except Exception as e:
                    logger.error(f"Error handling progress update: {e}")
                
                # Check for results
                try:
                    if not result_queue.empty():
                        result, error = result_queue.get(block=False)
                        completed = True
                except Exception as e:
                    logger.error(f"Error checking for results: {e}")
                
                # Small delay to prevent busy waiting
                time.sleep(0.1)
            else:
                # Process ended
                if not result_queue.empty():
                    try:
                        result, error = result_queue.get(block=False)
                        completed = True
                    except Exception as e:
                        logger.error(f"Error retrieving results after process ended: {e}")
                else:
                    error = "Transcription process terminated unexpectedly"
                    completed = True
        
        # Handle timeout
        if not completed:
            logger.warning(f"Transcription timeout after {timeout} seconds")
            stop_event.set()
            error = f"Transcription timeout after {timeout} seconds"
            
            # Give the process a moment to clean up after stop signal
            time.sleep(0.5)
            
            if worker.is_alive():
                logger.warning(f"Terminating transcription process after timeout")
                worker.terminate()
                worker.join(timeout=1.0)
                if worker.is_alive():
                    logger.warning(f"Forcibly killing transcription process")
                    worker.kill()
        
        # Unregister process from tracking
        _unregister_process(worker)
        
        return result, error
    
    except Exception as e:
        logger.error(f"Error in transcription controller: {e}", exc_info=True)
        
        # Ensure process is terminated
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=1.0)
        
        # Unregister process from tracking
        _unregister_process(worker)
        
        return None, f"Transcription failed: {e}"
