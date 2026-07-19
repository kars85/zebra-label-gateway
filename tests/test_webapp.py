import io
import tomllib
from pathlib import Path

import fitz
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from zebra_label_gateway.webapp import server


def _pdf_bytes() -> bytes:
    doc = fitz.open()
    page = doc.new_page(width=288, height=432)
    page.insert_text((20, 40), "WEBAPP TEST")
    page.draw_rect(fitz.Rect(20, 200, 260, 260), fill=(0, 0, 0))
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Isolate saved-label history to a temp data dir per test.
    monkeypatch.setenv("ZLG_DATA_DIR", str(tmp_path / "data"))
    return TestClient(server.create_app())


def test_profiles_endpoint(client) -> None:
    data = client.get("/api/profiles").json()
    names = {p["name"] for p in data}
    assert "generic_4x6" in names and "ups" in names


def test_index_served(client) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert "Zebra Label Gateway" in res.text


def test_pwa_assets_served(client) -> None:
    manifest = client.get("/manifest.webmanifest").json()
    assert client.get("/sw.js").status_code == 200
    for icon in manifest["icons"]:
        response = client.get(icon["src"])
        assert response.status_code == 200 and response.content.startswith(b"\x89PNG")
    touch_icon = client.get("/static/pwa/icons/apple-touch-icon.png?v=2")
    assert Image.open(io.BytesIO(touch_icon.content)).size == (180, 180)


