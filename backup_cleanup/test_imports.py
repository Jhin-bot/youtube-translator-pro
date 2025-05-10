""""
Test script to debug import issues
""""
import sys
import traceback

def test_import(module_name):
    try:
        print(f"\n==== Attempting to import {module_name}... ====")
        __import__(module_name)
        print(f"✓ Successfully imported {module_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to import {module_name}: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # First test ui.py in isolation
    print("\n\n===== TESTING UI IMPORT =====")
    test_import("ui")
    
    # Test application_manager with detailed error handling
    print("\n\n===== TESTING APPLICATION MANAGER =====")
    try:
        from application_manager import ApplicationManager
        print("✓ Successfully imported ApplicationManager class")
    except Exception as e:
        print(f"✗ Failed to import ApplicationManager: {e}")
        traceback.print_exc()
