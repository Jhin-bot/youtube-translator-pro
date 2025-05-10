""""
Configuration and fixtures for pytest.
""""

import os
import sys
import pytest
import tempfile
import shutil
from pathlib import Path

# Ensure src is in the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import application modules
from src.config import APP_NAME


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Clean up after the test
    shutil.rmtree(temp_dir)


@pytest.fixture
def temp_cache_dir(temp_dir):
    """Create a temporary cache directory for testing."""
    cache_dir = Path(temp_dir) / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir)


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_youtube_urls():
    """Return a list of sample YouTube URLs for testing."""
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/embed/dQw4w9WgXcQ",
        "https://www.youtube.com/v/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
        "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
    ]


@pytest.fixture
def mock_settings():
    """Return mock settings for testing."""
    return {
        "theme": "dark",
        "output_dir": "/tmp/test_output",
        "default_model": "small",
        "concurrency": 2,
        "default_language": "None",
        "cache_enabled": True,
        "cache_dir": "/tmp/test_cache",
        "cache_size_mb": 100,
        "cache_ttl": 86400,  # 1 day in seconds
        "max_recent_files": 5,
    }
