from zebra_label_gateway.print_tcp import save_zpl
from zebra_label_gateway.zpl_encoder import build_test_label_zpl


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
