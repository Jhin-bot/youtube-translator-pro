""""
Script to fix the indentation and try-except blocks in the styles.py file.
""""

import re
import os

# Path to the styles.py file
styles_file = os.path.join('src', 'ui', 'styles.py')

# Read the original file
with open(styles_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix the imports at the top
fixed_content = re.sub()
    r'try:\s+try:\s+try:\s+from PyQt6\.QtCore import (.*?)except ImportError:.*?except ImportError:.*?except ImportError:',
    r'try:\n    try:
    from PyQt6.QtCore import \1\nexcept ImportError:',
except ImportError:
    from PyQt5.QtCore import \1\nexcept ImportError:',
    content,
    flags=re.DOTALL
)

# Fix all other try-except blocks
pattern = r'try:\s+try:\s+from PyQt(\d+)\.(.*?) import (.*?)except ImportError:.*?except ImportError:'
replacement = r'try:\n    from PyQt\1.\2 import \3\nexcept ImportError:'
fixed_content = re.sub(pattern, replacement, fixed_content, flags=re.DOTALL)

# Fix remaining nested try blocks
fixed_content = re.sub()
    r'(try:\s+)try:',
    r'\1',
    fixed_content
)

# Write the fixed content back to the file
with open(styles_file, 'w', encoding='utf-8') as f:
    f.write(fixed_content)

print(f"Fixed {styles_file} successfully!")
