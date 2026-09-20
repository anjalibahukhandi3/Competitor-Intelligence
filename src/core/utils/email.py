"""Email delivery for AI-generated competitor intelligence reports via Resend.

Configuration is read from the project's existing settings
(`src/config.py` → `ExternalApiSettings`), which already maps
``RESEND_API_KEY`` and ``SENDER_EMAIL`` from the environment — no new
configuration surface is introduced here.
"""

from __future__ import annotations

import asyncio
import time

import resend
import structlog

from src.config import settings
from src.exceptions import AppException

logger = structlog.get_logger(__name__)


class EmailException(AppException):
    """Base exception for report email delivery failures."""
    pass


class EmailConfigurationException(EmailException):
    """Permanent configuration problem — missing/placeholder Resend API key,
    an unverified/placeholder sender address, or an invalid recipient.

    Retrying will never help until a human fixes the configuration, so
    callers should treat this the same way as `AIConfigurationException`
    from the AI clients: log it and stop, don't retry.
    """
    pass


class EmailDeliveryException(EmailException):
    """The Resend API rejected the request, or all retries were exhausted."""
    pass


def _is_key_valid(api_key: str | None) -> bool:
    return bool(api_key and not api_key.startswith("your_"))


def _is_sender_configured(sender: str | None) -> bool:
    return bool(sender) and not sender.endswith("@yourdomain.com")


async def send_intelligence_report_email(
    to_email: str,
    subject: str,
    pdf_bytes: bytes,
    text_summary: str,
    pdf_filename: str = "competitor_intelligence_report.pdf",
    html_body: str | None = None,
    retries: int = 3,
) -> bool:
    """Sends the generated PDF intelligence report to a user via the Resend API.

    Parameters
    ----------
    to_email:
        Recipient's email address (the report owner).
    subject:
        Email subject line.
    pdf_bytes:
        The generated PDF file content to attach.
    text_summary:
        Plain-text body (also used as the fallback if no `html_body` is given).
    pdf_filename:
        Attachment file name shown to the recipient.
    html_body:
        Optional HTML body. Defaults to a minimal wrapper around `text_summary`.
    retries:
        Attempts for transient Resend API errors (429 / 5xx), matching the
        retry-with-backoff pattern used by FirecrawlClient / TavilyClient /
        GeminiClient.

    Returns
    -------
    bool
        True once Resend accepts the send request.

    Raises
    ------
    EmailConfigurationException
        API key, sender address, or recipient address is missing/invalid —
        callers should NOT retry this.
    EmailDeliveryException
        Resend rejected the request, or all retries were exhausted.
    """
    api_key = settings.external.resend_api_key
    sender = settings.external.sender_email

    log = logger.bind(
        client="ResendClient",
        to_domain=to_email.rsplit("@", 1)[-1] if to_email and "@" in to_email else "unknown",
    )

    if not _is_key_valid(api_key):
        log.warning("Resend API key is missing or default placeholder")
        raise EmailConfigurationException("Resend API key is not configured.")

    if not _is_sender_configured(sender):
        log.warning("Resend sender email is missing or a default placeholder domain")
        raise EmailConfigurationException(
            "SENDER_EMAIL is not configured with a verified sending domain."
        )

    if not to_email or "@" not in to_email:
        log.warning("Recipient email address is missing or malformed")
        raise EmailConfigurationException(f"Invalid recipient email address: {to_email!r}")

    if not pdf_bytes:
        log.warning("Refusing to send report email without PDF content")
        raise EmailConfigurationException("PDF content is empty — refusing to send report email.")

    resend.api_key = api_key

    safe_html = html_body or (
        "<div style=\"font-family:Helvetica,Arial,sans-serif;white-space:pre-wrap;\">"
        f"{text_summary}"
        "</div>"
    )

    params: resend.Emails.SendParams = {
        "from": sender,
        "to": [to_email],
        "subject": subject,
        "html": safe_html,
        "text": text_summary,
        "attachments": [
            {
                "filename": pdf_filename,
                "content": list(pdf_bytes),
            }
        ],
    }

    start_time = time.perf_counter()
    attempt = 0

    while attempt < retries:
        attempt += 1
        try:
            log.info("Sending intelligence report email", attempt=attempt)
            # The Resend SDK is synchronous (blocking HTTP) — run it off the
            # event loop thread so it doesn't stall other async work.
            response = await asyncio.to_thread(resend.Emails.send, params)
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            email_id = response.get("id") if isinstance(response, dict) else None
            log.info("Report email sent successfully", duration_ms=duration_ms, email_id=email_id)
            return True

        except Exception as exc:  # noqa: BLE001 - resend raises its own exception hierarchy
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
            log.error(
                "Resend API error while sending report email",
                attempt=attempt,
                duration_ms=duration_ms,
                status_code=status_code,
                error=str(exc),
            )
            if attempt < retries and status_code in (429, 500, 502, 503, 504):
                await asyncio.sleep(2 ** attempt)
                continue
            raise EmailDeliveryException(f"Resend API error: {exc}") from exc

    raise EmailDeliveryException("Resend email send retries exhausted.")
