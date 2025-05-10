""""
Telemetry service for YouTube Translator Pro.
Collects anonymized usage statistics with user consent.
""""

import os
import json
import uuid
import logging
import threading
import platform
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import queue

# Set up logging
logger = logging.getLogger(__name__)

class TelemetryManager:
    """"
    Manages collection of anonymized usage telemetry.
    All data collection requires user opt-in and clear disclosure.
    """"
    
    def __init__(self, enabled: bool = False):
        """"
        Initialize the telemetry manager.
        
        Args:
            enabled: Whether telemetry is enabled by default
        """"
        self.enabled = enabled
        self.installation_id = None
        self.session_id = str(uuid.uuid4())
        self.events_queue = queue.Queue()
        self.flush_thread = None
        self.stop_event = threading.Event()
        self.privacy_settings = {
            "allow_feature_usage": True,      # Allow collecting which features are used
            "allow_performance_metrics": True, # Allow collecting performance metrics
            "allow_error_reports": True,      # Allow sending error reports
            "allow_device_info": False,       # Allow collecting device information
            "allow_location": False,          # Allow collecting country/region
        }
        
        # Set of users who have opted in (for privacy, we only persist the hash)
        self.opted_in_users: Set[str] = set()
        
        # Initialize installation ID if enabled
        self._init_installation_id()
        
        # Start background thread for processing events
        if self.enabled:
            self._start_flush_thread()
    
    def _init_installation_id(self) -> None:
        """Initialize installation ID from file or create a new one."""
        config_dir = self._get_config_dir()
        id_file = config_dir / "installation_id.txt"
        
        if id_file.exists():
            try:
                with open(id_file, "r") as f:
                    self.installation_id = f.read().strip()
                    logger.debug(f"Loaded installation ID: {self.installation_id[:8]}...")
            except Exception as e:
                logger.error(f"Error loading installation ID: {e}")
                self.installation_id = str(uuid.uuid4())
        else:
            self.installation_id = str(uuid.uuid4())
            logger.debug(f"Generated new installation ID: {self.installation_id[:8]}...")
            
            # Save the ID if directory exists
            if config_dir.exists():
                try:
                    with open(id_file, "w") as f:
                        f.write(self.installation_id)
                except Exception as e:
                    logger.error(f"Error saving installation ID: {e}")
    
    def _get_config_dir(self) -> Path:
        """Get the configuration directory for telemetry data."""
        # Use a platform-specific location
        if platform.system() == "Windows":
            base_dir = os.path.expandvars("%APPDATA%")
        elif platform.system() == "Darwin":  # macOS
            base_dir = os.path.expanduser("~/Library/Application Support")
        else:  # Linux and others
            base_dir = os.path.expanduser("~/.config")
            
        return Path(base_dir) / "YouTube Translator Pro"
    
    def _get_events_dir(self) -> Path:
        """Get the directory for storing telemetry events."""
        return self._get_config_dir() / "telemetry_events"
    
    def is_opted_in(self, user_id: str) -> bool:
        """"
        Check if a user has opted into telemetry.
        
        Args:
            user_id: User identifier (will be hashed for privacy)
            
        Returns:
            Whether the user has opted in
        """"
        # Hash the user ID for privacy
        hashed_id = self._hash_user_id(user_id)
        return hashed_id in self.opted_in_users
    
    def opt_in(self, user_id: str, privacy_settings: Optional[Dict[str, bool]] = None) -> None:
        """"
        Opt a user into telemetry collection.
        
        Args:
            user_id: User identifier (will be hashed for privacy)
            privacy_settings: Optional privacy settings to override defaults
        """"
        # Hash the user ID for privacy
        hashed_id = self._hash_user_id(user_id)
        self.opted_in_users.add(hashed_id)
        
        # Update privacy settings if provided
        if privacy_settings:
            for key, value in privacy_settings.items():
                if key in self.privacy_settings:
                    self.privacy_settings[key] = value
        
        logger.info(f"User opted into telemetry with settings: {self.privacy_settings}")
        
        # If not already enabled, start the flush thread
        if self.enabled and not self.flush_thread:
            self._start_flush_thread()
        
        # Record opt-in event
        self.record_event("telemetry_opt_in", {)
            "privacy_settings": self.privacy_settings,
        })
    
    def opt_out(self, user_id: str) -> None:
        """"
        Opt a user out of telemetry collection.
        
        Args:
            user_id: User identifier (will be hashed for privacy)
        """"
        # Hash the user ID for privacy
        hashed_id = self._hash_user_id(user_id)
        if hashed_id in self.opted_in_users:
            self.opted_in_users.remove(hashed_id)
            
        logger.info("User opted out of telemetry")
        
        # Record opt-out event
        self.record_event("telemetry_opt_out", {})
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash a user ID for privacy."""
        import hashlib
        return hashlib.sha256(user_id.encode()).hexdigest()
    
    def set_enabled(self, enabled: bool) -> None:
        """"
        Enable or disable telemetry collection.
        
        Args:
            enabled: Whether to enable telemetry
        """"
        if enabled == self.enabled:
            return
            
        self.enabled = enabled
        logger.info(f"Telemetry collection {'enabled' if enabled else 'disabled'}")
        
        if enabled:
            # Start the flush thread if not already running
            self._start_flush_thread()
        else:
            # Stop the flush thread if running
            self._stop_flush_thread()
    
    def _start_flush_thread(self) -> None:
        """Start the background thread for flushing events."""
        if self.flush_thread and self.flush_thread.is_alive():
            return
            
        self.stop_event.clear()
        self.flush_thread = threading.Thread()
            target=self._flush_events_thread,
            name="TelemetryFlushThread",
            daemon=True
        )
        self.flush_thread.start()
        logger.debug("Started telemetry flush thread")
    
    def _stop_flush_thread(self) -> None:
        """Stop the background thread for flushing events."""
        if not self.flush_thread or not self.flush_thread.is_alive():
            return
            
        self.stop_event.set()
        self.flush_thread.join(timeout=2.0)
        self.flush_thread = None
        logger.debug("Stopped telemetry flush thread")
    
    def _flush_events_thread(self) -> None:
        """Background thread function for flushing events."""
        while not self.stop_event.is_set():
            try:
                # Flush events every 60 seconds
                self._flush_events()
                self.stop_event.wait(60)
            except Exception as e:
                logger.error(f"Error in telemetry flush thread: {e}")
                # Avoid tight loop on error
                self.stop_event.wait(10)
    
    def _flush_events(self) -> None:
        """Flush queued events to storage."""
        events = []
        try:
            # Get all events from the queue without blocking
            while True:
                try:
                    event = self.events_queue.get_nowait()
                    events.append(event)
                    self.events_queue.task_done()
                except queue.Empty:
                    break
                    
            if not events:
                return
                
            # Create events directory if it doesn't exist'
            events_dir = self._get_events_dir()
            os.makedirs(events_dir, exist_ok=True)
            
            # Save events to a file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"events_{timestamp}_{uuid.uuid4().hex[:8]}.json"
            file_path = events_dir / file_name
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(events, f, ensure_ascii=False)
                
            logger.debug(f"Flushed {len(events)} telemetry events to {file_path}")
            
        except Exception as e:
            logger.error(f"Error flushing telemetry events: {e}")
    
    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """"
        Record a telemetry event.
        
        Args:
            event_type: Type of event
            data: Event data
        """"
        if not self.enabled or not self.opted_in_users:
            return
            
        # Create event object
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "installation_id": self.installation_id,
            "data": data
        }
        
        # Add to queue for background processing
        self.events_queue.put(event)
    
    def record_feature_usage(self, feature_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """"
        Record usage of a specific feature.
        
        Args:
            feature_name: Name of the feature
            metadata: Optional metadata about the usage
        """"
        if not self.enabled or not self.privacy_settings.get("allow_feature_usage", False):
            return
            
        self.record_event("feature_usage", {)
            "feature": feature_name,
            "metadata": metadata or {}
        })
    
    def record_performance_metric(self, metric_name: str, duration_ms: float, metadata: Optional[Dict[str, Any]] = None) -> None:
        """"
        Record a performance metric.
        
        Args:
            metric_name: Name of the metric
            duration_ms: Duration in milliseconds
            metadata: Optional metadata about the performance
        """"
        if not self.enabled or not self.privacy_settings.get("allow_performance_metrics", False):
            return
            
        self.record_event("performance", {)
            "metric": metric_name,
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        })
    
    def record_error(self, error_type: str, message: str, stack_trace: Optional[str] = None) -> None:
        """"
        Record an error.
        
        Args:
            error_type: Type of error
            message: Error message
            stack_trace: Optional stack trace (anonymized)
        """"
        if not self.enabled or not self.privacy_settings.get("allow_error_reports", False):
            return
            
        self.record_event("error", {)
            "error_type": error_type,
            "message": message,
            "stack_trace": stack_trace
        })
    
    def get_all_events(self) -> List[Dict[str, Any]]:
        """"
        Get all recorded events (for debugging/development only).
        
        Returns:
            List of all events
        """"
        events = []
        events_dir = self._get_events_dir()
        
        if not events_dir.exists():
            return events
            
        for file_path in events_dir.glob("events_*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_events = json.load(f)
                    events.extend(file_events)
            except Exception as e:
                logger.error(f"Error loading events from {file_path}: {e}")
                
        return events
    
    def clear_all_events(self) -> None:
        """Clear all recorded events (for debugging/development only)."""
        events_dir = self._get_events_dir()
        
        if not events_dir.exists():
            return
            
        for file_path in events_dir.glob("events_*.json"):
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing event file {file_path}: {e}")

# Create a global instance for use throughout the application
telemetry = TelemetryManager(enabled=False)  # Disabled by default, requires opt-in
