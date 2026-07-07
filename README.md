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

## Command-Line Interface

The unified entry point is `zebra_label_gateway.app` (installed as the
`zebra-label-gateway` command after `pip install -e .`). Printer host/port and
folders default to `config/default.yaml`; flags override them.

```powershell
python -m zebra_label_gateway.app --help

python -m zebra_label_gateway.app profiles                       # list normalization profiles
python -m zebra_label_gateway.app test-label --host <printer-ip> # built-in ZPL test label
python -m zebra_label_gateway.app print --input label.pdf --profile ups --save-only
python -m zebra_label_gateway.app print --input label.pdf --host <printer-ip>
python -m zebra_label_gateway.app status   --host <printer-ip>   # decoded ~HS
python -m zebra_label_gateway.app diagnose --host <printer-ip>   # SGD diagnostics
python -m zebra_label_gateway.app watch --profile ups            # LabelDrop watched folder
python -m zebra_label_gateway.app ui                             # local preview web UI
```

## Normalizing PDF / Image Labels

The `print` command (and `print_label.py`) turns a PDF or image into a
print-ready 4x6 raster ZPL label. The pipeline is: detect input type -> render
(PDF page 1) or open (image) -> crop and rotate per profile -> normalize to a
1-bit 812x1218 canvas -> encode as a `^GFA` raster -> save a preview and
optionally print.

Normalization preserves aspect ratio (letterboxed with white, never stretched)
and auto-rotates landscape sources to portrait, so barcodes stay scannable.
Conversion to black-and-white uses a hard threshold (not dithering). Output
lands in `samples/` by default (`--output-dir` to change) as `<name>.zpl` and
`<name>.preview.png`. Always check the preview before printing.

### Profiles

Profiles are crop/rotate/threshold presets per label source. `generic_4x6`
prints a full-page 4x6 as-is; `generic_letter_embedded`, `ups`, `fedex`,
`usps`, and `amazon_return` auto-crop a label out of a larger page. Auto-crop
finds the largest connected block of dark content, so a stray footer or packing
slip on the page does not defeat it. Override or add profiles in
`config/profiles.yaml` (crop may be `auto`, `null`, or four `0..1` fractions;
threshold may be `light`/`standard`/`dark` or `0-255`).

## Watched Folder (LabelDrop)

`watch` monitors the input folder from `config/default.yaml`. Each dropped PDF
or image is normalized, its preview and ZPL saved to the printed folder, and the
original moved to `printed/` on success or `failed/` on error (with an
`.error.txt`). Printing happens only when `printing.auto_print` is enabled (or
`--print` is passed); otherwise it renders previews for manual review. Failures
never crash the watcher.

## Web UI (interactive editor)

The full-featured editor is a FastAPI app: upload a PDF/image, then crop
(drag box or auto), rotate, and adjust the threshold with a live 4x6 preview
before printing. Run it locally:

```powershell
pip install -e ".[web]"
python -m zebra_label_gateway.app ui        # http://127.0.0.1:8000
```

`ui` falls back to a basic stdlib preview UI if the `[web]` extra is not
installed.

The editor also supports:

- **Multi-page PDFs** — Prev/Next page navigation; each page normalizes and
  prints independently.
- **Saved label history** — every printed label is kept (preview + exact ZPL) in
  a "Recent labels" grid; **Reprint** re-sends the stored ZPL, **Delete** removes
  it. Persisted under the data dir (`ZLG_DATA_DIR`).
- **Crop preset training** — in Manual crop mode, frame a real label with the
  drag box and **Save crop as profile…**. The tuned crop/rotate/threshold is
  written to `<data_dir>/profiles.yaml` and auto-applies next time. The same is
  scriptable: `zebra-label-gateway save-profile --name ups_returns --crop
  l,t,r,b --rotate 0 --threshold 128`.

## Docker

The web app runs in a container that reaches the printer over TCP (no host
printer drivers needed). The printer is configured with environment variables.

```bash
docker build -t zebra-label-gateway:latest .
docker run -d -p 8000:8000 \
  -e ZLG_PRINTER_HOST=10.10.100.107 -e ZLG_PRINTER_PORT=9100 \
  zebra-label-gateway:latest
# open http://localhost:8000
```

Or with Compose (set the printer host, and a host port if 8000 is reserved):

```bash
ZLG_PRINTER_HOST=10.10.100.107 ZLG_HOST_PORT=8420 docker compose up -d --build
```

Environment variables: `ZLG_PRINTER_HOST` (required), `ZLG_PRINTER_PORT`
(default 9100), `ZLG_CONFIG_DIR` (default `/app/config`), `ZLG_DATA_DIR`
(default `/app/data`). The container runs as a non-root user and includes a
healthcheck against `/api/profiles`. Saved-label history and trained crop
profiles live in `/app/data`, which Compose mounts as the persistent `zlg-data`
volume so they survive restarts.

## iPhone / iPad (installable PWA)

The web app is an installable PWA — add it to the Home Screen for a standalone,
offline-capable app with a native icon, safe-area layout, touch-sized crop
handles, and camera capture (photograph a paper label straight into the
pipeline). iOS requires HTTPS for install, so run the bundled Caddy TLS sidecar:

```bash
ZLG_HOSTNAME=gateway.local ZLG_PRINTER_HOST=10.10.100.107 \
  docker compose --profile tls up -d --build
```

Then trust Caddy's internal CA once per device and Add to Home Screen — full
steps in [docs/tls-setup.md](docs/tls-setup.md). To print from Mail/Files via the
iOS share sheet, build the [Apple Shortcut](docs/ios-shortcut.md) that POSTs to
the API.

## Windows desktop app

A standalone Windows installer runs the gateway in a native window (WebView2) —
no Python or Docker on the target machine. Build it with
`pwsh packaging\build.ps1` (frontend → PyInstaller → NSIS), producing
`ZebraLabelGateway-Setup.exe`. Printer settings are configured in-app; history
persists under `%LOCALAPPDATA%\ZebraLabelGateway`. See
[docs/desktop-installer.md](docs/desktop-installer.md).

## Application plugins

Send a document straight to the gateway from your authoring app:

- **LibreOffice** — an `.oxt` extension adds *Send / Send & Print* to Tools →
  Add-Ons and a toolbar button.
- **Microsoft Word** — an Office-JS task-pane add-in adds a ribbon button
  (needs the HTTPS gateway host).
- **Adobe / everything else** — use the LabelDrop watched folder instead of a
  per-app plugin.

Build and install steps are in [docs/plugins.md](docs/plugins.md).

## Frontend development

The UI is a Vite + Svelte 5 + TypeScript app in `web/`, built to
`src/zebra_label_gateway/webapp/static/dist/` and served by FastAPI. Design
tokens and the component system are documented in [DESIGN.md](DESIGN.md).

```bash
cd web
npm install
npm run dev     # dev server on :5173, proxies /api to :8000
npm run build   # emit production assets served by FastAPI
```

## Windows Printer Queue

The default transport is raw TCP (port 9100). To print through a Windows printer
queue instead, set `printer.connection_type: windows` and
`printer.windows_queue_name` in the config, and install the optional dependency:
`pip install -e ".[windows]"` (pywin32). ZPL is sent as a RAW spool job.

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
