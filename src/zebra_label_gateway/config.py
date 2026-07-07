"""Configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]


def config_dir() -> Path:
    """Locate the config directory across dev, installed, and container layouts.

    Order: ``ZLG_CONFIG_DIR`` env var, the source-tree ``config/`` (dev), the
    working directory's ``config/`` (the container's ``/app/config``), then
    ``/app/config``. Falls back to the source-tree path if none exist yet.
    """
    candidates = []
    env = os.environ.get("ZLG_CONFIG_DIR")
    if env:
        candidates.append(Path(env))
    candidates += [REPO_ROOT / "config", Path.cwd() / "config", Path("/app/config")]
    for candidate in candidates:
        if (candidate / "default.yaml").exists():
            return candidate
    return candidates[0]


def config_path(name: str) -> Path:
    """Return the path to a named config file (e.g. ``default.yaml``)."""
    return config_dir() / name


DEFAULT_CONFIG_PATH = config_path("default.yaml")


@dataclass(frozen=True)
class PrinterConfig:
    name: str
    dpi: int
    label_width_in: int
    label_height_in: int
    output_width_dots: int
    output_height_dots: int
    connection_type: str
    tcp_host: str
    tcp_port: int
    windows_queue_name: str


@dataclass(frozen=True)
class FoldersConfig:
    input: Path
    printed: Path
    failed: Path


@dataclass(frozen=True)
class PrintingConfig:
    preview_before_print: bool
    auto_print: bool


@dataclass(frozen=True)
class AppConfig:
    printer: PrinterConfig
    folders: FoldersConfig
    printing: PrintingConfig


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}")
    return data


def load_default_config() -> dict[str, Any]:
    return load_yaml(DEFAULT_CONFIG_PATH)


def load_printer_config(path: Path = DEFAULT_CONFIG_PATH) -> PrinterConfig:
    data = load_yaml(path)
    printer = data.get("printer", {})
    if not isinstance(printer, dict):
        raise ValueError("printer config must be a mapping")
    return PrinterConfig(
        name=str(printer["name"]),
        dpi=int(printer["dpi"]),
        label_width_in=int(printer["label_width_in"]),
        label_height_in=int(printer["label_height_in"]),
        output_width_dots=int(printer["output_width_dots"]),
        output_height_dots=int(printer["output_height_dots"]),
        connection_type=str(printer["connection_type"]),
        tcp_host=str(printer["tcp_host"]),
        tcp_port=int(printer["tcp_port"]),
        windows_queue_name=str(printer["windows_queue_name"]),
    )


def load_folders_config(path: Path = DEFAULT_CONFIG_PATH) -> FoldersConfig:
    folders = load_yaml(path).get("folders", {})
    if not isinstance(folders, dict):
        raise ValueError("folders config must be a mapping")
    return FoldersConfig(
        input=Path(folders["input"]),
        printed=Path(folders["printed"]),
        failed=Path(folders["failed"]),
    )


def load_printing_config(path: Path = DEFAULT_CONFIG_PATH) -> PrintingConfig:
    printing = load_yaml(path).get("printing", {})
    if not isinstance(printing, dict):
        raise ValueError("printing config must be a mapping")
    return PrintingConfig(
        preview_before_print=bool(printing.get("preview_before_print", True)),
        auto_print=bool(printing.get("auto_print", False)),
    )


def load_app_config(path: Path = DEFAULT_CONFIG_PATH) -> AppConfig:
    """Load the full application config (printer, folders, printing)."""
    return AppConfig(
        printer=load_printer_config(path),
        folders=load_folders_config(path),
        printing=load_printing_config(path),
    )
