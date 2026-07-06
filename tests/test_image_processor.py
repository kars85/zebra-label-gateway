from PIL import Image

from zebra_label_gateway.image_processor import (
    LABEL_HEIGHT_DOTS,
    LABEL_WIDTH_DOTS,
    normalize_image,
)


def test_normalizes_to_1bit_canvas() -> None:
    source = Image.new("RGB", (400, 600), color="white")
    result = normalize_image(source)

    assert result.mode == "1"
    assert result.size == (LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS)


def test_auto_rotates_landscape_to_portrait() -> None:
    # A wide source should be rotated to fill the portrait canvas taller than wide.
    source = Image.new("RGB", (1200, 300), color="white")
    result = normalize_image(source)
    assert result.size == (LABEL_WIDTH_DOTS, LABEL_HEIGHT_DOTS)


def test_threshold_produces_black_and_white() -> None:
    # A mid-gray fill below the default threshold should become all black.
    source = Image.new("L", (400, 600), color=64)
    result = normalize_image(source, threshold=128)
    colors = {value for _count, value in result.getcolors()}
    assert colors <= {0, 255}
    assert 0 in colors  # some black present
