import pytest

from zebra_label_gateway.profiles import (
    BUILTIN_PROFILES,
    Profile,
    get_profile,
    load_profiles,
    profile_from_dict,
    save_profile,
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


def test_save_profile_persists_and_reloads(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZLG_DATA_DIR", str(tmp_path))
    save_profile(Profile(name="ups_returns", description="trained", page_type="letter",
                         rotate=90, threshold=140, crop=(0.05, 0.05, 0.5, 0.6)))

    profiles = load_profiles()  # merges builtins + config + data dir
    assert "ups_returns" in profiles
    trained = profiles["ups_returns"]
    assert trained.rotate == 90 and trained.threshold == 140
    assert tuple(round(v, 2) for v in trained.crop) == (0.05, 0.05, 0.5, 0.6)


def test_save_profile_updates_existing(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("ZLG_DATA_DIR", str(tmp_path))
    save_profile(Profile(name="ups", crop="auto", threshold=128))
    save_profile(Profile(name="ups", crop=(0.1, 0.1, 0.9, 0.9), threshold=150))
    assert load_profiles()["ups"].threshold == 150


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
