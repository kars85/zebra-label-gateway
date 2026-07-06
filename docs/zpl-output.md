# ZPL Output

## Native Test Label

The first supported output is a native ZPL test label using `^PW812` and `^LL1218`.

## Raster Output

Normalized 1-bit images are encoded as `^GFA` ZPL graphics payloads by
`zpl_encoder.build_raster_label_zpl`. Black pixels become set bits, and each row
is padded to a byte boundary with white so no black edge stripe appears. Byte
counts in the `^GFA` header are computed as `bytes_per_row = ceil(width / 8)` and
`total = bytes_per_row * height`.

## Determinism

Printer output should be reproducible from saved `.zpl` files. Generated samples are ignored by Git because they may contain private label data in later phases.
