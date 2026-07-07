"""Unified command-line entry point for Zebra Label Gateway.

Subcommands:
  test-label   generate and send the built-in ZPL test label
  print        normalize a PDF/image to 4x6 ZPL and optionally print it
  watch        run the LabelDrop watched-folder workflow
  status       query printer host status (~HS)
  diagnose     dump printer SGD diagnostics
  profiles     list available normalization profiles
  ui           launch the local preview web UI

Defaults (printer host/port, folders) come from config/default.yaml; flags
override them.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .config import PrinterConfig, load_app_config
from .pipeline import render_input
from .printer_tcp import decode_status, diagnose, format_status, query_status_raw, send_zpl_tcp
from .profiles import DEFAULT_PROFILE_NAME, load_profiles
from .transport import send_zpl
from .zpl_encoder import build_test_label_zpl

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "samples"


def _resolve_host(args, printer: PrinterConfig) -> str | None:
    host = getattr(args, "host", None) or printer.tcp_host
    # The shipped default is a placeholder; treat it as "unset".
    return None if host in {None, "192.168.x.x"} else host


def _cmd_test_label(args, config) -> int:
    zpl = build_test_label_zpl()
    if args.save_only:
        out = DEFAULT_OUTPUT_DIR / "test-label.zpl"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(zpl, encoding="ascii", newline="\n")
        print(f"Saved test label to {out}")
        return 0
    host = _resolve_host(args, config.printer)
    if not host:
        print("No printer host configured; pass --host or set printer.tcp_host.", file=sys.stderr)
        return 1
    send_zpl_tcp(zpl, host, args.port or config.printer.tcp_port)
    print(f"Sent test label to {host}:{args.port or config.printer.tcp_port}")
    return 0


def _cmd_print(args, config) -> int:
    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 1
    result = render_input(args.input, args.profile)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    zpl_path = args.output_dir / f"{args.input.stem}.zpl"
    preview_path = args.output_dir / f"{args.input.stem}.preview.png"
    zpl_path.write_text(result.zpl, encoding="ascii", newline="\n")
    result.preview.save(preview_path)
    print(f"Profile: {result.profile_name}")
    print(f"Saved ZPL to {zpl_path}")
    print(f"Saved preview to {preview_path}")

    if args.save_only:
        print("Save-only; review the preview before printing.")
        return 0
    host = _resolve_host(args, config.printer)
    if config.printer.connection_type.lower() == "tcp" and not host:
        print("No printer host configured; pass --host or set printer.tcp_host.", file=sys.stderr)
        return 1
    printer = config.printer if host is None else _override_host(config.printer, host, args.port)
    where = send_zpl(result.zpl, printer)
    print(f"Sent normalized label to {where}")
    return 0


def _override_host(printer: PrinterConfig, host: str, port: int | None) -> PrinterConfig:
    from dataclasses import replace

    return replace(printer, tcp_host=host, tcp_port=port or printer.tcp_port)


def _cmd_watch(args, config) -> int:
    from .watcher import start_watcher

    do_print = None
    if args.print:
        do_print = True
    elif args.no_print:
        do_print = False
    start_watcher(profile_name=args.profile, do_print=do_print)
    return 0


def _cmd_status(args, config) -> int:
    host = _resolve_host(args, config.printer)
    if not host:
        print("No printer host configured; pass --host.", file=sys.stderr)
        return 1
    print(format_status(decode_status(query_status_raw(host, args.port or config.printer.tcp_port))))
    return 0


def _cmd_diagnose(args, config) -> int:
    host = _resolve_host(args, config.printer)
    if not host:
        print("No printer host configured; pass --host.", file=sys.stderr)
        return 1
    print(diagnose(host, args.port or config.printer.tcp_port))
    return 0


def _cmd_profiles(args, config) -> int:
    for name, profile in sorted(load_profiles().items()):
        print(f"{name:26} {profile.description}")
    return 0


def _cmd_ui(args, config) -> int:
    port = args.port or 8000
    try:
        import uvicorn  # noqa: F401
    except ImportError:
        # Fall back to the dependency-free stdlib preview UI.
        from .ui.web import run_web_ui

        print("FastAPI/uvicorn not installed; using the basic stdlib UI. "
              'Install the full editor with: pip install -e ".[web]"')
        run_web_ui(host=args.bind, port=args.port or 8420)
        return 0

    import uvicorn

    print(f"Full editor UI at http://{args.bind}:{port}  (Ctrl+C to stop)")
    uvicorn.run("zebra_label_gateway.webapp.server:app", host=args.bind, port=port)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="zebra-label-gateway", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_test = sub.add_parser("test-label", help="Generate/send the built-in test label.")
    p_test.add_argument("--host")
    p_test.add_argument("--port", type=int)
    p_test.add_argument("--save-only", action="store_true")
    p_test.set_defaults(func=_cmd_test_label)

    p_print = sub.add_parser("print", help="Normalize a PDF/image and optionally print it.")
    p_print.add_argument("--input", required=True, type=Path)
    p_print.add_argument("--profile", default=DEFAULT_PROFILE_NAME)
    p_print.add_argument("--host")
    p_print.add_argument("--port", type=int)
    p_print.add_argument("--save-only", action="store_true")
    p_print.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    p_print.set_defaults(func=_cmd_print)

    p_watch = sub.add_parser("watch", help="Run the LabelDrop watched-folder workflow.")
    p_watch.add_argument("--profile", default=DEFAULT_PROFILE_NAME)
    p_watch.add_argument("--print", action="store_true", help="Force printing on.")
    p_watch.add_argument("--no-print", action="store_true", help="Force printing off (preview only).")
    p_watch.set_defaults(func=_cmd_watch)

    p_status = sub.add_parser("status", help="Query printer ~HS status.")
    p_status.add_argument("--host")
    p_status.add_argument("--port", type=int)
    p_status.set_defaults(func=_cmd_status)

    p_diag = sub.add_parser("diagnose", help="Dump printer SGD diagnostics.")
    p_diag.add_argument("--host")
    p_diag.add_argument("--port", type=int)
    p_diag.set_defaults(func=_cmd_diagnose)

    p_prof = sub.add_parser("profiles", help="List normalization profiles.")
    p_prof.set_defaults(func=_cmd_profiles)

    p_ui = sub.add_parser("ui", help="Launch the local preview web UI.")
    p_ui.add_argument("--bind", default="127.0.0.1")
    p_ui.add_argument("--port", type=int)
    p_ui.set_defaults(func=_cmd_ui)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_app_config()
    return args.func(args, config)


if __name__ == "__main__":
    raise SystemExit(main())
