import fitz
import pytest

from zebra_label_gateway.config import AppConfig, FoldersConfig, PrinterConfig, PrintingConfig
from zebra_label_gateway.watcher import process_file, scan_existing


def _make_pdf(path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=288, height=432)
    page.insert_text((20, 40), "LABEL")
    doc.save(path)
    doc.close()


def _config(tmp_path, auto_print: bool) -> AppConfig:
    return AppConfig(
        printer=PrinterConfig("t", 203, 4, 6, 812, 1218, "tcp", "10.0.0.1", 9100, "Q"),
        folders=FoldersConfig(
            input=tmp_path / "In",
            printed=tmp_path / "Printed",
            failed=tmp_path / "Failed",
        ),
        printing=PrintingConfig(preview_before_print=True, auto_print=auto_print),
    )


def test_render_without_printing(tmp_path) -> None:
    config = _config(tmp_path, auto_print=False)
    config.folders.input.mkdir(parents=True)
    pdf = config.folders.input / "job.pdf"
    _make_pdf(pdf)

    outcome = process_file(pdf, config, wait_stable=False)

    assert outcome.status == "rendered"
    assert (config.folders.printed / "job.zpl").exists()
    assert (config.folders.printed / "job.preview.png").exists()
    assert not pdf.exists()  # original moved to printed/
    assert (config.folders.printed / "job.pdf").exists()


def test_print_uses_injected_sender(tmp_path) -> None:
    config = _config(tmp_path, auto_print=True)
    config.folders.input.mkdir(parents=True)
    pdf = config.folders.input / "job.pdf"
    _make_pdf(pdf)
    sent = []

    outcome = process_file(pdf, config, sender=lambda zpl: sent.append(zpl) or "fake-dest", wait_stable=False)

    assert outcome.status == "printed"
    assert len(sent) == 1 and sent[0].startswith("^XA")
    assert "printed to fake-dest" in outcome.detail


def test_failure_routes_to_failed(tmp_path) -> None:
    config = _config(tmp_path, auto_print=False)
    config.folders.input.mkdir(parents=True)
    bad = config.folders.input / "broken.pdf"
    bad.write_bytes(b"not a real pdf")

    outcome = process_file(bad, config, wait_stable=False)

    assert outcome.status == "failed"
    assert (config.folders.failed / "broken.pdf").exists()
    assert (config.folders.failed / "broken.error.txt").exists()


def test_unsupported_type_skipped(tmp_path) -> None:
    config = _config(tmp_path, auto_print=False)
    config.folders.input.mkdir(parents=True)
    doc = config.folders.input / "notes.docx"
    doc.write_text("hello")

    outcome = process_file(doc, config, wait_stable=False)
    assert outcome.status == "skipped"


def test_scan_existing_processes_all(tmp_path) -> None:
    config = _config(tmp_path, auto_print=False)
    config.folders.input.mkdir(parents=True)
    for i in range(3):
        _make_pdf(config.folders.input / f"job{i}.pdf")

    outcomes = scan_existing(config)
    assert len(outcomes) == 3
    assert all(o.status == "rendered" for o in outcomes)
