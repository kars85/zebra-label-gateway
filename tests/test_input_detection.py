from zebra_label_gateway.input_detection import detect_input_type


def test_detects_pdf() -> None:
    assert detect_input_type("label.PDF") == "pdf"


def test_detects_images() -> None:
    assert detect_input_type("label.png") == "image"
    assert detect_input_type("label.jpeg") == "image"


def test_detects_zpl() -> None:
    assert detect_input_type("label.zpl") == "zpl"


def test_unknown_extension() -> None:
    assert detect_input_type("label.docx") == "unknown"
