# Architecture

## Pipeline

```text
input source -> detection -> normalization -> preview -> ZPL output -> printer transport
```

## Initial Scope

The initial implementation focuses only on native ZPL generation and raw TCP transport.

## Planned Components

- `input_detection.py`: identify PDF, image, and ZPL inputs.
- `pdf_renderer.py`: render PDF pages to images.
- `image_processor.py`: rotate, resize, threshold, and normalize images.
- `crop_detector.py`: detect or apply crop regions.
- `zpl_encoder.py`: produce native and raster ZPL payloads.
- `printer_tcp.py`: send raw ZPL to port 9100.
- `printer_windows.py`: future Windows print queue support.
- `watcher.py`: future LabelDrop watched-folder workflow.
