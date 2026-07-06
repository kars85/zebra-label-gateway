import pytest

from zebra_label_gateway.pdf_renderer import render_first_page_to_image


def test_pdf_renderer_is_future_work() -> None:
    with pytest.raises(NotImplementedError):
        render_first_page_to_image()
