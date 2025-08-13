"""Operating system detection and platform-specific utilities."""

import platform
import sys
import os
from typing import Tuple


def get_os_info() -> dict:
    """Get detailed OS information."""
    return {
        'system': platform.system(),
        'release': platform.release(),
        'version': platform.version(),
        'machine': platform.machine(),
        'processor': platform.processor(),
        'python_version': sys.version,
        'python_implementation': platform.python_implementation(),
    }


def is_windows() -> bool:
    """Check if running on Windows."""
    return platform.system() == 'Windows'


def is_macos() -> bool:
    """Check if running on macOS."""
    return platform.system() == 'Darwin'


def is_linux() -> bool:
    """Check if running on Linux."""
    return platform.system() == 'Linux'


def get_cpu_count() -> int:
    """Get number of CPU cores."""
    try:
        # Use os.cpu_count() for physical cores
        count = os.cpu_count()
        if count:
            return count
    except:
        pass
    
    # Fallback
    return 4


def supports_color() -> bool:
    """Check if terminal supports color output."""
    # Windows
    if is_windows():
        return (
            os.environ.get('ANSICON') is not None or
            os.environ.get('WT_SESSION') is not None or  # Windows Terminal
            'PYCHARM' in os.environ
        )
    
    # Unix-like
    return sys.stdout.isatty()


def get_default_threads() -> int:
    """Get recommended number of threads for encoding."""
    cpu_count = get_cpu_count()
    
    # Use about 75% of cores, min 1, max 8
    return max(1, min(int(cpu_count * 0.75), 8))


def get_temp_dir() -> str:
    """Get system temporary directory."""
    import tempfile
    return tempfile.gettempdir()