"""Opusenc encoding engine implementation."""

from pathlib import Path
from typing import Optional, Callable
import subprocess
import re

from .base import EncodingEngine


class OpusencEngine(EncodingEngine):
    """Opusenc encoding engine."""
    
    def encode(
        self,
        input_path: Path,
        output_path: Path,
        bitrate: int,
        vbr: bool = True,
        application: str = "audio",
        progress_callback: Optional[Callable[[float], None]] = None,
        **kwargs
    ) -> bool:
        """Encode using opusenc."""
        
        # Build opusenc command
        cmd = [
            self.binary_path or "opusenc",
            "--bitrate", str(bitrate),
        ]
        
        # VBR settings
        if vbr:
            cmd.append("--vbr")
        else:
            cmd.append("--hard-cbr")
        
        # Additional options
        if "complexity" in kwargs:
            cmd.extend(["--comp", str(kwargs["complexity"])])
        
        if "frame_size" in kwargs:
            cmd.extend(["--framesize", str(kwargs["frame_size"])])
        
        # Input and output
        cmd.extend([str(input_path), str(output_path)])
        
        # Run encoding
        # Note: opusenc doesn't provide granular progress, so we'll just run it
        return self._run_command(cmd, progress_callback=progress_callback)
    
    def get_duration(self, file_path: Path) -> float:
        """Get audio file duration."""
        # Use mutagen as fallback for opusenc
        try:
            from mutagen import File
            audio = File(str(file_path))
            if audio and audio.info:
                return audio.info.length
        except:
            pass
        return 0.0
    
    def is_available(self) -> bool:
        """Check if opusenc is available."""
        try:
            cmd = [self.binary_path or "opusenc", "--version"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return "opusenc" in result.stdout.lower()
        except:
            return False