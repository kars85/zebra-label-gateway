"""Package the LibreOffice extension into plugins/zebra-label-gateway.oxt.

Run from anywhere:  python plugins/libreoffice/build.py
An .oxt is just a ZIP with a specific layout; order/content is what matters.
"""

from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "zebra-label-gateway.oxt"
FILES = [
    "description.xml",
    "Addons.xcu",
    "Scripts/python/zlg_gateway.py",
    "META-INF/manifest.xml",
]


def build() -> Path:
    with ZipFile(OUT, "w", ZIP_DEFLATED) as zf:
        for rel in FILES:
            zf.write(HERE / rel, rel)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"Wrote {path} ({path.stat().st_size} bytes)")
