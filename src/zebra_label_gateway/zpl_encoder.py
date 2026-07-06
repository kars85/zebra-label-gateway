"""ZPL generation helpers."""

from __future__ import annotations


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
