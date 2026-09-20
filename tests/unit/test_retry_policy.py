"""Tests for the Celery retry policy on report/monitoring tasks (Part 8).

`generate_report_task` and `run_competitor_monitoring_task` both use
`autoretry_for=RETRYABLE_PIPELINE_EXCEPTIONS` instead of the old blanket
`autoretry_for=(Exception,)`. This file locks in the intent: transient
external-service failures should be retried, permanent configuration
problems should not.
"""

from src.ai.exceptions import AIConfigurationException, FirecrawlException, GeminiException, TavilyException
from src.core.utils.email import EmailConfigurationException
from src.jobs.tasks import RETRYABLE_PIPELINE_EXCEPTIONS, generate_report_task, run_competitor_monitoring_task


def test_retryable_exceptions_cover_known_transient_client_errors() -> None:
    """Retrying makes sense for these — a network blip or a rate limit can
    legitimately succeed on a later attempt.
    """
    assert issubclass(FirecrawlException, RETRYABLE_PIPELINE_EXCEPTIONS)
    assert issubclass(TavilyException, RETRYABLE_PIPELINE_EXCEPTIONS)
    assert issubclass(GeminiException, RETRYABLE_PIPELINE_EXCEPTIONS)


def test_permanent_configuration_errors_are_excluded_from_retry() -> None:
    """A missing/placeholder API key can never be fixed by retrying — Celery
    must fail these immediately rather than scheduling 3 wasted retries.
    """
    assert not issubclass(AIConfigurationException, RETRYABLE_PIPELINE_EXCEPTIONS)
    assert not issubclass(EmailConfigurationException, RETRYABLE_PIPELINE_EXCEPTIONS)


def test_generate_report_task_autoretry_matches_the_shared_policy() -> None:
    assert generate_report_task.autoretry_for == RETRYABLE_PIPELINE_EXCEPTIONS
    assert generate_report_task.max_retries == 3


def test_run_competitor_monitoring_task_autoretry_matches_the_shared_policy() -> None:
    assert run_competitor_monitoring_task.autoretry_for == RETRYABLE_PIPELINE_EXCEPTIONS
    assert run_competitor_monitoring_task.max_retries == 2
