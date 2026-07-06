from zebra_label_gateway.config import (
    DEFAULT_CONFIG_PATH,
    load_app_config,
    load_folders_config,
    load_printer_config,
    load_printing_config,
)


def test_load_printer_config() -> None:
    printer = load_printer_config()
    assert printer.dpi == 203
    assert printer.output_width_dots == 812
    assert printer.output_height_dots == 1218
    assert printer.tcp_port == 9100


def test_load_folders_config() -> None:
    folders = load_folders_config()
    assert folders.input.name == "In"
    assert folders.printed.name == "Printed"
    assert folders.failed.name == "Failed"


def test_load_printing_config() -> None:
    printing = load_printing_config()
    assert printing.preview_before_print is True
    assert printing.auto_print is False


def test_load_app_config() -> None:
    config = load_app_config(DEFAULT_CONFIG_PATH)
    assert config.printer.dpi == 203
    assert config.printing.auto_print is False
    assert config.folders.input.name == "In"
