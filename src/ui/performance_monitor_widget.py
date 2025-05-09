"""
Performance monitoring widget for YouTube Translator Pro.
Displays real-time performance metrics for the application.
"""

import logging
import time
from datetime import datetime, timedelta

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QProgressBar, QSplitter, QDialog, QTabWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QBrush, QFont

from src.utils.performance_monitor import monitor as performance_monitor
from src.utils.localization import get_string

# Set up logging
logger = logging.getLogger(__name__)

class PerformanceMetricWidget(QWidget):
    """Widget displaying a single performance metric."""
    
    def __init__(self, name, parent=None):
        """Initialize the performance metric widget."""
        super().__init__(parent)
        
        # Store metric name
        self.metric_name = name
        self.last_update = time.time()
        
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Create header
        self.header = QLabel(name)
        self.header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.header.font()
        font.setBold(True)
        self.header.setFont(font)
        layout.addWidget(self.header)
        
        # Create time label
        self.time_label = QLabel("0.00 ms")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.time_label.font()
        font.setPointSize(font.pointSize() + 2)
        self.time_label.setFont(font)
        layout.addWidget(self.time_label)
        
        # Create count label
        self.count_label = QLabel("Count: 0")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)
        
        # Create average label
        self.avg_label = QLabel("Avg: 0.00 ms")
        self.avg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.avg_label)
        
        # Initial styling
        self.setAutoFillBackground(True)
        
        # Set fixed size
        self.setMinimumWidth(150)
        self.setMinimumHeight(100)
        
    def update_metric(self, stats):
        """Update the widget with new statistics."""
        if self.metric_name not in stats:
            self.time_label.setText("0.00 ms")
            self.count_label.setText("Count: 0")
            self.avg_label.setText("Avg: 0.00 ms")
            return
            
        # Get metric stats
        metric = stats[self.metric_name]
        
        # Update labels
        if 'avg_time' in metric:
            avg_time = metric['avg_time'] * 1000  # Convert to ms
            self.avg_label.setText(f"Avg: {avg_time:.2f} ms")
        
        if 'max_time' in metric:
            max_time = metric['max_time'] * 1000  # Convert to ms
            self.time_label.setText(f"{max_time:.2f} ms")
        
        if 'count' in metric:
            self.count_label.setText(f"Count: {metric['count']}")
            
        # Update background color based on performance
        # Green for good, yellow for warning, red for poor
        if 'avg_time' in metric:
            palette = self.palette()
            if avg_time < 100:  # Less than 100ms is good
                palette.setColor(self.backgroundRole(), QColor(200, 255, 200))
            elif avg_time < 500:  # Less than 500ms is acceptable
                palette.setColor(self.backgroundRole(), QColor(255, 255, 200))
            else:  # More than 500ms is poor
                palette.setColor(self.backgroundRole(), QColor(255, 200, 200))
            self.setPalette(palette)
            
        # Update last update time
        self.last_update = time.time()

