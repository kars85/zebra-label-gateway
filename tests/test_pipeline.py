import fitz
from PIL import Image

from zebra_label_gateway.image_processor import LABEL_HEIGHT_DOTS, LABEL_WIDTH_DOTS
from zebra_label_gateway.pipeline import (
    load_source_image,
    normalize_with_profile,
    render_input,
)
from zebra_label_gateway.profiles import get_profile


def _make_pdf(path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=288, height=432)
    page.insert_text((20, 40), "SHIP TO: TEST")
    page.draw_rect(fitz.Rect(20, 200, 260, 260), fill=(0, 0, 0))
    doc.save(path)
    doc.close()


def test_render_input_produces_canvas_and_zpl(tmp_path) -> None:
    pdf = tmp_path / "label.pdf"
    _make_pdf(pdf)
    result = render_input(pdf, "generic_4x6")

    assert result.profile_name == "generic_4x6"
    assert result.preview.mode == "1"
    assert result.preview.size == (LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS)
    assert result.zpl.startswith("^XA")
    assert "^GFA," in result.zpl


def test_load_image_input(tmp_path) -> None:
    img_path = tmp_path / "label.png"
    Image.new("RGB", (400, 600), color="white").save(img_path)
    image = load_source_image(img_path)
    assert image.mode == "RGB"


def test_letter_profile_auto_crops(tmp_path) -> None:
    # Small label block on a big white page; auto-crop should scale it up to fill.
    page = Image.new("RGB", (2000, 2000), color="white")
    page.paste(Image.new("RGB", (400, 600), color="black"), (100, 100))
    normalized = normalize_with_profile(page, get_profile("generic_letter_embedded"))
    assert normalized.size == (LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS)
    # The cropped black block, scaled up, should dominate the canvas (mostly black).
    black = dict((v, c) for c, v in normalized.getcolors())[0]
    assert black > (LABEL_WIDTH_DOTS * LABEL_HEIGHT_DOTS) * 0.5


def test_rotate_profile(tmp_path) -> None:
    from zebra_label_gateway.profiles import Profile

    tall = Image.new("RGB", (400, 800), color="white")
    result = normalize_with_profile(tall, Profile(name="r", rotate=90))
    assert result.size == (LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS)
