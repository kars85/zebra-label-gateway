"""Detect and apply label crop regions.

A "letter"-type input is a full page with a shipping label somewhere on it and
often other content too (a packing slip, footers, marketing). The label is the
largest dense block of dark content, so auto-cropping finds the largest connected
region of content rather than the bounding box of *all* content -- which would be
defeated by a single stray mark elsewhere on the page. Profiles may instead supply
explicit fractional crop coordinates for known layouts, and manual override is
always available for questionable inputs.
"""

from __future__ import annotations

from collections import deque

from PIL import Image, ImageFilter

# Pixels darker than this (0-255) count as content when locating the label.
CONTENT_THRESHOLD = 200
# Grow the detected box by this fraction of its size so nothing is clipped.
DEFAULT_PADDING_FRAC = 0.02
# Downscale the mask to this longest edge before region analysis (speed + merging).
WORK_MAX_DIM = 240
# Dilation passes merge a label's separate text/barcode blocks into one region.
DILATION_PASSES = 6

CropBox = tuple[int, int, int, int]


def _content_mask(gray: Image.Image, threshold: int) -> Image.Image:
    """1-channel mask where content pixels (darker than threshold) are 255."""
    return gray.point(lambda level: 255 if level < threshold else 0)


def _largest_region_bbox(mask: Image.Image) -> CropBox | None:
    """Bounding box (on ``mask``'s scale) of the largest 4-connected content region."""
    width, height = mask.size
    pixels = mask.load()
    visited = bytearray(width * height)
    best_box: CropBox | None = None
    best_area = 0

    for start_y in range(height):
        row = start_y * width
        for start_x in range(width):
            if not pixels[start_x, start_y] or visited[row + start_x]:
                continue
            visited[row + start_x] = 1
            queue = deque(((start_x, start_y),))
            min_x = max_x = start_x
            min_y = max_y = start_y
            while queue:
                x, y = queue.popleft()
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if 0 <= nx < width and 0 <= ny < height:
                        idx = ny * width + nx
                        if pixels[nx, ny] and not visited[idx]:
                            visited[idx] = 1
                            queue.append((nx, ny))
            area = (max_x - min_x + 1) * (max_y - min_y + 1)
            if area > best_area:
                best_area = area
                best_box = (min_x, min_y, max_x, max_y)
    return best_box


def detect_content_bbox(
    image: Image.Image,
    threshold: int = CONTENT_THRESHOLD,
    padding_frac: float = DEFAULT_PADDING_FRAC,
    largest_region: bool = True,
) -> CropBox | None:
    """Return ``(left, top, right, bottom)`` of the label, or ``None`` if blank.

    With ``largest_region`` (default) the largest connected block of content is
    used, isolating the label from stray marks. With it off, the bounding box of
    all content is returned.
    """
    gray = image.convert("L")

    if not largest_region:
        bbox = _content_mask(gray, threshold).getbbox()
        return _pad_and_clamp(bbox, image, padding_frac) if bbox else None

    # Downscale for speed, then dilate so a label's text and barcode merge into
    # one region while distant stray marks stay separate.
    scale = min(1.0, WORK_MAX_DIM / max(gray.width, gray.height))
    small = gray.resize((max(1, round(gray.width * scale)), max(1, round(gray.height * scale))))
    mask = _content_mask(small, threshold)
    for _ in range(DILATION_PASSES):
        mask = mask.filter(ImageFilter.MaxFilter(3))

    box = _largest_region_bbox(mask)
    if box is None:
        return None
    # Map back to full resolution.
    full = tuple(round(v / scale) for v in box)
    return _pad_and_clamp((full[0], full[1], full[2] + 1, full[3] + 1), image, padding_frac)


def _pad_and_clamp(bbox: CropBox, image: Image.Image, padding_frac: float) -> CropBox:
    left, top, right, bottom = bbox
    pad_x = round((right - left) * padding_frac)
    pad_y = round((bottom - top) * padding_frac)
    return (
        max(0, left - pad_x),
        max(0, top - pad_y),
        min(image.width, right + pad_x),
        min(image.height, bottom + pad_y),
    )


def _fractional_box(image: Image.Image, fractions: tuple[float, float, float, float]) -> CropBox:
    left, top, right, bottom = fractions
    return (
        round(left * image.width),
        round(top * image.height),
        round(right * image.width),
        round(bottom * image.height),
    )


def apply_crop(
    image: Image.Image,
    crop: str | tuple[float, float, float, float] | None,
    threshold: int = CONTENT_THRESHOLD,
) -> Image.Image:
    """Apply a profile crop directive: ``None`` (no crop), ``"auto"``, or fractions."""
    if crop is None:
        return image
    if crop == "auto":
        bbox = detect_content_bbox(image, threshold=threshold)
        return image.crop(bbox) if bbox else image
    return image.crop(_fractional_box(image, crop))  # type: ignore[arg-type]


def detect_label_crop(image: Image.Image, threshold: int = CONTENT_THRESHOLD) -> Image.Image:
    """Auto-detect the label region and return the cropped image (whole image if blank)."""
    return apply_crop(image, "auto", threshold=threshold)
