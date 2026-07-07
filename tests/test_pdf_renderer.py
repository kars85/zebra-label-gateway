import fitz
import pytest
from PIL import Image

from zebra_label_gateway.pdf_renderer import (
    PDF_BASE_DPI,
    pdf_page_count_from_bytes,
    render_first_page_from_bytes,
    render_first_page_to_image,
    render_page_from_bytes,
)


def _make_pdf(path, width_pt=288, height_pt=432) -> None:
    """Write a minimal one-page PDF (default 4x6 inches at 72pt/inch)."""
    doc = fitz.open()
    page = doc.new_page(width=width_pt, height=height_pt)
    page.insert_text((20, 40), "SHIP TO: TEST")
    doc.save(path)
    doc.close()


def test_renders_first_page_at_target_dpi(tmp_path) -> None:
    pdf_path = tmp_path / "label.pdf"
    _make_pdf(pdf_path, width_pt=288, height_pt=432)

    image = render_first_page_to_image(pdf_path, dpi=203)

    assert isinstance(image, Image.Image)
    assert image.mode == "RGB"
    # 288pt / 72 * 203dpi = 812 dots wide; allow a rounding dot of slack.
    assert abs(image.width - round(288 / PDF_BASE_DPI * 203)) <= 1
    assert abs(image.height - round(432 / PDF_BASE_DPI * 203)) <= 1


def test_missing_pdf_raises(tmp_path) -> None:
    with pytest.raises(Exception):
        render_first_page_to_image(tmp_path / "does-not-exist.pdf")


def test_render_from_bytes(tmp_path) -> None:
    pdf_path = tmp_path / "label.pdf"
    _make_pdf(pdf_path, width_pt=288, height_pt=432)
    image = render_first_page_from_bytes(pdf_path.read_bytes(), dpi=203)
    assert image.mode == "RGB"
    assert abs(image.width - round(288 / PDF_BASE_DPI * 203)) <= 1


def _make_multipage_pdf(path, pages=3) -> None:
    doc = fitz.open()
    for i in range(pages):
        page = doc.new_page(width=288, height=432)
        page.insert_text((20, 40 + i), f"PAGE {i + 1}")
    doc.save(path)
    doc.close()


def test_page_count_and_render_specific_page(tmp_path) -> None:
    pdf = tmp_path / "multi.pdf"
    _make_multipage_pdf(pdf, pages=3)
    data = pdf.read_bytes()
    assert pdf_page_count_from_bytes(data) == 3
    # Each page renders without error and returns an image.
    for idx in range(3):
        assert render_page_from_bytes(data, idx).mode == "RGB"


def test_out_of_range_page_raises(tmp_path) -> None:
    pdf = tmp_path / "multi.pdf"
    _make_multipage_pdf(pdf, pages=2)
    with pytest.raises(ValueError):
        render_page_from_bytes(pdf.read_bytes(), 5)
