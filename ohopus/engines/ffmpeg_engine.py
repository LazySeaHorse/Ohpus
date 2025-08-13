"""FFmpeg encoding engine implementation."""

from pathlib import Path
from typing import Optional, Callable
import subprocess
import re
import json

from .base import EncodingEngine


class FFmpegEngine(EncodingEngine):
    """FFmpeg/libopus encoding engine."""
    
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
        """Encode using FFmpeg with libopus codec."""
        
        # Build FFmpeg command
        cmd = [
            self.binary_path or "ffmpeg",
            "-i", str(input_path),
            "-c:a", "libopus",
            "-b:a", f"{bitrate}k",
        ]
        
        # VBR settings
        if vbr:
            cmd.extend(["-vbr", "on"])
        else:
            cmd.extend(["-vbr", "off"])
        
        # Application mode
        if application:
            cmd.extend(["-application", application])
        
        # Additional options
        if "frame_size" in kwargs:
            cmd.extend(["-frame_duration", str(kwargs["frame_size"])])
        
        if "complexity" in kwargs:
            cmd.extend(["-compression_level", str(kwargs["complexity"])])
        
        # Progress reporting
        if progress_callback:
            duration = self.get_duration(input_path)
            cmd.extend(["-progress", "pipe:1"])
        
        # Output file (overwrite)
        cmd.extend(["-y", str(output_path)])
        
        # Run encoding
        if progress_callback and duration:
            def parse_progress(line: str) -> Optional[float]:
                if line.startswith("out_time_us="):
                    time_us = int(line.split("=")[1])
                    time_s = time_us / 1_000_000
                    return min(time_s / duration, 1.0)
                return None
            
            return self._run_command(cmd, parse_progress, progress_callback)
        else:
            return self._run_command(cmd)
    
    def get_duration(self, file_path: Path) -> float:
        """Get audio file duration using ffprobe."""
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "json",
            str(file_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            data = json.loads(result.stdout)
            return float(data["format"]["duration"])
        except Exception as e:
            self.logger.warning(f"Failed to get duration: {e}")
            return 0.0
    
    def is_available(self) -> bool:
        """Check if FFmpeg with libopus is available."""
        try:
            cmd = [self.binary_path or "ffmpeg", "-codecs"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return "libopus" in result.stdout
        except:
            return False