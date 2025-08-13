"""Application settings management."""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict, field

from ..utils.paths import get_config_dir


logger = logging.getLogger(__name__)


@dataclass
class Settings:
    """Application settings."""
    
    # Paths
    source_folder: str = ""
    dest_folder: str = ""
    
    # Encoding
    engine: str = "ffmpeg"
    bitrate: int = 160
    vbr: bool = True
    application_mode: str = "audio"
    frame_size: float = 20.0
    complexity: int = 10
    
    # Behavior
    skip_existing: bool = True
    overwrite_mode: str = "skip"  # skip, overwrite, rename
    genre_bitrate_boost: bool = True
    
    # Performance
    max_threads: int = 4
    buffer_size: int = 262144  # 256KB
    
    # ReplayGain
    replaygain_mode: str = "off"  # off, track, album
    replaygain_reference: float = -18.0
    
    # Binary paths (stored separately in discovery)
    
    def __post_init__(self):
        self.config_file = get_config_dir() / "settings.json"
    
    def load(self) -> bool:
        """Load settings from disk."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                # Update settings
                for key, value in data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                logger.info(f"Settings loaded from {self.config_file}")
                return True
            
        except Exception as e:
            logger.warning(f"Failed to load settings: {e}")
        
        return False
    
    def save(self) -> bool:
        """Save settings to disk."""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to dict (excluding config_file itself)
            data = asdict(self)
            data.pop('config_file', None)
            
            # Save to file
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Settings saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False
    
    def reset(self):
        """Reset settings to defaults."""
        default = Settings()
        for key, value in asdict(default).items():
            if key != 'config_file' and hasattr(self, key):
                setattr(self, key, value)