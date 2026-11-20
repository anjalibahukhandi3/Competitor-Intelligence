import pytest

from src.core.utils.pdf import generate_report_pdf


def test_legacy_pdf_helper_does_not_return_invalid_pdf_bytes():
    with pytest.raises(NotImplementedError):
        generate_report_pdf({})
