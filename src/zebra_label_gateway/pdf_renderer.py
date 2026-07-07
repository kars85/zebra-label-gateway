"""Render PDF pages to raster images via PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

# PDF user space is defined at 72 dots per inch; scale up to the printer's DPI.
PDF_BASE_DPI = 72
TARGET_DPI = 203


def _pixmap_to_image(doc, dpi: int) -> Image.Image:
    if doc.page_count == 0:
        raise ValueError("PDF has no pages")
    page = doc.load_page(0)
    zoom = dpi / PDF_BASE_DPI
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csRGB, alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def render_first_page_to_image(pdf_path: str | Path, dpi: int = TARGET_DPI) -> Image.Image:
    """Render the first page of ``pdf_path`` to an RGB :class:`PIL.Image` at ``dpi``."""
    with fitz.open(Path(pdf_path)) as doc:
        return _pixmap_to_image(doc, dpi)


def render_first_page_from_bytes(data: bytes, dpi: int = TARGET_DPI) -> Image.Image:
    """Render the first PDF page from in-memory bytes (no temp file needed)."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        return _pixmap_to_image(doc, dpi)
