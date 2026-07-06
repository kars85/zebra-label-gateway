"""Render PDF pages to raster images via PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

# PDF user space is defined at 72 dots per inch; scale up to the printer's DPI.
PDF_BASE_DPI = 72
TARGET_DPI = 203


def render_first_page_to_image(pdf_path: str | Path, dpi: int = TARGET_DPI) -> Image.Image:
    """Render the first page of ``pdf_path`` to an RGB :class:`PIL.Image` at ``dpi``."""
    path = Path(pdf_path)
    with fitz.open(path) as doc:
        if doc.page_count == 0:
            raise ValueError(f"PDF has no pages: {path}")
        page = doc.load_page(0)
        zoom = dpi / PDF_BASE_DPI
        pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csRGB, alpha=False)
        return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
