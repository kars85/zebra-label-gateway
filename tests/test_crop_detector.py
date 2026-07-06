from PIL import Image

from zebra_label_gateway.crop_detector import apply_crop, detect_content_bbox, detect_label_crop


def _page_with_label() -> Image.Image:
    """A white page with a solid black label block in the upper-left."""
    page = Image.new("RGB", (600, 800), color="white")
    page.paste(Image.new("RGB", (200, 300), color="black"), (50, 40))
    return page


def test_exact_bbox_finds_the_block() -> None:
    bbox = detect_content_bbox(_page_with_label(), padding_frac=0.0, largest_region=False)
    assert bbox == (50, 40, 250, 340)


def test_blank_page_returns_none() -> None:
    blank = Image.new("RGB", (300, 300), color="white")
    assert detect_content_bbox(blank) is None


def test_largest_region_ignores_stray_footer() -> None:
    # Big label block top-left + a tiny stray mark bottom-right.
    page = Image.new("RGB", (600, 800), color="white")
    page.paste(Image.new("RGB", (240, 340), color="black"), (40, 40))
    page.paste(Image.new("RGB", (8, 8), color="black"), (560, 780))  # stray footer speck

    left, top, right, bottom = detect_content_bbox(page)
    # The box should hug the label, not stretch to the bottom-right speck.
    assert right < 400 and bottom < 500


def test_apply_auto_crop_shrinks_to_content() -> None:
    cropped = detect_label_crop(_page_with_label())
    assert cropped.width < 320 and cropped.height < 420


def test_apply_fractional_crop() -> None:
    image = Image.new("RGB", (1000, 1000), color="white")
    cropped = apply_crop(image, (0.1, 0.2, 0.6, 0.8))
    assert cropped.size == (500, 600)


def test_apply_no_crop_is_identity() -> None:
    image = Image.new("RGB", (100, 100), color="white")
    assert apply_crop(image, None).size == (100, 100)
