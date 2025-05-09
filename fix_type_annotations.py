"""
Script to find and fix problematic type annotations in Python files
"""
import re
import os
import sys

def fix_type_annotations(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Find problematic pattern: @pyqtSlot with complex type annotations
    pyqtslot_pattern = r'@pyqtSlot\((.*?)\)'
    pyqtslot_matches = re.findall(pyqtslot_pattern, content)
    print(f"Found {len(pyqtslot_matches)} @pyqtSlot decorators")
    
    # Find function parameters with Optional type annotations
    optional_pattern = r': Optional\[([^\]]+)\]'
    optional_matches = re.findall(optional_pattern, content)
    print(f"Found {len(optional_matches)} Optional type annotations in parameters")
    
    # Find pyqtSignal with complex type parameters
    signal_pattern = r'= pyqtSignal\((.*?)\)'
    signal_matches = re.findall(signal_pattern, content)
    print(f"Found {len(signal_matches)} pyqtSignal declarations")
    
    # Process all type annotations that might cause issues
    modified_content = content
    
    # Replace Optional[type] in parameters with just 'type'
    modified_content = re.sub(r': Optional\[([^\]]+)\]', r': \1', modified_content)
    
    # Replace List[type] in parameters with just 'list'
    modified_content = re.sub(r': List\[([^\]]+)\]', r': list', modified_content)
    
    # Replace Dict[keytype, valtype] in parameters with just 'dict'
    modified_content = re.sub(r': Dict\[([^\]]+), ([^\]]+)\]', r': dict', modified_content)
    
    # Write modified content back to file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print(f"Completed processing {file_path}")
    return True

if __name__ == "__main__":
    app_manager_path = "application_manager.py"
    if os.path.exists(app_manager_path):
        fix_type_annotations(app_manager_path)
    else:
        print(f"File {app_manager_path} not found")
