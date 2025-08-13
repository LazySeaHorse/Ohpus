"""Main application window and UI coordination."""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
from pathlib import Path
from typing import Optional
import threading
import queue

from ..core.settings import Settings
from ..core.discovery import BinaryDiscovery
from ..core.convert import ConversionManager
from .widgets import (
    PathSelector, ProgressPanel, LogPanel, 
    AdvancedPanel, EngineSelector, BitrateSelector
)
from .visualize import VisualizationWindow


class OhOpusApp:
    """Main application window."""
    
    def __init__(self, settings: Settings, discovery: BinaryDiscovery):
        self.settings = settings
        self.discovery = discovery
        self.converter = ConversionManager(settings, discovery)
        
        self.root = tk.Tk()
        self.root.title("Oh OPUS - MP3 to Opus Converter")
        self.root.geometry("900x700")
        
        # Message queue for thread communication
        self.message_queue = queue.Queue()
        
        self._setup_ui()
        self._check_binaries()
        self._start_message_handler()
    
    def _setup_ui(self):
        """Setup the main UI layout."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        row = 0
        
        # Title
        title_label = ttk.Label(
            main_frame, 
            text="Oh OPUS Batch Converter",
            font=('Arial', 16, 'bold')
        )
        title_label.grid(row=row, column=0, pady=(0, 20))
        row += 1
        
        # Path selectors
        self.source_selector = PathSelector(
            main_frame, 
            "Source Folder (MP3s):",
            self.settings.source_folder
        )
        self.source_selector.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        self.dest_selector = PathSelector(
            main_frame,
            "Destination Folder:",
            self.settings.dest_folder
        )
        self.dest_selector.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=5)
        row += 1
        
        # Settings frame
        settings_frame = ttk.LabelFrame(main_frame, text="Conversion Settings", padding="10")
        settings_frame.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=10)
        settings_frame.columnconfigure(1, weight=1)
        row += 1
        
        # Engine selector
        self.engine_selector = EngineSelector(
            settings_frame,
            self.settings.engine,
            self.discovery
        )
        self.engine_selector.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Bitrate selector
        self.bitrate_selector = BitrateSelector(
            settings_frame,
            self.settings.bitrate
        )
        self.bitrate_selector.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Options
        self.skip_existing_var = tk.BooleanVar(value=self.settings.skip_existing)
        skip_cb = ttk.Checkbutton(
            settings_frame,
            text="Skip existing files",
            variable=self.skip_existing_var
        )
        skip_cb.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        self.vbr_var = tk.BooleanVar(value=self.settings.vbr)
        vbr_cb = ttk.Checkbutton(
            settings_frame,
            text="Variable bitrate (VBR)",
            variable=self.vbr_var
        )
        vbr_cb.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, pady=10)
        row += 1
        
        self.start_btn = ttk.Button(
            button_frame,
            text="Start Conversion",
            command=self._start_conversion,
            style='Accent.TButton'
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(
            button_frame,
            text="Pause",
            command=self._pause_conversion,
            state=tk.DISABLED
        )
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(
            button_frame,
            text="Cancel",
            command=self._cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Visualization",
            command=self._show_visualization
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            button_frame,
            text="Advanced",
            command=self._toggle_advanced
        ).pack(side=tk.LEFT, padx=5)
        
        # Progress panel
        self.progress_panel = ProgressPanel(main_frame)
        self.progress_panel.grid(row=row, column=0, sticky=(tk.W, tk.E), pady=10)
        row += 1
        
        # Log panel
        self.log_panel = LogPanel(main_frame)
        self.log_panel.grid(row=row, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_frame.rowconfigure(row, weight=1)
        row += 1
        
        # Advanced panel (initially hidden)
        self.advanced_panel = None
        self.advanced_window = None
    
    def _check_binaries(self):
        """Check for required binaries and show warning if missing."""
        missing = []
        
        if not self.discovery.ffmpeg_path:
            missing.append("FFmpeg")
        
        if self.settings.engine == "opusenc" and not self.discovery.opusenc_path:
            missing.append("opusenc")
        
        if missing:
            msg = f"Missing binaries: {', '.join(missing)}\n"
            msg += "Some features may be unavailable. Configure paths in Advanced settings."
            self.log_panel.log(msg, "warning")
    
    def _start_message_handler(self):
        """Start the message queue handler."""
        self._process_messages()
    
    def _process_messages(self):
        """Process messages from worker threads."""
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()
                
                if msg_type == "progress":
                    self.progress_panel.update_progress(data['overall'], data['current'])
                    if 'file' in data:
                        self.progress_panel.set_current_file(data['file'])
                
                elif msg_type == "log":
                    self.log_panel.log(data['message'], data.get('level', 'info'))
                
                elif msg_type == "complete":
                    self._on_conversion_complete(data)
                
                elif msg_type == "error":
                    messagebox.showerror("Conversion Error", data['message'])
        
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self._process_messages)
    
    def _start_conversion(self):
        """Start the batch conversion process."""
        # Update settings from UI
        self.settings.source_folder = self.source_selector.get_path()
        self.settings.dest_folder = self.dest_selector.get_path()
        self.settings.engine = self.engine_selector.get_selected()
        self.settings.bitrate = self.bitrate_selector.get_selected()
        self.settings.skip_existing = self.skip_existing_var.get()
        self.settings.vbr = self.vbr_var.get()
        
        # Validate paths
        if not self.settings.source_folder or not Path(self.settings.source_folder).exists():
            messagebox.showerror("Error", "Please select a valid source folder")
            return
        
        if not self.settings.dest_folder:
            messagebox.showerror("Error", "Please select a destination folder")
            return
        
        # Update UI state
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.NORMAL)
        self.progress_panel.reset()
        
        # Start conversion in background thread
        thread = threading.Thread(
            target=self._run_conversion,
            daemon=True
        )
        thread.start()
    
    def _run_conversion(self):
        """Run the conversion process in a background thread."""
        try:
            self.converter.convert_batch(self.message_queue)
        except Exception as e:
            logging.exception("Conversion failed")
            self.message_queue.put(("error", {"message": str(e)}))
    
    def _pause_conversion(self):
        """Pause the conversion process."""
        if self.converter.is_paused:
            self.converter.resume()
            self.pause_btn.config(text="Pause")
            self.log_panel.log("Conversion resumed", "info")
        else:
            self.converter.pause()
            self.pause_btn.config(text="Resume")
            self.log_panel.log("Conversion paused", "info")
    
    def _cancel_conversion(self):
        """Cancel the conversion process."""
        if messagebox.askyesno("Confirm", "Cancel the conversion?"):
            self.converter.cancel()
            self.log_panel.log("Conversion cancelled", "warning")
            self._reset_ui_state()
    
    def _on_conversion_complete(self, data):
        """Handle conversion completion."""
        self._reset_ui_state()
        
        msg = f"Conversion complete!\n"
        msg += f"Files converted: {data['converted']}\n"
        msg += f"Files skipped: {data['skipped']}\n"
        msg += f"Errors: {data['errors']}"
        
        self.log_panel.log(msg, "success")
        messagebox.showinfo("Complete", msg)
    
    def _reset_ui_state(self):
        """Reset UI to idle state."""
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED, text="Pause")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def _show_visualization(self):
        """Show the visualization window."""
        viz_window = VisualizationWindow(self.root)
    
    def _toggle_advanced(self):
        """Toggle the advanced settings panel."""
        if self.advanced_window is None:
            self.advanced_window = tk.Toplevel(self.root)
            self.advanced_window.title("Advanced Settings")
            self.advanced_window.geometry("600x500")
            
            self.advanced_panel = AdvancedPanel(
                self.advanced_window,
                self.settings,
                self.discovery
            )
            self.advanced_panel.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self.advanced_window.protocol(
                "WM_DELETE_WINDOW",
                self._close_advanced
            )
        else:
            self.advanced_window.lift()
    
    def _close_advanced(self):
        """Close the advanced settings window."""
        if self.advanced_panel:
            self.advanced_panel.save_settings()
        self.advanced_window.destroy()
        self.advanced_window = None
        self.advanced_panel = None
    
    def run(self):
        """Start the application main loop."""
        self.root.mainloop()