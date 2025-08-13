"""Binary discovery and path management."""

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Optional
import platform

from ..utils.paths import get_config_dir


logger = logging.getLogger(__name__)


class BinaryDiscovery:
    """Discover and manage external binary paths."""
    
    def __init__(self):
        self.ffmpeg_path: Optional[str] = None
        self.opusenc_path: Optional[str] = None
        self.opusgain_path: Optional[str] = None
        self.loudgain_path: Optional[str] = None
        
        self.config_file = get_config_dir() / "binaries.json"
        self.load_paths()
    
    def discover_all(self):
        """Discover all binaries."""
        self.ffmpeg_path = self._find_binary("ffmpeg")
        self.opusenc_path = self._find_binary("opusenc")
        self.opusgain_path = self._find_binary("opusgain")
        self.loudgain_path = self._find_binary("loudgain")
        
        self.save_paths()
    
    def _find_binary(self, name: str) -> Optional[str]:
        """Find a binary in the system PATH."""
        # Check if already set
        current = getattr(self, f"{name}_path", None)
        if current and Path(current).exists():
            return current
        
        # Try to find in PATH
        path = shutil.which(name)
        if path:
            logger.info(f"Found {name} at: {path}")
            return path
        
        # Platform-specific locations
        if platform.system() == "Windows":
            # Common Windows install locations
            common_paths = [
                Path("C:/Program Files/ffmpeg/bin"),
                Path("C:/Program Files (x86)/ffmpeg/bin"),
                Path("C:/ffmpeg/bin"),
                Path("C:/opus-tools"),
            ]
            
            for base_path in common_paths:
                exe_path = base_path / f"{name}.exe"
                if exe_path.exists():
                    logger.info(f"Found {name} at: {exe_path}")
                    return str(exe_path)
        
        elif platform.system() == "Darwin":
            # macOS with Homebrew
            brew_paths = [
                Path("/usr/local/bin"),
                Path("/opt/homebrew/bin"),
            ]
            
            for base_path in brew_paths:
                bin_path = base_path / name
                if bin_path.exists():
                    logger.info(f"Found {name} at: {bin_path}")
                    return str(bin_path)
        
        logger.warning(f"Could not find {name}")
        return None
    
    def verify_binary(self, path: str, expected_name: str) -> bool:
        """Verify that a binary path is valid."""
        try:
            binary_path = Path(path)
            if not binary_path.exists():
                return False
            
            # Try to run with version flag
            result = subprocess.run(
                [str(binary_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Check if expected name appears in output
            output = (result.stdout + result.stderr).lower()
            return expected_name.lower() in output
            
        except Exception as e:
            logger.warning(f"Failed to verify {path}: {e}")
            return False
    
    def set_binary_path(self, name: str, path: str) -> bool:
        """Manually set a binary path."""
        if self.verify_binary(path, name):
            setattr(self, f"{name}_path", path)
            self.save_paths()
            return True
        return False
    
    def load_paths(self):
        """Load saved binary paths."""
        try:
            if self.config_file.exists():
                import json
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                
                for key, value in data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                logger.info("Binary paths loaded")
        except Exception as e:
            logger.warning(f"Failed to load binary paths: {e}")
    
    def save_paths(self):
        """Save binary paths."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            data = {
                "ffmpeg_path": self.ffmpeg_path,
                "opusenc_path": self.opusenc_path,
                "opusgain_path": self.opusgain_path,
                "loudgain_path": self.loudgain_path,
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info("Binary paths saved")
            
        except Exception as e:
            logger.error(f"Failed to save binary paths: {e}")