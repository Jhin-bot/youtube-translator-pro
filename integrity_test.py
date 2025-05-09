"""
Integrity test for YouTube Translator Pro.
This script verifies that all important components of the application can be imported
and basic functionality works as expected.
"""

import importlib
import os
import sys
import traceback
import pkgutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("integrity_test")

# Results tracking
RESULTS = {
    "total_files": 0,
    "tested_modules": 0,
    "successful": 0,
    "failed": 0,
    "errors": [],
}

def import_module_safe(module_name):
    """Try to import a module safely, returning success status and error."""
    try:
        importlib.import_module(module_name)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"

def is_python_module(path):
    """Check if path is a Python module (directory with __init__.py)"""
    return (path / "__init__.py").exists()

def is_python_package(path):
    """Check if path is a Python package"""
    return path.is_dir() and any(f.name == "__init__.py" for f in path.iterdir())

def is_python_file(path):
    """Check if path is a Python file"""
    return path.is_file() and path.suffix == ".py"

def get_module_name(file_path, base_dir):
    """Convert file path to module name"""
    rel_path = file_path.relative_to(base_dir)
    if rel_path.name == "__init__.py":
        rel_path = rel_path.parent
    else:
        # Remove .py extension
        rel_path = rel_path.with_suffix("")
    
    # Convert path separators to dots for module name
    return str(rel_path).replace(os.sep, ".")

def test_file_imports(file_path, base_dir=None):
    """Test importing a Python file or module"""
    if base_dir is None:
        base_dir = Path.cwd()
    
    try:
        if is_python_file(file_path):
            module_name = get_module_name(file_path, base_dir)
            return test_import(module_name)
        return True, None
    except Exception as e:
        return False, f"Error processing {file_path}: {str(e)}"

def test_import(module_name):
    """Test importing a module by name"""
    logger.info(f"Testing import: {module_name}")
    RESULTS["tested_modules"] += 1
    success, error = import_module_safe(module_name)
    
    if success:
        logger.info(f"✓ Successfully imported {module_name}")
        RESULTS["successful"] += 1
    else:
        logger.error(f"✗ Failed to import {module_name}")
        logger.error(error)
        RESULTS["failed"] += 1
        RESULTS["errors"].append((module_name, error))
    
    return success, error

def test_src_directory():
    """Test all modules in the src directory"""
    src_dir = Path("src")
    if not src_dir.exists():
        logger.error("src directory not found!")
        return
    
    # First test importing the main src package
    test_import("src")
    
    # Add src to path to help with relative imports
    base_dir = Path.cwd()
    sys.path.insert(0, str(base_dir))
    
    # Test all Python files in src recursively
    for root, dirs, files in os.walk("src"):
        root_path = Path(root)
        
        # Test if directory is a package
        if is_python_module(root_path):
            module_name = get_module_name(root_path / "__init__.py", base_dir)
            test_import(module_name)
        
        # Test individual Python files
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                file_path = root_path / file
                RESULTS["total_files"] += 1
                test_file_imports(file_path, base_dir)

def test_main_modules():
    """Test importing main project modules"""
    logger.info("Testing main modules...")
    
    main_modules = [
        "main",
        "settings",
        "application_manager",
        "transcribe",
        "translate",
        "srt_export",
        "batch",
        "ui",
        "cache"
    ]
    
    for module in main_modules:
        test_import(module)

def test_ui_components():
    """Test UI components"""
    logger.info("Testing UI components...")
    ui_modules = [
        "src.ui",
        "src.ui.keyboard_shortcuts",
        "src.ui.rtl_support",
    ]
    
    for module in ui_modules:
        test_import(module)

def test_utils_components():
    """Test utility components"""
    logger.info("Testing utility components...")
    util_modules = [
        "src.utils",
        "src.utils.thread_pool",
        "src.utils.lazy_loader",
    ]
    
    for module in util_modules:
        test_import(module)

def print_summary():
    """Print test summary"""
    success_rate = (RESULTS["successful"] / RESULTS["tested_modules"]) * 100 if RESULTS["tested_modules"] > 0 else 0
    
    logger.info("=" * 60)
    logger.info("INTEGRITY TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Total files scanned: {RESULTS['total_files']}")
    logger.info(f"Total modules tested: {RESULTS['tested_modules']}")
    logger.info(f"Successful imports: {RESULTS['successful']}")
    logger.info(f"Failed imports: {RESULTS['failed']}")
    logger.info(f"Success rate: {success_rate:.2f}%")
    logger.info("=" * 60)
    
    if RESULTS["failed"] > 0:
        logger.info("FAILED MODULES:")
        for module, error in RESULTS["errors"]:
            logger.info(f"- {module}")
        
        logger.info("\nTo see detailed error for a specific module, run:")
        logger.info("python -c \"import <module_name>\"")
    
    return RESULTS["failed"] == 0

def main():
    """Run all integrity tests"""
    logger.info("Starting YouTube Translator Pro integrity test...")
    
    # Test main application modules
    test_main_modules()
    
    # Test all modules in src directory
    test_src_directory()
    
    # Test specific component categories
    test_ui_components()
    test_utils_components()
    
    # Print summary
    success = print_summary()
    
    # Return exit code (0 for success, 1 for failures)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
