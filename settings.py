"""
Application settings for YouTube Transcriber Pro.
Defines default settings and provides functions to load and save settings
from a JSON file.
"""

import os
import json
import logging
from typing import Dict, Any
from pathlib import Path # Added for Path object usage

# Setup logger
logger = logging.getLogger(__name__)

# Define the base directory for application data (e.g., logs, settings, cache)
# This is typically in the user's home directory, in a hidden folder specific to the app.
# Using QStandardPaths might be more robust for different OS, but Path.home() is a good start.
# APP_DATA_DIR = Path.home() / f".{APP_NAME.replace(' ', '_').lower()}" # Requires APP_NAME from ui
# For now, define a default fallback path
APP_DATA_DIR = Path(os.path.join(os.path.expanduser("~"), ".ytpro_app_data"))


# Default settings
DEFAULT_SETTINGS: Dict[str, Any] = {
    "theme": "dark",
    # Use APP_DATA_DIR for default output and cache directories
    "output_dir": str(Path.home() / "Downloads" / "YouTubeTranscriber"), # Default to Downloads
    "default_model": "small",
    "concurrency": 2,
    "default_language": "None", # Use "None" string for no translation
    "cache_enabled": True,
    "cache_dir": str(APP_DATA_DIR / "cache"), # Cache inside app data dir
    "cache_size_mb": 1000, # 1 GB default cache size
    "cache_ttl": 60 * 60 * 24 * 30,  # 30 days in seconds
    "max_recent_files": 20, # Number of recent files to track
    "update_config": { # Auto-update configuration
        "update_url": "https://api.github.com/repos/yourusername/YouTubeTranscriberPro/releases/latest", # Replace with your repo URL
        "timeout": 10,  # seconds
        "verify_ssl": True,
        "check_interval": 24,  # hours
        "auto_check": True,
        "retry_delay_hours": 6 # Delay after a failed update check before retrying
    },
    "keyboard_shortcuts": {}, # Store keyboard shortcut configurations here
    "max_retries": 3, # Default max retries for a failed task
    "retry_delay": 5.0, # Default initial retry delay in seconds
    "max_retry_delay": 60.0, # Default max retry delay in seconds
}

# Define the path to the settings file within the application data directory
SETTINGS_FILE = APP_DATA_DIR / "settings.json"


def load_settings() -> Dict[str, Any]:
    """
    Load application settings from the settings file.

    If the file does not exist or loading fails, return default settings.
    """
    # Ensure the application data directory exists
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if SETTINGS_FILE.exists():
            with SETTINGS_FILE.open('r', encoding='utf-8') as f:
                settings = json.load(f)
            logger.info(f"Settings loaded from {SETTINGS_FILE}")
            # Merge loaded settings with default settings to handle new settings in updates
            # Loaded settings override defaults
            merged_settings = DEFAULT_SETTINGS.copy()
            merged_settings.update(settings)
            return merged_settings
        else:
            logger.info(f"Settings file not found at {SETTINGS_FILE}. Using default settings.")
            return DEFAULT_SETTINGS.copy()
    except (json.JSONDecodeError, Exception) as e:
        logger.error(f"Error loading settings from {SETTINGS_FILE}: {str(e)}. Using default settings.", exc_info=True)
        # Optionally back up the corrupted settings file before returning defaults
        try:
            backup_path = SETTINGS_FILE.with_suffix(".json.bak")
            shutil.copy2(SETTINGS_FILE, backup_path)
            logger.warning(f"Backed up corrupted settings file to {backup_path}")
        except Exception as backup_err:
            logger.warning(f"Failed to back up corrupted settings file: {backup_err}")

        return DEFAULT_SETTINGS.copy()


def save_settings(settings: Dict[str, Any]) -> bool:
    """
    Save application settings to the settings file.

    Args:
        settings: The dictionary containing the settings to save.

    Returns:
        True if saving was successful, False otherwise.
    """
    # Ensure the application data directory exists
    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)

    try:
        # Save only settings that are different from the default settings
        # This prevents the settings file from growing unnecessarily with default values.
        settings_to_save = {
            key: value for key, value in settings.items()
            if key in DEFAULT_SETTINGS and value != DEFAULT_SETTINGS[key]
            # Special handling for nested dictionaries like update_config
            or (key == "update_config" and isinstance(value, dict) and value != DEFAULT_SETTINGS.get("update_config", {}))
            # Add similar checks for other nested structures if any
        }

        with SETTINGS_FILE.open('w', encoding='utf-8') as f:
            json.dump(settings_to_save, f, indent=2)
        logger.info(f"Settings saved to {SETTINGS_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving settings to {SETTINGS_FILE}: {str(e)}", exc_info=True)
        return False

# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     # Load settings
#     current_settings = load_settings()
#     logger.info(f"Loaded settings: {current_settings}")

#     # Modify settings
#     current_settings["theme"] = "light"
#     current_settings["concurrency"] = 4
#     current_settings["new_setting"] = "test_value" # Add a new setting

#     # Save settings
#     if save_settings(current_settings):
#         logger.info("Settings saved successfully.")
#     else:
#         logger.error("Failed to save settings.")

#     # Load settings again to verify
#     reloaded_settings = load_settings()
#     logger.info(f"Reloaded settings: {reloaded_settings}")

#     # Test loading with a corrupted file (simulate by writing invalid JSON)
#     # try:
#     #     with SETTINGS_FILE.open('w') as f:
#     #         f.write("{invalid json")
#     #     logger.warning("Simulated corrupted settings file.")
#     #     corrupted_load_settings = load_settings()
#     #     logger.info(f"Loaded settings after corruption: {corrupted_load_settings}")
#     # except Exception as e:
#     #      logger.error(f"Error simulating corruption or loading: {e}")

#     # Clean up the test settings file and directory if needed
#     # try:
#     #     if SETTINGS_FILE.exists():
#     #         SETTINGS_FILE.unlink()
#     #     # Clean up the parent directory if it's the test app data dir
#     #     if APP_DATA_DIR.exists() and APP_DATA_DIR.name == ".ytpro_app_data":
#     #          # Check if it's safe to remove (e.g., only contains settings.json and backup)
#     #          contents = list(APP_DATA_DIR.iterdir())
#     #          if all(c.name in ["settings.json", "settings.json.bak", "cache", "logs"] for c in contents): # Add other expected subdirs
#     #               # Check if cache and logs are empty or only contain metadata/logs
#     #               safe_to_remove_app_data = True
#     #               if (APP_DATA_DIR / "cache").exists():
#     #                    cache_contents = list((APP_DATA_DIR / "cache").iterdir())
#     #                    if any(c.suffix != ".json" for c in cache_contents): # Check for non-metadata files
#     #                         safe_to_remove_app_data = False
#     #               if (APP_DATA_DIR / "logs").exists():
#     #                    # Check if logs directory is empty or only contains log files
#     #                    pass # More complex check needed here

#     #               if safe_to_remove_app_data:
#     #                    shutil.rmtree(APP_DATA_DIR)
#     #                    logger.info(f"Cleaned up test app data directory: {APP_DATA_DIR}")

#     # except Exception as e:
#     #     logger.error(f"Error during test cleanup: {e}")

