from zebra_label_gateway.storage import HistoryStore


def _png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"fakepngdata"


def test_add_and_list(tmp_path) -> None:
    store = HistoryStore(tmp_path)
    entry = store.add("label.pdf", "ups", 0, _png(), "^XA^XZ", printed=True, when="2026-07-06T12:00:00+00:00")
    listed = store.list()
    assert len(listed) == 1
    assert listed[0]["id"] == entry.id
    assert listed[0]["name"] == "label.pdf"
    assert listed[0]["printed"] is True
    assert listed[0]["preview_url"].endswith(f"/{entry.id}/preview")


def test_newest_first(tmp_path) -> None:
    store = HistoryStore(tmp_path)
    a = store.add("a.pdf", "p", 0, _png(), "^XA^XZ", printed=True, when="2026-01-01T00:00:00+00:00")
    b = store.add("b.pdf", "p", 0, _png(), "^XA^XZ", printed=True, when="2026-01-02T00:00:00+00:00")
    ids = [e["id"] for e in store.list()]
    assert ids == [b.id, a.id]


def test_zpl_and_preview_roundtrip(tmp_path) -> None:
    store = HistoryStore(tmp_path)
    entry = store.add("x.pdf", "p", 1, _png(), "^XAraster^XZ", printed=False)
    assert store.zpl(entry.id) == "^XAraster^XZ"
    assert store.preview_path(entry.id).read_bytes() == _png()


def test_delete_removes_files(tmp_path) -> None:
    store = HistoryStore(tmp_path)
    entry = store.add("x.pdf", "p", 0, _png(), "^XA^XZ", printed=True)
    assert store.delete(entry.id) is True
    assert store.list() == []
    assert store.preview_path(entry.id) is None
    assert store.zpl(entry.id) is None
    assert store.delete("missing") is False


def test_capping_prunes_oldest(tmp_path) -> None:
    store = HistoryStore(tmp_path, max_entries=3)
    ids = [store.add(f"{i}.pdf", "p", 0, _png(), "^XA^XZ", printed=True,
                     when=f"2026-01-0{i}T00:00:00+00:00").id for i in range(1, 6)]
    listed = [e["id"] for e in store.list()]
    assert len(listed) == 3
    # Oldest two pruned (files gone), newest three kept.
    assert ids[0] not in listed and ids[1] not in listed
    assert store.preview_path(ids[0]) is None
