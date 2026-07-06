# ZPL Output

## Native Test Label

The first supported output is a native ZPL test label using `^PW812` and `^LL1218`.

## Future Raster Output

Normalized 1-bit images will be encoded as ZPL graphics payloads after PDF and image normalization are stable.

## Determinism

Printer output should be reproducible from saved `.zpl` files. Generated samples are ignored by Git because they may contain private label data in later phases.
