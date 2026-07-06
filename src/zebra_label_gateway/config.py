"""Configuration helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = REPO_ROOT / "config" / "default.yaml"


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