class PerformanceMonitorWidget(QWidget):
    """Widget for monitoring application performance."""
    
    def __init__(self, parent=None):
        """Initialize the performance monitor widget."""
        super().__init__(parent)
        
        # Set up layout
        layout = QVBoxLayout(self)
        
        # Create header
        header_layout = QHBoxLayout()
        title = QLabel(get_string("performance.title", "Performance Monitor"))
        font = title.font()
        font.setBold(True)
        font.setPointSize(font.pointSize() + 2)
        title.setFont(font)
        header_layout.addWidget(title)
        
        # Add refresh button
        self.refresh_button = QPushButton(get_string("performance.refresh", "Refresh"))
        self.refresh_button.clicked.connect(self.refresh_metrics)
        header_layout.addWidget(self.refresh_button)
        
        # Add auto-refresh checkbox
        self.auto_refresh = QLabel(get_string("performance.auto_refresh", "Auto-refresh"))
        header_layout.addWidget(self.auto_refresh)
        
        # Add reset button
        self.reset_button = QPushButton(get_string("performance.reset", "Reset"))
        self.reset_button.clicked.connect(self.reset_metrics)
        header_layout.addWidget(self.reset_button)
        
        layout.addLayout(header_layout)
        
        # Create metrics container
        metrics_group = QGroupBox(get_string("performance.metrics", "Performance Metrics"))
        metrics_layout = QHBoxLayout(metrics_group)
        
        # Create common metric widgets
        self.metrics = {}
        common_metrics = [
            "download_youtube_audio",
            "transcribe_audio",
            "translate_text",
            "cache_audio",
            "cache_transcription"
        ]
        
        for metric in common_metrics:
            widget = PerformanceMetricWidget(metric)
            metrics_layout.addWidget(widget)
            self.metrics[metric] = widget
            
        layout.addWidget(metrics_group)
        
        # Create table for all metrics
        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(6)
        self.metrics_table.setHorizontalHeaderLabels([
            get_string("performance.operation", "Operation"),
            get_string("performance.count", "Count"),
            get_string("performance.total_time", "Total Time (ms)"),
            get_string("performance.avg_time", "Avg Time (ms)"),
            get_string("performance.max_time", "Max Time (ms)"),
            get_string("performance.percent", "% of Total")
        ])
        
        # Set table properties
        self.metrics_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, 6):
            self.metrics_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
            
        layout.addWidget(self.metrics_table)
        
        # Add status bar
        status_layout = QHBoxLayout()
        
        self.last_update_label = QLabel(get_string("performance.last_update", "Last update: Never"))
        status_layout.addWidget(self.last_update_label)
        
        self.total_runtime_label = QLabel(get_string("performance.total_runtime", "Total runtime: 0s"))
        status_layout.addWidget(self.total_runtime_label)
        
        layout.addLayout(status_layout)
        
        # Timer for auto-refresh
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_metrics)
        self.refresh_timer.start(2000)  # Refresh every 2 seconds
        
        # Initial refresh
        self.refresh_metrics()
        
    def refresh_metrics(self):
        """Refresh performance metrics."""
        # Generate performance report
        report = performance_monitor.generate_report()
        
        # Update metrics widgets
        for name, widget in self.metrics.items():
            widget.update_metric(report.get("metrics_by_name", {}))
            
        # Update table
        self.update_metrics_table(report)
        
        # Update status
        update_time = datetime.now().strftime("%H:%M:%S")
        self.last_update_label.setText(get_string("performance.last_update", f"Last update: {update_time}"))
        
        total_runtime = report.get("total_runtime", 0)
        if total_runtime < 60:
            runtime_text = f"{total_runtime:.1f}s"
        elif total_runtime < 3600:
            minutes = int(total_runtime / 60)
            seconds = int(total_runtime % 60)
            runtime_text = f"{minutes}m {seconds}s"
        else:
            hours = int(total_runtime / 3600)
            minutes = int((total_runtime % 3600) / 60)
            runtime_text = f"{hours}h {minutes}m"
            
        self.total_runtime_label.setText(get_string("performance.total_runtime", f"Total runtime: {runtime_text}"))
        
    def update_metrics_table(self, report):
        """Update the metrics table with data from the report."""
        metrics = report.get("metrics_by_name", {})
        
        # Set row count
        self.metrics_table.setRowCount(len(metrics))
        
        # Fill table
        for row, (name, data) in enumerate(sorted(metrics.items())):
            # Name
            self.metrics_table.setItem(row, 0, QTableWidgetItem(name))
            
            # Count
            count_item = QTableWidgetItem(str(data.get("count", 0)))
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 1, count_item)
            
            # Total time
            total_time = data.get("total_time", 0) * 1000  # Convert to ms
            total_time_item = QTableWidgetItem(f"{total_time:.2f}")
            total_time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 2, total_time_item)
            
            # Average time
            avg_time = data.get("avg_time", 0) * 1000  # Convert to ms
            avg_time_item = QTableWidgetItem(f"{avg_time:.2f}")
            avg_time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Color code based on performance
            if avg_time < 100:
                avg_time_item.setBackground(QBrush(QColor(200, 255, 200)))
            elif avg_time < 500:
                avg_time_item.setBackground(QBrush(QColor(255, 255, 200)))
            else:
                avg_time_item.setBackground(QBrush(QColor(255, 200, 200)))
                
            self.metrics_table.setItem(row, 3, avg_time_item)
            
            # Max time
            max_time = data.get("max_time", 0) * 1000  # Convert to ms
            max_time_item = QTableWidgetItem(f"{max_time:.2f}")
            max_time_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 4, max_time_item)
            
            # Percent of total
            percent = data.get("percent_of_total", 0)
            percent_item = QTableWidgetItem(f"{percent:.1f}%")
            percent_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.metrics_table.setItem(row, 5, percent_item)
            
    def reset_metrics(self):
        """Reset all performance metrics."""
        # Reset performance monitor
        performance_monitor.reset()
        
        # Refresh displays
        self.refresh_metrics()
        
    def refresh_text(self):
        """Refresh text after language change."""
        # Update table headers
        self.metrics_table.setHorizontalHeaderLabels([
            get_string("performance.operation", "Operation"),
            get_string("performance.count", "Count"),
            get_string("performance.total_time", "Total Time (ms)"),
            get_string("performance.avg_time", "Avg Time (ms)"),
            get_string("performance.max_time", "Max Time (ms)"),
            get_string("performance.percent", "% of Total")
        ])
        
        # Update buttons
        self.refresh_button.setText(get_string("performance.refresh", "Refresh"))
        self.reset_button.setText(get_string("performance.reset", "Reset"))
        self.auto_refresh.setText(get_string("performance.auto_refresh", "Auto-refresh"))
        
        # Refresh metrics
        self.refresh_metrics()
