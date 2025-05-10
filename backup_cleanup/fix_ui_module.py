""""
Script to fix common syntax issues in the UI module files:
1. Replace quad quotes with triple quotes in docstrings
2. Fix nested try-except blocks for PyQt imports
3. Fix indentation issues
""""

import os
import re
import glob

# Get all Python files in the UI module
ui_files = glob.glob(os.path.join('src', 'ui', '*.py'))

fixed_count = 0

# Process each file
for file_path in ui_files:
    print(f"Processing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Keep track of whether we've made changes'
    original_content = content
    
    # 1. Fix quad quotes in docstrings
    content = re.sub(r'""""(.*?)""""', r'"""\1"""', content, flags=re.DOTALL)
    content = re.sub(r'""""(.*?)"""', r'"""\1"""', content, flags=re.DOTALL)"
    
    # 2. Fix PyQt Core imports with nested try blocks
    core_pattern = r'try:\s+try:\s+try:\s+try:\s+from PyQt6\.QtCore import (.*?)except ImportError:.*?except ImportError:.*?except ImportError:.*?except ImportError:'
    core_replacement = r'try:\n    try:
    from PyQt6.QtCore import \1\nexcept ImportError:\n    from PyQt5.QtCore import \1'
except ImportError:
    from PyQt5.QtCore import \1\nexcept ImportError:\n    from PyQt5.QtCore import \1'
    content = re.sub(core_pattern, core_replacement, content, flags=re.DOTALL)
    
    # 3. Fix simpler nested try blocks for Core
    core_pattern2 = r'try:\s+try:\s+try:\s+from PyQt6\.QtCore import (.*?)except ImportError:.*?except ImportError:.*?except ImportError:'
    content = re.sub(core_pattern2, core_replacement, content, flags=re.DOTALL)
    
    # 4. Fix even simpler nested try blocks for Core
    core_pattern3 = r'try:\s+try:\s+from PyQt6\.QtCore import (.*?)except ImportError:.*?except ImportError:'
    content = re.sub(core_pattern3, core_replacement, content, flags=re.DOTALL)
    
    # 5. Fix Widget imports with nested try blocks
    widgets_pattern = r'try:\s+try:\s+try:\s+from PyQt6\.QtWidgets import \((.*?)\)except ImportError:.*?except ImportError:.*?except ImportError:'
    widgets_replacement = r'try:\n    try:
    from PyQt6.QtWidgets import (\n        \1\n    )\nexcept ImportError:\n    from PyQt5.QtWidgets import (\n        \1\n    )'
except ImportError:
    from PyQt5.QtWidgets import (\n        \1\n    )\nexcept ImportError:\n    from PyQt5.QtWidgets import (\n        \1\n    )'
    content = re.sub(widgets_pattern, widgets_replacement, content, flags=re.DOTALL)
    
    # 6. Fix simpler Widget imports with nested try blocks
    widgets_pattern2 = r'try:\s+try:\s+from PyQt6\.QtWidgets import \((.*?)\)except ImportError:.*?except ImportError:'
    content = re.sub(widgets_pattern2, widgets_replacement, content, flags=re.DOTALL)
    
    # 7. Fix even simpler Widget imports
    widgets_pattern3 = r'try:\s+from PyQt6\.QtWidgets import \((.*?)\)except ImportError:\s+from PyQt5\.QtWidgets import \((.*?)\)except ImportError:\s+from PyQt5\.QtWidgets import \(')
    content = re.sub(widgets_pattern3, r'try:\n    try:
    from PyQt6.QtWidgets import (\n        \1\n    )\nexcept ImportError:\n    from PyQt5.QtWidgets import (\n', content, flags=re.DOTALL))
except ImportError:
    from PyQt5.QtWidgets import (\n        \1\n    )\nexcept ImportError:\n    from PyQt5.QtWidgets import (\n', content, flags=re.DOTALL))
    
    # 8. Fix Gui imports with nested try blocks
    gui_pattern = r'try:\s+try:\s+try:\s+from PyQt6\.QtGui import (.*?)except ImportError:.*?except ImportError:.*?except ImportError:'
    gui_replacement = r'try:\n    try:
    from PyQt6.QtGui import \1\nexcept ImportError:\n    from PyQt5.QtGui import \1'
except ImportError:
    from PyQt5.QtGui import \1\nexcept ImportError:\n    from PyQt5.QtGui import \1'
    content = re.sub(gui_pattern, gui_replacement, content, flags=re.DOTALL)
    
    # 9. Fix simpler Gui imports with nested try blocks
    gui_pattern2 = r'try:\s+try:\s+from PyQt6\.QtGui import (.*?)except ImportError:.*?except ImportError:'
    content = re.sub(gui_pattern2, gui_replacement, content, flags=re.DOTALL)
    
    # 10. Fix unterminated method docstrings
    content = re.sub(r'        """"\n(.+?)\n        """"\n', r'        """\n\1\n        """\n', content, flags=re.DOTALL)
    
    # 11. Fix unterminated method docstrings (another case)
    content = re.sub(r'        """"\n(.+?)\n        """\n', r'        """\n\1\n        """\n', content, flags=re.DOTALL)"
    
    # 12. Fix spacing in indented blocks within try-except
    content = re.sub(r'try:\n\s+from PyQt6', r'try:\n    from PyQt6', content)
    content = re.sub(r'except ImportError:\n\s+from PyQt5', r'except ImportError:\n    from PyQt5', content)
    
    # 13. Fix QDesktopServices imports at the end of methods
    content = re.sub()
        r'    try:\s+from PyQt6\.QtGui import QDesktopServices\nexcept ImportError:\s+from PyQt5\.QtGui import QDesktopServices\nexcept ImportError:',
        r'    try:\n        try:
    from PyQt6.QtGui import QDesktopServices\n    except ImportError:\n        from PyQt5.QtGui import QDesktopServices',
except ImportError:
    from PyQt5.QtGui import QDesktopServices\n    except ImportError:\n        from PyQt5.QtGui import QDesktopServices',
        content
    )
    
    # Check if we made any changes
    if content != original_content:
        # Write the fixed content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed issues in {file_path}")
        fixed_count += 1
    else:
        print(f"No issues found in {file_path}")

print(f"\nFixed {fixed_count} files in the UI module.")
