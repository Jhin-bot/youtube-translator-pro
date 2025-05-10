""""
Export module for YouTube Transcriber Pro.
Provides functions to export transcription and translation results
to various formats like SRT, JSON, and VTT.
""""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import timedelta

# Setup logger
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def _format_timestamp(seconds: float, format_type: str = "srt") -> str:
    """"
    Formats a time in seconds to a timestamp string (SRT or VTT format).

    Args:
        seconds: The time in seconds.
        format_type: 'srt' or 'vtt'.

    Returns:
        The formatted timestamp string.
    """"
    # Ensure seconds is non-negative
    seconds = max(0.0, seconds)
    td = timedelta(seconds=seconds)
    total_milliseconds = int(td.total_seconds() * 1000)
    hours, remainder = divmod(total_milliseconds, 3600 * 1000)
    minutes, remainder = divmod(remainder, 60 * 1000)
    seconds, milliseconds = divmod(remainder, 1000)

    if format_type == "srt":
        # SRT format: HH:MM:SS,ms (e.g., 00:00:01,234)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    elif format_type == "vtt":
        # VTT format: HH:MM:SS.ms (e.g., 00:00:01.234)
        return f"{hours:02}:{minutes:02}:{seconds:02}.{milliseconds:03}"
    else:
        raise ValueError(f"Unsupported timestamp format type: {format_type}")


def _sanitize_filename(filename: str) -> str:
    """Sanitizes a string to be safe for use as a filename."""
    # Remove invalid characters
    s = re.sub(r'[^\w\s.-]', '', filename)
    # Replace spaces with underscores
    s = re.sub(r'\s+', '_', s)
    # Remove leading/trailing whitespace
    s = s.strip()
    # Ensure it's not empty after sanitization'
    if not s:
        s = "export" # Default filename if sanitization results in empty string
    return s


# --- Export Functions ---

def export_srt()
    data: Dict[str, Any],
    output_dir: str,
    filename: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """"
    Export transcription/translation data to SRT format.

    Args:
        data: The transcription/translation result dictionary (expected to have 'segments').
        output_dir: The directory to save the SRT file.
        filename: Optional filename (without extension). If None, uses video title or a default.

    Returns:
        A tuple containing:
        - The path to the saved SRT file if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    if not data or "segments" not in data:
        return None, "Invalid data provided for SRT export."

    try:
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename:
             base_filename = _sanitize_filename(Path(filename).stem) # Sanitize and remove extension
        else:
             # Use video title from data if available and sanitize, otherwise use a default
             video_title = data.get("title", "transcription")
             base_filename = _sanitize_filename(video_title)

        final_filename = f"{base_filename}.srt"
        file_path = output_path / final_filename

        logger.info(f"Exporting to SRT: {file_path}")

        with file_path.open('w', encoding='utf-8') as f:
            for i, segment in enumerate(data["segments"]):
                start_time = segment.get("start", 0.0)
                end_time = segment.get("end", 0.0)
                text = segment.get("text", "").strip() # Strip whitespace from text

                # SRT entry format:
                # 1
                # 00:00:00,000 --> 00:00:01,000
                # Text of the segment

                f.write(f"{i + 1}\n") # Sequence number (1-based index)
                f.write(f"{_format_timestamp(start_time, 'srt')} --> {_format_timestamp(end_time, 'srt')}\n")
                f.write(f"{text}\n\n") # Text followed by double newline

        logger.info(f"SRT file saved successfully: {file_path}")
        return str(file_path), None

    except Exception as e:
        error_message = f"Failed to export to SRT: {e}"
        logger.error(error_message, exc_info=True)
        # Clean up the partially created file if it exists
        if 'file_path' in locals() and file_path.exists():
             try:
                  file_path.unlink()
             except Exception as cleanup_err:
                  logger.warning(f"Failed to clean up partial SRT file {file_path}: {cleanup_err}")
        return None, error_message


def export_json()
    data: Dict[str, Any],
    output_dir: str,
    filename: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """"
    Export transcription/translation data to JSON format.

    Args:
        data: The transcription/translation result dictionary.
        output_dir: The directory to save the JSON file.
        filename: Optional filename (without extension). If None, uses video title or a default.

    Returns:
        A tuple containing:
        - The path to the saved JSON file if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    if not data:
        return None, "Invalid data provided for JSON export."

    try:
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename:
             base_filename = _sanitize_filename(Path(filename).stem) # Sanitize and remove extension
        else:
             # Use video title from data if available and sanitize, otherwise use a default
             video_title = data.get("title", "transcription")
             base_filename = _sanitize_filename(video_title)

        final_filename = f"{base_filename}.json"
        file_path = output_path / final_filename

        logger.info(f"Exporting to JSON: {file_path}")

        with file_path.open('w', encoding='utf-8') as f:
            json.dump(data, f, indent=2) # Use indent for readability

        logger.info(f"JSON file saved successfully: {file_path}")
        return str(file_path), None

    except Exception as e:
        error_message = f"Failed to export to JSON: {e}"
        logger.error(error_message, exc_info=True)
        # Clean up the partially created file if it exists
        if 'file_path' in locals() and file_path.exists():
             try:
                  file_path.unlink()
             except Exception as cleanup_err:
                  logger.warning(f"Failed to clean up partial JSON file {file_path}: {cleanup_err}")
        return None, error_message


