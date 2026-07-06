# Label Normalization

Normalization converts inconsistent label-like inputs into a single 812x1218 dot
1-bit canvas.

## Behavior

- Detect input type and preserve the original file (the watcher moves, never
  deletes, originals).
- Render (PDF page 1) or load (image) into an image.
- Apply profile defaults: crop (`auto`, fractional, or none), rotation, threshold.
- Auto-crop finds the largest connected block of dark content, isolating the
  label from stray page content such as footers or packing slips.
- Fit onto the canvas preserving aspect ratio (letterboxed with white, never
  stretched) so barcodes stay scannable; auto-rotate landscape sources.
- Convert to 1-bit with a hard threshold (not dithering, which would corrupt
  barcodes and small text).
- Save a preview image before printing.

Automatic printing stays disabled by default (`printing.auto_print: false`);
the preview is always produced first. Manual override remains available for
questionable inputs.
