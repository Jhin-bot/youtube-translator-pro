""""
Test script to debug application_manager import issues
""""
import sys
import traceback

def test_app_manager():
    try:
        print("Attempting to import application_manager...")
        from application_manager import ApplicationManager
        print("Successfully imported ApplicationManager class")
        return True
    except Exception as e:
        print(f"Failed to import ApplicationManager: {e}")
        traceback.print_exc()
        # Get more detailed error message
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
        for line in tb_lines:
            print(line, end="")
        return False

if __name__ == "__main__":
    test_app_manager()
