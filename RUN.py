#!/usr/bin/env python3
"""
Oh OPUS - First Run Bootstrap
Sets up virtual environment, installs dependencies, and launches the app.
"""

import sys
import os
import subprocess
from pathlib import Path
import platform


def is_in_venv() -> bool:
    """Check if running inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def get_venv_python() -> Path:
    """Get path to Python executable in virtual environment."""
    venv_path = Path(".venv")
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"→ {description}...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"✗ Failed: {result.stderr}")
            return False
        print(f"✓ {description} complete")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Bootstrap the Oh OPUS application."""
    print("=" * 60)
    print("Oh OPUS - First Run Setup")
    print("=" * 60)
    
    if is_in_venv():
        print("✓ Already running in virtual environment")
        print("→ Launching Oh OPUS...")
        subprocess.run([sys.executable, "main.py"])
        return
    
    # Create virtual environment
    venv_path = Path(".venv")
    if not venv_path.exists():
        print("→ Creating virtual environment...")
        subprocess.run([sys.executable, "-m", "venv", ".venv"])
        print("✓ Virtual environment created")
    else:
        print("✓ Virtual environment exists")
    
    vpy = get_venv_python()
    if not vpy.exists():
        print(f"✗ Virtual environment Python not found: {vpy}")
        sys.exit(1)
    
    # Upgrade pip and install dependencies
    steps = [
        ([str(vpy), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"],
         "Upgrading pip, setuptools, and wheel"),
        ([str(vpy), "-m", "pip", "install", "-r", "requirements.txt"],
         "Installing dependencies"),
    ]
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            print("\n✗ Setup failed. Please check the error messages above.")
            sys.exit(1)
    
    # Validate imports
    print("→ Validating imports...")
    test_imports = "import librosa, mutagen, PIL, matplotlib, numpy, scipy, soundfile"
    result = subprocess.run(
        [str(vpy), "-c", test_imports],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"✗ Import validation failed: {result.stderr}")
        print("\nPlease ensure all dependencies are properly installed.")
        sys.exit(1)
    print("✓ All imports validated")
    
    # Launch main application
    print("\n" + "=" * 60)
    print("✓ Setup complete! Launching Oh OPUS...")
    print("=" * 60)
    
    subprocess.run([str(vpy), "main.py"])
    
    print("\n" + "=" * 60)
    print("Next time, activate the virtual environment and run:")
    if platform.system() == "Windows":
        print("  .venv\\Scripts\\activate")
    else:
        print("  source .venv/bin/activate")
    print("  python main.py")
    print("=" * 60)


if __name__ == "__main__":
    main()