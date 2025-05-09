"""
Performance monitoring utilities for YouTube Translator Pro.
"""

import time
import logging
import functools
import threading
import psutil
from typing import Dict, List, Callable, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager

# Set up logging
logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Performance metric data class."""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_before: Optional[int] = None
    memory_after: Optional[int] = None
    memory_diff: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def complete(self) -> None:
        """Complete the metric by setting end time and calculating duration."""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        
        # Get current memory usage
        process = psutil.Process()
        self.memory_after = process.memory_info().rss
        
        if self.memory_before is not None:
            self.memory_diff = self.memory_after - self.memory_before

class PerformanceMonitor:
    """
    Performance monitoring utility for tracking execution time and memory usage.
    """
    
    def __init__(self):
        """Initialize the performance monitor."""
        self._metrics: List[PerformanceMetric] = []
        self._lock = threading.RLock()
        self._start_time = time.time()
        
    def start_metric(self, name: str, **metadata) -> PerformanceMetric:
        """
        Start tracking a new performance metric.
        
        Args:
            name: Name of the metric
            **metadata: Additional metadata to store with the metric
            
        Returns:
            PerformanceMetric object
        """
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        metric = PerformanceMetric(
            name=name,
            start_time=time.time(),
            memory_before=memory_before,
            metadata=metadata
        )
        
        with self._lock:
            self._metrics.append(metric)
            
        logger.debug(f"Started performance metric: {name}")
        return metric
    
    def end_metric(self, metric: PerformanceMetric) -> None:
        """
        Complete a performance metric.
        
        Args:
            metric: The metric to complete
        """
        metric.complete()
        logger.debug(f"Completed performance metric: {metric.name} - Duration: {metric.duration:.4f}s")
        
        if metric.memory_diff is not None:
            memory_diff_mb = metric.memory_diff / (1024 * 1024)
            logger.debug(f"Memory change for {metric.name}: {memory_diff_mb:.2f} MB")
    
    def get_metrics(self) -> List[PerformanceMetric]:
        """
        Get all recorded metrics.
        
        Returns:
            List of all performance metrics
        """
        with self._lock:
            return self._metrics.copy()
    
    def get_metrics_by_name(self, name: str) -> List[PerformanceMetric]:
        """
        Get metrics filtered by name.
        
        Args:
            name: Name to filter by
            
        Returns:
            List of matching metrics
        """
        with self._lock:
            return [m for m in self._metrics if m.name == name]
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a performance report.
        
        Returns:
            Dictionary with performance statistics
        """
        metrics = self.get_metrics()
        total_runtime = time.time() - self._start_time
        
        # Group metrics by name
        grouped: Dict[str, List[PerformanceMetric]] = {}
        for metric in metrics:
            if metric.name not in grouped:
                grouped[metric.name] = []
            grouped[metric.name].append(metric)
        
        # Calculate statistics for each group
        stats = {}
        for name, group in grouped.items():
            completed = [m for m in group if m.duration is not None]
            if not completed:
                continue
                
            durations = [m.duration for m in completed]
            memory_diffs = [m.memory_diff for m in completed if m.memory_diff is not None]
            
            stats[name] = {
                "count": len(completed),
                "total_time": sum(durations),
                "avg_time": sum(durations) / len(durations),
                "min_time": min(durations),
                "max_time": max(durations),
                "percent_of_total": (sum(durations) / total_runtime) * 100 if total_runtime > 0 else 0
            }
            
            if memory_diffs:
                avg_memory_mb = sum(memory_diffs) / len(memory_diffs) / (1024 * 1024)
                stats[name]["avg_memory_change_mb"] = avg_memory_mb
        
        return {
            "total_runtime": total_runtime,
            "total_metrics": len(metrics),
            "metrics_by_name": stats
        }
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._metrics.clear()
            self._start_time = time.time()
            
    @contextmanager
    def measure(self, name: str, **metadata):
        """
        Context manager for measuring a code block.
        
        Args:
            name: Metric name
            **metadata: Additional metadata
            
        Example:
            with performance_monitor.measure("download_video"):
                # Code to be measured
                download_video()
        """
        metric = self.start_metric(name, **metadata)
        try:
            yield
        finally:
            self.end_metric(metric)
            
# Create a global instance for use throughout the application
monitor = PerformanceMonitor()

def measure_performance(func: Callable) -> Callable:
    """
    Decorator to measure the performance of a function.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
        
    Example:
        @measure_performance
        def process_video(video_id):
            # Process the video
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with monitor.measure(func.__name__, args=args, kwargs=kwargs):
            return func(*args, **kwargs)
    return wrapper
