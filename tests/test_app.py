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


def test_save_profile_command(tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("ZLG_DATA_DIR", str(tmp_path))
    code = main(["save-profile", "--name", "cli_prof", "--crop", "0.1,0.1,0.9,0.9",
                 "--rotate", "90", "--threshold", "130"])
    assert code == 0
    assert (tmp_path / "profiles.yaml").exists()

    from zebra_label_gateway.profiles import load_profiles

    assert load_profiles()["cli_prof"].rotate == 90


def test_save_profile_command_bad_crop(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZLG_DATA_DIR", str(tmp_path))
    assert main(["save-profile", "--name", "x", "--crop", "0.1,0.2"]) == 1
