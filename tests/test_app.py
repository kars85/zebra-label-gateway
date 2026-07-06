import fitz

from zebra_label_gateway.app import build_parser, main


def _make_pdf(path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=288, height=432)
    page.insert_text((20, 40), "LABEL")
    doc.save(path)
    doc.close()


def test_parser_has_all_commands() -> None:
    parser = build_parser()
    # Argparse stores subcommand names on the subparsers action.
    sub = next(a for a in parser._actions if a.dest == "command")
    for name in ("test-label", "print", "watch", "status", "diagnose", "profiles", "ui"):
        assert name in sub.choices


def test_profiles_command(capsys) -> None:
    assert main(["profiles"]) == 0
    out = capsys.readouterr().out
    assert "generic_4x6" in out
    assert "ups" in out


def test_print_save_only(tmp_path, capsys) -> None:
    pdf = tmp_path / "job.pdf"
    _make_pdf(pdf)
    code = main(["print", "--input", str(pdf), "--save-only", "--output-dir", str(tmp_path)])
    assert code == 0
    assert (tmp_path / "job.zpl").exists()
    assert (tmp_path / "job.preview.png").exists()


def test_print_missing_input(tmp_path) -> None:
    code = main(["print", "--input", str(tmp_path / "nope.pdf"), "--save-only"])
    assert code == 1
