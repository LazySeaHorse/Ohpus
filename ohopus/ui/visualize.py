"""Audio visualization using librosa."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
import logging

try:
    import librosa
    import librosa.display
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logging.warning("librosa not available for visualization")


class VisualizationWindow:
    """Audio visualization window."""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Audio Visualization")
        self.window.geometry("800x600")
        
        if not LIBROSA_AVAILABLE:
            self._show_error()
            return
        
        self._setup_ui()
        self.audio_data = None
        self.sample_rate = None
    
    def _show_error(self):
        """Show error message if librosa is not available."""
        label = ttk.Label(
            self.window,
            text="Visualization requires librosa. Please install it.",
            font=('Arial', 12)
        )
        label.pack(expand=True)
    
    def _setup_ui(self):
        """Setup the visualization UI."""
        # Control frame
        control_frame = ttk.Frame(self.window, padding="10")
        control_frame.pack(side=tk.TOP, fill=tk.X)
        
        ttk.Button(
            control_frame,
            text="Load Audio File",
            command=self._load_audio
        ).pack(side=tk.LEFT, padx=5)
        
        self.viz_type = tk.StringVar(value="spectrogram")
        ttk.Combobox(
            control_frame,
            textvariable=self.viz_type,
            values=["spectrogram", "mel_spectrogram", "waveform", "histogram"],
            state="readonly",
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            control_frame,
            text="Update",
            command=self._update_visualization
        ).pack(side=tk.LEFT, padx=5)
        
        # Info label
        self.info_label = ttk.Label(control_frame, text="No file loaded")
        self.info_label.pack(side=tk.LEFT, padx=20)
        
        # Canvas frame
        canvas_frame = ttk.Frame(self.window)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create matplotlib figure
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.figure, master=canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def _load_audio(self):
        """Load an audio file for visualization."""
        filetypes = [
            ("Audio files", "*.mp3 *.opus *.ogg *.flac *.wav *.m4a"),
            ("All files", "*.*")
        ]
        
        filename = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=filetypes
        )
        
        if not filename:
            return
        
        try:
            self.audio_data, self.sample_rate = load_preview(
                filename,
                duration=30,
                sr=22050,
                mono=True
            )
            
            # Update info
            duration = len(self.audio_data) / self.sample_rate
            self.info_label.config(
                text=f"{Path(filename).name} | {self.sample_rate}Hz | {duration:.1f}s"
            )
            
            # Show initial visualization
            self._update_visualization()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audio:\n{str(e)}")
    
    def _update_visualization(self):
        """Update the visualization based on selected type."""
        if self.audio_data is None:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        viz_type = self.viz_type.get()
        
        try:
            if viz_type == "waveform":
                self._plot_waveform(ax)
            elif viz_type == "spectrogram":
                self._plot_spectrogram(ax)
            elif viz_type == "mel_spectrogram":
                self._plot_mel_spectrogram(ax)
            elif viz_type == "histogram":
                self._plot_histogram(ax)
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            logging.exception("Visualization failed")
            messagebox.showerror("Error", f"Visualization failed:\n{str(e)}")
    
    def _plot_waveform(self, ax):
        """Plot audio waveform."""
        time = np.arange(len(self.audio_data)) / self.sample_rate
        ax.plot(time, self.audio_data, linewidth=0.5)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Amplitude")
        ax.set_title("Waveform")
        ax.grid(True, alpha=0.3)
    
    def _plot_spectrogram(self, ax):
        """Plot spectrogram."""
        D = librosa.stft(self.audio_data)
        S_db = librosa.amplitude_to_db(np.abs(D), ref=np.max)
        
        img = librosa.display.specshow(
            S_db,
            sr=self.sample_rate,
            x_axis='time',
            y_axis='hz',
            ax=ax,
            cmap='viridis'
        )
        ax.set_title("Spectrogram")
        self.figure.colorbar(img, ax=ax, format='%+2.0f dB')
    
    def _plot_mel_spectrogram(self, ax):
        """Plot mel spectrogram."""
        S_db = mel_spectrogram(self.audio_data, self.sample_rate)
        
        img = librosa.display.specshow(
            S_db,
            sr=self.sample_rate,
            x_axis='time',
            y_axis='mel',
            ax=ax,
            cmap='viridis'
        )
        ax.set_title("Mel Spectrogram")
        self.figure.colorbar(img, ax=ax, format='%+2.0f dB')
    
    def _plot_histogram(self, ax):
        """Plot amplitude histogram."""
        bins, counts = amplitude_histogram(self.audio_data)
        ax.bar(bins[:-1], counts, width=np.diff(bins), alpha=0.7)
        ax.set_xlabel("Amplitude")
        ax.set_ylabel("Count")
        ax.set_title("Amplitude Distribution")
        ax.grid(True, alpha=0.3)


def load_preview(
    path: str,
    duration: float = 20.0,
    sr: int = 22050,
    mono: bool = True
) -> Tuple[np.ndarray, int]:
    """
    Load audio file for preview.
    
    Args:
        path: Path to audio file
        duration: Max duration to load in seconds
        sr: Sample rate
        mono: Convert to mono
    
    Returns:
        Tuple of (audio_data, sample_rate)
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError("librosa is required for audio visualization")
    
    y, sr = librosa.load(
        path,
        sr=sr,
        mono=mono,
        duration=duration
    )
    
    return y, sr


def amplitude_histogram(y: np.ndarray, bins: int = 50) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate amplitude histogram.
    
    Args:
        y: Audio signal
        bins: Number of histogram bins
    
    Returns:
        Tuple of (bin_edges, counts)
    """
    counts, bins = np.histogram(y, bins=bins)
    return bins, counts


def mel_spectrogram(y: np.ndarray, sr: int) -> np.ndarray:
    """
    Calculate mel spectrogram.
    
    Args:
        y: Audio signal
        sr: Sample rate
    
    Returns:
        Mel spectrogram in dB
    """
    if not LIBROSA_AVAILABLE:
        raise ImportError("librosa is required for mel spectrogram")
    
    S = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=128)
    S_db = librosa.power_to_db(S, ref=np.max)
    return S_db