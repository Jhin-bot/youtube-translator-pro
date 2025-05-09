"""
Error handling and exception management framework for YouTube Translator Pro.

This module provides centralized error handling, including:
- Custom exception classes
- Error logging and reporting
- Crash recovery mechanisms
- User-friendly error messages
"""

import sys
import traceback
import logging
from typing import Optional, Dict, Any, Callable, Type, Union
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    try:
    from PyQt6.QtWidgets import QMessageBox, QApplication
except ImportError:
    from PyQt5.QtWidgets import QMessageBox, QApplication
except ImportError:
    from PyQt5.QtWidgets import QMessageBox, QApplication

from src.config import APP_NAME, setup_logging, LOG_DIR

# Initialize logger
logger = setup_logging()

@dataclass
class ErrorReport:
    """Data class for structured error reports."""
    
    error_type: str
    error_message: str
    traceback: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    handled: bool = False
    critical: bool = False
    user_notified: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error report to dictionary for serialization."""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "traceback": self.traceback,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "handled": self.handled,
            "critical": self.critical,
            "user_notified": self.user_notified
        }
    
    def log_error(self) -> None:
        """Log the error to the application log."""
        if self.critical:
            logger.critical(f"CRITICAL ERROR: {self.error_type}: {self.error_message}")
        else:
            logger.error(f"ERROR: {self.error_type}: {self.error_message}")
        
        logger.debug(f"Error context: {self.context}")
        logger.debug(f"Traceback: {self.traceback}")


class ApplicationError(Exception):
    """Base exception class for application-specific errors."""
    
    def __init__(self, message: str, context: Dict[str, Any] = None):
        self.message = message
        self.context = context or {}
        super().__init__(message)


class ConfigurationError(ApplicationError):
    """Error raised for configuration issues."""
    pass


class NetworkError(ApplicationError):
    """Error raised for network connectivity issues."""
    pass


class YoutubeError(ApplicationError):
    """Error raised for YouTube API or download issues."""
    pass


class TranscriptionError(ApplicationError):
    """Error raised for transcription process issues."""
    pass


class TranslationError(ApplicationError):
    """Error raised for translation process issues."""
    pass


class ResourceError(ApplicationError):
    """Error raised for resource access or availability issues."""
    pass


class ErrorHandler:
    """Centralized error handler for the application."""
    
    _instance = None
    _error_handlers: Dict[Type[Exception], Callable] = {}
    _last_error: Optional[ErrorReport] = None
    _error_count: int = 0
    
    def __new__(cls):
        """Implement singleton pattern for error handler."""
        if cls._instance is None:
            cls._instance = super(ErrorHandler, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the error handler."""
        # Register default handlers for known exception types
        self.register_handler(ConfigurationError, self._handle_configuration_error)
        self.register_handler(NetworkError, self._handle_network_error)
        self.register_handler(YoutubeError, self._handle_youtube_error)
        self.register_handler(TranscriptionError, self._handle_transcription_error)
        self.register_handler(TranslationError, self._handle_translation_error)
        self.register_handler(ResourceError, self._handle_resource_error)
        
        # Set up crash report directory
        self.crash_dir = LOG_DIR / "crash_reports"
        self.crash_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def register_handler(cls, exception_type: Type[Exception], handler: Callable) -> None:
        """
        Register a custom handler for a specific exception type.
        
        Args:
            exception_type: The exception class to handle
            handler: Callable that will handle the exception
        """
        cls._error_handlers[exception_type] = handler
    
    def handle_exception(self, 
                        exception: Exception, 
                        context: Dict[str, Any] = None, 
                        critical: bool = False,
                        notify_user: bool = True) -> ErrorReport:
        """
        Handle an exception according to its type and severity.
        
        Args:
            exception: The exception to handle
            context: Additional context information about when/where the error occurred
            critical: Whether this is a critical error that may impact application stability
            notify_user: Whether to show a notification to the user
            
        Returns:
            ErrorReport object with details about the handled error
        """
        context = context or {}
        error_type = type(exception).__name__
        
        # Generate traceback
        tb = traceback.format_exc()
        
        # Create error report
        error_report = ErrorReport(
            error_type=error_type,
            error_message=str(exception),
            traceback=tb,
            context=context,
            critical=critical,
            user_notified=False
        )
        
        # Log the error
        error_report.log_error()
        
        # Save crash report for critical errors
        if critical:
            self._save_crash_report(error_report)
        
        # Find and execute appropriate handler
        for exc_type, handler in self._error_handlers.items():
            if isinstance(exception, exc_type):
                try:
                    handler(exception, error_report)
                    error_report.handled = True
                except Exception as handler_error:
                    logger.error(f"Error in exception handler: {handler_error}")
                break
        
        # Default handling if no specific handler was found or succeeded
        if not error_report.handled:
            self._default_handler(exception, error_report)
            error_report.handled = True
        
        # Notify user if requested and not already notified
        if notify_user and not error_report.user_notified:
            self._notify_user(error_report)
            error_report.user_notified = True
        
        # Update internal state
        self._last_error = error_report
        self._error_count += 1
        
        return error_report
    
    def _save_crash_report(self, error_report: ErrorReport) -> None:
        """Save a crash report to disk for later analysis."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = self.crash_dir / f"crash_{timestamp}.log"
        
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                f.write(f"=== {APP_NAME} Crash Report ===\n")
                f.write(f"Timestamp: {error_report.timestamp}\n")
                f.write(f"Error Type: {error_report.error_type}\n")
                f.write(f"Error Message: {error_report.error_message}\n\n")
                f.write("Context:\n")
                for key, value in error_report.context.items():
                    f.write(f"  {key}: {value}\n")
                f.write("\nTraceback:\n")
                f.write(error_report.traceback)
                
            logger.info(f"Crash report saved to {crash_file}")
        except Exception as e:
            logger.error(f"Failed to save crash report: {e}")
    
    def _notify_user(self, error_report: ErrorReport) -> None:
        """Show an error message to the user."""
        try:
            app = QApplication.instance()
            if not app:
                # Can't show GUI notification without QApplication
                return
                
            msg_box = QMessageBox()
            
            if error_report.critical:
                msg_box.setIcon(QMessageBox.Icon.Critical)
                msg_box.setWindowTitle(f"{APP_NAME} - Critical Error")
                msg_box.setText("A critical error has occurred:")
            else:
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle(f"{APP_NAME} - Error")
                msg_box.setText("An error has occurred:")
                
            msg_box.setInformativeText(str(error_report.error_message))
            msg_box.setDetailedText(error_report.traceback)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Execute asynchronously to avoid blocking the GUI thread
            msg_box.open()
            
        except Exception as e:
            logger.error(f"Failed to show error notification: {e}")
    
    def _default_handler(self, exception: Exception, error_report: ErrorReport) -> None:
        """Default handler for unhandled exception types."""
        logger.error(f"Unhandled exception: {exception}")
    
    def _handle_configuration_error(self, exception: ConfigurationError, error_report: ErrorReport) -> None:
        """Handle configuration errors."""
        logger.error(f"Configuration error: {exception}")
        # Attempt to reset to default configuration
        from src.config import save_settings, DEFAULT_SETTINGS
        save_settings(DEFAULT_SETTINGS)
    
    def _handle_network_error(self, exception: NetworkError, error_report: ErrorReport) -> None:
        """Handle network connectivity errors."""
        logger.error(f"Network error: {exception}")
        # Could implement automatic retry or offline mode switch
    
    def _handle_youtube_error(self, exception: YoutubeError, error_report: ErrorReport) -> None:
        """Handle YouTube API or download errors."""
        logger.error(f"YouTube error: {exception}")
        # Could implement alternative download methods or retry logic
    
    def _handle_transcription_error(self, exception: TranscriptionError, error_report: ErrorReport) -> None:
        """Handle transcription process errors."""
        logger.error(f"Transcription error: {exception}")
        # Could implement fallback to different model or retry with different settings
    
    def _handle_translation_error(self, exception: TranslationError, error_report: ErrorReport) -> None:
        """Handle translation process errors."""
        logger.error(f"Translation error: {exception}")
        # Could implement fallback to different translation engine
    
    def _handle_resource_error(self, exception: ResourceError, error_report: ErrorReport) -> None:
        """Handle resource access errors."""
        logger.error(f"Resource error: {exception}")
        # Could implement resource cleanup or alternative resource finding


# Global exception handler to catch unhandled exceptions
def global_exception_handler(exctype, value, tb):
    """Global exception handler to catch and log uncaught exceptions."""
    error_handler = ErrorHandler()
    
    # Create context with basic info
    context = {
        "uncaught": True,
        "thread": "main"
    }
    
    # Format traceback
    tb_str = ''.join(traceback.format_exception(exctype, value, tb))
    
    # Create synthetic exception
    error_report = ErrorReport(
        error_type=exctype.__name__,
        error_message=str(value),
        traceback=tb_str,
        context=context,
        critical=True
    )
    
    # Log and save crash report
    error_report.log_error()
    error_handler._save_crash_report(error_report)
    
    # Show error to user
    error_handler._notify_user(error_report)
    
    # Call the original exception hook
    sys.__excepthook__(exctype, value, tb)


# Install the global exception handler
sys.excepthook = global_exception_handler


def try_except_decorator(func):
    """
    Decorator to wrap functions in try-except blocks with proper error handling.
    
    Example usage:
    
    @try_except_decorator
    def some_function(arg1, arg2):
        # function implementation
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            handler = ErrorHandler()
            context = {
                "function": func.__name__,
                "module": func.__module__,
                "args": str(args),
                "kwargs": str(kwargs)
            }
            handler.handle_exception(e, context=context)
            # Re-raise to let calling code decide how to proceed
            raise
    
    return wrapper
