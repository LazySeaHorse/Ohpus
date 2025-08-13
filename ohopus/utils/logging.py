"""Logging configuration and utilities."""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """Colored console formatter."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        return super().format(record)


def setup_logging(
    log_file: Optional[Path] = None,
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
):
    """
    Setup application logging.
    
    Args:
        log_file: Path to log file
        console_level: Console log level
        file_level: File log level
    """
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    
    if sys.stdout.isatty():
        # Use colored formatter for terminal
        console_formatter = ColoredFormatter(
            '%(levelname)s - %(message)s'
        )
    else:
        console_formatter = logging.Formatter(
            '%(levelname)-8s - %(message)s'
        )
    
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(file_level)
            
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
        except Exception as e:
            logger.warning(f"Failed to setup file logging: {e}")
    
    # Suppress some noisy loggers
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)