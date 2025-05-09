"""
Task list widget for YouTube Translator Pro.
Displays the list of tasks, their status, and allows management.
"""

import logging
from typing import Dict, Any, List, Optional
from enum import Enum, auto

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QMenu, QAbstractItemView
)
from PyQt6.QtGui import QAction, QColor, QIcon

from src.ui.styles import StyleManager

# Logger setup
logger = logging.getLogger(__name__)

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

class TaskListWidget(QWidget):
    """Widget for displaying and managing the list of tasks."""
    
    def __init__(self, app_manager, parent=None):
        """
        Initialize the task list widget.
        
        Args:
            app_manager: Reference to the ApplicationManager
            parent: The parent widget
        """
        super().__init__(parent)
        self.app_manager = app_manager
        self.style_manager = StyleManager()
        self.tasks = {}  # Store task data by URL
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Set up the user interface."""
        # Create layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Create group box
        group_box = QGroupBox("Tasks")
        group_layout = QVBoxLayout(group_box)
        
        # Create table widget
        self.task_table = QTableWidget(0, 5)  # 0 rows, 5 columns initially
        self.task_table.setHorizontalHeaderLabels(["Video", "Status", "Progress", "Action", "Output"])
        self.task_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.task_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.task_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.task_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.task_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.task_table.verticalHeader().setVisible(False)
        self.task_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.task_table.customContextMenuRequested.connect(self._show_context_menu)
        
        group_layout.addWidget(self.task_table)
        
        # Summary label
        self.summary_label = QLabel("No tasks")
        group_layout.addWidget(self.summary_label)
        
        # Add group to main layout
        main_layout.addWidget(group_box)
        
        # Apply styles
        self.style_manager.apply_styles(self)
    
    @pyqtSlot(dict)
    def update_task(self, task_data: Dict[str, Any]):
        """
        Update a task in the task list.
        
        Args:
            task_data: Dictionary containing task data
        """
        url = task_data.get("url")
        if not url:
            return
        
        # Store or update task data
        self.tasks[url] = task_data
        
        # Check if task already exists in table
        row = self._find_task_row(url)
        if row == -1:
            # Add new task
            row = self.task_table.rowCount()
            self.task_table.insertRow(row)
        
        # Update table row
        self._update_task_row(row, task_data)
        
        # Update summary
        self._update_summary()
    
    def remove_task(self, url: str):
        """
        Remove a task from the task list.
        
        Args:
            url: URL of the task to remove
        """
        row = self._find_task_row(url)
        if row != -1:
            self.task_table.removeRow(row)
            if url in self.tasks:
                del self.tasks[url]
            
            # Update summary
            self._update_summary()
    
    def _find_task_row(self, url: str) -> int:
        """
        Find the row index for a task URL.
        
        Args:
            url: The URL to find
            
        Returns:
            The row index, or -1 if not found
        """
        for row in range(self.task_table.rowCount()):
            item = self.task_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == url:
                return row
        return -1
    
    def _update_task_row(self, row: int, task_data: Dict[str, Any]):
        """
        Update a task row with new data.
        
        Args:
            row: The row index to update
            task_data: The task data
        """
        url = task_data.get("url", "")
        title = task_data.get("title", "Unknown video")
        status = task_data.get("status", "PENDING")
        progress = task_data.get("progress", 0.0)
        output_files = task_data.get("output_files", [])
        
        # Format progress as percentage
        progress_text = f"{int(progress * 100)}%"
        
        # Video title/URL
        title_item = QTableWidgetItem(title)
        title_item.setData(Qt.ItemDataRole.UserRole, url)
        title_item.setToolTip(url)
        self.task_table.setItem(row, 0, title_item)
        
        # Status
        status_item = QTableWidgetItem(status)
        self._style_status_item(status_item, status)
        self.task_table.setItem(row, 1, status_item)
        
        # Progress
        progress_item = QTableWidgetItem(progress_text)
        self.task_table.setItem(row, 2, progress_item)
        
        # Action button (cell widget)
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(2, 2, 2, 2)
        
        if status in ["FAILED", "CANCELLED"]:
            retry_button = QPushButton("Retry")
            retry_button.clicked.connect(lambda: self._retry_task(url))
            action_layout.addWidget(retry_button)
        elif status in ["PENDING", "RUNNING", "PAUSED", "RETRYING"]:
            cancel_button = QPushButton("Cancel")
            cancel_button.clicked.connect(lambda: self._cancel_task(url))
            action_layout.addWidget(cancel_button)
        else:
            # Completed, nothing to do
            placeholder = QLabel("")
            action_layout.addWidget(placeholder)
        
        self.task_table.setCellWidget(row, 3, action_widget)
        
        # Output button/link (cell widget)
        output_widget = QWidget()
        output_layout = QHBoxLayout(output_widget)
        output_layout.setContentsMargins(2, 2, 2, 2)
        
        if output_files and status == "COMPLETED":
            open_button = QPushButton("Open")
            open_button.clicked.connect(lambda: self._open_output(output_files[0]))
            output_layout.addWidget(open_button)
        else:
            placeholder = QLabel("")
            output_layout.addWidget(placeholder)
        
        self.task_table.setCellWidget(row, 4, output_widget)
    
    def _style_status_item(self, item: QTableWidgetItem, status: str):
        """
        Apply styling to a status item based on the status.
        
        Args:
            item: The QTableWidgetItem to style
            status: The status string
        """
        if status == "COMPLETED":
            item.setForeground(QColor(self.style_manager.colors["success"]))
        elif status == "FAILED":
            item.setForeground(QColor(self.style_manager.colors["error"]))
        elif status in ["CANCELLED", "SKIPPED"]:
            item.setForeground(QColor(self.style_manager.colors["warning"]))
        elif status == "RUNNING":
            item.setForeground(QColor(self.style_manager.colors["accent"]))
        elif status == "PAUSED":
            item.setForeground(QColor(self.style_manager.colors["warning"]))
    
    def _update_summary(self):
        """Update the task summary label."""
        total_tasks = len(self.tasks)
        completed = sum(1 for task in self.tasks.values() if task.get("status") == "COMPLETED")
        running = sum(1 for task in self.tasks.values() if task.get("status") in ["RUNNING", "VALIDATING", "DOWNLOADING", "CONVERTING", "TRANSCRIBING", "TRANSLATING", "EXPORTING"])
        failed = sum(1 for task in self.tasks.values() if task.get("status") == "FAILED")
        
        summary = f"Total: {total_tasks}"
        if completed > 0:
            summary += f" | Completed: {completed}"
        if running > 0:
            summary += f" | Running: {running}"
        if failed > 0:
            summary += f" | Failed: {failed}"
        
        self.summary_label.setText(summary)
    
    def _show_context_menu(self, position):
        """
        Show context menu for a task.
        
        Args:
            position: The position where the context menu should appear
        """
        row = self.task_table.rowAt(position.y())
        if row == -1:
            return
        
        item = self.task_table.item(row, 0)
        if not item:
            return
        
        url = item.data(Qt.ItemDataRole.UserRole)
        if not url or url not in self.tasks:
            return
        
        task_data = self.tasks[url]
        status = task_data.get("status", "PENDING")
        
        # Create context menu
        menu = QMenu(self)
        
        # Add actions based on task status
        if status in ["FAILED", "CANCELLED"]:
            retry_action = QAction("Retry", self)
            retry_action.triggered.connect(lambda: self._retry_task(url))
            menu.addAction(retry_action)
        
        if status in ["PENDING", "RUNNING", "PAUSED", "RETRYING"]:
            cancel_action = QAction("Cancel", self)
            cancel_action.triggered.connect(lambda: self._cancel_task(url))
            menu.addAction(cancel_action)
        
        # Always allow removal
        menu.addSeparator()
        remove_action = QAction("Remove from list", self)
        remove_action.triggered.connect(lambda: self._remove_task(url))
        menu.addAction(remove_action)
        
        # Add output options if available
        output_files = task_data.get("output_files", [])
        if output_files and status == "COMPLETED":
            menu.addSeparator()
            open_action = QAction("Open output", self)
            open_action.triggered.connect(lambda: self._open_output(output_files[0]))
            menu.addAction(open_action)
        
        # Show menu
        menu.exec(self.task_table.mapToGlobal(position))
    
    def _retry_task(self, url: str):
        """
        Retry a failed task.
        
        Args:
            url: URL of the task to retry
        """
        if hasattr(self.app_manager, 'batch_processor'):
            self.app_manager.batch_processor.retry_task(url)
    
    def _cancel_task(self, url: str):
        """
        Cancel a task.
        
        Args:
            url: URL of the task to cancel
        """
        if hasattr(self.app_manager, 'batch_processor'):
            self.app_manager.batch_processor.cancel_task(url)
    
    def _remove_task(self, url: str):
        """
        Remove a task from the list.
        
        Args:
            url: URL of the task to remove
        """
        # First make sure it's cancelled if running
        if url in self.tasks:
            status = self.tasks[url].get("status", "PENDING")
            if status in ["RUNNING", "PENDING", "PAUSED", "RETRYING"]:
                self._cancel_task(url)
        
        # Now remove it
        self.remove_task(url)
        if hasattr(self.app_manager, 'batch_processor'):
            self.app_manager.batch_processor.remove_task(url)
    
    def _open_output(self, output_file: str):
        """
        Open an output file.
        
        Args:
            output_file: Path to the output file
        """
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        from pathlib import Path
        
        try:
            path = Path(output_file)
            if path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))
            else:
                # Try to open the parent directory
                parent = path.parent
                if parent.exists():
                    QDesktopServices.openUrl(QUrl.fromLocalFile(str(parent)))
        except Exception as e:
            logger.error(f"Failed to open output file: {e}")
