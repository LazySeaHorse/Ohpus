# Oh OPUS

A cross-platform desktop application for batch converting MP3 files to Opus format with metadata preservation, album art embedding, and audio visualizations.

> [!NOTE]
> Coded to life with help from Claude 4.1 Opus (hehe. OPUS with Opus)

## Features

- **Batch Conversion**: Convert entire MP3 libraries to Opus format
- **Metadata Preservation**: Maintains ID3 tags, album art, and other metadata
- **Multiple Engines**: Choose between FFmpeg (libopus) or opusenc
- **Audio Visualizations**: View spectrograms and waveforms using librosa
- **Smart Settings**: Genre-based bitrate boosting for complex audio
- **ReplayGain Support**: Optional track/album gain normalization
- **Cross-Platform**: Works on Windows, macOS, and Linux

[![Ohpus-3.png](https://i.postimg.cc/SNc7JKrY/Ohpus-3.png)](https://postimg.cc/tYCVcp89)
[![Ohpus-2.png](https://i.postimg.cc/P54WQF0t/Ohpus-2.png)](https://postimg.cc/188V9M9T)
[![Ohpus-1.png](https://i.postimg.cc/2Smdvfcc/Ohpus-1.png)](https://postimg.cc/9r8q5sjZ)

## Quick Start

### First Run

Download the project files, then run RUN.py

   ```bash
   python RUN.py
   ```

   This will:
   - Create a virtual environment
   - Install all dependencies
   - Launch the application

## Requirements

- Python 3.8 or higher
- FFmpeg with libopus support (recommended)
- Optional: opus-tools for opusenc engine
- Optional: opusgain or loudgain for ReplayGain

## Installation

### Dependencies

The application will automatically install Python dependencies, but you'll need:

**FFmpeg** (recommended):
- Windows: Download from https://ffmpeg.org/download.html
- macOS: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg` or equivalent

**Opus Tools** (optional):
- Windows: Download from https://opus-codec.org/downloads/
- macOS: `brew install opus-tools`
- Linux: `sudo apt install opus-tools`

## Usage

1. **Select Source Folder**: Choose the root directory containing your MP3 files
2. **Select Destination Folder**: Choose where to save the converted Opus files
3. **Configure Settings**:
   - Encoding engine (FFmpeg or opusenc)
   - Target bitrate (96-256 kbps)
   - VBR (Variable Bitrate) on/off
4. **Start Conversion**: Click "Start Conversion" to begin batch processing

### Advanced Options

Access advanced settings by clicking the "Advanced" button:

- **Binary Paths**: Manually specify paths to FFmpeg, opusenc, and opusgain
- **Encoding Options**: Frame size, complexity, application mode
- **Performance**: Thread count, buffer size
- **ReplayGain**: Track or album normalization

## Features in Detail

### Metadata Handling

- Automatically maps ID3 tags to Vorbis comments
- Preserves album artwork as METADATA_BLOCK_PICTURE
- Maintains track/disc numbers with totals
- Supports multi-value tags (multiple artists, genres)

### Audio Visualization

Click "Visualization" to analyze audio files:
- Waveform display
- Spectrogram
- Mel spectrogram
- Amplitude histogram

### Resume-Friendly

- Skip existing files option
- Pause/resume conversion
- Cancel with proper cleanup

### Genre-Based Optimization

Automatically increases bitrate for complex genres:
- Classical
- Electronic/EDM
- Metal
- Jazz

## Configuration

Settings are saved in platform-specific locations:
- Windows: `%APPDATA%\OhOpus\`
- macOS: `~/Library/Application Support/OhOpus/`
- Linux: `~/.config/oh-opus/`

## Troubleshooting

### FFmpeg Not Found
- Install FFmpeg and ensure it's in your system PATH
- Or manually specify the path in Advanced settings

### Visualization Not Working
- Ensure librosa is installed: `pip install librosa`
- Check that audio file format is supported

### Conversion Errors
- Check the log panel for detailed error messages
- Ensure source files are valid MP3s
- Verify destination folder has write permissions

## License

MIT License - See LICENSE file for details

## Acknowledgments

- FFmpeg team for the excellent multimedia framework
- Opus codec developers for the superior audio codec
- librosa developers for audio analysis tools

## Alternatives

- fre:ac (Windows/macOS/Linux/FreeBSD): Open source, batch converter, Opus support, preserves tags, integrated tag editor with cover art, multi‑core, can convert whole libraries while keeping folder structure.
- foobar2000 (Windows/macOS): Extremely good batch converter with Opus (install the Free Encoder Pack). Great metadata handling; no analysis visuals.
