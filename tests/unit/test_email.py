"""Unit tests for Resend-backed report email delivery (src/core/utils/email.py)."""

from unittest.mock import patch

import pytest

from src.core.utils.email import (
    EmailConfigurationException,
    EmailDeliveryException,
    send_intelligence_report_email,
)


class _FakeSettings:
    """Minimal stand-in for `settings.external` used across these tests."""

    def __init__(self, resend_api_key: str | None, sender_email: str) -> None:
        self.resend_api_key = resend_api_key
        self.sender_email = sender_email


def _patch_external_settings(resend_api_key: str | None, sender_email: str):
    fake_external = _FakeSettings(resend_api_key=resend_api_key, sender_email=sender_email)
    return patch("src.core.utils.email.settings.external", fake_external)


@pytest.mark.asyncio
async def test_raises_configuration_exception_when_api_key_missing() -> None:
    """A missing/placeholder Resend API key must fail fast (no retries),
    matching the AIConfigurationException pattern used by the other clients.
    """
    with _patch_external_settings(resend_api_key=None, sender_email="alerts@realdomain.com"):
        with pytest.raises(EmailConfigurationException):
            await send_intelligence_report_email(
                to_email="user@example.com",
                subject="Report",
                pdf_bytes=b"%PDF-1.4 fake",
                text_summary="summary",
            )


@pytest.mark.asyncio
async def test_raises_configuration_exception_when_api_key_is_placeholder() -> None:
    with _patch_external_settings(resend_api_key="your_resend_api_key_here", sender_email="alerts@realdomain.com"):
        with pytest.raises(EmailConfigurationException):
            await send_intelligence_report_email(
                to_email="user@example.com",
                subject="Report",
                pdf_bytes=b"%PDF-1.4 fake",
                text_summary="summary",
            )


@pytest.mark.asyncio
async def test_raises_configuration_exception_when_sender_is_placeholder_domain() -> None:
    """SENDER_EMAIL still pointing at the example `@yourdomain.com` placeholder
    must also fail fast rather than attempting a doomed API call.
    """
    with _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@yourdomain.com"):
        with pytest.raises(EmailConfigurationException):
            await send_intelligence_report_email(
                to_email="user@example.com",
                subject="Report",
                pdf_bytes=b"%PDF-1.4 fake",
                text_summary="summary",
            )


@pytest.mark.asyncio
async def test_raises_configuration_exception_for_invalid_recipient() -> None:
    """An invalid recipient address is a permanent error — never retried."""
    with _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@realdomain.com"):
        with pytest.raises(EmailConfigurationException):
            await send_intelligence_report_email(
                to_email="not-an-email",
                subject="Report",
                pdf_bytes=b"%PDF-1.4 fake",
                text_summary="summary",
            )


@pytest.mark.asyncio
async def test_raises_configuration_exception_for_empty_pdf() -> None:
    """Must never send an email claiming to attach a report with no PDF content."""
    with _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@realdomain.com"):
        with pytest.raises(EmailConfigurationException):
            await send_intelligence_report_email(
                to_email="user@example.com",
                subject="Report",
                pdf_bytes=b"",
                text_summary="summary",
            )


@pytest.mark.asyncio
async def test_sends_successfully_and_attaches_pdf() -> None:
    """A valid configuration must call resend.Emails.send once with the PDF
    attached as a list-of-ints payload, and return True.
    """
    with (
        _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@realdomain.com"),
        patch("src.core.utils.email.resend.Emails.send", return_value={"id": "email_123"}) as mock_send,
    ):
        result = await send_intelligence_report_email(
            to_email="user@example.com",
            subject="Competitor Intelligence Report — Acme Corp",
            pdf_bytes=b"%PDF-1.4 fake pdf bytes",
            text_summary="Your report is ready.",
            pdf_filename="Acme_Corp_intelligence_report.pdf",
        )

    assert result is True
    mock_send.assert_called_once()
    sent_params = mock_send.call_args[0][0]
    assert sent_params["to"] == ["user@example.com"]
    assert sent_params["from"] == "alerts@realdomain.com"
    assert sent_params["attachments"][0]["filename"] == "Acme_Corp_intelligence_report.pdf"
    assert sent_params["attachments"][0]["content"] == list(b"%PDF-1.4 fake pdf bytes")


@pytest.mark.asyncio
async def test_retries_on_transient_5xx_then_succeeds() -> None:
    """A 500 on the first attempt should be retried (with backoff) and
    succeed on the second attempt — matching the Firecrawl/Tavily/Gemini
    client retry pattern.
    """
    class _TransientThenOk:
        def __init__(self) -> None:
            self.calls = 0

        def __call__(self, params):
            self.calls += 1
            if self.calls == 1:
                err = Exception("server error")
                err.status_code = 500  # noqa: BLE001 - simulating Resend's error shape
                raise err
            return {"id": "email_456"}

    flaky_send = _TransientThenOk()

    with (
        _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@realdomain.com"),
        patch("src.core.utils.email.resend.Emails.send", side_effect=flaky_send),
        patch("src.core.utils.email.asyncio.sleep", return_value=None),  # skip real backoff delay
    ):
        result = await send_intelligence_report_email(
            to_email="user@example.com",
            subject="Report",
            pdf_bytes=b"%PDF-1.4 fake",
            text_summary="summary",
        )

    assert result is True
    assert flaky_send.calls == 2


@pytest.mark.asyncio
async def test_raises_delivery_exception_after_retries_exhausted() -> None:
    """Persistent 5xx errors across all retry attempts must raise
    EmailDeliveryException (a type the report pipeline treats as a
    best-effort failure, not a reason to fail the whole report).
    """

    def always_fails(params):
        err = Exception("still down")
        err.status_code = 503
        raise err

    with (
        _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@realdomain.com"),
        patch("src.core.utils.email.resend.Emails.send", side_effect=always_fails),
        patch("src.core.utils.email.asyncio.sleep", return_value=None),
    ):
        with pytest.raises(EmailDeliveryException):
            await send_intelligence_report_email(
                to_email="user@example.com",
                subject="Report",
                pdf_bytes=b"%PDF-1.4 fake",
                text_summary="summary",
                retries=2,
            )


@pytest.mark.asyncio
async def test_does_not_retry_permanent_4xx_error() -> None:
    """A permanent client error (e.g. 422 validation) should NOT be retried —
    it should raise immediately after the first attempt.
    """
    call_count = 0

    def permanent_failure(params):
        nonlocal call_count
        call_count += 1
        err = Exception("invalid request")
        err.status_code = 422
        raise err

    with (
        _patch_external_settings(resend_api_key="re_real_key_123", sender_email="alerts@realdomain.com"),
        patch("src.core.utils.email.resend.Emails.send", side_effect=permanent_failure),
    ):
        with pytest.raises(EmailDeliveryException):
            await send_intelligence_report_email(
                to_email="user@example.com",
                subject="Report",
                pdf_bytes=b"%PDF-1.4 fake",
                text_summary="summary",
                retries=3,
            )

    assert call_count == 1
