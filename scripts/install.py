#!/usr/bin/env python3
"""Setup script for GhostLink.

This script ensures a suitable Python version, creates a local
virtual environment, installs the project in editable mode and
verifies that the GhostLink command line tools are available.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MIN_PYTHON = (3, 8)


def check_python_version() -> None:
    if sys.version_info < MIN_PYTHON:
        ver = ".".join(str(v) for v in MIN_PYTHON)
        print(f"Python {ver}+ is required (found {sys.version.split()[0]}).", file=sys.stderr)
        raise SystemExit(1)


def venv_paths(root: Path) -> tuple[Path, Path]:
    """Return paths to the virtualenv directory and its binary folder."""
    venv_dir = root / ".venv"
    bindir = venv_dir / ("Scripts" if os.name == "nt" else "bin")
    return venv_dir, bindir


def create_venv(venv_dir: Path) -> None:
    if venv_dir.exists():
        print(f"Virtual environment already exists at {venv_dir}.")
        return
    print("Creating virtual environment (.venv)...")
    subprocess.check_call([sys.executable, "-m", "venv", str(venv_dir)])


def install_project(pip: Path, root: Path) -> None:
    print("Installing project dependencies (pip install -e .)...")
    subprocess.check_call([str(pip), "install", "-e", str(root)])


def verify_executables(bindir: Path) -> None:
    executables = ["ghostlink", "ghostlink-decode", "ghostlink-web"]
    for exe in executables:
        exe_path = bindir / (exe + (".exe" if os.name == "nt" else ""))
        print(f"Verifying {exe}...")
        try:
            subprocess.check_call([str(exe_path), "--help"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as exc:  # pragma: no cover - diagnostic output
            print(f"[x] Failed to run {exe}: {exc}", file=sys.stderr)
            raise SystemExit(1)


def print_env_instructions() -> None:
    if os.name == "nt":
        print("Activate the virtual environment with:\n  .\\.venv\\Scripts\\Activate.ps1")
        print("(cmd.exe users: .\\.venv\\Scripts\\activate.bat)")
    else:
        print("Activate the virtual environment with:\n  source .venv/bin/activate")
    print("After activation, the 'ghostlink' commands will be available in your PATH.")


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    check_python_version()
    venv_dir, bindir = venv_paths(root)
    create_venv(venv_dir)
    pip = bindir / ("pip.exe" if os.name == "nt" else "pip")
    install_project(pip, root)
    verify_executables(bindir)
    print_env_instructions()
    print("Installation complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
