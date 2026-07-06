"""Normalize a label file (PDF or image) into 4x6 raster ZPL and optionally print it.

Pipeline: input detection -> render/open -> crop/rotate per profile -> normalize
to 1-bit 4x6 -> ZPL raster -> preview + optional raw-TCP send.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zebra_label_gateway.pipeline import render_input
from zebra_label_gateway.printer_tcp import DEFAULT_ZPL_PORT, send_zpl_tcp
from zebra_label_gateway.profiles import DEFAULT_PROFILE_NAME, load_profiles

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "samples"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize a label file into 4x6 raster ZPL.")
    parser.add_argument("--input", required=True, type=Path, help="PDF or image file to normalize.")
    parser.add_argument("--host", help="Printer hostname or IP address. Omit to only save output.")
    parser.add_argument("--port", type=int, default=DEFAULT_ZPL_PORT, help="Raw TCP printer port. Defaults to 9100.")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE_NAME,
        help=f"Retailer/carrier profile. Defaults to {DEFAULT_PROFILE_NAME}. See --list-profiles.",
    )
    parser.add_argument("--list-profiles", action="store_true", help="List available profiles and exit.")
    parser.add_argument("--save-only", action="store_true", help="Save ZPL and preview without printing.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory for the .zpl payload and .preview.png. Defaults to samples/.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.list_profiles:
        for name, profile in sorted(load_profiles().items()):
            print(f"{name:26} {profile.description}")
        return 0

    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1

    result = render_input(args.input, args.profile)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem
    zpl_path = args.output_dir / f"{stem}.zpl"
    preview_path = args.output_dir / f"{stem}.preview.png"
    zpl_path.write_text(result.zpl, encoding="ascii", newline="\n")
    result.preview.save(preview_path)
    print(f"Profile: {result.profile_name}")
    print(f"Saved ZPL to {zpl_path}")
    print(f"Saved preview to {preview_path}")

    if args.save_only or not args.host:
        print("Not printing (no --host, or --save-only). Review the preview before sending.")
        return 0

    send_zpl_tcp(result.zpl, args.host, args.port)
    print(f"Sent normalized label to {args.host}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
