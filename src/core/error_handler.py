"""
Error handling module for YouTube Translator Pro.
Provides error reporting, logging, and crash handling functionality.
"""

import os
import sys
import traceback
import logging
import json
import platform
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from enum import Enum, auto

from PyQt6.QtCore import QObject, pyqtSignal

# Logger setup
logger = logging.getLogger(__name__)

class ErrorSeverity(Enum):
    """Enum representing error severity levels."""
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

class ErrorReporter(QObject):
    """
    Handles reporting and logging of application errors.
    Provides a unified interface for error reporting.
    """
    
    error_reported = pyqtSignal(str, str, object)  # message, details, severity
    
    def __init__(self, log_dir: Optional[str] = None, parent=None):
        """
        Initialize the error reporter.
        
        Args:
            log_dir: Directory where error logs are stored
            parent: Parent QObject
        """
        super().__init__(parent)
        
        # Set default log directory if not provided
        if log_dir is None:
            home_dir = os.path.expanduser("~")
            log_dir = os.path.join(home_dir, ".youtube_translator_pro", "logs")
            
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        self.log_dir = log_dir
        self.error_log_file = os.path.join(log_dir, "errors.json")
        
        logger.info(f"Error reporter initialized with log directory {log_dir}")
    
    def report_error(self, message: str, details: str = "", 
                     severity: ErrorSeverity = ErrorSeverity.ERROR,
                     log_to_file: bool = True) -> Dict[str, Any]:
        """
        Report an error.
        
        Args:
            message: Error message
            details: Detailed error information
            severity: Error severity level
            log_to_file: Whether to log the error to file
            
        Returns:
            Dictionary with error information
        """
        # Create error information
        error_info = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "details": details,
            "severity": severity.name,
            "thread": threading.current_thread().name
        }
        
        # Log to Python logger
        if severity == ErrorSeverity.INFO:
            logger.info(f"{message} - {details}")
        elif severity == ErrorSeverity.WARNING:
            logger.warning(f"{message} - {details}")
        elif severity == ErrorSeverity.ERROR:
            logger.error(f"{message} - {details}")
        elif severity == ErrorSeverity.CRITICAL:
            logger.critical(f"{message} - {details}")
        
        # Log to file if requested
        if log_to_file:
            self._log_error_to_file(error_info)
        
        # Emit signal
        self.error_reported.emit(message, details, severity)
        
        return error_info
    
    def _log_error_to_file(self, error_info: Dict[str, Any]) -> None:
        """
        Log error information to file.
        
        Args:
            error_info: Dictionary with error information
        """
        try:
            # Load existing errors
            errors = []
            if os.path.exists(self.error_log_file):
                try:
                    with open(self.error_log_file, 'r', encoding='utf-8') as f:
                        errors = json.load(f)
                except Exception as e:
                    logger.error(f"Failed to load error log file: {e}")
            
            # Add new error
            errors.append(error_info)
            
            # Keep only last 100 errors
            if len(errors) > 100:
                errors = errors[-100:]
                
            # Save to file
            with open(self.error_log_file, 'w', encoding='utf-8') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to log error to file: {e}")
    
    def get_error_log(self, max_errors: int = 100) -> List[Dict[str, Any]]:
        """
        Get the error log.
        
        Args:
            max_errors: Maximum number of errors to return
            
        Returns:
            List of dictionaries with error information
        """
        if not os.path.exists(self.error_log_file):
            return []
            
        try:
            with open(self.error_log_file, 'r', encoding='utf-8') as f:
                errors = json.load(f)
                
            # Return the last max_errors
            return errors[-max_errors:]
        except Exception as e:
            logger.error(f"Failed to get error log: {e}")
            return []
    
    def clear_error_log(self) -> bool:
        """
        Clear the error log.
        
        Returns:
            True if the error log was cleared successfully, False otherwise
        """
        if not os.path.exists(self.error_log_file):
            return True
            
        try:
            os.remove(self.error_log_file)
            logger.info("Error log cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear error log: {e}")
            return False

