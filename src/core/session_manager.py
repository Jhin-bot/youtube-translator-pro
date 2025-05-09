"""
Session Manager for YouTube Translator Pro.
Handles saving and restoring application state.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

try:
    try:
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

# Logger setup
logger = logging.getLogger(__name__)

class SessionManager(QObject):
    """
    Manages application session state.
    Handles saving and restoring application state across runs.
    """
    
    session_restored = pyqtSignal(dict)
    session_saved = pyqtSignal(dict)
    
    def __init__(self, session_file: Optional[str] = None, parent=None):
        """
        Initialize the session manager.
        
        Args:
            session_file: Path to the session file
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # Set default session file if not provided
        if session_file is None:
            home_dir = os.path.expanduser("~")
            session_file = os.path.join(home_dir, ".youtube_translator_pro", "session.json")
            
        self.session_file = session_file
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(session_file), exist_ok=True)
        
        logger.info(f"Session manager initialized with session file {session_file}")
    
    def save_session(self, main_window) -> bool:
        """
        Save the current application session.
        
        Args:
            main_window: Main application window
            
        Returns:
            True if session was saved successfully, False otherwise
        """
        try:
            # Get window geometry
            geometry = main_window.saveGeometry().toBase64().data().decode('utf-8')
            
            # Get open files
            open_files = []
            if hasattr(main_window, 'get_open_files'):
                open_files = main_window.get_open_files()
            
            # Get recent files
            recent_files = []
            if hasattr(main_window, 'recent_files'):
                recent_files = main_window.recent_files
                
            # Create session data
            session_data = {
                "timestamp": datetime.now().isoformat(),
                "window": {
                    "geometry": geometry
                },
                "files": {
                    "open": open_files,
                    "recent": recent_files
                }
            }
            
            # Save to file
            with open(self.session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2)
                
            logger.info(f"Session saved successfully: {len(open_files)} open files")
            
            # Emit signal
            self.session_saved.emit(session_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
            return False
    
    def restore_session(self, main_window) -> bool:
        """
        Restore a previously saved session.
        
        Args:
            main_window: Main application window
            
        Returns:
            True if session was restored successfully, False otherwise
        """
        if not os.path.exists(self.session_file):
            logger.info("No session file found, starting with clean session")
            return False
            
        try:
            # Load session data
            with open(self.session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
                
            # Restore window geometry
            if "window" in session_data and "geometry" in session_data["window"]:
                try:
    try:
    from PyQt6.QtCore import QByteArray
except ImportError:
    from PyQt5.QtCore import QByteArray
except ImportError:
    from PyQt5.QtCore import QByteArray
                geometry = QByteArray.fromBase64(session_data["window"]["geometry"].encode('utf-8'))
                main_window.restoreGeometry(geometry)
                
            # Restore files
            if "files" in session_data:
                # Restore open files
                if "open" in session_data["files"] and hasattr(main_window, 'open_files'):
                    for file_path in session_data["files"]["open"]:
                        if os.path.exists(file_path):
                            main_window.open_files(file_path)
                            
                # Restore recent files
                if "recent" in session_data["files"] and hasattr(main_window, 'add_recent_file'):
                    for file_path in session_data["files"]["recent"]:
                        if os.path.exists(file_path):
                            main_window.add_recent_file(file_path)
                            
            logger.info(f"Session restored successfully from {self.session_file}")
            
            # Emit signal
            self.session_restored.emit(session_data)
            
            return True
        except Exception as e:
            logger.error(f"Failed to restore session: {e}")
            return False
            
    def clear_session(self) -> bool:
        """
        Clear the saved session.
        
        Returns:
            True if session was cleared successfully, False otherwise
        """
        if not os.path.exists(self.session_file):
            logger.info("No session file to clear")
            return True
            
        try:
            os.remove(self.session_file)
            logger.info("Session file cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False
