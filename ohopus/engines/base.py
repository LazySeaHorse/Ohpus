"""Base engine interface for audio encoding."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import subprocess
import logging


class EncodingEngine(ABC):
    """Abstract base class for encoding engines."""
    
    def __init__(self, binary_path: Optional[str] = None):
        self.binary_path = binary_path
        self.process: Optional[subprocess.Popen] = None
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
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
        """
        Encode audio file to Opus.
        
        Args:
            input_path: Input audio file path
            output_path: Output Opus file path
            bitrate: Target bitrate in kbps
            vbr: Use variable bitrate
            application: Application mode (audio/voip/lowdelay)
            progress_callback: Callback for progress updates
            **kwargs: Additional engine-specific options
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def get_duration(self, file_path: Path) -> float:
        """Get audio file duration in seconds."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the engine is available."""
        pass
    
    def cancel(self):
        """Cancel the current encoding process."""
        if self.process:
            self.logger.info("Cancelling encoding process")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger.warning("Process didn't terminate, killing")
                self.process.kill()
            self.process = None
    
    def _run_command(
        self,
        cmd: list,
        progress_parser: Optional[Callable[[str], Optional[float]]] = None,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> bool:
        """
        Run encoding command with optional progress monitoring.
        
        Args:
            cmd: Command and arguments
            progress_parser: Function to parse progress from output
            progress_callback: Callback for progress updates
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.debug(f"Running command: {' '.join(cmd)}")
            
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Monitor progress if parser provided
            if progress_parser and progress_callback:
                for line in self.process.stdout:
                    progress = progress_parser(line)
                    if progress is not None:
                        progress_callback(progress)
            
            # Wait for completion
            stdout, stderr = self.process.communicate()
            
            if self.process.returncode != 0:
                self.logger.error(f"Encoding failed: {stderr}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.exception(f"Encoding error: {e}")
            return False
        finally:
            self.process = None