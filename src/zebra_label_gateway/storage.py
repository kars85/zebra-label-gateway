"""Persistent saved-label history.

Each entry stores the normalized preview PNG, the exact ZPL that was sent, and
metadata (source name, profile, page, timestamp). Entries live under
``<data_dir>/history`` so they survive restarts when that path is a mounted
volume. The newest entries are kept up to ``max_entries``; older ones are pruned
along with their files.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .config import data_dir

MAX_ENTRIES = 200


@dataclass(frozen=True)
class HistoryEntry:
    id: str
    name: str
    profile: str
    page: int
    created: str  # ISO-8601 UTC
    zpl_bytes: int
    printed: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "profile": self.profile,
            "page": self.page,
            "created": self.created,
            "zpl_bytes": self.zpl_bytes,
            "printed": self.printed,
            "preview_url": f"/api/history/{self.id}/preview",
        }


class HistoryStore:
    def __init__(self, base: Path | None = None, max_entries: int = MAX_ENTRIES) -> None:
        self.dir = (base or data_dir()) / "history"
        self.index = self.dir / "index.json"
        self.max_entries = max_entries

    def _load(self) -> list[dict]:
        if self.index.exists():
            try:
                return json.loads(self.index.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return []
        return []

    def _write(self, entries: list[dict]) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        self.index.write_text(json.dumps(entries, indent=2), encoding="utf-8")

    def _remove_files(self, entry_id: str) -> None:
        for suffix in (".png", ".zpl"):
            (self.dir / f"{entry_id}{suffix}").unlink(missing_ok=True)

    def add(self, name: str, profile: str, page: int, preview_png: bytes, zpl: str,
            printed: bool, when: str | None = None) -> HistoryEntry:
        """Save a label; returns the created entry (newest first in the index)."""
        self.dir.mkdir(parents=True, exist_ok=True)
        entry_id = uuid.uuid4().hex
        (self.dir / f"{entry_id}.png").write_bytes(preview_png)
        (self.dir / f"{entry_id}.zpl").write_text(zpl, encoding="ascii", newline="\n")

        created = when or datetime.now(timezone.utc).isoformat(timespec="seconds")
        entry = HistoryEntry(entry_id, name, profile, page, created, len(zpl), printed)

        entries = [entry.to_dict()] + self._load()
        for stale in entries[self.max_entries:]:
            self._remove_files(stale["id"])
        self._write(entries[: self.max_entries])
        return entry

    def list(self) -> list[dict]:
        return self._load()

    def get(self, entry_id: str) -> dict | None:
        return next((e for e in self._load() if e["id"] == entry_id), None)

    def preview_path(self, entry_id: str) -> Path | None:
        path = self.dir / f"{entry_id}.png"
        return path if path.exists() else None

    def zpl(self, entry_id: str) -> str | None:
        path = self.dir / f"{entry_id}.zpl"
        return path.read_text(encoding="ascii") if path.exists() else None

    def delete(self, entry_id: str) -> bool:
        entries = self._load()
        remaining = [e for e in entries if e["id"] != entry_id]
        if len(remaining) == len(entries):
            return False
        self._remove_files(entry_id)
        self._write(remaining)
        return True
