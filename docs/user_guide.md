# YouTube Translator Pro - User Guide

Welcome to YouTube Translator Pro! This guide will help you get started and make the most of this powerful tool for transcribing and translating YouTube videos.

## Table of Contents

1. [Installation](#installation)
2. [Getting Started](#getting-started)
3. [Basic Features](#basic-features)
4. [Advanced Features](#advanced-features)
5. [Settings](#settings)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)

## Installation

### System Requirements

- **Operating System**: Windows 10/11, macOS 10.14+, or Linux
- **Processor**: Multi-core CPU (recommended for faster transcription)
- **RAM**: 4GB minimum, 8GB+ recommended
- **Storage**: 500MB for the application, plus space for downloaded videos and transcripts
- **Internet Connection**: Required for downloading videos and updates

### Installation Steps

1. Download the latest version from our [website](https://www.youtubetranslatorpro.com/download) or [GitHub releases](https://github.com/youtube-translator-pro/youtube-translator-pro/releases)
2. Run the installer and follow the on-screen instructions
3. Launch the application after installation completes

### Installing from Source

For advanced users who want to install from source:

1. Ensure you have Python 3.9+ installed
2. Clone the repository: `git clone https://github.com/youtube-translator-pro/youtube-translator-pro.git`
3. Navigate to the directory: `cd youtube-translator-pro`
4. Install dependencies: `pip install -r requirements.txt`
5. Run the application: `python main.py`

## Getting Started

### First Launch

Upon first launch, YouTube Translator Pro will:

1. Check for required dependencies (like FFmpeg)
2. Initialize the configuration
3. Set up default directories for downloads and exports

### Downloading Your First Video

1. Launch YouTube Translator Pro
2. Paste a YouTube URL into the URL input field
3. Select your desired transcription and translation options
4. Click "Add to Queue" to add the video to the processing queue
5. Click "Start Processing" to begin

### Understanding the Interface

![YouTube Translator Pro Interface](./images/app_interface.png)

The main interface consists of:

1. **URL Input**: Enter YouTube URLs here
2. **Control Panel**: Configure transcription and translation options
3. **Task List**: View and manage the list of videos in the queue
4. **Batch Status**: Monitor the overall progress of the current batch
5. **Menu Bar**: Access additional options and features

## Basic Features

### Transcribing Videos

1. Enter a YouTube URL in the URL input field
2. Select a transcription model (small, medium, or large) from the dropdown menu
   - Smaller models are faster but less accurate
   - Larger models are more accurate but slower
3. Click "Add to Queue"
4. Click "Start Processing"

### Translating Transcriptions

1. Follow the steps for transcribing videos
2. Select a target language from the "Translation Language" dropdown
3. The video will be transcribed and then translated to the selected language

### Exporting Results

Export your transcriptions and translations in multiple formats:

1. Select a completed task in the task list
2. Click the "Export" button
3. Choose from available formats:
   - **SRT**: Standard subtitle format compatible with most video players
   - **VTT**: Web-based subtitle format
   - **TXT**: Plain text format
   - **JSON**: Structured data format with all information
   - **CSV**: Spreadsheet compatible format

## Advanced Features

### Batch Processing

Process multiple videos at once:

1. Enter multiple YouTube URLs (one per line) in the URL input field
2. Configure transcription and translation options
3. Click "Add All to Queue"
4. Click "Start Processing"

### Customizing Transcription

Adjust transcription settings for better results:

1. Click "Settings" in the menu bar
2. Navigate to the "Transcription" tab
3. Modify options such as:
   - **Model Size**: Balance between speed and accuracy
   - **Word-level timestamps**: Enable for precise word timing
   - **Language Detection**: Auto-detect or specify a language
   - **Confidence Threshold**: Filter out low-confidence segments

### Working with Playlists

Process entire YouTube playlists:

1. Enter a YouTube playlist URL in the URL input field
2. Select "Extract Videos from Playlist"
3. Choose which videos from the playlist to process
4. Configure transcription and translation options
5. Click "Add Selected to Queue"
6. Click "Start Processing"

## Settings

### General Settings

- **Theme**: Choose between light and dark themes
- **Output Directory**: Set default location for saved files
- **Auto-Update**: Enable/disable automatic updates
- **Concurrency**: Set how many videos can be processed simultaneously

### Transcription Settings

- **Default Model**: Set the default Whisper model size
- **Word-level Timestamps**: Enable for precise timing
- **Confidence Threshold**: Filter out low-confidence segments
- **Profanity Filter**: Enable to filter out profanity

### Translation Settings

- **Default Language**: Set your preferred target language
- **Translation Engine**: Choose between available translation engines
- **Preserve Formatting**: Maintain original formatting in translations

### Cache Settings

- **Enable Cache**: Toggle caching to improve performance
- **Cache Size**: Set maximum cache size
- **Clear Cache**: Remove all cached data

## Troubleshooting

### Common Issues

#### Video Download Failed

**Possible causes**:
- The video is private or restricted
- The video is age-restricted
- Network connection issues

**Solutions**:
1. Verify the video is publicly accessible
2. Check your internet connection
3. Try again later as temporary YouTube API issues may occur

#### Transcription Errors

**Possible causes**:
- Audio quality is poor
- Background noise or music
- Multiple speakers talking simultaneously

**Solutions**:
1. Try a larger transcription model for better accuracy
2. For videos with music, try enabling "Music Filter" in settings
3. For multiple speakers, enable "Speaker Diarization" if available

#### Application Crashes

**Possible causes**:
- Insufficient system resources
- Corrupted application files
- Conflicting software

**Solutions**:
1. Restart the application
2. Close other resource-intensive applications
3. Reinstall the application
4. Check the logs (Help > Open Logs Folder) for specific error messages

### Log Files

The application stores log files that can help diagnose issues:

1. Click "Help" in the menu bar
2. Select "Open Logs Folder"
3. The most recent log file will contain information about the latest application session

## FAQ

### General Questions

**Q: Is YouTube Translator Pro free?**  
A: Yes, YouTube Translator Pro is open-source and free to use. We welcome contributions to the project.

**Q: Does the application need internet access?**  
A: Yes, internet access is required to download videos from YouTube and check for updates.

**Q: Can I use this for commercial purposes?**  
A: Yes, the application is available under the MIT license, which allows commercial use.

### Technical Questions

**Q: Which transcription models are available?**  
A: YouTube Translator Pro uses OpenAI's Whisper models, including tiny, base, small, medium, and large.

**Q: What languages are supported for transcription?**  
A: Whisper supports transcription in 100+ languages. See the [full list](https://github.com/openai/whisper#available-models-and-languages) for details.

**Q: What languages are supported for translation?**  
A: The application supports translation to 10+ major languages including English, Spanish, French, German, Italian, Japanese, Korean, Portuguese, Russian, and Chinese.

**Q: Can I run this application offline?**  
A: Partially. You need internet access to download videos, but transcription and translation can be performed offline if you have the necessary models downloaded.

**Q: Where are my transcription files saved?**  
A: By default, files are saved to your "Documents/YouTube Translator Pro" folder. You can change this location in the Settings.

### Feature Questions

**Q: Can I edit transcriptions within the application?**  
A: Not in the current version, but we plan to add an editor in a future update.

**Q: Can I process videos from platforms other than YouTube?**  
A: The current version only supports YouTube. Support for other platforms may be added in future updates.

**Q: What's the maximum length of video I can process?**  
A: There's no hard limit, but longer videos require more time and system resources. For very long videos (1+ hours), we recommend using a larger model for better results.

## Getting Help

If you need additional assistance:

- Check our [online documentation](https://www.youtubetranslatorpro.com/docs)
- Visit our [GitHub repository](https://github.com/youtube-translator-pro/youtube-translator-pro)
- Submit issues on [GitHub Issues](https://github.com/youtube-translator-pro/youtube-translator-pro/issues)
- Contact us at support@youtubetranslatorpro.com
