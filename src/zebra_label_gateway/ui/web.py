"""Local preview web UI for Zebra Label Gateway.

A dependency-free (stdlib ``http.server``) local tool: enter the path to a PDF or
image, pick a profile, and see the exact 1-bit 4x6 preview before printing. This
enforces the charter's "make transformations visible before printing" principle.
Bound to localhost by default; it reads local file paths the operator supplies.
"""

from __future__ import annotations

import html
import io
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..config import AppConfig, load_app_config
from ..pipeline import render_input
from ..profiles import DEFAULT_PROFILE_NAME, load_profiles
from ..transport import send_zpl

# Rendered previews are cached here in-process, keyed by a safe name.
_PREVIEW_CACHE: dict[str, bytes] = {}


def _page(config: AppConfig, message: str = "", preview_name: str = "", profile_selected: str = "") -> bytes:
    profiles = load_profiles()
    options = "\n".join(
        f'<option value="{html.escape(name)}"{" selected" if name == profile_selected else ""}>'
        f"{html.escape(name)}</option>"
        for name in sorted(profiles)
    )
    preview_block = (
        f'<div class="preview"><h2>Preview</h2>'
        f'<img src="/preview?name={html.escape(preview_name)}" alt="label preview"></div>'
        if preview_name
        else '<div class="preview muted">No preview yet. Render a file to see it here.</div>'
    )
    msg_block = f'<p class="msg">{html.escape(message)}</p>' if message else ""
    printer_desc = (
        f"{config.printer.connection_type} -> "
        f"{config.printer.tcp_host}:{config.printer.tcp_port}"
        if config.printer.connection_type == "tcp"
        else f"{config.printer.connection_type} -> {config.printer.windows_queue_name}"
    )
    return f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Zebra Label Gateway</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; }}
  h1 {{ font-size: 1.4rem; }}
  form {{ display: grid; gap: .75rem; padding: 1rem; border: 1px solid #8884; border-radius: 8px; }}
  label {{ font-weight: 600; font-size: .9rem; }}
  input[type=text], select {{ padding: .5rem; font-size: 1rem; width: 100%; box-sizing: border-box; }}
  .row {{ display: flex; gap: .75rem; }}
  button {{ padding: .6rem 1.2rem; font-size: 1rem; border-radius: 6px; border: 1px solid #8886; cursor: pointer; }}
  button.print {{ font-weight: 700; }}
  .muted {{ color: #8889; }}
  .msg {{ padding: .6rem; background: #8882; border-radius: 6px; white-space: pre-wrap; }}
  .preview img {{ max-width: 100%; border: 1px solid #8884; image-rendering: pixelated; }}
  .printer {{ font-size: .85rem; color: #8889; }}
</style></head>
<body>
  <h1>Zebra Label Gateway</h1>
  <p class="printer">Printer: {html.escape(printer_desc)}</p>
  {msg_block}
  <form method="post" action="/process">
    <div><label>File path (PDF or image)</label>
      <input type="text" name="path" placeholder="C:\\path\\to\\label.pdf" required></div>
    <div><label>Profile</label><select name="profile">{options}</select></div>
    <div class="row">
      <button type="submit" name="action" value="render">Render preview</button>
      <button type="submit" name="action" value="print" class="print">Render &amp; print</button>
    </div>
  </form>
  {preview_block}
</body></html>""".encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    config: AppConfig  # set on the server subclass

    def log_message(self, *args) -> None:  # quieter console
        pass

    def _send_html(self, body: bytes, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            query = parse_qs(parsed.query)
            self._send_html(_page(
                self.config,
                message=query.get("msg", [""])[0],
                preview_name=query.get("preview", [""])[0],
                profile_selected=query.get("profile", [DEFAULT_PROFILE_NAME])[0],
            ))
        elif parsed.path == "/preview":
            name = parse_qs(parsed.query).get("name", [""])[0]
            data = _PREVIEW_CACHE.get(name)
            if not data:
                self.send_error(404, "no such preview")
                return
            self.send_response(200)
            self.send_header("Content-Type", "image/png")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/process":
            self.send_error(404)
            return
        length = int(self.headers.get("Content-Length", 0))
        form = parse_qs(self.rfile.read(length).decode("utf-8"))
        path = form.get("path", [""])[0].strip()
        profile = form.get("profile", [DEFAULT_PROFILE_NAME])[0]
        action = form.get("action", ["render"])[0]

        try:
            source = Path(path)
            if not source.exists():
                raise FileNotFoundError(f"File not found: {path}")
            result = render_input(source, profile)
            buffer = io.BytesIO()
            result.preview.save(buffer, format="PNG")
            preview_name = source.stem
            _PREVIEW_CACHE[preview_name] = buffer.getvalue()

            message = f"Rendered {source.name} with profile '{result.profile_name}'."
            if action == "print":
                where = send_zpl(result.zpl, self.config.printer)
                message += f" Printed to {where}."
            self._redirect(message, preview_name, profile)
        except Exception as exc:  # noqa: BLE001 - surface any error to the operator
            detail = f"{type(exc).__name__}: {exc}"
            traceback.print_exc()
            self._redirect(f"Error: {detail}", "", profile)

    def _redirect(self, message: str, preview_name: str, profile: str) -> None:
        from urllib.parse import urlencode

        query = urlencode({"msg": message, "preview": preview_name, "profile": profile})
        self.send_response(303)
        self.send_header("Location", f"/?{query}")
        self.end_headers()


def run_web_ui(host: str = "127.0.0.1", port: int = 8420, config: AppConfig | None = None) -> None:
    """Start the preview web UI (blocks until interrupted)."""
    resolved = config or load_app_config()

    handler = type("BoundHandler", (_Handler,), {"config": resolved})
    server = ThreadingHTTPServer((host, port), handler)
    print(f"Preview UI running at http://{host}:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
