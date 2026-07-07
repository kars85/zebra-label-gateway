"""End-to-end normalization pipeline shared by the CLI, watcher, and web UI.

Flow: load (PDF page 1 or image) -> crop (profile) -> rotate (profile) ->
normalize to 1-bit 4x6 -> encode as raster ZPL. Every step is deterministic and
produces a previewable 1-bit image before any bytes reach the printer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from .crop_detector import apply_crop
from .image_processor import LABEL_HEIGHT_DOTS, LABEL_WIDTH_DOTS, normalize_image
from .input_detection import detect_input_type
from .pdf_renderer import render_page_to_image
from .profiles import Profile, get_profile
from .zpl_encoder import build_raster_label_zpl


@dataclass(frozen=True)
class RenderResult:
    """The normalized preview image and its ZPL payload."""

    preview: Image.Image  # 1-bit, canvas-sized
    zpl: str
    profile_name: str


def load_source_image(input_path: str | Path, page: int = 0) -> Image.Image:
    """Turn a PDF or image path into a single RGB image (page ``page`` for PDFs)."""
    path = Path(input_path)
    kind = detect_input_type(path)
    if kind == "pdf":
        return render_page_to_image(path, page)
    if kind == "image":
        return Image.open(path).convert("RGB")
    raise ValueError(f"Unsupported input type {kind!r} for {path.name}; expected a PDF or image.")


def normalize_with_profile(
    image: Image.Image,
    profile: Profile,
    width: int = LABEL_WIDTH_DOTS,
    height: int = LABEL_HEIGHT_DOTS,
) -> Image.Image:
    """Crop, rotate, and normalize ``image`` to a 1-bit canvas per ``profile``."""
    cropped = apply_crop(image, profile.crop, threshold=profile.threshold)

    rotated = cropped
    if profile.rotate:
        rotated = cropped.rotate(-profile.rotate, expand=True)  # clockwise degrees

    # A manual rotation already fixed orientation; only auto-rotate when none was set.
    return normalize_image(
        rotated,
        width=width,
        height=height,
        threshold=profile.threshold,
        auto_rotate=profile.rotate == 0,
    )


def render_input(
    input_path: str | Path,
    profile: Profile | str | None = None,
    page: int = 0,
    width: int = LABEL_WIDTH_DOTS,
    height: int = LABEL_HEIGHT_DOTS,
) -> RenderResult:
    """Full pipeline: path + profile (+ PDF page) -> normalized preview + raster ZPL."""
    if not isinstance(profile, Profile):
        profile = get_profile(profile)
    source = load_source_image(input_path, page=page)
    preview = normalize_with_profile(source, profile, width=width, height=height)
    zpl = build_raster_label_zpl(preview, width_dots=width, height_dots=height)
    return RenderResult(preview=preview, zpl=zpl, profile_name=profile.name)