class CrashHandler(QObject):
    """
    Handles application crashes.
    Provides crash reporting and recovery functionality.
    """
    
    crash_detected = pyqtSignal(dict)
    
    def __init__(self, session_manager=None, crash_dir: Optional[str] = None, parent=None):
        """
        Initialize the crash handler.
        
        Args:
            session_manager: Session manager instance
            crash_dir: Directory where crash reports are stored
            parent: Parent QObject
        """
        super().__init__(parent)
        
        self.session_manager = session_manager
        
        # Set default crash directory if not provided
        if crash_dir is None:
            home_dir = os.path.expanduser("~")
            crash_dir = os.path.join(home_dir, ".youtube_translator_pro", "crashes")
            
        # Create crash directory if it doesn't exist
        os.makedirs(crash_dir, exist_ok=True)
        
        self.crash_dir = crash_dir
        
        logger.info(f"Crash handler initialized with crash directory {crash_dir}")
    
    def handle_exception(self, exc_type, exc_value, exc_traceback) -> None:
        """
        Handle uncaught exception.
        
        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Don't handle keyboard interrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Log the exception
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        
        # Get exception details
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Create crash report
        crash_report = {
            "timestamp": datetime.now().isoformat(),
            "exception_type": exc_type.__name__,
            "exception_value": str(exc_value),
            "traceback": tb_str,
            "system_info": {
                "platform": platform.platform(),
                "python_version": platform.python_version(),
                "system": platform.system(),
                "release": platform.release(),
                "version": platform.version(),
                "processor": platform.processor()
            }
        }
        
        # Save crash report
        self._save_crash_report(crash_report)
        
        # Emit signal
        self.crash_detected.emit(crash_report)
        
    def _save_crash_report(self, crash_report: Dict[str, Any]) -> None:
        """
        Save crash report to file.
        
        Args:
            crash_report: Dictionary with crash information
        """
        try:
            # Generate crash report filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            crash_file = os.path.join(self.crash_dir, f"crash_{timestamp}.json")
            
            # Save to file
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(crash_report, f, indent=2)
                
            logger.info(f"Crash report saved to {crash_file}")
        except Exception as e:
            logger.error(f"Failed to save crash report: {e}")
    
    def get_crash_reports(self, max_reports: int = 10) -> List[Dict[str, Any]]:
        """
        Get the crash reports.
        
        Args:
            max_reports: Maximum number of reports to return
            
        Returns:
            List of dictionaries with crash information
        """
        reports = []
        
        try:
            # Get crash files
            crash_files = [os.path.join(self.crash_dir, f) for f in os.listdir(self.crash_dir) 
                          if f.startswith("crash_") and f.endswith(".json")]
            
            # Sort by modification time (newest first)
            crash_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Limit to max_reports
            crash_files = crash_files[:max_reports]
            
            # Load crash reports
            for file_path in crash_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        report = json.load(f)
                        reports.append(report)
                except Exception as e:
                    logger.error(f"Failed to load crash report {file_path}: {e}")
        except Exception as e:
            logger.error(f"Failed to get crash reports: {e}")
            
        return reports
    
    def clear_crash_reports(self) -> bool:
        """
        Clear all crash reports.
        
        Returns:
            True if crash reports were cleared successfully, False otherwise
        """
        try:
            # Get crash files
            crash_files = [os.path.join(self.crash_dir, f) for f in os.listdir(self.crash_dir) 
                          if f.startswith("crash_") and f.endswith(".json")]
            
            # Delete each file
            for file_path in crash_files:
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Failed to delete crash report {file_path}: {e}")
                    
            logger.info(f"Cleared {len(crash_files)} crash reports")
            return True
        except Exception as e:
            logger.error(f"Failed to clear crash reports: {e}")
            return False
