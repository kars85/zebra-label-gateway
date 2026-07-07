"""Retailer/carrier profiles: crop, rotation, and threshold presets.

Each built-in profile module exposes a ``PROFILE`` dict. This package turns those
into frozen :class:`Profile` objects and lets ``config/profiles.yaml`` override or
extend them, so operators can tune behavior without editing code. Profiles never
hide irreversible transformations -- a preview is always produced before printing.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from . import (
    amazon_return,
    fedex,
    generic_4x6,
    generic_letter_embedded,
    ups,
    usps,
)

# Named threshold presets map to a 0-255 cutoff; lower burns less ink.
THRESHOLD_ALIASES = {"light": 96, "standard": 128, "dark": 160}
DEFAULT_THRESHOLD = THRESHOLD_ALIASES["standard"]
VALID_ROTATIONS = {0, 90, 180, 270}


@dataclass(frozen=True)
class Profile:
    """A normalization preset for one label source."""

    name: str
    description: str = ""
    page_type: str = "label"  # "label" = full-page 4x6, "letter" = embedded label
    rotate: int = 0  # 0/90/180/270, applied after cropping
    threshold: int = DEFAULT_THRESHOLD  # 0-255 black/white cutoff
    crop: str | tuple[float, float, float, float] | None = None  # None, "auto", or fractions

    def __post_init__(self) -> None:
        if self.rotate not in VALID_ROTATIONS:
            raise ValueError(f"rotate must be one of {sorted(VALID_ROTATIONS)}, got {self.rotate}")
        if not 0 <= self.threshold <= 255:
            raise ValueError(f"threshold must be 0-255, got {self.threshold}")
        if isinstance(self.crop, (tuple, list)):
            if len(self.crop) != 4 or not all(0.0 <= float(v) <= 1.0 for v in self.crop):
                raise ValueError("crop fractions must be four values in 0..1")


def _coerce_threshold(value: Any) -> int:
    if value is None:
        return DEFAULT_THRESHOLD
    if isinstance(value, str):
        if value not in THRESHOLD_ALIASES:
            raise ValueError(f"unknown threshold preset {value!r}; use {list(THRESHOLD_ALIASES)} or 0-255")
        return THRESHOLD_ALIASES[value]
    return int(value)


def _coerce_crop(value: Any) -> str | tuple[float, float, float, float] | None:
    if value is None:
        return None
    if isinstance(value, str):
        if value != "auto":
            raise ValueError(f"crop string must be 'auto', got {value!r}")
        return "auto"
    return tuple(float(v) for v in value)  # type: ignore[return-value]


def profile_from_dict(data: dict[str, Any]) -> Profile:
    """Build a :class:`Profile` from a raw dict (built-in module or YAML)."""
    return Profile(
        name=str(data["name"]),
        description=str(data.get("description", "")),
        page_type=str(data.get("page_type", "label")),
        rotate=int(data.get("rotate", 0)),
        threshold=_coerce_threshold(data.get("threshold")),
        crop=_coerce_crop(data.get("crop")),
    )


# Built-in registry, keyed by profile name.
_BUILTIN_MODULES = (amazon_return, fedex, generic_4x6, generic_letter_embedded, ups, usps)
BUILTIN_PROFILES: dict[str, Profile] = {
    module.PROFILE["name"]: profile_from_dict(module.PROFILE) for module in _BUILTIN_MODULES
}
DEFAULT_PROFILE_NAME = "generic_4x6"


def load_profiles(yaml_path: Path | None = None) -> dict[str, Profile]:
    """Return built-in profiles merged with any overrides in ``config/profiles.yaml``.

    A YAML entry may override individual fields of a built-in profile or define a
    brand-new one; ``name`` defaults to the YAML key.
    """
    profiles = dict(BUILTIN_PROFILES)
    if yaml_path is None:
        from ..config import config_path

        yaml_path = config_path("profiles.yaml")
    if not yaml_path.exists():
        return profiles

    import yaml

    data = yaml.safe_load(yaml_path.read_text(encoding="utf-8")) or {}
    for name, overrides in (data.get("profiles") or {}).items():
        overrides = dict(overrides or {})
        overrides.setdefault("name", name)
        if name in profiles:
            base = profiles[name]
            profiles[name] = replace(
                base,
                description=str(overrides.get("description", base.description)),
                page_type=str(overrides.get("page_type", base.page_type)),
                rotate=int(overrides.get("rotate", base.rotate)),
                threshold=_coerce_threshold(overrides["threshold"]) if "threshold" in overrides else base.threshold,
                crop=_coerce_crop(overrides["crop"]) if "crop" in overrides else base.crop,
            )
        else:
            profiles[name] = profile_from_dict(overrides)
    return profiles


def get_profile(name: str | None = None, yaml_path: Path | None = None) -> Profile:
    """Look up a profile by name (defaults to ``generic_4x6``)."""
    profiles = load_profiles(yaml_path)
    key = name or DEFAULT_PROFILE_NAME
    if key not in profiles:
        raise KeyError(f"unknown profile {key!r}; available: {sorted(profiles)}")
    return profiles[key]
