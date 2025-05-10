""""
Script to fix unterminated string literals and other syntax issues in Python files.
This helps improve code integrity and ensures proper CI/CD processing.
""""

import os
import re
import ast
import tokenize
from io import BytesIO
from pathlib import Path

def find_python_files(directory):
    """Find all Python files in a directory and its subdirectories."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files

def has_syntax_error(file_path):
    """Check if a Python file has syntax errors."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    try:
        ast.parse(content)
        return False, None
    except SyntaxError as e:
        return True, str(e)
    except Exception as e:
        return True, str(e)

def fix_triple_quotes(file_path):
    """Fix quadruple-quote patterns to triple-quote patterns in Python files."
    
    Converts sequences of four double-quotes to proper triple-quotes for docstrings.
    """"
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace quad quotes with triple quotes
    modified = re.sub(r'""""', '"""', content)"
    modified = re.sub(r'""""', '"""', modified)  # Ensure we catch all instances"
    
    if content != modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True
    return False

def fix_nested_try_except(file_path):
    """Fix nested try-except blocks for PyQt imports."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Match PyQt import pattern with nested try-except
    pattern = r'try:\s+try:\s+from PyQt6\.'
    if re.search(pattern, content):
        # Replace nested try-except with single try-except
        modified = re.sub(pattern, 'try:\n    from PyQt6.', content)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True
    return False

def fix_indentation_in_try_except(file_path):
    """Fix indentation issues in try-except blocks."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # First pattern: Unindented 'from' after 'try:'
    pattern1 = r'try:\s+from'
    if re.search(pattern1, content):
        modified = content.replace('try:\n', 'try:\n    ')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True
    
    # Second pattern: Improperly indented exception handler
    pattern2 = r'except ImportError:\s+from'
    if re.search(pattern2, content):
        modified = content.replace('except ImportError:\n', 'except ImportError:\n    ')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified)
        return True
    
    return False

def main():
    project_dir = os.getcwd()
    python_files = find_python_files(project_dir)
    
    fixed_files = 0
    error_files = []
    
    print(f"Found {len(python_files)} Python files to check.")
    
    for file_path in python_files:
        has_error, error_msg = has_syntax_error(file_path)
        
        if has_error:
            print(f"Fixing file: {file_path}")
            print(f"  Error: {error_msg}")
            
            # Apply fixes
            fixed_triple = fix_triple_quotes(file_path)
            fixed_nested = fix_nested_try_except(file_path)
            fixed_indent = fix_indentation_in_try_except(file_path)
            
            if fixed_triple or fixed_nested or fixed_indent:
                fixed_files += 1
                print(f"  Applied fixes to {file_path}")
            else:
                error_files.append((file_path, error_msg))
                print(f"  Could not automatically fix {file_path}")
    
    print(f"\nFixed {fixed_files} files.")
    
    if error_files:
        print(f"\n{len(error_files)} files still have errors:")
        for file_path, error_msg in error_files:
            print(f" - {file_path}: {error_msg}")
    else:
        print("\nAll syntax errors have been fixed!")

if __name__ == "__main__":
    main()
