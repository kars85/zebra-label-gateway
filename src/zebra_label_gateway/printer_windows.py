"""Windows print-spooler transport for sending raw ZPL to a printer queue.

Use this when the ZD421 is installed as a Windows printer rather than reached
over raw TCP. It sends the ZPL as a RAW spool job (bytes passed straight to the
printer, bypassing the driver's rendering), which is required for ZPL.

Depends on ``pywin32`` (the ``win32print`` module), an optional extra:
``pip install pywin32``.
"""

from __future__ import annotations


class WindowsPrintingUnavailable(RuntimeError):
    """Raised when pywin32 is not installed or not on Windows."""


def _require_win32print():
    try:
        import win32print  # type: ignore
    except ImportError as exc:  # pragma: no cover - exercised only without pywin32
        raise WindowsPrintingUnavailable(
            "Windows queue printing needs pywin32. Install it with: pip install pywin32"
        ) from exc
    return win32print


def list_windows_printers() -> list[str]:
    """Return the names of installed Windows printers."""
    win32print = _require_win32print()
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    return [printer[2] for printer in win32print.EnumPrinters(flags)]


def send_zpl_windows(zpl: str, queue_name: str, job_name: str = "Zebra Label Gateway") -> None:
    """Send ``zpl`` to the named Windows printer queue as a RAW spool job."""
    win32print = _require_win32print()
    payload = zpl.encode("ascii")
    handle = win32print.OpenPrinter(queue_name)
    try:
        # datatype RAW = pass bytes to the printer untouched (required for ZPL).
        win32print.StartDocPrinter(handle, 1, (job_name, None, "RAW"))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, payload)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)
