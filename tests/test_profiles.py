import pytest

from zebra_label_gateway.profiles import (
    BUILTIN_PROFILES,
    Profile,
    get_profile,
    load_profiles,
    profile_from_dict,
)


def test_builtin_profiles_present() -> None:
    for name in ("generic_4x6", "generic_letter_embedded", "ups", "fedex", "usps", "amazon_return"):
        assert name in BUILTIN_PROFILES


def test_threshold_alias_resolves() -> None:
    profile = profile_from_dict({"name": "x", "threshold": "standard"})
    assert profile.threshold == 128


def test_get_default_profile() -> None:
    assert get_profile().name == "generic_4x6"


def test_unknown_profile_raises() -> None:
    with pytest.raises(KeyError):
        get_profile("does-not-exist")


def test_invalid_rotate_rejected() -> None:
    with pytest.raises(ValueError):
        Profile(name="bad", rotate=45)


def test_invalid_threshold_rejected() -> None:
    with pytest.raises(ValueError):
        Profile(name="bad", threshold=999)


def test_letter_profiles_auto_crop() -> None:
    assert get_profile("generic_letter_embedded").crop == "auto"
    assert get_profile("generic_4x6").crop is None


def test_yaml_overrides_builtin(tmp_path) -> None:
    yaml_path = tmp_path / "profiles.yaml"
    yaml_path.write_text(
        "profiles:\n  generic_4x6:\n    threshold: dark\n  custom_one:\n    rotate: 90\n",
        encoding="utf-8",
    )
    profiles = load_profiles(yaml_path)
    assert profiles["generic_4x6"].threshold == 160  # "dark"
    assert profiles["custom_one"].rotate == 90
    assert profiles["custom_one"].name == "custom_one"
