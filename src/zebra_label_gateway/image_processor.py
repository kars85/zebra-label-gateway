"""Normalize arbitrary label images onto a 1-bit 4x6 canvas for ZPL raster output."""

from __future__ import annotations

from PIL import Image

LABEL_WIDTH_DOTS = 812
LABEL_HEIGHT_DOTS = 1218
DEFAULT_THRESHOLD = 128


def normalize_image(
    image: Image.Image,
    width: int = LABEL_WIDTH_DOTS,
    height: int = LABEL_HEIGHT_DOTS,
    threshold: int = DEFAULT_THRESHOLD,
    auto_rotate: bool = True,
) -> Image.Image:
    """Fit ``image`` onto a ``width`` x ``height`` white canvas as a 1-bit image.

    The aspect ratio is preserved (letterboxed with white), never stretched, so
    barcodes stay scannable. Conversion to 1-bit uses a hard threshold rather
    than dithering, which would corrupt barcodes and small text.
    """
    gray = image.convert("L")

    # A landscape source on a portrait canvas is almost always a rotated label.
    if auto_rotate and gray.width > gray.height and width < height:
        gray = gray.rotate(90, expand=True)

    scale = min(width / gray.width, height / gray.height)
    scaled_size = (max(1, round(gray.width * scale)), max(1, round(gray.height * scale)))
    scaled = gray.resize(scaled_size, Image.LANCZOS)

    canvas = Image.new("L", (width, height), color=255)
    offset = ((width - scaled_size[0]) // 2, (height - scaled_size[1]) // 2)
    canvas.paste(scaled, offset)

    # Map through a threshold LUT, then pack to 1-bit. Values are already 0/255,
    # so convert("1") maps them cleanly without a second implicit threshold.
    lut = [0 if level < threshold else 255 for level in range(256)]
    return canvas.point(lut).convert("1")
