"""Progress tracking and time utilities."""

import re
import time
from typing import Optional, Tuple
from datetime import timedelta


class ProgressParser:
    """Parse progress from encoder output."""
    
    # FFmpeg progress pattern
    FFMPEG_TIME_PATTERN = re.compile(r'out_time_us=(\d+)')
    FFMPEG_PROGRESS_PATTERN = re.compile(r'progress=(\w+)')
    
    # Opusenc doesn't provide detailed progress
    
    @classmethod
    def parse_ffmpeg_progress(cls, line: str, duration: float) -> Optional[float]:
        """
        Parse progress from FFmpeg output.
        
        Args:
            line: Output line from FFmpeg
            duration: Total duration in seconds
        
        Returns:
            Progress as float between 0 and 1, or None
        """
        if not duration:
            return None
        
        # Check for time progress
        match = cls.FFMPEG_TIME_PATTERN.search(line)
        if match:
            time_us = int(match.group(1))
            time_s = time_us / 1_000_000
            return min(time_s / duration, 1.0)
        
        # Check for end
        if cls.FFMPEG_PROGRESS_PATTERN.search(line):
            if 'progress=end' in line:
                return 1.0
        
        return None


class TimeEstimator:
    """Estimate remaining time for operations."""
    
    def __init__(self):
        self.start_time = None
        self.last_progress = 0.0
        self.last_update = None
        
    def start(self):
        """Start timing."""
        self.start_time = time.time()
        self.last_update = self.start_time
        self.last_progress = 0.0
    
    def update(self, progress: float) -> Tuple[timedelta, timedelta]:
        """
        Update progress and calculate times.
        
        Args:
            progress: Current progress (0-1)
        
        Returns:
            Tuple of (elapsed_time, estimated_remaining)
        """
        if not self.start_time:
            self.start()
        
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        if progress > 0 and progress < 1:
            # Estimate total time
            total_estimated = elapsed / progress
            remaining = total_estimated - elapsed
        else:
            remaining = 0
        
        self.last_progress = progress
        self.last_update = current_time
        
        return (
            timedelta(seconds=int(elapsed)),
            timedelta(seconds=int(remaining))
        )
    
    def get_rate(self, items_completed: int) -> float:
        """
        Get processing rate.
        
        Args:
            items_completed: Number of items completed
        
        Returns:
            Items per second
        """
        if not self.start_time:
            return 0.0
        
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            return items_completed / elapsed
        
        return 0.0


def format_time(seconds: float) -> str:
    """
    Format seconds into human-readable time.
    
    Args:
        seconds: Time in seconds
    
    Returns:
        Formatted string (e.g., "1h 23m 45s")
    """
    if seconds < 0:
        return "Unknown"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")
    
    return " ".join(parts)


def format_size(bytes_size: int) -> str:
    """
    Format byte size into human-readable string.
    
    Args:
        bytes_size: Size in bytes
    
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    
    return f"{bytes_size:.1f} PB"


def calculate_bitrate(file_size: int, duration: float) -> int:
    """
    Calculate actual bitrate from file size and duration.
    
    Args:
        file_size: File size in bytes
        duration: Duration in seconds
    
    Returns:
        Bitrate in kbps
    """
    if duration <= 0:
        return 0
    
    bits = file_size * 8
    kbps = (bits / duration) / 1000
    
    return int(kbps)