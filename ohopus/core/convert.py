"""Conversion orchestration and job management."""

import logging
import queue
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from pathlib import Path
from typing import List, Optional, Dict, Any
import time

from ..engines.base import EncodingEngine
from ..engines.ffmpeg_engine import FFmpegEngine
from ..engines.opusenc_engine import OpusencEngine
from ..tagging.tags import TagHandler
from .settings import Settings
from .discovery import BinaryDiscovery


logger = logging.getLogger(__name__)


class ConversionJob:
    """Single conversion job."""
    
    def __init__(
        self,
        source_path: Path,
        dest_path: Path,
        settings: Settings
    ):
        self.source_path = source_path
        self.dest_path = dest_path
        self.settings = settings
        self.progress = 0.0
        self.status = "pending"
        self.error: Optional[str] = None


class ConversionManager:
    """Manage batch conversion process."""
    
    def __init__(self, settings: Settings, discovery: BinaryDiscovery):
        self.settings = settings
        self.discovery = discovery
        self.is_running = False
        self.is_paused = False
        self.should_cancel = False
        
        self.jobs: List[ConversionJob] = []
        self.active_engines: List[EncodingEngine] = []
        self.executor: Optional[ThreadPoolExecutor] = None
        
        self.converted_count = 0
        self.skipped_count = 0
        self.error_count = 0
    
    def convert_batch(self, message_queue: queue.Queue):
        """
        Convert batch of MP3 files to Opus.
        
        Args:
            message_queue: Queue for sending progress updates to UI
        """
        self.is_running = True
        self.should_cancel = False
        self.converted_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
        try:
            # Discover MP3 files
            message_queue.put(("log", {
                "message": "Scanning for MP3 files...",
                "level": "info"
            }))
            
            self.jobs = self._discover_files()
            total_jobs = len(self.jobs)
            
            if total_jobs == 0:
                message_queue.put(("log", {
                    "message": "No MP3 files found in source directory",
                    "level": "warning"
                }))
                return
            
            message_queue.put(("log", {
                "message": f"Found {total_jobs} MP3 files to convert",
                "level": "info"
            }))
            
            # Create thread pool
            max_workers = min(self.settings.max_threads, total_jobs)
            self.executor = ThreadPoolExecutor(max_workers=max_workers)
            
            # Process jobs
            futures: Dict[Future, ConversionJob] = {}
            
            for i, job in enumerate(self.jobs):
                if self.should_cancel:
                    break
                
                # Wait if paused
                while self.is_paused and not self.should_cancel:
                    time.sleep(0.1)
                
                # Check if should skip
                if self._should_skip(job):
                    self.skipped_count += 1
                    job.status = "skipped"
                    message_queue.put(("log", {
                        "message": f"Skipped: {job.source_path.name}",
                        "level": "info"
                    }))
                    continue
                
                # Submit job
                future = self.executor.submit(
                    self._process_job,
                    job,
                    message_queue
                )
                futures[future] = job
                
                # Update overall progress
                completed = self.converted_count + self.skipped_count + self.error_count
                progress = completed / total_jobs
                message_queue.put(("progress", {
                    "overall": progress,
                    "current": 0,
                    "file": job.source_path.name
                }))
            
            # Wait for completion
            for future in futures:
                if self.should_cancel:
                    future.cancel()
                else:
                    try:
                        future.result()
                    except Exception as e:
                        logger.exception(f"Job failed: {e}")
                        self.error_count += 1
            
            # Send completion message
            message_queue.put(("complete", {
                "converted": self.converted_count,
                "skipped": self.skipped_count,
                "errors": self.error_count
            }))
            
        except Exception as e:
            logger.exception(f"Batch conversion failed: {e}")
            message_queue.put(("error", {
                "message": f"Batch conversion failed: {str(e)}"
            }))
        
        finally:
            self.is_running = False
            if self.executor:
                self.executor.shutdown(wait=False)
                self.executor = None
    
    def _discover_files(self) -> List[ConversionJob]:
        """Discover MP3 files in source directory."""
        jobs = []
        source_dir = Path(self.settings.source_folder)
        dest_dir = Path(self.settings.dest_folder)
        
        for mp3_path in source_dir.rglob("*.mp3"):
            # Calculate destination path
            rel_path = mp3_path.relative_to(source_dir)
            opus_path = dest_dir / rel_path.with_suffix(".opus")
            
            job = ConversionJob(mp3_path, opus_path, self.settings)
            jobs.append(job)
        
        return jobs
    
    def _should_skip(self, job: ConversionJob) -> bool:
        """Check if job should be skipped."""
        if not self.settings.skip_existing:
            return False
        
        if job.dest_path.exists():
            # Could add additional checks here (size, date, etc.)
            return True
        
        return False
    
    def _process_job(
        self,
        job: ConversionJob,
        message_queue: queue.Queue
    ):
        """Process a single conversion job."""
        try:
            # Log start
            message_queue.put(("log", {
                "message": f"Converting: {job.source_path.name}",
                "level": "info"
            }))
            
            # Create output directory
            job.dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get engine
            engine = self._create_engine()
            self.active_engines.append(engine)
            
            # Check for genre-based bitrate boost
            bitrate = self._get_adjusted_bitrate(job)
            
            # Progress callback
            def progress_callback(progress: float):
                job.progress = progress
                message_queue.put(("progress", {
                    "overall": self._calculate_overall_progress(),
                    "current": progress,
                    "file": job.source_path.name
                }))
            
            # Encode
            success = engine.encode(
                job.source_path,
                job.dest_path,
                bitrate=bitrate,
                vbr=self.settings.vbr,
                application=self.settings.application_mode,
                progress_callback=progress_callback,
                complexity=self.settings.complexity,
                frame_size=self.settings.frame_size
            )
            
            if not success:
                raise Exception("Encoding failed")
            
            # Copy tags
            TagHandler.copy_tags(job.source_path, job.dest_path)
            
            # Apply ReplayGain if enabled
            if self.settings.replaygain_mode != "off":
                self._apply_replaygain(job.dest_path)
            
            # Success
            self.converted_count += 1
            job.status = "completed"
            
            message_queue.put(("log", {
                "message": f"Completed: {job.dest_path.name}",
                "level": "success"
            }))
            
        except Exception as e:
            logger.exception(f"Job failed: {job.source_path}")
            self.error_count += 1
            job.status = "error"
            job.error = str(e)
            
            message_queue.put(("log", {
                "message": f"Failed: {job.source_path.name} - {str(e)}",
                "level": "error"
            }))
        
        finally:
            if engine in self.active_engines:
                self.active_engines.remove(engine)
    
    def _create_engine(self) -> EncodingEngine:
        """Create encoding engine based on settings."""
        if self.settings.engine == "opusenc":
            return OpusencEngine(self.discovery.opusenc_path)
        else:
            return FFmpegEngine(self.discovery.ffmpeg_path)
    
    def _get_adjusted_bitrate(self, job: ConversionJob) -> int:
        """Get bitrate, potentially adjusted for genre."""
        bitrate = self.settings.bitrate
        
        if not self.settings.genre_bitrate_boost:
            return bitrate
        
        # Check genre tag
        try:
            from mutagen import File
            audio = File(str(job.source_path))
            if audio and audio.tags:
                genre = str(audio.tags.get('TCON', '')).lower()
                
                # Boost for complex genres
                complex_genres = ['classical', 'edm', 'electronic', 'metal', 'jazz']
                for g in complex_genres:
                    if g in genre:
                        # Boost by 25%
                        return min(int(bitrate * 1.25), 320)
        except:
            pass
        
        return bitrate
    
    def _apply_replaygain(self, opus_path: Path):
        """Apply ReplayGain to Opus file."""
        if not self.discovery.opusgain_path:
            return
        
        try:
            import subprocess
            
            cmd = [self.discovery.opusgain_path]
            
            if self.settings.replaygain_mode == "track":
                cmd.append("--track")
            elif self.settings.replaygain_mode == "album":
                cmd.append("--album")
            
            cmd.append(str(opus_path))
            
            subprocess.run(cmd, capture_output=True, check=True)
            
        except Exception as e:
            logger.warning(f"ReplayGain failed: {e}")
    
    def _calculate_overall_progress(self) -> float:
        """Calculate overall conversion progress."""
        if not self.jobs:
            return 0.0
        
        completed = self.converted_count + self.skipped_count + self.error_count
        in_progress = sum(job.progress for job in self.jobs if job.status == "processing")
        
        return (completed + in_progress) / len(self.jobs)
    
    def pause(self):
        """Pause conversion."""
        self.is_paused = True
    
    def resume(self):
        """Resume conversion."""
        self.is_paused = False
    
    def cancel(self):
        """Cancel conversion."""
        self.should_cancel = True
        
        # Cancel active engines
        for engine in self.active_engines:
            engine.cancel()
        
        # Shutdown executor
        if self.executor:
            self.executor.shutdown(wait=False)