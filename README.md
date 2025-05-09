# YouTube Translator Pro

A professional desktop application for transcribing and translating YouTube videos using AI-powered speech recognition.

## Features

- **High-Quality Transcription**: Powered by OpenAI's Whisper models for accurate speech recognition
- **Multi-Language Translation**: Translate transcriptions into various languages
- **Batch Processing**: Queue multiple videos for efficient processing
- **Export Options**: Export transcriptions and translations in multiple formats (SRT, TXT, VTT, JSON, CSV)
- **Modern UI**: Clean and intuitive interface built with PyQt6
- **Advanced Caching**: Efficient resource management for improved performance

## Installation

### Requirements

- Python 3.9 or higher
- FFmpeg installed on your system (for audio processing)
- GPU recommended for faster transcription (but not required)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/your-username/youtube-translator-pro.git
   cd youtube-translator-pro
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run the application:
   ```
   python main.py
   ```

## Project Structure

The application follows a modular architecture:

```
YouTube Translator Pro/
├── src/                      # Source code
│   ├── core/                 # Core application logic
│   ├── services/             # Service components (transcription, translation)
│   ├── ui/                   # User interface components
│   └── utils/                # Utility functions
├── resources/                # Application resources
├── docs/                     # Documentation
└── tests/                    # Test suite
```

## Usage

1. Launch the application by running `python main.py`
2. Enter one or more YouTube URLs in the input field
3. Configure transcription and translation options in the control panel
4. Click "Start" to begin processing
5. Monitor progress in the batch status section
6. When complete, access your transcriptions/translations from the output directory

## Dependencies

- **PyQt6**: Modern UI framework
- **openai-whisper**: AI-powered speech recognition
- **pytube**: YouTube video downloading
- **ffmpeg-python**: Audio processing
- **torch**: Machine learning framework for Whisper models

## License

[MIT License](LICENSE)

## Acknowledgements

- [OpenAI Whisper](https://github.com/openai/whisper) for providing the transcription models
- [PyQt](https://www.riverbankcomputing.com/software/pyqt/) for the UI framework
- [pytube](https://github.com/pytube/pytube) for YouTube integration
