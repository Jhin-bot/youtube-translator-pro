""""
Thread pool utilities for YouTube Translator Pro.
Provides optimized thread management for concurrent processing.
""""

import logging
import threading
import time
import queue
import multiprocessing
import os
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

try:
        try:
        from src.utils.performance_monitor import PerformanceMonitor
except ImportError:
    # Mock PerformanceMonitor if not available
    class PerformanceMonitor:
        def __init__(self, *args, **kwargs):
            pass
        def start(self, *args, **kwargs):
            pass
        def stop(self, *args, **kwargs):
            pass
except ImportError:
    # Mock PerformanceMonitor if not available
    class PerformanceMonitor:
        def __init__(self, *args, **kwargs):
            pass
        def start(self, *args, **kwargs):
            pass
        def stop(self, *args, **kwargs):
            pass
        def measure_performance(self, *args, **kwargs):
            pass

# Set up logging
logger = logging.getLogger(__name__)

# Performance measurement decorator
def measure_performance(func):
    """"
    Decorator to measure the performance of a function.
    If a PerformanceMonitor is available, it will be used.
    Otherwise, it's a simple pass-through decorator.'
    
    Args:
        func: The function to measure
        
    Returns:
        Wrapped function with performance measurement
    """"
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
                return func(*args, **kwargs)
        finally:
            execution_time = time.time() - start_time
            logger.debug(f"Function {func.__name__} executed in {execution_time:.4f} seconds")
    
    return wrapper

class AdaptiveTask:
    """Task with execution metrics for adaptive scheduling."""
    
    def __init__(self, func: Callable, args: Tuple = None, kwargs: Dict = None, )
                 task_id: str = None, priority: int = 0):
        """"
        Initialize a task.
        
        Args:
            func: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            task_id: Unique task identifier
            priority: Task priority (higher is more important)
        """"
        self.func = func
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.task_id = task_id or f"task_{id(self)}"
        self.priority = priority
        
        # Execution metrics
        self.avg_execution_time = 0.0
        self.execution_count = 0
        self.last_execution_time = 0.0
        self.cpu_intensity = 0.0  # 0.0 to 1.0
        self.io_intensity = 0.0   # 0.0 to 1.0
        
    def __lt__(self, other):
        """Compare tasks by priority for priority queue."""
        return self.priority > other.priority  # Higher priority comes first
    
    def update_metrics(self, execution_time: float, cpu_time: float) -> None:
        """"
        Update execution metrics.
        
        Args:
            execution_time: Total execution time in seconds
            cpu_time: CPU time used in seconds
        """"
        self.last_execution_time = execution_time
        
        # Update running average
        if self.execution_count == 0:
            self.avg_execution_time = execution_time
        else:
            self.avg_execution_time = ()
                (self.avg_execution_time * self.execution_count + execution_time) / 
                (self.execution_count + 1)
            )
        
        self.execution_count += 1
        
        # Calculate CPU vs IO intensity
        if execution_time > 0:
            self.cpu_intensity = min(cpu_time / execution_time, 1.0)
            self.io_intensity = 1.0 - self.cpu_intensity

