"""Path utilities and helpers."""

from pathlib import Path
import platform
import os


def get_config_dir() -> Path:
    """Get the configuration directory for the application."""
    
    system = platform.system()
    
    if system == "Windows":
        # Use AppData on Windows
        base = Path(os.environ.get('APPDATA', Path.home() / 'AppData' / 'Roaming'))
        config_dir = base / 'OhOpus'
    
    elif system == "Darwin":
        # Use ~/Library/Application Support on macOS
        config_dir = Path.home() / 'Library' / 'Application Support' / 'OhOpus'
    
    else:
        # Use XDG config directory on Linux/Unix
        xdg_config = os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config')
        config_dir = Path(xdg_config) / 'oh-opus'
    
    # Create directory if it doesn't exist
    config_dir.mkdir(parents=True, exist_ok=True)
    
    return config_dir


def get_cache_dir() -> Path:
    """Get the cache directory for the application."""
    
    system = platform.system()
    
    if system == "Windows":
        base = Path(os.environ.get('LOCALAPPDATA', Path.home() / 'AppData' / 'Local'))
        cache_dir = base / 'OhOpus' / 'Cache'
    
    elif system == "Darwin":
        cache_dir = Path.home() / 'Library' / 'Caches' / 'OhOpus'
    
    else:
        xdg_cache = os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')
        cache_dir = Path(xdg_cache) / 'oh-opus'
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    return cache_dir


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename for safe filesystem usage.
    
    Args:
        filename: Original filename
    
    Returns:
        Sanitized filename
    """
    # Replace invalid characters
    invalid_chars = '<>:"/\\|?*' if platform.system() == "Windows" else '/'
    
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove control characters
    filename = ''.join(char for char in filename if ord(char) >= 32)
    
    # Limit length (leave room for extension)
    max_length = 200
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        filename = name[:max_length - len(ext)] + ext
    
    return filename.strip()


def ensure_unique_path(path: Path) -> Path:
    """
    Ensure a path is unique by adding a number suffix if needed.
    
    Args:
        path: Original path
    
    Returns:
        Unique path
    """
    if not path.exists():
        return path
    
    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    
    counter = 1
    while True:
        new_path = parent / f"{stem}_{counter}{suffix}"
        if not new_path.exists():
            return new_path
        counter += 1