# YouTube Translator Pro - Developer Guide

This guide provides detailed information for developers working with the YouTube Translator Pro codebase.

## Project Architecture

YouTube Translator Pro follows a modular architecture designed for maintainability, extensibility, and testability. The main components are:

### Core Components

- **Application Manager**: Central coordinator that initializes components and manages application state
- **Batch Processor**: Handles the processing of multiple videos in batches, manages the worker thread pool

### Services

- **Transcription Service**: Manages audio transcription using OpenAI's Whisper models
- **Translation Service**: Handles translation of transcriptions to different languages

### UI Components

- **Main Window**: Primary application interface
- **URL Input Widget**: Component for entering and validating YouTube URLs
- **Batch Status Widget**: Displays status and progress of batch operations
- **Task List Widget**: Shows the list of processing tasks with their statuses
- **Control Panel Widget**: Provides controls for configuring transcription and translation options
- **Dialogs**: Various dialog boxes for settings, errors, etc.

### Utilities

- **YouTube Utils**: Functions for downloading and extracting information from YouTube videos
- **Export Utils**: Functions for exporting transcriptions to various formats
- **Cache Manager**: Advanced caching system for optimizing performance with LRU eviction policy
- **Update Manager**: Handles application updates
- **Error Handling**: Centralized error management system with custom exceptions and crash reporting
- **Performance Monitor**: Analyzes application performance to identify bottlenecks
- **Localization**: Internationalization support for multiple languages

## Code Organization

```
YouTube Translator Pro/
├── src/                      # Source code
│   ├── core/                 # Core application logic
│   │   ├── application_manager.py
│   │   └── batch_processor.py
│   ├── services/             # Services for external APIs
│   │   ├── transcription_service.py
│   │   └── translation_service.py
│   ├── ui/                   # User interface components
│   │   ├── main_window.py
│   │   ├── url_input_widget.py
│   │   ├── batch_status_widget.py
│   │   ├── task_list_widget.py
│   │   ├── control_panel_widget.py
│   │   ├── dialogs.py
│   │   └── styles.py
│   ├── utils/                # Utility modules
│   │   ├── youtube_utils.py
│   │   ├── export_utils.py
│   │   ├── cache_manager.py
│   │   ├── update_manager.py
│   │   └── error_handling.py
│   ├── __init__.py
│   ├── __main__.py
│   └── config.py
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_youtube_utils.py
│   └── test_cache_manager.py
├── resources/                # Application resources
├── docs/                     # Documentation
├── .github/                  # GitHub workflows and configuration
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── main.py                   # Application entry point
├── pyproject.toml            # Project configuration
├── README.md
└── requirements.txt          # Dependencies
```

## Development Workflow

### Setting Up Development Environment

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Install development dependencies: `pip install -e ".[dev]"`

### Running the Application

Run the application in development mode:

```bash
python main.py
```

Or as a module:

```bash
python -m src
```

### Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=src
```

### Linting and Type Checking

Format code with Black:

```bash
black src tests
```

Sort imports with isort:

```bash
isort src tests
```

Type checking with mypy:

```bash
mypy src
```

Lint with ruff:

```bash
ruff check src tests
```

## Core Components Details

### Application Manager

The `ApplicationManager` class is the central coordinator for the application. It:

- Initializes all application components
- Manages component communication through signals
- Handles application lifecycle events

```python
# Example: Application initialization
def initialize(self):
    """Initialize application components."""
    # Initialize services
    self.transcription_service = TranscriptionService()
    self.translation_service = TranslationService()
    
    # Initialize batch processor
    self.batch_processor = BatchProcessor(
        self.transcription_service,
        self.translation_service
    )
    
    # Connect signals
    self.connect_signals()
```

### Batch Processor

The `BatchProcessor` handles processing of multiple YouTube videos in batches. It:

- Manages a pool of worker threads
- Tracks task status and progress
- Handles task prioritization and errors

## Services

### Transcription Service

The `TranscriptionService` handles audio transcription using OpenAI's Whisper model. It:

- Manages model loading and caching
- Processes audio files to generate transcriptions
- Provides accurate timestamps for subtitles

### Translation Service

The `TranslationService` handles translation of transcriptions. It:

- Supports multiple translation engines
- Provides a unified interface for all translation methods
- Handles translation quality assurance

## Key Design Patterns

### Singleton Pattern

Used for managers that should have only one instance:

- `CacheManager`
- `ErrorHandler`

### Observer Pattern 

Used for components that need to be notified of changes:

- Qt signals and slots connect components without tight coupling

### Factory Pattern

Used for creating different implementations of interfaces:

- Translation engines

### Strategy Pattern

Used for interchangeable algorithms:

- Export formats
- Transcription models

## Error Handling

The application uses a centralized error handling system:

- Custom exception classes for different error types
- Automatic error logging and reporting
- Consistent user feedback for errors

## Multithreading

The application uses multithreading for performance:

- UI runs in the main thread
- Processing tasks run in worker threads
- Thread-safe communication via Qt signals and slots

## Caching Strategy

The application implements an intelligent caching system:

- Least Recently Used (LRU) eviction policy
- Time-based expiration
- Size-limited cache with automatic cleanup

## Contributing Guidelines

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings in Google style format

### Pull Request Process

1. Create a feature branch from `develop`
2. Make your changes
3. Add tests for your changes
4. Ensure all tests pass
5. Submit a pull request to `develop`

### Commit Message Format

Follow the conventional commits format:

```
feat: Add batch processing feature
fix: Resolve issue with YouTube URL validation
docs: Update developer documentation
test: Add tests for cache manager
chore: Update dependencies
```

## API Documentation

For detailed API documentation, see the individual module docstrings or generate API documentation with:

```bash
pdoc --html src
```
