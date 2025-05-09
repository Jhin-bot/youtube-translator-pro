""""
Detailed test script for application_manager with line-by-line import
""""
import sys
import traceback
import importlib.util
import os

def debug_import_module_line_by_line(module_path, start_line=0, end_line=None):
    """"
    Import a module line by line to find where exactly the error occurs
    """"
    with open(module_path, 'r') as f:
        lines = f.readlines()
    
    if end_line is None:
        end_line = len(lines)
        
    for i in range(start_line, min(end_line, len(lines))):
        try:
            line = lines[i].strip()
            if line and not line.startswith('#'):
                print(f"Executing line {i+1}: {line}")
                exec(line)
        except Exception as e:
            print(f"Error at line {i+1}: {e}")
            return False, i+1
    
    return True, None

if __name__ == "__main__":
    # Test application_manager specifically
    module_path = "application_manager.py"
    if os.path.exists(module_path):
        success, error_line = debug_import_module_line_by_line(module_path)
        if not success:
            print(f"First error found at line {error_line}")
    else:
        print(f"Module {module_path} not found")