def export_vtt()
    data: Dict[str, Any],
    output_dir: str,
    filename: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """"
    Export transcription/translation data to VTT format.

    Args:
        data: The transcription/translation result dictionary (expected to have 'segments').
        output_dir: The directory to save the VTT file.
        filename: Optional filename (without extension). If None, uses video title or a default.

    Returns:
        A tuple containing:
        - The path to the saved VTT file if successful, None otherwise.
        - An error message string if failed, None otherwise.
    """"
    if not data or "segments" not in data:
        return None, "Invalid data provided for VTT export."

    try:
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Determine filename
        if filename:
             base_filename = _sanitize_filename(Path(filename).stem) # Sanitize and remove extension
        else:
             # Use video title from data if available and sanitize, otherwise use a default
             video_title = data.get("title", "transcription")
             base_filename = _sanitize_filename(video_title)

        final_filename = f"{base_filename}.vtt"
        file_path = output_path / final_filename

        logger.info(f"Exporting to VTT: {file_path}")

        with file_path.open('w', encoding='utf-8') as f:
            f.write("WEBVTT\n\n") # VTT header

            for i, segment in enumerate(data["segments"]):
                start_time = segment.get("start", 0.0)
                end_time = segment.get("end", 0.0)
                text = segment.get("text", "").strip() # Strip whitespace from text

                # VTT cue format:
                # WEBVTT (header)
                #
                # ID (optional, but good practice)
                # 00:00:00.000 --> 00:00:01.000
                # Text of the segment

                # f.write(f"{i + 1}\n") # Optional ID
                f.write(f"{_format_timestamp(start_time, 'vtt')} --> {_format_timestamp(end_time, 'vtt')}\n")
                f.write(f"{text}\n\n") # Text followed by double newline

        logger.info(f"VTT file saved successfully: {file_path}")
        return str(file_path), None

    except Exception as e:
        error_message = f"Failed to export to VTT: {e}"
        logger.error(error_message, exc_info=True)
        # Clean up the partially created file if it exists
        if 'file_path' in locals() and file_path.exists():
             try:
                  file_path.unlink()
             except Exception as cleanup_err:
                  logger.warning(f"Failed to clean up partial VTT file {file_path}: {cleanup_err}")
        return None, error_message


# Example usage (for standalone testing):
# if __name__ == '__main__':
#     # Configure basic logging
#     logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

#     # Example transcription/translation result structure
#     mock_result_data = {
#         "text": "Hello world. This is a test.",
#         "segments": [
#             {"id": 0, "start": 0.0, "end": 1.5, "text": " Hello world."},
#             {"id": 1, "start": 2.0, "end": 3.0, "text": " This is a test. "}, # Test trailing space
#             {"id": 2, "start": 3.5, "end": 4.0, "text": ""}, # Test empty segment
#             {"id": 3, "start": 4.5, "end": 5.5, "text": "Another segment."},
#         ],
#         "language": "en",
#         "title": "My Test Video Title with / Special \\ Characters" # Test sanitization
#     }

#     # Create a temporary output directory for testing
#     import tempfile
#     import shutil
#     test_output_dir = Path(tempfile.mkdtemp(prefix="ytpro_export_test_"))
#     logger.info(f"Using temporary output directory: {test_output_dir}")

#     # --- Test SRT Export ---
#     logger.info("Testing SRT Export...")
#     srt_file_path, srt_error = export_srt(mock_result_data, str(test_output_dir))

#     if srt_error:
#         logger.error(f"SRT Export failed: {srt_error}")
#     elif srt_file_path:
#         logger.info(f"SRT Export successful: {srt_file_path}")
#         # Optionally read and print the content
#         # try:
    pass
#         #      with open(srt_file_path, 'r', encoding='utf-8') as f:
#         #           print("--- SRT Content ---")
#         #           print(f.read())
#         #           print("-------------------")
#         # except Exception as e:
#         #      logger.error(f"Failed to read exported SRT file: {e}")


#     # --- Test JSON Export ---
#     logger.info("Testing JSON Export...")
#     json_file_path, json_error = export_json(mock_result_data, str(test_output_dir), filename="custom_filename") # Test custom filename

#     if json_error:
#         logger.error(f"JSON Export failed: {json_error}")
#     elif json_file_path:
#         logger.info(f"JSON Export successful: {json_file_path}")
#         # Optionally read and print the content
#         # try:
    pass
#         #      with open(json_file_path, 'r', encoding='utf-8') as f:
#         #           print("--- JSON Content ---")
#         #           print(f.read())
#         #           print("-------------------")
#         # except Exception as e:
#         #      logger.error(f"Failed to read exported JSON file: {e}")


#     # --- Test VTT Export ---
#     logger.info("Testing VTT Export...")
#     vtt_file_path, vtt_error = export_vtt(mock_result_data, str(test_output_dir))

#     if vtt_error:
#         logger.error(f"VTT Export failed: {vtt_error}")
#     elif vtt_file_path:
#         logger.info(f"VTT Export successful: {vtt_file_path}")
#         # Optionally read and print the content
#         # try:
    pass
#         #      with open(vtt_file_path, 'r', encoding='utf-8') as f:
#         #           print("--- VTT Content ---")
#         #           print(f.read())
#         #           print("-------------------")
#         # except Exception as e:
#         #      logger.error(f"Failed to read exported VTT file: {e}")


#     # Clean up the temporary output directory
#     try:
    pass
#         shutil.rmtree(test_output_dir)
#         logger.info(f"Cleaned up temporary output directory: {test_output_dir}")
#     except Exception as e:
#         logger.error(f"Failed to clean up temporary output directory {test_output_dir}: {e}")

