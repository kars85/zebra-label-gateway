"""ZPL generation helpers."""

from __future__ import annotations

from PIL import Image


LABEL_WIDTH_DOTS = 812
LABEL_HEIGHT_DOTS = 1218


def build_test_label_zpl() -> str:
    """Return a deterministic native ZPL 4x6-ish test label."""
    return "\n".join(
        [
            "^XA",
            "^PW812",
            "^LL1218",
            "^FO40,40^GB730,1130,4^FS",
            "^FO80,100^A0N,55,55^FDZebra Label Gateway^FS",
            "^FO80,180^A0N,35,35^FDZD421 203dpi ZPL Test^FS",
            "^FO80,260^BY3",
            "^BCN,120,Y,N,N",
            "^FD123456789012^FS",
            "^FO80,450^A0N,35,35^FDIf this printed correctly:^FS",
            "^FO100,510^A0N,32,32^FD- Printer connection works^FS",
            "^FO100,560^A0N,32,32^FD- ZPL is being accepted^FS",
            "^FO100,610^A0N,32,32^FD- Label size is close to 4x6^FS",
            "^XZ",
            "",
        ]
    )


def build_raster_label_zpl(
    image: Image.Image,
    width_dots: int = LABEL_WIDTH_DOTS,
    height_dots: int = LABEL_HEIGHT_DOTS,
) -> str:
    """Encode a 1-bit :class:`PIL.Image` as a native ZPL ``^GFA`` raster label.

    In ZPL a set bit (1) prints black, whereas PIL mode "1" stores white as 1;
    rows are padded to a byte boundary with white so no black edge stripe
    appears, then every byte is inverted so black pixels become set bits.
    """
    mono = image.convert("1")
    bytes_per_row = (mono.width + 7) // 8
    padded_width = bytes_per_row * 8
    if padded_width != mono.width:
        padded = Image.new("1", (padded_width, mono.height), color=1)  # white padding
        padded.paste(mono, (0, 0))
        mono = padded

    inverted = bytes(byte ^ 0xFF for byte in mono.tobytes())
    total_bytes = len(inverted)
    hex_data = inverted.hex().upper()

    return "\n".join(
        [
            "^XA",
            f"^PW{width_dots}",
            f"^LL{height_dots}",
            "^FO0,0",
            f"^GFA,{total_bytes},{total_bytes},{bytes_per_row},{hex_data}",
            "^FS",
            "^XZ",
            "",
        ]
    )
