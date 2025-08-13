#!/usr/bin/env python3
"""
Oh OPUS - Main Entry Point
Cross-platform batch MP3 to Opus converter with Tkinter GUI
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ohopus.ui.app import OhOpusApp
from ohopus.core.settings import Settings
from ohopus.core.discovery import BinaryDiscovery
from ohopus.utils.paths import get_config_dir
from ohopus.utils.logging import setup_logging


def main():
    """Main entry point for Oh OPUS."""
    # Setup logging
    log_file = get_config_dir() / "oh_opus.log"
    setup_logging(log_file)
    logging.info("Starting Oh OPUS")
    
    # Load settings
    settings = Settings()
    settings.load()
    
    # Discover binaries
    discovery = BinaryDiscovery()
    discovery.discover_all()
    
    # Create and run application
    app = OhOpusApp(settings, discovery)
    app.run()
    
    # Save settings on exit
    settings.save()
    logging.info("Oh OPUS closed")


if __name__ == "__main__":
    main()