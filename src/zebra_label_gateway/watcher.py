"""LabelDrop watched-folder workflow.

Drop a PDF or image into the input folder; the gateway normalizes it to 4x6,
writes a preview and ZPL into the printed folder, optionally prints it (when
``printing.auto_print`` is enabled), and moves the original to ``printed`` on
success or ``failed`` on error. Failures never crash the watcher -- they are
recorded next to the moved file.
"""

from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from .config import AppConfig, load_app_config
from .input_detection import detect_input_type
from .pipeline import render_input
from .transport import send_zpl

SUPPORTED_KINDS = {"pdf", "image"}
Sender = Callable[[str], str]


@dataclass(frozen=True)
class ProcessOutcome:
    source: Path
    status: str  # "printed", "rendered", "failed", or "skipped"
    detail: str
    moved_to: Path | None = None


def _unique_destination(directory: Path, name: str) -> Path:
    """Return a non-colliding path in ``directory`` for ``name``."""
    candidate = directory / name
    stem, suffix = candidate.stem, candidate.suffix
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}-{counter}{suffix}"
        counter += 1
    return candidate


def wait_until_stable(path: Path, timeout: float = 10.0, interval: float = 0.3) -> bool:
    """Wait until ``path``'s size stops changing (a proxy for 'finished writing')."""
    deadline = time.monotonic() + timeout
    last_size = -1
    while time.monotonic() < deadline:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == last_size and size > 0:
            return True
        last_size = size
        time.sleep(interval)
    return path.exists()


def process_file(
    path: Path,
    config: AppConfig,
    profile_name: str = "generic_4x6",
    do_print: bool | None = None,
    sender: Sender | None = None,
    wait_stable: bool = True,
) -> ProcessOutcome:
    """Normalize one dropped file, optionally print it, and move the original.

    ``do_print`` overrides ``config.printing.auto_print`` when not ``None``.
    ``sender`` (used only when printing) defaults to the configured transport.
    """
    path = Path(path)
    if detect_input_type(path) not in SUPPORTED_KINDS:
        return ProcessOutcome(path, "skipped", f"unsupported type: {path.name}")

    should_print = config.printing.auto_print if do_print is None else do_print
    config.folders.printed.mkdir(parents=True, exist_ok=True)
    config.folders.failed.mkdir(parents=True, exist_ok=True)

    if wait_stable and not wait_until_stable(path):
        return ProcessOutcome(path, "skipped", "file did not stabilize")

    try:
        result = render_input(path, profile_name)
        zpl_path = config.folders.printed / f"{path.stem}.zpl"
        preview_path = config.folders.printed / f"{path.stem}.preview.png"
        zpl_path.write_text(result.zpl, encoding="ascii", newline="\n")
        result.preview.save(preview_path)

        detail = f"profile={result.profile_name}; preview={preview_path.name}"
        if should_print:
            send = sender or (lambda zpl: send_zpl(zpl, config.printer))
            where = send(result.zpl)
            detail = f"printed to {where}; {detail}"
            status = "printed"
        else:
            detail = f"auto_print disabled; {detail}"
            status = "rendered"

        moved = _unique_destination(config.folders.printed, path.name)
        shutil.move(str(path), str(moved))
        return ProcessOutcome(path, status, detail, moved)
    except Exception as exc:  # noqa: BLE001 - any failure routes the file to failed/
        moved = _unique_destination(config.folders.failed, path.name)
        try:
            shutil.move(str(path), str(moved))
        except OSError:
            moved = None
        error_note = config.folders.failed / f"{path.stem}.error.txt"
        error_note.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        return ProcessOutcome(path, "failed", f"{type(exc).__name__}: {exc}", moved)


def scan_existing(
    config: AppConfig,
    profile_name: str = "generic_4x6",
    do_print: bool | None = None,
) -> list[ProcessOutcome]:
    """Process any files already sitting in the input folder at startup."""
    outcomes = []
    for entry in sorted(config.folders.input.glob("*")):
        if entry.is_file():
            outcomes.append(process_file(entry, config, profile_name, do_print))
    return outcomes


class LabelDropHandler(FileSystemEventHandler):
    """Processes files as they are created/moved into the input folder."""

    def __init__(self, config: AppConfig, profile_name: str, do_print: bool | None,
                 on_outcome: Callable[[ProcessOutcome], None] | None = None) -> None:
        self.config = config
        self.profile_name = profile_name
        self.do_print = do_print
        self.on_outcome = on_outcome or (lambda outcome: None)

    def _handle(self, path_str: str) -> None:
        outcome = process_file(Path(path_str), self.config, self.profile_name, self.do_print)
        self.on_outcome(outcome)

    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory:
            self._handle(event.src_path)

    def on_moved(self, event: FileSystemEvent) -> None:
        dest = getattr(event, "dest_path", None)
        if not event.is_directory and dest:
            self._handle(dest)


def _default_reporter(outcome: ProcessOutcome) -> None:
    print(f"[{outcome.status:8}] {outcome.source.name}: {outcome.detail}")


def start_watcher(
    config_path: Path | None = None,
    profile_name: str = "generic_4x6",
    do_print: bool | None = None,
    on_outcome: Callable[[ProcessOutcome], None] = _default_reporter,
) -> None:
    """Start watching the configured input folder (blocks until interrupted)."""
    config = load_app_config(config_path) if config_path else load_app_config()
    for folder in (config.folders.input, config.folders.printed, config.folders.failed):
        folder.mkdir(parents=True, exist_ok=True)

    for outcome in scan_existing(config, profile_name, do_print):
        on_outcome(outcome)

    handler = LabelDropHandler(config, profile_name, do_print, on_outcome)
    observer = Observer()
    observer.schedule(handler, str(config.folders.input), recursive=False)
    observer.start()
    print(f"Watching {config.folders.input} (auto_print={config.printing.auto_print if do_print is None else do_print}).")
    print("Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()
