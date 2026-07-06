import pytest

from zebra_label_gateway import transport
from zebra_label_gateway.config import PrinterConfig


def _printer(connection_type: str) -> PrinterConfig:
    return PrinterConfig(
        name="test",
        dpi=203,
        label_width_in=4,
        label_height_in=6,
        output_width_dots=812,
        output_height_dots=1218,
        connection_type=connection_type,
        tcp_host="10.0.0.5",
        tcp_port=9100,
        windows_queue_name="Zebra Queue",
    )


def test_tcp_routing(monkeypatch) -> None:
    sent = {}

    def fake_send(zpl, host, port):
        sent.update(zpl=zpl, host=host, port=port)

    monkeypatch.setattr(transport, "send_zpl_tcp", fake_send)
    where = transport.send_zpl("^XA^XZ", _printer("tcp"))
    assert sent == {"zpl": "^XA^XZ", "host": "10.0.0.5", "port": 9100}
    assert "10.0.0.5:9100" in where


def test_windows_routing(monkeypatch) -> None:
    sent = {}
    monkeypatch.setattr(transport, "send_zpl_windows", lambda zpl, queue: sent.update(zpl=zpl, queue=queue))
    where = transport.send_zpl("^XA^XZ", _printer("windows"))
    assert sent == {"zpl": "^XA^XZ", "queue": "Zebra Queue"}
    assert "windows queue" in where


def test_unknown_transport_raises() -> None:
    with pytest.raises(ValueError):
        transport.send_zpl("^XA^XZ", _printer("carrier-pigeon"))
