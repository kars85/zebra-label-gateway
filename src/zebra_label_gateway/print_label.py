"""Normalize a label file (PDF or image) into 4x6 raster ZPL and optionally print it.

Pipeline: input detection -> render/open -> normalize to 1-bit 4x6 -> ZPL raster
-> preview + optional raw-TCP send.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zebra_label_gateway.image_processor import DEFAULT_THRESHOLD, normalize_image
from zebra_label_gateway.input_detection import detect_input_type
from zebra_label_gateway.pdf_renderer import render_first_page_to_image
from zebra_label_gateway.printer_tcp import DEFAULT_ZPL_PORT, send_zpl_tcp
from zebra_label_gateway.zpl_encoder import build_raster_label_zpl

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "samples"


def load_source_image(input_path: Path) -> Image.Image:
    """Turn a PDF or image input into a single RGB image (first page for PDFs)."""
    kind = detect_input_type(input_path)
    if kind == "pdf":
        return render_first_page_to_image(input_path)
    if kind == "image":
        return Image.open(input_path)
    raise ValueError(
        f"Unsupported input type {kind!r} for {input_path.name}; expected a PDF or image."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize a label file into 4x6 raster ZPL.")
    parser.add_argument("--input", required=True, type=Path, help="PDF or image file to normalize.")
    parser.add_argument("--host", help="Printer hostname or IP address. Omit to only save output.")
    parser.add_argument("--port", type=int, default=DEFAULT_ZPL_PORT, help="Raw TCP printer port. Defaults to 9100.")
    parser.add_argument("--save-only", action="store_true", help="Save ZPL and preview without printing.")
    parser.add_argument(
        "--threshold",
        type=int,
        default=DEFAULT_THRESHOLD,
        help=f"Black/white threshold 0-255. Defaults to {DEFAULT_THRESHOLD}. Lower = less ink.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the .zpl payload and .preview.png. Defaults to samples/.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1

    source = load_source_image(args.input)
    normalized = normalize_image(source, threshold=args.threshold)
    zpl = build_raster_label_zpl(normalized)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    zpl_path = args.output_dir / f"{stem}.zpl"
    preview_path = args.output_dir / f"{stem}.preview.png"
    zpl_path.write_text(zpl, encoding="ascii", newline="\n")
    normalized.save(preview_path)
    print(f"Saved ZPL to {zpl_path}")
    print(f"Saved preview to {preview_path}")

    if args.save_only or not args.host:
        print("Not printing (no --host, or --save-only). Review the preview before sending.")
        return 0

    send_zpl_tcp(zpl, args.host, args.port)
    print(f"Sent normalized label to {args.host}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
