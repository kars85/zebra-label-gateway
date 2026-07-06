"""Input type detection for label-like files."""

from __future__ import annotations

from pathlib import Path


PDF_EXTENSIONS = {".pdf"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"}
ZPL_EXTENSIONS = {".zpl", ".txt"}


def detect_input_type(path: str | Path) -> str:
    suffix = Path(path).suffix.lower()
    if suffix in PDF_EXTENSIONS:
        return "pdf"
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in ZPL_EXTENSIONS:
        return "zpl"
    return "unknown"
