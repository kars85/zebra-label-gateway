"""Generate and optionally send a native ZPL test label over raw TCP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zebra_label_gateway.printer_tcp import (
    DEFAULT_ZPL_PORT,
    decode_status,
    diagnose,
    format_status,
    getvar,
    query_status_raw,
    send_zpl_tcp,
    setvar,
)
from zebra_label_gateway.zpl_encoder import build_test_label_zpl


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = REPO_ROOT / "samples" / "test-label.zpl"


def save_zpl(zpl: str, output_path: Path = DEFAULT_OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(zpl, encoding="ascii", newline="\n")
    return output_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate and optionally print a Zebra ZPL test label.")
    parser.add_argument("--host", required=True, help="Printer hostname or IP address.")
    parser.add_argument("--port", type=int, default=DEFAULT_ZPL_PORT, help="Raw TCP printer port. Defaults to 9100.")
    parser.add_argument("--save-only", action="store_true", help="Save samples/test-label.zpl without printing.")
    parser.add_argument(
        "--status",
        action="store_true",
        help="Query printer status (~HS) and print a decoded report instead of printing a label.",
    )
    parser.add_argument(
        "--getvar",
        metavar="NAME",
        help='Query an SGD variable (e.g. device.languages) and print the reply. Works in any language mode.',
    )
    parser.add_argument(
        "--setvar",
        nargs=2,
        metavar=("NAME", "VALUE"),
        help='Set an SGD variable, e.g. --setvar device.languages zpl.',
    )
    parser.add_argument(
        "--diagnose",
        action="store_true",
        help="Query a battery of SGD variables (head latch, media, darkness) to explain a no-print.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.diagnose:
        print(diagnose(args.host, args.port))
        return 0

    if args.setvar:
        name, value = args.setvar
        setvar(args.host, name, value, args.port)
        print(f"Set {name} = {value!r} (verifying)...")
        print(f"{name} = {getvar(args.host, name, args.port)!r}")
        return 0

    if args.getvar:
        reply = getvar(args.host, args.getvar, args.port)
        print(f"{args.getvar} = {reply!r}" if reply else f"No reply for {args.getvar!r}.")
        return 0

    if args.status:
        raw = query_status_raw(args.host, args.port)
        print(format_status(decode_status(raw)))
        return 0

    zpl = build_test_label_zpl()
    output_path = save_zpl(zpl)
    print(f"Saved test label to {output_path}")

    if args.save_only:
        print("Save-only mode selected; not sending to printer.")
        return 0

    send_zpl_tcp(zpl, args.host, args.port)
    print(f"Sent test label to {args.host}:{args.port}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
