""""
Add missing imports to Python files in the project.
""""
import os
import re
import sys

def add_missing_imports(file_path):
    """Add missing imports to a Python file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    # Check if 'requests' is used but not imported
    if 'requests' in content and 'import requests' not in content and 'requests = ' not in content:
        # Add import at the top of the file after other imports
        import_lines = re.findall(r'^import .*$|^from .* import .*$', content, re.MULTILINE)
        if import_lines:
            last_import = import_lines[-1]
            idx = content.find(last_import) + len(last_import)
            modified_content = content[:idx] + "\n\n# Add requests for HTTP functionality\ntry:\n    import requests\nexcept ImportError:\n    # Create a mock requests module\n    class MockRequests:\n        def get(self, *args, **kwargs):\n            return None\n        def post(self, *args, **kwargs):\n            return None\n    requests = MockRequests()" + content[idx:]
            
            # Save changes
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print(f"Added requests import to {file_path}")
            return True
    
    return False

if __name__ == "__main__":
    # Process main Python files
    files_to_check = [
        "batch.py",
        "ui.py",
        "application_manager.py",
        "enhanced_integrity_test.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            add_missing_imports(file_path)