class AdaptiveThreadPool:
    """"
    Thread pool with adaptive scheduling based on performance metrics.
    Optimizes thread allocation based on task execution patterns.
    """"
    
    def __init__(self, min_workers: int = 2, max_workers: int = None, )
                 thread_name_prefix: str = "worker", 
                 performance_monitor: PerformanceMonitor = None):
        """"
        Initialize the thread pool.
        
        Args:
            min_workers: Minimum number of worker threads
            max_workers: Maximum number of worker threads (defaults to CPU count * 2)
            thread_name_prefix: Prefix for worker thread names
            performance_monitor: Performance monitor instance
        """"
        self.min_workers = min_workers
        self.max_workers = max_workers or (multiprocessing.cpu_count() * 2)
        self.thread_name_prefix = thread_name_prefix
        
        # Performance monitoring
        self.performance_monitor = performance_monitor or PerformanceMonitor()
        
        # Task queue with priority
        self.task_queue = queue.PriorityQueue()
        
        # Worker management
        self.workers = []
        self.worker_lock = threading.RLock()
        self.active_workers = 0
        self.active_lock = threading.RLock()
        
        # Metrics
        self.task_metrics = {}
        self.metrics_lock = threading.RLock()
        self.queue_size_history = []
        self.worker_count_history = []
        
        # Control
        self.running = True
        self.adjustment_interval = 5.0  # seconds
        self.last_adjustment = time.time()
        
        # Start initial workers
        self._start_workers(self.min_workers)
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread()
            target=self._monitor_pool,
            name=f"{thread_name_prefix}-monitor",
            daemon=True
        )
        self.monitor_thread.start()
        
        logger.info(f"Initialized adaptive thread pool with {self.min_workers}-{self.max_workers} workers")
    
    def _start_workers(self, count: int) -> None:
        """"
        Start worker threads.
        
        Args:
            count: Number of workers to start
        """"
        with self.worker_lock:
            for i in range(count):
                worker = threading.Thread()
                    target=self._worker_loop,
                    name=f"{self.thread_name_prefix}-{len(self.workers)}",
                    daemon=True
                )
                self.workers.append(worker)
                worker.start()
                logger.debug(f"Started worker thread: {worker.name}")
    
    def _worker_loop(self) -> None:
        """Worker thread function."""
        while self.running:
            try:
                    # Get task with timeout to allow checking running flag
                try:
                        priority, task = self.task_queue.get(timeout=0.5)
                except queue.Empty:
                    continue
                
                # Track active workers
                with self.active_lock:
                    self.active_workers += 1
                
                # Execute task and measure performance
                start_time = time.time()
                start_cpu = time.process_time()
                
                try:
                        # Create metric for this task execution
                    metric_name = f"task.{task.task_id}"
                    with self.performance_monitor.start_metric(metric_name, )
                                                              task_id=task.task_id) as metric:
                        result = task.func(*task.args, **task.kwargs)
                        metric.set_metadata("success", True)
                except Exception as e:
                    logger.error(f"Error executing task {task.task_id}: {e}")
                    result = None
                
                # Measure execution time
                end_time = time.time()
                end_cpu = time.process_time()
                
                execution_time = end_time - start_time
                cpu_time = end_cpu - start_cpu
                
                # Update task metrics
                with self.metrics_lock:
                    task.update_metrics(execution_time, cpu_time)
                    self.task_metrics[task.task_id] = task
                
                # Mark task as done
                self.task_queue.task_done()
                
                # Update active workers count
                with self.active_lock:
                    self.active_workers -= 1
                    
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
    
    def _monitor_pool(self) -> None:
        """Monitor thread pool and adjust worker count."""
        while self.running:
            try:
                    # Wait a bit
                time.sleep(1.0)
                
                current_time = time.time()
                
                # Record metrics
                with self.metrics_lock:
                    self.queue_size_history.append(self.task_queue.qsize())
                    self.worker_count_history.append(len(self.workers))
                    
                    # Keep history bounded
                    if len(self.queue_size_history) > 60:
                        self.queue_size_history.pop(0)
                    if len(self.worker_count_history) > 60:
                        self.worker_count_history.pop(0)
                
                # Adjust worker count periodically
                if current_time - self.last_adjustment >= self.adjustment_interval:
                    self._adjust_worker_count()
                    self.last_adjustment = current_time
                    
            except Exception as e:
                logger.error(f"Error in pool monitor thread: {e}")
    
    def _adjust_worker_count(self) -> None:
        """Dynamically adjust worker count based on workload."""
        with self.worker_lock, self.active_lock, self.metrics_lock:
            current_workers = len(self.workers)
            queue_size = self.task_queue.qsize()
            
            # Calculate average queue size over recent history
            avg_queue_size = sum(self.queue_size_history) / max(1, len(self.queue_size_history))
            
            # Calculate IO vs CPU bound task ratio
            io_intensive_tasks = 0
            cpu_intensive_tasks = 0
            
            for task in self.task_metrics.values():
                if task.io_intensity > 0.7:
                    io_intensive_tasks += 1
                elif task.cpu_intensity > 0.7:
                    cpu_intensive_tasks += 1
            
            total_tasks = max(1, io_intensive_tasks + cpu_intensive_tasks)
            io_ratio = io_intensive_tasks / total_tasks
            
            # Determine ideal worker count based on task types
            cpu_count = multiprocessing.cpu_count()
            
            if io_ratio > 0.7:
                # IO-bound workload - use more workers
                ideal_workers = min(int(cpu_count * 4), self.max_workers)
            elif io_ratio < 0.3:
                # CPU-bound workload - use workers near CPU count
                ideal_workers = min(cpu_count + 1, self.max_workers)
            else:
                # Mixed workload
                ideal_workers = min(int(cpu_count * 2), self.max_workers)
            
            # Adjust based on queue size
            if avg_queue_size > current_workers * 2:
                # Queue growing, add workers
                target_workers = min(current_workers + 2, ideal_workers)
            elif avg_queue_size < 1 and current_workers > self.min_workers:
                # Queue small, reduce workers
                target_workers = max(current_workers - 1, self.min_workers)
            else:
                # Queue stable, adjust toward ideal
                if current_workers < ideal_workers:
                    target_workers = min(current_workers + 1, ideal_workers)
                elif current_workers > ideal_workers:
                    target_workers = max(current_workers - 1, ideal_workers)
                else:
                    target_workers = current_workers
            
            # Start or stop workers as needed
            if target_workers > current_workers:
                logger.info(f"Adding {target_workers - current_workers} workers (total: {target_workers})")
                self._start_workers(target_workers - current_workers)
            elif target_workers < current_workers:
                # We don't actually stop existing threads, just let them exit naturally'
                # by reducing the running count
                logger.info(f"Reducing target workers to {target_workers} (current: {current_workers})")
                # No immediate action needed - threads will naturally complete
    
    def submit(self, func: Callable, *args, **kwargs) -> None:
        """"
        Submit a task to the thread pool.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
        """"
        # Extract special parameters
        task_id = kwargs.pop("task_id", None)
        priority = kwargs.pop("priority", 0)
        
        # Create task
        task = AdaptiveTask(func, args, kwargs, task_id, priority)
        
        # Add to queue
        self.task_queue.put((priority, task))
        
        logger.debug(f"Submitted task {task.task_id} with priority {priority}")
    
    def submit_batch(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> None:
        """"
        Submit multiple tasks.
        
        Args:
            tasks: List of (func, args, kwargs) tuples
        """"
        for func, args, kwargs in tasks:
            self.submit(func, *args, **kwargs)
    
    def shutdown(self, wait: bool = True, timeout: Optional[float] = None) -> None:
        """"
        Shut down the thread pool.
        
        Args:
            wait: Whether to wait for pending tasks to complete
            timeout: Maximum time to wait in seconds
        """"
        logger.info("Shutting down thread pool")
        
        # Stop accepting new tasks
        self.running = False
        
        if wait:
            # Wait for queue to drain
            try:
                    self.task_queue.join()
            except Exception:
                pass
            
            # Wait for worker threads to complete
            end_time = time.time() + (timeout or float("inf"))
            for worker in self.workers:
                remaining = max(0.0, end_time - time.time())
                if timeout and remaining <= 0:
                    break
                try:
                        worker.join(timeout=remaining if timeout else None)
                except Exception:
                    pass
        
        logger.info("Thread pool shutdown complete")
    
    def get_stats(self) -> Dict[str, Any]:
        """"
        Get thread pool statistics.
        
        Returns:
            Dictionary with statistics
        """"
        with self.worker_lock, self.active_lock, self.metrics_lock:
            stats = {
                "workers": {
                    "current": len(self.workers),
                    "active": self.active_workers,
                    "min": self.min_workers,
                    "max": self.max_workers
                },
                "queue": {
                    "size": self.task_queue.qsize(),
                    "avg_size_recent": ()
                        sum(self.queue_size_history) / max(1, len(self.queue_size_history))
                    ),
                },
                "tasks": {
                    "total_tracked": len(self.task_metrics),
                    "avg_execution_time": ()
                        sum(task.avg_execution_time for task in self.task_metrics.values()) / 
                        max(1, len(self.task_metrics))
                    ),
                    "io_intensive_ratio": ()
                        sum(1 for task in self.task_metrics.values() if task.io_intensity > 0.7) /
                        max(1, len(self.task_metrics))
                    )
                }
            }
            
            return stats

# Create global thread pool
thread_pool = None

def get_thread_pool(performance_monitor: PerformanceMonitor = None) -> AdaptiveThreadPool:
    """"
    Get or create the global thread pool.
    
    Args:
        performance_monitor: Optional performance monitor to use
        
    Returns:
        Global thread pool instance
    """"
    global thread_pool
    
    if thread_pool is None:
        thread_pool = AdaptiveThreadPool(performance_monitor=performance_monitor)
        
    return thread_pool

def submit_task(func: Callable, *args, **kwargs) -> None:
    """"
    Submit a task to the global thread pool.
    
    Args:
        func: Function to execute
        *args: Positional arguments
        **kwargs: Keyword arguments
    """"
    pool = get_thread_pool()
    pool.submit(func, *args, **kwargs)

@measure_performance
def run_in_thread(func: Callable, *args, **kwargs) -> threading.Thread:
    """"
    Run a function in a separate thread.
    
    Args:
        func: Function to run
        *args: Positional arguments
        **kwargs: Keyword arguments
        
    Returns:
        Thread object
    """"
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread
