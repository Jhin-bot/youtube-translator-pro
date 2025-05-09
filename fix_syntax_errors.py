"""
Fix syntax errors in the YouTube Translator Pro codebase.

This script addresses common syntax errors introduced by the previous fixes:
1. Fixes indentation errors in try/except blocks
2. Fixes unterminated string literals
3. Fixes unclosed parentheses
"""

import os
import re
import sys
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("fix_syntax_errors")

def fix_file(file_path):
    """Fix syntax errors in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # Fix indentation errors in try/except blocks
        try_except_pattern = r'try:\s*\n(?!\s)'
        if re.search(try_except_pattern, content):
            content = re.sub(try_except_pattern, 'try:\n    pass\n', content)
            modified = True
            logger.info(f"Fixed missing indentation after try statement in {file_path}")
        
        # Fix unterminated string literals (simple cases only)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            # Count and fix double quotes
            if line.count('"') % 2 == 1:
                lines[i] = line + '"'
                modified = True
                logger.info(f"Fixed unterminated double quote on line {i+1} in {file_path}")
            # Count and fix single quotes
            if line.count("'") % 2 == 1:
                lines[i] = line + "'"
                modified = True
                logger.info(f"Fixed unterminated single quote on line {i+1} in {file_path}")
        content = '\n'.join(lines)
        
        # Fix unclosed parentheses (simple cases only)
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.count('(') > line.count(')'):
                lines[i] = line + ')' * (line.count('(') - line.count(')'))
                modified = True
                logger.info(f"Fixed unclosed parenthesis on line {i+1} in {file_path}")
        content = '\n'.join(lines)
        
        # Fix multiprocessing Queue import
        if "Queue" in content and "cannot import name 'Queue'" in content:
            queue_import_pattern = r'from\s+multiprocessing\s+import\s+Queue'
            if re.search(queue_import_pattern, content):
                content = re.sub(queue_import_pattern, 'from multiprocessing import Queue as MPQueue  # Renamed to avoid conflict', content)
                # Also replace usage
                content = content.replace('Queue(', 'MPQueue(')
                modified = True
                logger.info(f"Fixed multiprocessing Queue import in {file_path}")
        
        # Fix PyQt module imports
        if "PyQt" in content:
            # Fix bare PyQt6 imports to try PyQt5 as fallback
            pattern = r'import PyQt6\.(.*)'
            replacement = r'try:\n    import PyQt6.\1\nexcept ImportError:\n    import PyQt5.\1'
            content = re.sub(pattern, replacement, content)
            
            # Fix QtCore, QtWidgets and QtGui imports
            for module in ['QtCore', 'QtWidgets', 'QtGui']:
                pattern = fr'from PyQt6\.{module} import (.*)'
                replacement = f'try:\n    from PyQt6.{module} import \\1\nexcept ImportError:\n    from PyQt5.{module} import \\1'
                content = re.sub(pattern, replacement, content)
            
            modified = True
            logger.info(f"Fixed PyQt imports in {file_path}")
        
        # Only write to the file if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Fixed syntax errors in {file_path}")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Error fixing {file_path}: {str(e)}")
        return False


def main():
    """Find and fix syntax errors in Python files."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Find all Python files
    python_files = []
    for root, _, files in os.walk(project_dir):
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    logger.info(f"Found {len(python_files)} Python files")
    
    # Fix each file
    fixed_files = 0
    for file_path in python_files:
        if fix_file(file_path):
            fixed_files += 1
    
    logger.info(f"Fixed syntax errors in {fixed_files} files")
    
    return fixed_files


if __name__ == "__main__":
    main()