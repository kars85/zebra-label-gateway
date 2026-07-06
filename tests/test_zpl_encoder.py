from PIL import Image

from zebra_label_gateway.print_tcp import save_zpl
from zebra_label_gateway.zpl_encoder import build_raster_label_zpl, build_test_label_zpl


def test_test_label_zpl_contains_expected_canvas() -> None:
    zpl = build_test_label_zpl()
    assert "^XA" in zpl
    assert "^PW812" in zpl
    assert "^LL1218" in zpl
    assert "^XZ" in zpl


def test_test_label_zpl_contains_barcode() -> None:
    zpl = build_test_label_zpl()
    assert "^BCN,120,Y,N,N" in zpl
    assert "^FD123456789012^FS" in zpl


def test_save_zpl_writes_ascii_file(tmp_path) -> None:
    output_path = tmp_path / "test-label.zpl"
    saved_path = save_zpl(build_test_label_zpl(), output_path)
    assert saved_path == output_path
    assert output_path.read_text(encoding="ascii").startswith("^XA")


def test_raster_label_zpl_byte_counts_are_consistent() -> None:
    # 16x16 image: 2 bytes/row * 16 rows = 32 bytes of graphic data.
    image = Image.new("1", (16, 16), color=1)
    zpl = build_raster_label_zpl(image, width_dots=16, height_dots=16)

    assert zpl.startswith("^XA")
    assert "^GFA,32,32,2," in zpl
    assert "^XZ" in zpl


def test_raster_label_pads_rows_to_byte_boundary() -> None:
    # 812-dot width rounds up to 102 bytes/row (816 bits), padded with white.
    image = Image.new("1", (812, 4), color=1)
    zpl = build_raster_label_zpl(image, width_dots=812, height_dots=4)
    assert "^GFA,408,408,102," in zpl  # 102 bytes/row * 4 rows


def test_raster_all_white_image_encodes_to_zeros() -> None:
    # White pixels (PIL 1) invert to 0x00 so they print as blank, not black.
    image = Image.new("1", (8, 1), color=1)
    zpl = build_raster_label_zpl(image, width_dots=8, height_dots=1)
    assert "^GFA,1,1,1,00" in zpl
