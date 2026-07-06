# Zebra Label Gateway

Local middleware for normalizing inconsistent shipping labels into reliable 4x6 ZPL output for a Zebra ZD421 203dpi printer.

## Purpose

Shipping labels arrive in inconsistent formats: native 4x6 PDFs, letter-size PDFs with embedded labels, screenshots, browser print dialogs, Adobe output, and Word documents. Zebra Label Gateway is intended to own the normalization step so those inputs become one predictable 4x6 Zebra print job.

This project is not starting as an Adobe, Word, or browser plugin. Those tools are treated as unreliable input sources. The app should convert anything label-like into a known-good 4x6 ZPL output path.

## Target Printer

- Printer: Zebra / ZDesigner ZD421
- DPI: 203
- Language: ZPL
- Label size: 4x6 inches
- Dot canvas: 812x1218 dots

## MVP Goal

The first milestone is intentionally small:

1. Generate one known-good native ZPL test label.
2. Send it to the ZD421.
3. Confirm printer connection, orientation, label size, and output.

PDF cropping, watched folders, UI, and retailer profiles come after raw ZPL printing works reliably.

## Quick Start

From PowerShell:

```powershell
cd C:\Dev\zebra-label-gateway

py -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip
pip install -e ".[dev]"

pytest

python .\src\zebra_label_gateway\print_tcp.py --host 192.168.x.x --save-only
python .\src\zebra_label_gateway\print_tcp.py --host <actual-printer-ip>
```

Optional printer port test:

```powershell
Test-NetConnection <actual-printer-ip> -Port 9100
```

## Normalizing PDF / Image Labels

`print_label.py` turns a PDF or image into a print-ready 4x6 raster ZPL label.
The pipeline is: detect input type -> render (PDF page 1) or open (image) ->
normalize to a 1-bit 812x1218 canvas -> encode as a `^GFA` raster -> save a
preview and optionally print.

```powershell
# Save ZPL + a preview PNG without printing (review the preview first)
python .\src\zebra_label_gateway\print_label.py --input path\to\label.pdf --save-only

# Normalize and print
python .\src\zebra_label_gateway\print_label.py --input path\to\label.pdf --host <printer-ip>
```

Normalization preserves aspect ratio (letterboxed with white, never stretched)
and auto-rotates landscape sources to portrait, so barcodes stay scannable.
Conversion to black-and-white uses a hard threshold (not dithering); tune it
with `--threshold 0-255` (lower burns less ink). Output lands in `samples/` by
default (`--output-dir` to change) as `<name>.zpl` and `<name>.preview.png`.
Always check the preview before printing.

## Troubleshooting

If a job sends successfully (`Test-NetConnection ... -Port 9100` succeeds and the
script prints `Sent test label to ...`) but nothing prints, the network path is
fine and the problem is on the printer. `print_tcp.py` has diagnostic modes that
query the printer directly instead of guessing:

```powershell
# Decoded ~HS host status: paper-out, pause, head-open, ribbon-out, temp, buffer
python .\src\zebra_label_gateway\print_tcp.py --host <printer-ip> --status

# Battery of SGD variables (language mode, head latch, print method, media, darkness)
python .\src\zebra_label_gateway\print_tcp.py --host <printer-ip> --diagnose

# Read or write any single SGD variable (works in any language mode)
python .\src\zebra_label_gateway\print_tcp.py --host <printer-ip> --getvar device.languages
python .\src\zebra_label_gateway\print_tcp.py --host <printer-ip> --setvar device.languages zpl
```

### Gotcha: `epl_zpl` dual-language mode silently drops ZPL jobs

If `--getvar device.languages` returns `"epl_zpl"`, the printer auto-detects the
language of each incoming job. That auto-detect can misfire on valid ZPL and
**discard the whole job with no motion and no error** — and `~HS` status queries
also go unanswered, so `--status` reports "No status returned".

Fix by locking the printer to ZPL-only processing:

```powershell
python .\src\zebra_label_gateway\print_tcp.py --host <printer-ip> --setvar device.languages zpl
```

The printer normalizes this to `hybrid_xml_zpl`. After the change, `--status`
should return a decoded report and labels print. The setting persists across
reboots but reverts to `epl_zpl` on a factory reset, so re-apply it if the
printer is ever reset.

## Safety Note

Do not commit real labels or private shipping data. That includes names, addresses, tracking numbers, barcodes, QR codes, order numbers, and screenshots of real shipments.
