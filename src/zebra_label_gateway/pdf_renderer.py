"""Render PDF pages to raster images via PyMuPDF."""

from __future__ import annotations

from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

# PDF user space is defined at 72 dots per inch; scale up to the printer's DPI.
PDF_BASE_DPI = 72
TARGET_DPI = 203


def _render_page(page, dpi: int) -> Image.Image:
    zoom = dpi / PDF_BASE_DPI
    pixmap = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), colorspace=fitz.csRGB, alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def _load_page(doc, page_index: int):
    if doc.page_count == 0:
        raise ValueError("PDF has no pages")
    if not 0 <= page_index < doc.page_count:
        raise ValueError(f"page index {page_index} out of range (0..{doc.page_count - 1})")
    return doc.load_page(page_index)


def pdf_page_count(pdf_path: str | Path) -> int:
    """Number of pages in a PDF file."""
    with fitz.open(Path(pdf_path)) as doc:
        return doc.page_count


def pdf_page_count_from_bytes(data: bytes) -> int:
    """Number of pages in an in-memory PDF."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        return doc.page_count


def render_page_to_image(pdf_path: str | Path, page_index: int = 0, dpi: int = TARGET_DPI) -> Image.Image:
    """Render page ``page_index`` (0-based) of ``pdf_path`` to an RGB image."""
    with fitz.open(Path(pdf_path)) as doc:
        return _render_page(_load_page(doc, page_index), dpi)


def render_page_from_bytes(data: bytes, page_index: int = 0, dpi: int = TARGET_DPI) -> Image.Image:
    """Render page ``page_index`` (0-based) from in-memory PDF bytes."""
    with fitz.open(stream=data, filetype="pdf") as doc:
        return _render_page(_load_page(doc, page_index), dpi)


def render_first_page_to_image(pdf_path: str | Path, dpi: int = TARGET_DPI) -> Image.Image:
    """Render the first page of ``pdf_path`` to an RGB :class:`PIL.Image` at ``dpi``."""
    return render_page_to_image(pdf_path, 0, dpi)


def render_first_page_from_bytes(data: bytes, dpi: int = TARGET_DPI) -> Image.Image:
    """Render the first PDF page from in-memory bytes (no temp file needed)."""
    return render_page_from_bytes(data, 0, dpi)
