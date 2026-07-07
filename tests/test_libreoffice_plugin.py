"""Tests for the LibreOffice plugin's gateway HTTP helper (no UNO/LibreOffice)."""

import importlib.util
import io
import json
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1] / "plugins" / "libreoffice" / "Scripts" / "python" / "zlg_gateway.py"


@pytest.fixture()
def zlg():
    spec = importlib.util.spec_from_file_location("zlg_gateway", PLUGIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _FakeResponse:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode()

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_upload_only_builds_multipart(zlg, monkeypatch):
    seen = {}

    def fake_urlopen(req, timeout=0):
        seen["url"] = req.full_url
        seen["ctype"] = req.headers.get("Content-type")
        seen["body"] = req.data
        return _FakeResponse({"id": "abc", "width": 812, "height": 1218, "pages": 1})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = zlg._upload_and_maybe_print("http://gw:8000", b"%PDF-fake", "doc.pdf", do_print=False)

    assert seen["url"] == "http://gw:8000/api/upload"
    assert "multipart/form-data; boundary=" in seen["ctype"]
    assert b'name="file"; filename="doc.pdf"' in seen["body"]
    assert b"%PDF-fake" in seen["body"]
    assert "812" in result and "review" in result.lower()


def test_print_flow_calls_print_endpoint(zlg, monkeypatch):
    calls = []

    def fake_urlopen(req, timeout=0):
        calls.append(req.full_url)
        if req.full_url.endswith("/api/upload"):
            return _FakeResponse({"id": "xyz", "width": 812, "height": 1218, "pages": 1})
        assert json.loads(req.data)["id"] == "xyz"
        return _FakeResponse({"ok": True, "detail": "Sent 100 bytes to 10.0.0.1:9100"})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    result = zlg._upload_and_maybe_print("http://gw:8000", b"%PDF", "d.pdf", do_print=True)

    assert calls == ["http://gw:8000/api/upload", "http://gw:8000/api/print"]
    assert "Sent 100 bytes" in result


def test_gateway_url_prefers_env(zlg, monkeypatch):
    monkeypatch.setenv("ZLG_GATEWAY_URL", "http://custom:1234/")
    assert zlg.gateway_url() == "http://custom:1234"
