"""
Export utilities for YouTube Translator Pro.
Handles exporting transcriptions to various formats.
"""

import os
import json
import logging
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

# Logger setup
logger = logging.getLogger(__name__)

def export_transcription(
    transcription_result: Dict[str, Any],
    output_dir: Union[str, Path],
    format_name: str,
    base_filename: str,
    video_info: Optional[Dict[str, Any]] = None
) -> Optional[Path]:
    """
    Export a transcription result to the specified format.
    
    Args:
        transcription_result: The transcription result dictionary
        output_dir: Directory to save the exported file
        format_name: Format to export to (srt, txt, vtt, json, csv)
        base_filename: Base filename without extension
        video_info: Optional video information for metadata
        
    Returns:
        Path to the exported file, or None if export failed
    """
    try:
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Clean format name (lowercase and remove any dots)
        format_name = format_name.lower().replace('.', '')
        
        # Generate full output path
        output_file = output_path / f"{base_filename}.{format_name}"
        
        # Choose the appropriate export function
        if format_name == 'srt':
            _export_srt(transcription_result, output_file)
        elif format_name == 'txt':
            _export_txt(transcription_result, output_file)
        elif format_name == 'vtt':
            _export_vtt(transcription_result, output_file)
        elif format_name == 'json':
            _export_json(transcription_result, output_file, video_info)
        elif format_name == 'csv':
            _export_csv(transcription_result, output_file)
        else:
            logger.warning(f"Unsupported export format: {format_name}")
            return None
        
        logger.info(f"Exported transcription to {output_file}")
        return output_file
    
    except Exception as e:
        logger.error(f"Error exporting transcription to {format_name}: {e}")
        return None


def _export_srt(transcription_result: Dict[str, Any], output_file: Path):
    """
    Export transcription to SRT subtitle format.
    
    Args:
        transcription_result: The transcription result dictionary
        output_file: Path to save the SRT file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        segments = transcription_result.get('segments', [])
        
        for i, segment in enumerate(segments):
            # Get segment data
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            # Format timestamps (HH:MM:SS,mmm)
            start_time = _format_timestamp(start, ',')
            end_time = _format_timestamp(end, ',')
            
            # Write SRT entry
            f.write(f"{i+1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")


def _export_vtt(transcription_result: Dict[str, Any], output_file: Path):
    """
    Export transcription to WebVTT subtitle format.
    
    Args:
        transcription_result: The transcription result dictionary
        output_file: Path to save the VTT file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Write WebVTT header
        f.write("WEBVTT\n\n")
        
        segments = transcription_result.get('segments', [])
        
        for i, segment in enumerate(segments):
            # Get segment data
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            # Format timestamps (HH:MM:SS.mmm)
            start_time = _format_timestamp(start, '.')
            end_time = _format_timestamp(end, '.')
            
            # Write VTT entry
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{text}\n\n")


def _export_txt(transcription_result: Dict[str, Any], output_file: Path):
    """
    Export transcription to plain text format.
    
    Args:
        transcription_result: The transcription result dictionary
        output_file: Path to save the text file
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Add the full text if available
        full_text = transcription_result.get('text', '')
        if full_text:
            f.write(f"{full_text.strip()}\n\n")
            f.write("--- Transcript with Timestamps ---\n\n")
        
        # Add each segment with timestamp
        segments = transcription_result.get('segments', [])
        
        for segment in segments:
            # Get segment data
            start = segment.get('start', 0)
            text = segment.get('text', '').strip()
            
            # Format timestamp (MM:SS)
            minutes = int(start // 60)
            seconds = int(start % 60)
            timestamp = f"[{minutes:02d}:{seconds:02d}]"
            
            # Write text with timestamp
            f.write(f"{timestamp} {text}\n")


def _export_json(transcription_result: Dict[str, Any], output_file: Path, video_info: Optional[Dict[str, Any]] = None):
    """
    Export transcription to JSON format.
    
    Args:
        transcription_result: The transcription result dictionary
        output_file: Path to save the JSON file
        video_info: Optional video information for metadata
    """
    # Create a complete result with metadata
    result = {
        'transcription': transcription_result,
        'metadata': {
            'timestamp': _get_current_timestamp(),
        }
    }
    
    # Add video info if available
    if video_info:
        result['video'] = video_info
    
    # Write JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)


def _export_csv(transcription_result: Dict[str, Any], output_file: Path):
    """
    Export transcription to CSV format.
    
    Args:
        transcription_result: The transcription result dictionary
        output_file: Path to save the CSV file
    """
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Write header
        writer.writerow(['Start', 'End', 'Text'])
        
        # Write segments
        segments = transcription_result.get('segments', [])
        
        for segment in segments:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()
            
            writer.writerow([start, end, text])


def _format_timestamp(seconds: float, separator: str = ',') -> str:
    """
    Format a timestamp in seconds to HH:MM:SS{separator}mmm format.
    
    Args:
        seconds: Time in seconds
        separator: Separator between seconds and milliseconds (comma for SRT, dot for VTT)
        
    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds_only = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{seconds_only:02d}{separator}{milliseconds:03d}"


def _get_current_timestamp() -> str:
    """
    Get the current timestamp in ISO format.
    
    Returns:
        Current timestamp string
    """
    from datetime import datetime
    return datetime.now().isoformat()
