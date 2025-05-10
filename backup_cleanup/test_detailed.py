""""
Detailed test script to debug the specific import issues in application_manager
""""
import os
import sys
import traceback

def test_module_import(module_name):
    try:
        print(f"\n==== Testing import of {module_name} ====")
        # Import the module with exec to get more control
        exec(f"import {module_name}")
        print(f"✓ Successfully imported {module_name}")
        return True
    except Exception as e:
        print(f"✗ Failed to import {module_name}: {e}")
        traceback.print_exc()
        return False

def trace_app_manager_classes():
    try:
        print("\n==== Detailed tracing of application_manager classes ====")
        
        # Try importing the module normally first
        print("Importing application_manager module...")
        import application_manager
        
        # If we get here, try accessing each class individually
        print("\nTesting ApplicationManager class...")
        try:
            from application_manager import ApplicationManager
            print("✓ ApplicationManager class imported successfully")
        except Exception as e:
            print(f"✗ Failed to import ApplicationManager: {e}")
            traceback.print_exc()
        
        return True
    except Exception as e:
        print(f"✗ Failed main trace: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # First test ui module
    test_module_import("ui")
    
    # Then test application_manager
    trace_app_manager_classes()
