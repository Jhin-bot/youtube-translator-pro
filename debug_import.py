"""
Debug script to identify import issues
"""
import sys
import importlib
import traceback

def test_import():
    try:
        print("Importing application_manager...")
        import application_manager
        print("Successfully imported application_manager")
        return True
    except Exception as e:
        print(f"Error importing application_manager: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_import()
