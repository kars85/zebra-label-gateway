import pytest

from zebra_label_gateway.crop_detector import detect_label_crop


def test_crop_detector_is_future_work() -> None:
    with pytest.raises(NotImplementedError):
        detect_label_crop()