def test_pwa_assets_are_packaged() -> None:
    project = tomllib.loads((Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8"))
    package_data = project["tool"]["setuptools"]["package-data"]["zebra_label_gateway.webapp"]
    assert {"static/pwa/*", "static/pwa/icons/*"} <= set(package_data)


def test_upload_render_print_flow(client, monkeypatch) -> None:
    # Upload
    up = client.post("/api/upload", files={"file": ("label.pdf", _pdf_bytes(), "application/pdf")})
    assert up.status_code == 200
    session = up.json()
    assert session["width"] > 0 and session["height"] > 0
    sid = session["id"]

    # Source preview is a PNG
    src = client.get(session["source_url"])
    assert src.status_code == 200 and src.content[:8] == b"\x89PNG\r\n\x1a\n"

    # Render with a manual crop + rotation + threshold
    payload = {"id": sid, "profile": "generic_4x6", "rotate": 90, "threshold": 100,
               "crop_mode": "manual", "crop": [0.0, 0.0, 1.0, 0.5]}
    rendered = client.post("/api/render", json=payload)
    assert rendered.status_code == 200
    assert rendered.content[:8] == b"\x89PNG\r\n\x1a\n"
    assert int(rendered.headers["X-Zpl-Bytes"]) > 0

    # Print (mock the transport)
    sent = {}
    monkeypatch.setattr(server, "send_zpl_tcp", lambda zpl, host, port: sent.update(zpl=zpl, host=host, port=port))
    printed = client.post("/api/print", json={"id": sid, "profile": "generic_4x6", "crop_mode": "auto"})
    assert printed.status_code == 200
    assert printed.json()["ok"] is True
    assert sent["zpl"].startswith("^XA")


def test_upload_and_print_raw_zpl(client, monkeypatch) -> None:
    raw = b"^XA\r\n^FDcaf\xe9^FS\r\n^XZ"
    expected = "^XA\r\n^FDcaf^FS\r\n^XZ"
    sent = {}
    monkeypatch.setenv("ZLG_PRINTER_HOST", "10.9.8.7")
    monkeypatch.setenv("ZLG_PRINTER_PORT", "9999")
    monkeypatch.setattr(
        server,
        "send_zpl_tcp",
        lambda zpl, host, port: sent.update(zpl=zpl, host=host, port=port),
    )

    uploaded = client.post(
        "/api/upload",
        files={"file": ("label.ZPL", raw, "application/octet-stream")},
    )

    assert uploaded.status_code == 200
    session = uploaded.json()
    assert session["kind"] == "zpl" and session["zpl_bytes"] == len(expected)
    assert client.post("/api/render", json={"id": session["id"]}).status_code == 400

    printed = client.post("/api/print", json={"id": session["id"]})
    assert printed.status_code == 200
    assert sent == {"zpl": expected, "host": "10.9.8.7", "port": 9999}


def _multipage_pdf_bytes(pages: int = 3) -> bytes:
    doc = fitz.open()
    for i in range(pages):
        doc.new_page(width=288, height=432).insert_text((20, 40), f"PAGE {i + 1}")
    out = io.BytesIO()
    doc.save(out)
    doc.close()
    return out.getvalue()


def test_multipage_upload_and_page_render(client) -> None:
    up = client.post("/api/upload", files={"file": ("multi.pdf", _multipage_pdf_bytes(3), "application/pdf")})
    assert up.status_code == 200
    session = up.json()
    assert session["pages"] == 3
    sid = session["id"]

    # Each page's source preview is fetchable.
    for page in range(3):
        res = client.get(f"/api/source/{sid}?page={page}")
        assert res.status_code == 200 and res.content[:8] == b"\x89PNG\r\n\x1a\n"

    # Rendering page 2 works.
    r = client.post("/api/render", json={"id": sid, "page": 2, "profile": "generic_4x6"})
    assert r.status_code == 200 and int(r.headers["X-Zpl-Bytes"]) > 0


def test_print_saves_and_manages_history(client, monkeypatch) -> None:
    monkeypatch.setattr(server, "send_zpl_tcp", lambda zpl, host, port: None)
    up = client.post("/api/upload", files={"file": ("hlabel.pdf", _pdf_bytes(), "application/pdf")}).json()
    client.post("/api/print", json={"id": up["id"], "profile": "generic_4x6", "crop_mode": "profile"})

    hist = client.get("/api/history").json()
    assert len(hist) == 1
    entry = hist[0]
    assert entry["name"] == "hlabel.pdf" and entry["printed"] is True

    # Preview PNG fetchable
    prev = client.get(f"/api/history/{entry['id']}/preview")
    assert prev.status_code == 200 and prev.content[:8] == b"\x89PNG\r\n\x1a\n"

    # Reprint (transport mocked) and delete
    assert client.post(f"/api/history/{entry['id']}/reprint").json()["ok"] is True
    assert client.delete(f"/api/history/{entry['id']}").status_code == 200
    assert client.get("/api/history").json() == []


def test_history_missing_entry(client) -> None:
    assert client.get("/api/history/nope/preview").status_code == 404
    assert client.post("/api/history/nope/reprint").status_code == 404
    assert client.delete("/api/history/nope").status_code == 404


def test_save_profile_endpoint(client) -> None:
    res = client.post("/api/profiles/save", json={
        "name": "trained_ups", "crop": [0.1, 0.1, 0.8, 0.7], "rotate": 0,
        "threshold": 120, "page_type": "letter", "description": "from real pdf"})
    assert res.status_code == 200 and res.json()["name"] == "trained_ups"
    names = {p["name"] for p in client.get("/api/profiles").json()}
    assert "trained_ups" in names


def test_save_profile_rejects_bad_rotate(client) -> None:
    res = client.post("/api/profiles/save", json={"name": "bad", "rotate": 45})
    assert res.status_code == 400


def test_render_unknown_id(client) -> None:
    res = client.post("/api/render", json={"id": "nope", "profile": "generic_4x6"})
    assert res.status_code == 404


def test_unsupported_upload(client) -> None:
    res = client.post("/api/upload", files={"file": ("notes.docx", b"hello", "application/msword")})
    assert res.status_code == 400


def test_status_offline(client, monkeypatch) -> None:
    monkeypatch.setattr(server, "query_status_raw", lambda host, port, timeout=5.0: (_ for _ in ()).throw(OSError("no route")))
    data = client.get("/api/status").json()
    assert data["ok"] is False


def test_cors_enabled_via_env(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZLG_DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("ZLG_CORS_ORIGINS", "https://word.example")
    c = TestClient(server.create_app())
    res = c.get("/api/profiles", headers={"Origin": "https://word.example"})
    assert res.headers.get("access-control-allow-origin") == "https://word.example"


def test_no_cors_by_default(client) -> None:
    res = client.get("/api/profiles", headers={"Origin": "https://word.example"})
    assert "access-control-allow-origin" not in res.headers


def test_env_overrides_printer(monkeypatch) -> None:
    from zebra_label_gateway.config import PrinterConfig

    base = PrinterConfig("t", 203, 4, 6, 812, 1218, "tcp", "1.1.1.1", 9100, "Q")
    monkeypatch.setenv("ZLG_PRINTER_HOST", "10.9.8.7")
    monkeypatch.setenv("ZLG_PRINTER_PORT", "9999")
    resolved = server.resolve_printer(base)
    assert resolved.tcp_host == "10.9.8.7" and resolved.tcp_port == 9999
