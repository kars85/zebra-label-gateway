"""Route a ZPL payload to the printer over the configured transport."""

from __future__ import annotations

from .config import PrinterConfig
from .printer_tcp import send_zpl_tcp
from .printer_windows import send_zpl_windows


def send_zpl(zpl: str, printer: PrinterConfig) -> str:
    """Send ``zpl`` using the transport named by ``printer.connection_type``.

    Returns a short human-readable description of where it was sent.
    """
    kind = printer.connection_type.lower()
    if kind == "tcp":
        send_zpl_tcp(zpl, printer.tcp_host, printer.tcp_port)
        return f"{printer.tcp_host}:{printer.tcp_port} (tcp)"
    if kind == "windows":
        send_zpl_windows(zpl, printer.windows_queue_name)
        return f"{printer.windows_queue_name!r} (windows queue)"
    raise ValueError(f"Unknown connection_type {printer.connection_type!r}; expected 'tcp' or 'windows'.")
