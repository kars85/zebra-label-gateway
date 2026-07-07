# Architecture

## Pipeline

```text
input source -> detection -> render/open -> crop -> rotate -> normalize -> preview -> ZPL -> transport -> printer
```

The pipeline is deterministic and produces a previewable 1-bit image before any
bytes reach the printer.

## Components

- `input_detection.py`: identify PDF, image, and ZPL inputs by extension.
- `pdf_renderer.py`: render PDF page 1 to an image at 203 dpi (PyMuPDF).
- `crop_detector.py`: auto-crop to the largest connected content region, or
  apply explicit fractional crops from a profile.
- `image_processor.py`: aspect-preserving letterbox onto the 812x1218 canvas,
  auto-rotate, and hard-threshold to 1-bit.
- `profiles/`: crop/rotate/threshold presets, overridable via `config/profiles.yaml`.
- `pipeline.py`: orchestrates the full input -> ZPL flow, shared by the CLI,
  watcher, and web UI.
- `zpl_encoder.py`: native test-label ZPL and `^GFA` raster encoding.
- `printer_tcp.py`: raw TCP transport (port 9100) plus `~HS` status and SGD
  diagnostics.
- `printer_windows.py`: Windows print-spooler transport (RAW jobs via pywin32).
- `transport.py`: routes a payload to TCP or the Windows queue by config.
- `watcher.py`: LabelDrop watched-folder workflow.
- `ui/web.py`: basic local preview web UI (stdlib http.server, no deps).
- `webapp/`: full FastAPI web app -- upload, live crop/rotate/threshold editor,
  and print. Served in the Docker image (see `Dockerfile`, `docker-compose.yml`).
- `app.py`: unified CLI entry point.
- `config.py`: typed loaders for printer, folders, and printing config, with
  layout-independent config-dir resolution (env, source tree, or container).

