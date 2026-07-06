"""Raw TCP printer transport."""

from __future__ import annotations

import re
import socket


DEFAULT_ZPL_PORT = 9100

# STX/ETX delimit each of the three status strings returned by ~HS.
_STATUS_STRING = re.compile(b"\x02([^\x03]*)\x03")


def send_zpl_tcp(zpl: str, host: str, port: int = DEFAULT_ZPL_PORT, timeout: float = 10.0) -> None:
    """Send a ZPL payload to a networked Zebra printer."""
    payload = zpl.encode("ascii")
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.sendall(payload)


def query_status_raw(host: str, port: int = DEFAULT_ZPL_PORT, timeout: float = 10.0) -> bytes:
    """Send ~HS and return the raw status bytes the printer replies with."""
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.sendall(b"~HS")
        connection.settimeout(timeout)
        chunks: list[bytes] = []
        while True:
            try:
                data = connection.recv(4096)
            except socket.timeout:
                break
            if not data:
                break
            chunks.append(data)
            # ~HS returns three STX/ETX-wrapped strings; stop once we have them all.
            if b"".join(chunks).count(b"\x03") >= 3:
                break
        return b"".join(chunks)


def getvar(host: str, name: str, port: int = DEFAULT_ZPL_PORT, timeout: float = 6.0) -> str:
    """Query a Set/Get/Do variable. Works in any language mode on Link-OS printers.

    Returns the printer's reply (typically a quoted string), or "" if silent.
    """
    payload = f'! U1 getvar "{name}"\r\n'.encode("ascii")
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.sendall(payload)
        connection.settimeout(timeout)
        chunks: list[bytes] = []
        while True:
            try:
                data = connection.recv(4096)
            except socket.timeout:
                break
            if not data:
                break
            chunks.append(data)
            # SGD replies are a quoted value terminated by CR/LF.
            if b"".join(chunks).rstrip().endswith(b'"'):
                break
        return b"".join(chunks).decode("ascii", errors="replace").strip()


def setvar(host: str, name: str, value: str, port: int = DEFAULT_ZPL_PORT, timeout: float = 6.0) -> None:
    """Set a Set/Get/Do variable (fire-and-forget; setvar returns no reply)."""
    payload = f'! U1 setvar "{name}" "{value}"\r\n'.encode("ascii")
    with socket.create_connection((host, port), timeout=timeout) as connection:
        connection.sendall(payload)


# SGD variables worth reading when a label refuses to print. Empty replies are harmless.
_DIAGNOSE_VARS = (
    ("device.languages", "control-language mode"),
    ("head.latch", "print head latched? (ok/open)"),
    ("ezpl.print_method", "direct-thermal vs thermal-transfer"),
    ("ezpl.media_type", "media tracking: continuous / gap / mark"),
    ("media.speed", "print speed"),
    ("print.tone", "darkness / burn tone"),
    ("odometer.total_print_length", "has it ever printed?"),
)


def diagnose(host: str, port: int = DEFAULT_ZPL_PORT, timeout: float = 6.0) -> str:
    """Query a battery of SGD variables and render an aligned report."""
    lines = ["Printer diagnostics (SGD):"]
    for name, why in _DIAGNOSE_VARS:
        reply = getvar(host, name, port=port, timeout=timeout)
        lines.append(f"  {name:28} {reply or '(no reply)':28} {why}")
    return "\n".join(lines)


def decode_status(raw: bytes) -> dict[str, object]:
    """Decode a ~HS reply into the flags most useful for 'why won't it print'."""
    strings = [match.decode("ascii", errors="replace") for match in _STATUS_STRING.findall(raw)]
    result: dict[str, object] = {"strings": strings}
    if not strings:
        return result

    s1 = strings[0].split(",")

    def field(parts: list[str], index: int) -> str:
        return parts[index].strip() if index < len(parts) else ""

    # String 1: aaa,b,c,dddd,eee,f,g,h,iii,j,k,l
    result["paper_out"] = field(s1, 1) == "1"
    result["paused"] = field(s1, 2) == "1"
    result["label_length_dots"] = field(s1, 3)
    result["formats_in_buffer"] = field(s1, 4)
    result["buffer_full"] = field(s1, 5) == "1"
    result["under_temp"] = field(s1, 10) == "1"
    result["over_temp"] = field(s1, 11) == "1"

    if len(strings) >= 2:
        # String 2: mmm,n,o,p,q,r,s,t,uuuuuuuu,v,www
        s2 = strings[1].split(",")
        result["head_open"] = field(s2, 2) == "1"
        result["ribbon_out"] = field(s2, 3) == "1"
        result["thermal_transfer_mode"] = field(s2, 4) == "1"

    return result


def format_status(status: dict[str, object]) -> str:
    """Render decoded status as a human-readable, ordered report."""
    strings = status.get("strings") or []
    if not strings:
        return "No status returned (printer sent no ~HS reply)."

    flags = [
        ("Paper out", status.get("paper_out")),
        ("Paused", status.get("paused")),
        ("Head open", status.get("head_open")),
        ("Ribbon out", status.get("ribbon_out")),
        ("Receive buffer full", status.get("buffer_full")),
        ("Head under temperature", status.get("under_temp")),
        ("Head over temperature", status.get("over_temp")),
    ]
    lines = ["Printer status (~HS):"]
    for label, value in flags:
        if value is None:
            continue
        lines.append(f"  {label:24} {'YES' if value else 'no'}")

    tt = status.get("thermal_transfer_mode")
    if tt is not None:
        lines.append(f"  {'Mode':24} {'thermal-transfer (ribbon)' if tt else 'direct-thermal'}")
    lines.append(f"  {'Formats in buffer':24} {status.get('formats_in_buffer', '?')}")
    lines.append(f"  {'Label length (dots)':24} {status.get('label_length_dots', '?')}")
    lines.append(f"  raw: {' | '.join(strings)}")
    return "\n".join(lines)
