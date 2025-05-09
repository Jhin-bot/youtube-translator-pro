"""
Script to fix any remaining Optional/Dict/List type annotations in PyQt signal declarations
"""
import re
import os

def fix_pyqt_signals(file_path):
    print(f"Processing {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Replace all pyqtSignal declarations with complex type parameters
    # Pattern: something = pyqtSignal(ComplexType[...], ...)
    # Replace with: something = pyqtSignal(object, ...)
    
    # First find all signal declarations
    signal_pattern = r'(\w+)\s*=\s*pyqtSignal\((.*?)\)'
    
    def replace_complex_types(match):
        signal_name = match.group(1)
        params = match.group(2)
        
        # Replace complex types with 'object'
        modified_params = re.sub(r'Optional\[[^\]]+\]', 'object', params)
        modified_params = re.sub(r'List\[[^\]]+\]', 'object', modified_params)
        modified_params = re.sub(r'Dict\[[^\]]+\]', 'object', modified_params)
        modified_params = re.sub(r'Tuple\[[^\]]+\]', 'object', modified_params)
        modified_params = re.sub(r'Union\[[^\]]+\]', 'object', modified_params)
        
        return f"{signal_name} = pyqtSignal({modified_params})"
    
    modified_content = re.sub(signal_pattern, replace_complex_types, content)
    
    # Also fix @pyqtSlot decorators
    slot_pattern = r'@pyqtSlot\((.*?)\)'
    
    def replace_complex_slot_types(match):
        params = match.group(1)
        
        # Replace complex types with 'object'
        modified_params = re.sub(r'Optional\[[^\]]+\]', 'object', params)
        modified_params = re.sub(r'List\[[^\]]+\]', 'object', modified_params)
        modified_params = re.sub(r'Dict\[[^\]]+\]', 'object', modified_params)
        modified_params = re.sub(r'Tuple\[[^\]]+\]', 'object', modified_params)
        modified_params = re.sub(r'Union\[[^\]]+\]', 'object', modified_params)
        
        return f"@pyqtSlot({modified_params})"
    
    modified_content = re.sub(slot_pattern, replace_complex_slot_types, modified_content)
    
    # Write modified content back to file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(modified_content)
    
    print(f"Completed processing {file_path}")
    return True

if __name__ == "__main__":
    files_to_process = [
        "application_manager.py",
        "ui.py",
        "batch.py"
    ]
    
    for file_path in files_to_process:
        if os.path.exists(file_path):
            fix_pyqt_signals(file_path)
        else:
            print(f"File {file_path} not found")
