"""Custom UI widgets for Oh OPUS."""

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from typing import Optional, List

from ..core.settings import Settings
from ..core.discovery import BinaryDiscovery


class PathSelector(ttk.Frame):
    """Widget for selecting a folder path."""
    
    def __init__(self, parent, label: str, initial_path: Optional[str] = None):
        super().__init__(parent)
        
        self.label = ttk.Label(self, text=label)
        self.label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.path_var = tk.StringVar(value=initial_path or "")
        self.entry = ttk.Entry(self, textvariable=self.path_var, width=50)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.browse_btn = ttk.Button(
            self,
            text="Browse...",
            command=self._browse
        )
        self.browse_btn.pack(side=tk.LEFT)
    
    def _browse(self):
        """Open folder selection dialog."""
        folder = filedialog.askdirectory(
            title=self.label.cget("text"),
            initialdir=self.path_var.get() or Path.home()
        )
        if folder:
            self.path_var.set(folder)
    
    def get_path(self) -> str:
        """Get the selected path."""
        return self.path_var.get()
    
    def set_path(self, path: str):
        """Set the path."""
        self.path_var.set(path)


class ProgressPanel(ttk.Frame):
    """Progress display panel."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Overall progress
        ttk.Label(self, text="Overall Progress:").grid(row=0, column=0, sticky=tk.W)
        self.overall_progress = ttk.Progressbar(
            self,
            mode='determinate',
            length=400
        )
        self.overall_progress.grid(row=0, column=1, padx=10, sticky=(tk.W, tk.E))
        self.overall_label = ttk.Label(self, text="0%")
        self.overall_label.grid(row=0, column=2)
        
        # Current file progress
        ttk.Label(self, text="Current File:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.file_label = ttk.Label(self, text="", foreground="blue")
        self.file_label.grid(row=1, column=1, columnspan=2, sticky=tk.W, padx=10, pady=(5, 0))
        
        self.file_progress = ttk.Progressbar(
            self,
            mode='determinate',
            length=400
        )
        self.file_progress.grid(row=2, column=1, padx=10, sticky=(tk.W, tk.E))
        self.file_percent_label = ttk.Label(self, text="0%")
        self.file_percent_label.grid(row=2, column=2)
        
        # Configure grid
        self.columnconfigure(1, weight=1)
    
    def update_progress(self, overall: float, current: float):
        """Update progress bars."""
        self.overall_progress['value'] = overall * 100
        self.overall_label['text'] = f"{int(overall * 100)}%"
        
        self.file_progress['value'] = current * 100
        self.file_percent_label['text'] = f"{int(current * 100)}%"
    
    def set_current_file(self, filename: str):
        """Set current file being processed."""
        # Truncate long filenames
        if len(filename) > 60:
            filename = "..." + filename[-57:]
        self.file_label['text'] = filename
    
    def reset(self):
        """Reset progress bars."""
        self.overall_progress['value'] = 0
        self.overall_label['text'] = "0%"
        self.file_progress['value'] = 0
        self.file_percent_label['text'] = "0%"
        self.file_label['text'] = ""


class LogPanel(ttk.Frame):
    """Scrollable log display panel."""
    
    def __init__(self, parent):
        super().__init__(parent)
        
        # Create text widget with scrollbar
        self.text = tk.Text(
            self,
            height=10,
            wrap=tk.WORD,
            state=tk.DISABLED,
            background="black",
            foreground="white"
        )
        
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.text.yview)
        self.text['yscrollcommand'] = scrollbar.set
        
        self.text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Configure grid
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Configure text tags for colors
        self.text.tag_config("info", foreground="white")
        self.text.tag_config("warning", foreground="yellow")
        self.text.tag_config("error", foreground="red")
        self.text.tag_config("success", foreground="green")
    
    def log(self, message: str, level: str = "info"):
        """Add a log message."""
        self.text.config(state=tk.NORMAL)
        self.text.insert(tk.END, f"{message}\n", level)
        self.text.see(tk.END)
        self.text.config(state=tk.DISABLED)
    
    def clear(self):
        """Clear the log."""
        self.text.config(state=tk.NORMAL)
        self.text.delete(1.0, tk.END)
        self.text.config(state=tk.DISABLED)


class EngineSelector(ttk.Frame):
    """Engine selection widget."""
    
    def __init__(self, parent, initial: str, discovery: BinaryDiscovery):
        super().__init__(parent)
        self.discovery = discovery
        
        ttk.Label(self, text="Encoding Engine:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.engine_var = tk.StringVar(value=initial)
        
        # FFmpeg option
        self.ffmpeg_radio = ttk.Radiobutton(
            self,
            text="FFmpeg (libopus) - Recommended",
            variable=self.engine_var,
            value="ffmpeg"
        )
        self.ffmpeg_radio.pack(side=tk.LEFT, padx=5)
        
        # Opusenc option
        self.opusenc_radio = ttk.Radiobutton(
            self,
            text="opusenc",
            variable=self.engine_var,
            value="opusenc"
        )
        self.opusenc_radio.pack(side=tk.LEFT, padx=5)
        
        # Disable if binary not found
        if not discovery.ffmpeg_path:
            self.ffmpeg_radio.config(state=tk.DISABLED)
        if not discovery.opusenc_path:
            self.opusenc_radio.config(state=tk.DISABLED)
    
    def get_selected(self) -> str:
        """Get selected engine."""
        return self.engine_var.get()


class BitrateSelector(ttk.Frame):
    """Bitrate selection widget."""
    
    def __init__(self, parent, initial: int):
        super().__init__(parent)
        
        ttk.Label(self, text="Target Bitrate:").pack(side=tk.LEFT, padx=(0, 10))
        
        self.bitrate_var = tk.StringVar(value=f"{initial}k")
        self.combo = ttk.Combobox(
            self,
            textvariable=self.bitrate_var,
            values=["96k", "112k", "128k", "160k", "192k", "256k"],
            width=10,
            state="readonly"
        )
        self.combo.pack(side=tk.LEFT)
    
    def get_selected(self) -> int:
        """Get selected bitrate as integer."""
        return int(self.bitrate_var.get().rstrip('k'))


class AdvancedPanel(ttk.Frame):
    """Advanced settings panel."""
    
    def __init__(self, parent, settings: Settings, discovery: BinaryDiscovery):
        super().__init__(parent)
        self.settings = settings
        self.discovery = discovery
        
        # Create notebook for tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Binary paths tab
        paths_frame = ttk.Frame(notebook, padding="10")
        notebook.add(paths_frame, text="Binary Paths")
        self._create_paths_tab(paths_frame)
        
        # Encoding settings tab
        encoding_frame = ttk.Frame(notebook, padding="10")
        notebook.add(encoding_frame, text="Encoding")
        self._create_encoding_tab(encoding_frame)
        
        # Performance tab
        perf_frame = ttk.Frame(notebook, padding="10")
        notebook.add(perf_frame, text="Performance")
        self._create_performance_tab(perf_frame)
        
        # ReplayGain tab
        gain_frame = ttk.Frame(notebook, padding="10")
        notebook.add(gain_frame, text="ReplayGain")
        self._create_replaygain_tab(gain_frame)
    
    def _create_paths_tab(self, parent):
        """Create binary paths configuration tab."""
        row = 0
        
        # FFmpeg path
        ttk.Label(parent, text="FFmpeg:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.ffmpeg_var = tk.StringVar(value=self.discovery.ffmpeg_path or "")
        ffmpeg_entry = ttk.Entry(parent, textvariable=self.ffmpeg_var, width=50)
        ffmpeg_entry.grid(row=row, column=1, padx=10, sticky=(tk.W, tk.E))
        ttk.Button(
            parent,
            text="Browse",
            command=lambda: self._browse_binary(self.ffmpeg_var)
        ).grid(row=row, column=2)
        row += 1
        
        # Opusenc path
        ttk.Label(parent, text="opusenc:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.opusenc_var = tk.StringVar(value=self.discovery.opusenc_path or "")
        opusenc_entry = ttk.Entry(parent, textvariable=self.opusenc_var, width=50)
        opusenc_entry.grid(row=row, column=1, padx=10, sticky=(tk.W, tk.E))
        ttk.Button(
            parent,
            text="Browse",
            command=lambda: self._browse_binary(self.opusenc_var)
        ).grid(row=row, column=2)
        row += 1
        
        # Opusgain path
        ttk.Label(parent, text="opusgain:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.opusgain_var = tk.StringVar(value=self.discovery.opusgain_path or "")
        opusgain_entry = ttk.Entry(parent, textvariable=self.opusgain_var, width=50)
        opusgain_entry.grid(row=row, column=1, padx=10, sticky=(tk.W, tk.E))
        ttk.Button(
            parent,
            text="Browse",
            command=lambda: self._browse_binary(self.opusgain_var)
        ).grid(row=row, column=2)
        row += 1
        
        # Auto-detect button
        ttk.Button(
            parent,
            text="Auto-Detect All",
            command=self._auto_detect_binaries
        ).grid(row=row, column=1, pady=20)
        
        parent.columnconfigure(1, weight=1)
    
    def _create_encoding_tab(self, parent):
        """Create encoding settings tab."""
        row = 0
        
        # Application mode
        ttk.Label(parent, text="Application Mode:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.app_mode_var = tk.StringVar(value=self.settings.application_mode)
        app_combo = ttk.Combobox(
            parent,
            textvariable=self.app_mode_var,
            values=["audio", "voip", "lowdelay"],
            state="readonly",
            width=15
        )
        app_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        row += 1
        
        # Frame size
        ttk.Label(parent, text="Frame Size (ms):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.frame_size_var = tk.StringVar(value=str(self.settings.frame_size))
        frame_combo = ttk.Combobox(
            parent,
            textvariable=self.frame_size_var,
            values=["2.5", "5", "10", "20", "40", "60"],
            state="readonly",
            width=15
        )
        frame_combo.grid(row=row, column=1, sticky=tk.W, padx=10)
        row += 1
        
        # Complexity
        ttk.Label(parent, text="Complexity (0-10):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.complexity_var = tk.IntVar(value=self.settings.complexity)
        complexity_scale = ttk.Scale(
            parent,
            from_=0,
            to=10,
            orient=tk.HORIZONTAL,
            variable=self.complexity_var,
            length=200
        )
        complexity_scale.grid(row=row, column=1, sticky=tk.W, padx=10)
        complexity_label = ttk.Label(parent, textvariable=self.complexity_var)
        complexity_label.grid(row=row, column=2, padx=5)
        row += 1
        
        # CBR option
        self.cbr_var = tk.BooleanVar(value=not self.settings.vbr)
        cbr_check = ttk.Checkbutton(
            parent,
            text="Use Constant Bitrate (CBR)",
            variable=self.cbr_var
        )
        cbr_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=10)
        row += 1
        
        # Genre-based bitrate boost
        self.genre_boost_var = tk.BooleanVar(value=self.settings.genre_bitrate_boost)
        genre_check = ttk.Checkbutton(
            parent,
            text="Auto-boost bitrate for complex genres (Classical, EDM, Metal)",
            variable=self.genre_boost_var
        )
        genre_check.grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=5)
    
    def _create_performance_tab(self, parent):
        """Create performance settings tab."""
        row = 0
        
        # Thread count
        ttk.Label(parent, text="Max Parallel Encodes:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.threads_var = tk.IntVar(value=self.settings.max_threads)
        threads_scale = ttk.Scale(
            parent,
            from_=1,
            to=16,
            orient=tk.HORIZONTAL,
            variable=self.threads_var,
            length=200
        )
        threads_scale.grid(row=row, column=1, sticky=tk.W, padx=10)
        threads_label = ttk.Label(parent, textvariable=self.threads_var)
        threads_label.grid(row=row, column=2, padx=5)
        row += 1
        
        # Buffer size
        ttk.Label(parent, text="Buffer Size (KB):").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.buffer_var = tk.IntVar(value=self.settings.buffer_size // 1024)
        buffer_scale = ttk.Scale(
            parent,
            from_=64,
            to=1024,
            orient=tk.HORIZONTAL,
            variable=self.buffer_var,
            length=200
        )
        buffer_scale.grid(row=row, column=1, sticky=tk.W, padx=10)
        buffer_label = ttk.Label(parent, textvariable=self.buffer_var)
        buffer_label.grid(row=row, column=2, padx=5)
        row += 1
        
        # Overwrite mode
        ttk.Label(parent, text="File Handling:").grid(row=row, column=0, sticky=tk.W, pady=10)
        self.overwrite_var = tk.StringVar(value=self.settings.overwrite_mode)
        ttk.Radiobutton(
            parent,
            text="Skip existing files",
            variable=self.overwrite_var,
            value="skip"
        ).grid(row=row+1, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(
            parent,
            text="Overwrite existing files",
            variable=self.overwrite_var,
            value="overwrite"
        ).grid(row=row+2, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(
            parent,
            text="Rename new files",
            variable=self.overwrite_var,
            value="rename"
        ).grid(row=row+3, column=1, sticky=tk.W, padx=10)
    
    def _create_replaygain_tab(self, parent):
        """Create ReplayGain settings tab."""
        row = 0
        
        # ReplayGain mode
        ttk.Label(parent, text="ReplayGain Mode:").grid(row=row, column=0, sticky=tk.W, pady=5)
        self.gain_mode_var = tk.StringVar(value=self.settings.replaygain_mode)
        
        ttk.Radiobutton(
            parent,
            text="Disabled",
            variable=self.gain_mode_var,
            value="off"
        ).grid(row=row+1, column=1, sticky=tk.W, padx=10)
        
        ttk.Radiobutton(
            parent,
            text="Track Gain",
            variable=self.gain_mode_var,
            value="track"
        ).grid(row=row+2, column=1, sticky=tk.W, padx=10)
        
        ttk.Radiobutton(
            parent,
            text="Album Gain",
            variable=self.gain_mode_var,
            value="album"
        ).grid(row=row+3, column=1, sticky=tk.W, padx=10)
        
        row += 4
        
        # ReplayGain reference
        ttk.Label(parent, text="Reference Level (dB):").grid(row=row, column=0, sticky=tk.W, pady=10)
        self.gain_ref_var = tk.DoubleVar(value=self.settings.replaygain_reference)
        gain_entry = ttk.Entry(parent, textvariable=self.gain_ref_var, width=10)
        gain_entry.grid(row=row, column=1, sticky=tk.W, padx=10)
        
        row += 1
        
        # Note about opusgain requirement
        note_text = "Note: ReplayGain requires opusgain or loudgain to be installed."
        note_label = ttk.Label(parent, text=note_text, foreground="gray")
        note_label.grid(row=row, column=0, columnspan=2, pady=20)
    
    def _browse_binary(self, var: tk.StringVar):
        """Browse for a binary executable."""
        import platform
        
        filetypes = [("All files", "*")]
        if platform.system() == "Windows":
            filetypes.insert(0, ("Executable", "*.exe"))
        
        filename = filedialog.askopenfilename(
            title="Select Binary",
            filetypes=filetypes
        )
        if filename:
            var.set(filename)
    
    def _auto_detect_binaries(self):
        """Auto-detect all binaries."""
        self.discovery.discover_all()
        
        if self.discovery.ffmpeg_path:
            self.ffmpeg_var.set(self.discovery.ffmpeg_path)
        if self.discovery.opusenc_path:
            self.opusenc_var.set(self.discovery.opusenc_path)
        if self.discovery.opusgain_path:
            self.opusgain_var.set(self.discovery.opusgain_path)
    
    def save_settings(self):
        """Save settings from UI."""
        # Binary paths
        self.discovery.ffmpeg_path = self.ffmpeg_var.get() or None
        self.discovery.opusenc_path = self.opusenc_var.get() or None
        self.discovery.opusgain_path = self.opusgain_var.get() or None
        
        # Encoding settings
        self.settings.application_mode = self.app_mode_var.get()
        self.settings.frame_size = float(self.frame_size_var.get())
        self.settings.complexity = self.complexity_var.get()
        self.settings.vbr = not self.cbr_var.get()
        self.settings.genre_bitrate_boost = self.genre_boost_var.get()
        
        # Performance settings
        self.settings.max_threads = self.threads_var.get()
        self.settings.buffer_size = self.buffer_var.get() * 1024
        self.settings.overwrite_mode = self.overwrite_var.get()
        
        # ReplayGain settings
        self.settings.replaygain_mode = self.gain_mode_var.get()
        self.settings.replaygain_reference = self.gain_ref_var.get()
        
        # Save to disk
        self.settings.save()