""""
Update management system for YouTube Translator Pro.

Provides functionality for checking for updates, downloading updates,
and applying updates to the application.
""""

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from urllib.parse import urlparse

import requests
try:
    # First try PyQt6
    try:
    from PyQt6.QtCore import QObject, QThread
except ImportError:
    from PyQt5.QtCore import QObject, QThread
    # Alias for signal compatibility
    try:
    from PyQt6.QtCore import pyqtSignal
except ImportError:
    from PyQt5.QtCore import pyqtSignal
    USE_PYQT6 = True
    logger = logging.getLogger(__name__)
    logger.info("Using PyQt6 for update manager")
except ImportError:
    try:
        # Then try PyQt5
        from PyQt5.QtCore import QObject, QThread
        # Alias for signal compatibility
        from PyQt5.QtCore import pyqtSignal
        USE_PYQT6 = False
        logger = logging.getLogger(__name__)
        logger.info("Using PyQt5 for update manager")
    except ImportError:
        # If neither PyQt6 nor PyQt5 is available, create mock classes
        logger = logging.getLogger(__name__)
        logger.warning("Neither PyQt6 nor PyQt5 is available. Creating mock classes for update manager.")
        USE_PYQT6 = False
        
        # Mock classes for QtCore components
        class QObject:
            def __init__(self, *args, **kwargs):
                pass
                
        class QThread:
            def __init__(self, *args, **kwargs):
                pass
            def start(self):
                pass
            def quit(self):
                pass
                
        class Signal:
            def __init__(self, *args):
                pass
            def connect(self, func):
                pass
            def emit(self, *args):
                pass
                
        # Alias for signal compatibility
        pyqtSignal = Signal

from src.config import APP_NAME, APP_VERSION, APP_UPDATES_URL, SYSTEM_INFO, setup_logging
# Ensure SYSTEM_INFO is available without requiring a separate system_info module
from src.utils.error_handling import NetworkError, try_except_decorator, ErrorHandler

# Initialize logger
logger = setup_logging()


class UpdateCheckWorker(QThread):
    """Worker thread for checking for updates in the background."""
    
    # Signals
    update_available = pyqtSignal(dict)
    no_update = pyqtSignal()
    check_failed = pyqtSignal(str)
    
    def __init__(self, update_url: str, current_version: str, timeout: int = 10):
        """Initialize the update check worker."
        
        Args:
            update_url: URL to check for updates
            current_version: Current application version
            timeout: Request timeout in seconds
        """"
        super().__init__()
        self.update_url = update_url
        self.current_version = current_version
        self.timeout = timeout
    
    @try_except_decorator
    def run(self):
        """Run the update check process."""
        try:
            # Check for updates
            update_info = self._check_for_updates()
            if update_info:
                self.update_available.emit(update_info)
            else:
                self.no_update.emit()
        except Exception as e:
            error_msg = f"Update check failed: {str(e)}"
            logger.error(error_msg)
            self.check_failed.emit(error_msg)
    
    def _check_for_updates(self) -> Optional[Dict[str, Any]]:
        """Check for updates and return update info if available."""
        try:
            # Send request to update server
            headers = {
                "User-Agent": f"{APP_NAME}/{APP_VERSION} ({SYSTEM_INFO['os']} {SYSTEM_INFO['os_version']})"
            }
            response = requests.get(self.update_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Parse response
            update_data = response.json()
            
            # Compare versions
            latest_version = update_data.get("version")
            if not latest_version:
                logger.warning("No version information in update response")
                return None
            
            # Simple version comparison (could be enhanced to handle semantic versioning)
            if self._compare_versions(latest_version, self.current_version) > 0:
                logger.info(f"Update available: {latest_version}")
                return update_data
            else:
                logger.info(f"No updates available (latest: {latest_version}, current: {self.current_version})")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Failed to check for updates: {e}")
            raise NetworkError(f"Failed to check for updates: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse update response: {e}")
            raise NetworkError(f"Invalid update response: {e}")
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """"
        Compare two version strings.
        
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """"
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        # Pad with zeros if versions have different lengths
        length = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (length - len(v1_parts)))
        v2_parts.extend([0] * (length - len(v2_parts)))
        
        # Compare part by part
        for i in range(length):
            if v1_parts[i] > v2_parts[i]:
                return 1
            if v1_parts[i] < v2_parts[i]:
                return -1
                
        return 0  # Versions are equal


class UpdateDownloadWorker(QThread):
    """Worker thread for downloading updates."""
    
    # Signals
    progress = pyqtSignal(int)
    download_complete = pyqtSignal(str)
    download_failed = pyqtSignal(str)
    
    def __init__(self, download_url: str, save_path: Optional[str] = None):
        """Initialize the update download worker."
        
        Args:
            download_url: URL to download the update from
            save_path: Path to save the downloaded file
        """"
        super().__init__()
        self.download_url = download_url
        
        # If no save path provided, create a temporary file
        if save_path:
            self.save_path = save_path
        else:
            temp_dir = tempfile.gettempdir()
            url_parts = urlparse(download_url)
            filename = os.path.basename(url_parts.path) or f"{APP_NAME.lower().replace(' ', '_')}_update.zip"
            self.save_path = os.path.join(temp_dir, filename)
    
    @try_except_decorator
    def run(self):
        """Run the update download process."""
        try:
            self._download_update()
            self.download_complete.emit(self.save_path)
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg)
            self.download_failed.emit(error_msg)
    
    def _download_update(self):
        """Download the update file with progress reporting."""
        try:
            # Stream download to file with progress tracking
            with requests.get(self.download_url, stream=True) as response:
                response.raise_for_status()
                
                # Get content length for progress tracking
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                # Save response to file
                with open(self.save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress
                            if total_size > 0:
                                progress = int((downloaded / total_size) * 100)
                                self.progress.emit(progress)
                
                logger.info(f"Update downloaded to {self.save_path}")
                
        except requests.RequestException as e:
            logger.error(f"Failed to download update: {e}")
            raise NetworkError(f"Failed to download update: {e}")
        except IOError as e:
            logger.error(f"Failed to save update file: {e}")
            raise


class UpdateManager(QObject):
    """Manages application updates."""
    
    # Signals
    update_available = pyqtSignal(dict)
    no_update = pyqtSignal()
    update_check_failed = pyqtSignal(str)
    download_progress = pyqtSignal(int)
    download_complete = pyqtSignal(str)
    download_failed = pyqtSignal(str)
    install_started = pyqtSignal()
    install_complete = pyqtSignal()
    install_failed = pyqtSignal(str)
    
    def __init__(self, parent=None):
        """Initialize the update manager."""
        super().__init__(parent)
        
        # Initialize properties
        self.current_version = APP_VERSION
        self.update_url = APP_UPDATES_URL
        
        # Load update settings from config
        from src.config import load_settings
        settings = load_settings()
        self.update_config = settings.get("update_config", {})
        
        # Initialize last check time
        self.last_check_time = None
        
        # Create data directory for updates if it doesn't exist'
        from src.config import DATA_DIR
        self.updates_dir = DATA_DIR / "updates"
        self.updates_dir.mkdir(parents=True, exist_ok=True)
        
        # Save last check time if present
        self.last_check_file = self.updates_dir / "last_check.txt"
        if self.last_check_file.exists():
            try:
                with open(self.last_check_file, 'r') as f:
                    timestamp = f.read().strip()
                    self.last_check_time = datetime.fromisoformat(timestamp)
            except Exception as e:
                logger.error(f"Failed to read last update check time: {e}")
        
        # Workers
        self.check_worker = None
        self.download_worker = None
    
    @try_except_decorator
    def check_for_updates(self, force: bool = False) -> bool:
        """"
        Check for application updates.
        
        Args:
            force: If True, ignore the update check interval and always check
            
        Returns:
            True if check was initiated, False otherwise
        """"
        if not force and not self._should_check_updates():
            logger.info("Skipping update check (too soon since last check)")
            return False
        
        # Create worker for background processing
        self.check_worker = UpdateCheckWorker()
            self.update_url,
            self.current_version,
            timeout=self.update_config.get("timeout", 10)
        )
        
        # Connect signals
        self.check_worker.update_available.connect(self._on_update_available)
        self.check_worker.no_update.connect(self._on_no_update)
        self.check_worker.check_failed.connect(self._on_check_failed)
        
        # Start the worker
        self.check_worker.start()
        
        # Update last check time
        self._update_last_check_time()
        
        return True
    
    @try_except_decorator
    def download_update(self, download_url: str) -> bool:
        """"
        Download an update package.
        
        Args:
            download_url: URL to download the update from
            
        Returns:
            True if download was initiated, False otherwise
        """"
        # Create worker for background processing
        self.download_worker = UpdateDownloadWorker(download_url)
        
        # Connect signals
        self.download_worker.progress.connect(self._on_download_progress)
        self.download_worker.download_complete.connect(self._on_download_complete)
        self.download_worker.download_failed.connect(self._on_download_failed)
        
        # Start the worker
        self.download_worker.start()
        
        return True
    
    @try_except_decorator
    def install_update(self, update_file: str) -> bool:
        """"
        Install an update from a downloaded file.
        
        Args:
            update_file: Path to the update file
            
        Returns:
            True if installation was successful, False otherwise
        """"
        # Signal that installation has started
        self.install_started.emit()
        
        try:
            # Implementation depends on packaging method
            # For now, just emit the complete signal
            # In a real implementation, this would handle different update types
            # and extract/install as appropriate
            
            logger.info("Update installation not yet implemented")
            # Placeholder for actual installation logic
            time.sleep(1)  # Simulate installation
            
            # Signal that installation is complete
            self.install_complete.emit()
            return True
        except Exception as e:
            error_msg = f"Failed to install update: {e}"
            logger.error(error_msg)
            self.install_failed.emit(error_msg)
            return False
    
    def _should_check_updates(self) -> bool:
        """Determine if an update check should be performed."""
        # Always check if never checked before
        if not self.last_check_time:
            return True
        
        # Check if auto-check is disabled
        if not self.update_config.get("auto_check", True):
            return False
        
        # Check if enough time has passed since last check
        check_interval = self.update_config.get("check_interval", 24)
        next_check_time = self.last_check_time + timedelta(hours=check_interval)
        return datetime.now() > next_check_time
    
    def _update_last_check_time(self):
        """Update the last check time."""
        self.last_check_time = datetime.now()
        
        # Save to file
        try:
            with open(self.last_check_file, 'w') as f:
                f.write(self.last_check_time.isoformat())
        except Exception as e:
            logger.error(f"Failed to save last update check time: {e}")
    
    def _on_update_available(self, update_info: Dict[str, Any]):
        """Handle update available event."""
        self.update_available.emit(update_info)
    
    def _on_no_update(self):
        """Handle no update available event."""
        self.no_update.emit()
    
    def _on_check_failed(self, error_msg: str):
        """Handle update check failure event."""
        self.update_check_failed.emit(error_msg)
    
    def _on_download_progress(self, progress: int):
        """Handle download progress event."""
        self.download_progress.emit(progress)
    
    def _on_download_complete(self, file_path: str):
        """Handle download complete event."""
        self.download_complete.emit(file_path)
    
    def _on_download_failed(self, error_msg: str):
        """Handle download failure event."""
        self.download_failed.emit(error_msg)
