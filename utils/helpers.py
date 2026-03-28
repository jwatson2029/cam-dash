"""
General utility functions for LaViewNVR.
"""
from __future__ import annotations

import re
from pathlib import Path


def ensure_dirs(*paths: str) -> None:
    """Create directories (and parents) if they don't exist."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def sanitize_name(name: str) -> str:
    """Convert a camera name to a filesystem-safe identifier."""
    clean = re.sub(r"[^\w\-]", "_", name.lower())
    clean = re.sub(r"_+", "_", clean).strip("_")
    return clean or "camera"
