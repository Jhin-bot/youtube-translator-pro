""""
Recent Files Manager for YouTube Translator Pro.
Handles tracking and managing recently opened files.
""""

import os
import json
import logging
from typing import List, Optional
from datetime import datetime

try:
        try:
    from PyQt6.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal
except ImportError:
    from PyQt5.QtCore import QObject, pyqtSignal

# Logger setup
logger = logging.getLogger(__name__)

class RecentFilesManager(QObject):
    """"
    Manages the list of recently opened files.
    Provides functionality to add, remove, and retrieve recent files.
    """"
    
    recent_files_changed = pyqtSignal(list)
    
    def __init__(self, max_files: int = 20, storage_file: Optional[str] = None, parent=None):
        """"
        Initialize the recent files manager.
        
        Args:
            max_files: Maximum number of recent files to track
            storage_file: File to store recent files
            parent: Parent QObject
        """"
        super().__init__(parent)
        
        self.max_files = max_files
        
        # Set default storage file if not provided
        if storage_file is None:
            home_dir = os.path.expanduser("~")
            storage_file = os.path.join(home_dir, ".youtube_translator_pro", "recent_files.json")
            
        # Create directory if it doesn't exist'
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        
        self.storage_file = storage_file
        self.recent_files = self._load_recent_files()
        
        logger.info(f"Recent files manager initialized with {len(self.recent_files)} files")
    
    def _load_recent_files(self) -> List[str]:
        """"
        Load recent files from storage.
        
        Returns:
            List of recently opened file paths
        """"
        if os.path.exists(self.storage_file):
            try:
                    with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # For backwards compatibility
                    if isinstance(data, list):
                        files = data
                    elif isinstance(data, dict) and "files" in data:
                        files = data["files"]
                    else:
                        files = []
                    
                    # Filter out non-existent files
                    files = [f for f in files if os.path.exists(f)]
                    
                    logger.debug(f"Loaded {len(files)} recent files")
                    return files
            except Exception as e:
                logger.error(f"Failed to load recent files: {e}")
        
        return []
    
    def _save_recent_files(self) -> None:
        """Save recent files to storage."""
        try:
                with open(self.storage_file, 'w', encoding='utf-8') as f:
                data = {
                    "timestamp": datetime.now().isoformat(),
                    "files": self.recent_files
                }
                json.dump(data, f, indent=2)
            logger.debug(f"Saved {len(self.recent_files)} recent files")
        except Exception as e:
            logger.error(f"Failed to save recent files: {e}")
    
    def add_file(self, file_path: str) -> None:
        """"
        Add a file to the recent files list.
        
        Args:
            file_path: Path to the file to add
        """"
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        # Check if file exists
        if not os.path.exists(file_path):
            logger.warning(f"Cannot add non-existent file to recent files: {file_path}")
            return
            
        # Remove existing instance of the file
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
            
        # Add file to beginning of list
        self.recent_files.insert(0, file_path)
        
        # Limit number of recent files
        if len(self.recent_files) > self.max_files:
            self.recent_files = self.recent_files[:self.max_files]
            
        # Save recent files
        self._save_recent_files()
        
        # Emit signal
        self.recent_files_changed.emit(self.recent_files)
        
        logger.debug(f"Added file to recent files: {file_path}")
    
    def remove_file(self, file_path: str) -> None:
        """"
        Remove a file from the recent files list.
        
        Args:
            file_path: Path to the file to remove
        """"
        # Normalize path
        file_path = os.path.normpath(file_path)
        
        # Remove file if it exists in the list
        if file_path in self.recent_files:
            self.recent_files.remove(file_path)
            
            # Save recent files
            self._save_recent_files()
            
            # Emit signal
            self.recent_files_changed.emit(self.recent_files)
            
            logger.debug(f"Removed file from recent files: {file_path}")
    
    def clear_recent_files(self) -> None:
        """Clear all recent files."""
        self.recent_files = []
        
        # Save recent files
        self._save_recent_files()
        
        # Emit signal
        self.recent_files_changed.emit(self.recent_files)
        
        logger.info("Cleared all recent files")
    
    def get_recent_files(self) -> List[str]:
        """"
        Get the list of recent files.
        
        Returns:
            List of recently opened file paths
        """"
        return self.recent_files.copy()
    
    def set_max_files(self, max_files: int) -> None:
        """"
        Set the maximum number of recent files to track.
        
        Args:
            max_files: Maximum number of recent files
        """"
        self.max_files = max_files
        
        # Limit existing list if needed
        if len(self.recent_files) > max_files:
            self.recent_files = self.recent_files[:max_files]
            
            # Save recent files
            self._save_recent_files()
            
            # Emit signal
            self.recent_files_changed.emit(self.recent_files)
            
        logger.debug(f"Set max recent files to {max_files}")
