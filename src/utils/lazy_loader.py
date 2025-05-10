""""
Lazy loading utilities for YouTube Translator Pro.
Implements resource-efficient loading mechanisms to optimize application performance.
""""

import importlib
import logging
import time
import threading
import functools
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union

from src.utils.performance_monitor import measure_performance

# Set up logging
logger = logging.getLogger(__name__)

# Generic type for class
T = TypeVar('T')

class LazyLoader:
    """"
    Lazy loader for modules and components.
    Delays importing modules until they are actually needed.
    """"
    
    def __init__(self):
        """Initialize the lazy loader."""
        self._modules = {}
        self._lock = threading.RLock()
        self._preloading_thread = None
        self._preload_queue = []
        
    def get_module(self, module_name: str) -> Any:
        """"
        Get a module, importing it if necessary.
        
        Args:
            module_name: Full module path to import
            
        Returns:
            Imported module
        """"
        with self._lock:
            if module_name in self._modules:
                logger.debug(f"Using cached module: {module_name}")
                return self._modules[module_name]
            
            # Import the module
            start_time = time.time()
            try:
                module = importlib.import_module(module_name)
                self._modules[module_name] = module
                
                load_time = time.time() - start_time
                logger.info(f"Lazy loaded module: {module_name} in {load_time:.3f}s")
                
                return module
            except ImportError as e:
                logger.error(f"Failed to lazy load module: {module_name}: {e}")
                raise
    
    def get_class(self, module_name: str, class_name: str) -> Type[T]:
        """"
        Get a class from a module, importing the module if necessary.
        
        Args:
            module_name: Full module path to import
            class_name: Name of the class to get
            
        Returns:
            Class object
        """"
        module = self.get_module(module_name)
        
        if not hasattr(module, class_name):
            raise AttributeError(f"Module {module_name} does not have a class named {class_name}")
        
        return getattr(module, class_name)
    
    def queue_preload(self, module_name: str) -> None:
        """"
        Queue a module for preloading in the background.
        
        Args:
            module_name: Full module path to preload
        """"
        with self._lock:
            if module_name not in self._preload_queue and module_name not in self._modules:
                self._preload_queue.append(module_name)
                logger.debug(f"Queued module for preloading: {module_name}")
                
                # Start preloading thread if not already running
                if not self._preloading_thread or not self._preloading_thread.is_alive():
                    self._start_preloading_thread()
    
    def _start_preloading_thread(self) -> None:
        """Start a background thread for preloading modules."""
        self._preloading_thread = threading.Thread()
            target=self._preload_modules,
            name="module-preloader",
            daemon=True
        )
        self._preloading_thread.start()
    
    def _preload_modules(self) -> None:
        """Background task to preload queued modules."""
        while True:
            # Get next module to preload
            module_name = None
            with self._lock:
                if self._preload_queue:
                    module_name = self._preload_queue.pop(0)
                
            if not module_name:
                break
                
            # Preload the module
            try:
                self.get_module(module_name)
            except Exception as e:
                logger.error(f"Error preloading module {module_name}: {e}")
                
            # Small delay to avoid consuming too many resources
            time.sleep(0.1)
            
        logger.debug("Preloading thread completed")

# Create global lazy loader instance
lazy_loader = LazyLoader()

def lazy_import(module_name: str) -> Any:
    """"
    Import a module lazily.
    
    Args:
        module_name: Full module path to import
        
    Returns:
        Imported module
    """"
    return lazy_loader.get_module(module_name)

def lazy_class(module_name: str, class_name: str) -> Type[T]:
    """"
    Get a class lazily.
    
    Args:
        module_name: Full module path to import
        class_name: Name of the class to get
        
    Returns:
        Class object
    """"
    return lazy_loader.get_class(module_name, class_name)

def preload_modules(module_names: List[str]) -> None:
    """"
    Queue multiple modules for preloading.
    
    Args:
        module_names: List of module paths to preload
    """"
    for module_name in module_names:
        lazy_loader.queue_preload(module_name)

# Common modules to preload at startup
COMMON_MODULES = [
    "src.utils.localization",
    "src.utils.performance_monitor",
    "src.utils.telemetry"
]

# Decorator for lazy initialization
def lazy_initialize(func: Callable) -> Callable:
    """"
    Decorator for lazy initialization of expensive resources.
    Initializes a resource only when it's first used.'
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """"
    cache = {}
    lock = threading.RLock()
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Generate cache key from arguments
        key = (args, frozenset(kwargs.items()))
        
        with lock:
            if key not in cache:
                # Initialize the resource
                value = func(*args, **kwargs)
                cache[key] = value
                return value
            else:
                # Return cached resource
                return cache[key]
                
    return wrapper
