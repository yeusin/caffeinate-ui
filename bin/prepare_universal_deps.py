#!/usr/bin/env python3
"""Prepare universal2 dependencies for macOS builds.

PyQt6 and pyqt6-sip provide universal2 macOS wheels, but PyQt6_Qt6 (which contains
the Qt6 binaries and dynamic libraries) is published only as separate x86_64 and
arm64 wheels. This script downloads both wheels from PyPI, merges them into a
universal2 wheel using delocate, and installs it into the local environment.
"""

from __future__ import annotations

import importlib.metadata
import json
import subprocess
import sys
import urllib.request
from pathlib import Path


def is_binary_universal(binary_path: Path) -> bool:
    try:
        res = subprocess.run(
            ["lipo", "-archs", str(binary_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        archs = res.stdout.strip().split()
        return "x86_64" in archs and "arm64" in archs
    except Exception:
        return False


def get_sample_qt_binary() -> Path | None:
    try:
        import PyQt6
    except ImportError:
        return None

    qt_dir = Path(PyQt6.__file__).parent / "Qt6" / "lib"
    if not qt_dir.exists():
        return None

    for p in qt_dir.rglob("*"):
        if p.is_file() and not p.is_symlink() and (p.suffix == ".dylib" or ".framework" in str(p)):
            return p
    return None


def main() -> None:
    if sys.platform != "darwin":
        print(f"Skipping universal dependencies: current platform is {sys.platform} (macOS only)")
        return

    # Check python interpreter architecture
    res = subprocess.run(["lipo", "-archs", sys.executable], capture_output=True, text=True)
    python_archs = res.stdout.strip().split()
    print(f"Python interpreter architectures: {python_archs}")
    if "x86_64" not in python_archs or "arm64" not in python_archs:
        print(
            "WARNING: The active Python interpreter does not have both x86_64 and arm64 slices.\n"
            "PyInstaller universal2 builds require a universal Python installation (e.g. from python.org)."
        )

    # Check if PyQt6_Qt6 is already universal
    sample_bin = get_sample_qt_binary()
    if sample_bin and is_binary_universal(sample_bin):
        print(f"PyQt6_Qt6 is already universal ({sample_bin.name} contains x86_64 and arm64).")
        return

    try:
        ver = importlib.metadata.version("PyQt6_Qt6")
    except importlib.metadata.PackageNotFoundError:
        sys.exit("Error: PyQt6_Qt6 is not installed in the environment.")

    print(f"Preparing universal2 wheel for PyQt6_Qt6=={ver}...")

    # Query PyPI for wheel URLs
    pypi_url = f"https://pypi.org/pypi/PyQt6_Qt6/{ver}/json"
    req = urllib.request.Request(pypi_url, headers={"User-Agent": "caffeinate-ui-build"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    arm_url = None
    arm_fn = None
    x86_url = None
    x86_fn = None

    for item in data.get("urls", []):
        fn = item["filename"]
        if "macosx" in fn and "arm64" in fn and fn.endswith(".whl"):
            arm_url = item["url"]
            arm_fn = fn
        elif "macosx" in fn and "x86_64" in fn and fn.endswith(".whl"):
            x86_url = item["url"]
            x86_fn = fn

    if not arm_url or not x86_url:
        sys.exit(f"Error: Could not find both arm64 and x86_64 wheels for PyQt6_Qt6 {ver} on PyPI.")

    cache_dir = Path("build/universal_wheels")
    cache_dir.mkdir(parents=True, exist_ok=True)

    arm_whl = cache_dir / arm_fn
    x86_whl = cache_dir / x86_fn

    if not arm_whl.exists():
        print(f"Downloading {arm_fn}...")
        urllib.request.urlretrieve(arm_url, arm_whl)

    if not x86_whl.exists():
        print(f"Downloading {x86_fn}...")
        urllib.request.urlretrieve(x86_url, x86_whl)

    try:
        from delocate.fuse import fuse_wheels
    except ImportError:
        sys.exit("Error: 'delocate' is required to fuse wheels. Please run 'uv sync --dev'.")

    print(f"Fusing {arm_fn} and {x86_fn} into universal2 wheel...")
    fused_wheel = fuse_wheels(arm_whl, x86_whl, cache_dir)
    print(f"Generated universal2 wheel: {fused_wheel}")

    print(f"Installing {fused_wheel.name} into environment...")
    subprocess.run(
        ["uv", "pip", "install", "--force-reinstall", "--no-deps", str(fused_wheel)],
        check=True,
    )

    print("Universal dependencies setup complete!")


if __name__ == "__main__":
    main()
