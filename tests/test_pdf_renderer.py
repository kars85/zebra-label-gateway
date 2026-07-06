import fitz
import pytest
from PIL import Image

from zebra_label_gateway.pdf_renderer import PDF_BASE_DPI, render_first_page_to_image


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
