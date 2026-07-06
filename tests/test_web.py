import threading
import urllib.parse
import urllib.request
from http.server import ThreadingHTTPServer

import fitz
import pytest

from zebra_label_gateway.config import AppConfig, FoldersConfig, PrinterConfig, PrintingConfig
from zebra_label_gateway.ui import web


def _config() -> AppConfig:
    return AppConfig(
        printer=PrinterConfig("t", 203, 4, 6, 812, 1218, "tcp", "10.0.0.1", 9100, "Q"),
        folders=FoldersConfig(input=__import__("pathlib").Path("."), printed=__import__("pathlib").Path("."),
                              failed=__import__("pathlib").Path(".")),
        printing=PrintingConfig(True, False),
    )


@pytest.fixture()
def server():
    handler = type("BoundHandler", (web._Handler,), {"config": _config()})
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    host, port = httpd.server_address
    yield f"http://{host}:{port}"
    httpd.shutdown()
    httpd.server_close()


def test_page_lists_profiles() -> None:
    body = web._page(_config()).decode("utf-8")
    assert "Zebra Label Gateway" in body
    assert "generic_4x6" in body
    assert "Render &amp; print" in body


def test_get_root(server) -> None:
    with urllib.request.urlopen(server + "/") as resp:
        assert resp.status == 200
        assert b"Zebra Label Gateway" in resp.read()


def test_render_roundtrip(server, tmp_path) -> None:
    pdf = tmp_path / "web.pdf"
    doc = fitz.open()
    doc.new_page(width=288, height=432).insert_text((20, 40), "WEB")
    doc.save(pdf)
    doc.close()

    data = urllib.parse.urlencode({"path": str(pdf), "profile": "generic_4x6", "action": "render"}).encode()
    req = urllib.request.Request(server + "/process", data=data)
    opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
    with opener.open(req) as resp:
        final_body = resp.read()
    assert b"Rendered web.pdf" in final_body

    # The preview PNG should now be fetchable.
    with urllib.request.urlopen(server + "/preview?name=web") as resp:
        assert resp.status == 200
        assert resp.read(8) == b"\x89PNG\r\n\x1a\n"  # PNG magic
