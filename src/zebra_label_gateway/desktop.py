"""Desktop app entry point: run the gateway locally in a native window.

Starts the FastAPI app on a private localhost port in a background thread, then
opens a pywebview window pointing at it. Config is bundled read-only; history and
trained profiles live in a writable per-user directory. Pass ``--server-only`` to
run headless (used for smoke-testing the frozen build).
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
from pathlib import Path


def _app_base() -> Path:
    """Directory holding bundled resources (PyInstaller unpack dir when frozen)."""
    meipass = getattr(sys, "_MEIPASS", None)
    return Path(meipass) if meipass else Path(__file__).resolve().parents[2]


def _user_data_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    data = Path(base) / "ZebraLabelGateway" / "data"
    data.mkdir(parents=True, exist_ok=True)
    return data


# Resolve config (bundled) and data (writable) before importing the app.
os.environ.setdefault("ZLG_CONFIG_DIR", str(_app_base() / "config"))
os.environ.setdefault("ZLG_DATA_DIR", str(_user_data_dir()))


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_ready(port: int, timeout: float = 25.0) -> bool:
    import urllib.request

    url = f"http://127.0.0.1:{port}/api/profiles"
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.2)
    return False


def _serve(port: int) -> None:
    import uvicorn

    from zebra_label_gateway.webapp.server import app

    # Server API (not uvicorn.run) so it works off the main thread without signals.
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    uvicorn.Server(config).run()


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    port = int(os.environ.get("ZLG_DESKTOP_PORT") or _free_port())

    threading.Thread(target=_serve, args=(port,), daemon=True).start()
    if not _wait_ready(port):
        print("Zebra Label Gateway: server failed to start.", file=sys.stderr)
        return 1

    if "--server-only" in argv:
        print(f"server-only mode on http://127.0.0.1:{port}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            return 0

    import webview

    webview.create_window(
        "Zebra Label Gateway",
        f"http://127.0.0.1:{port}",
        width=1300,
        height=880,
        min_size=(920, 620),
    )
    webview.start()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
