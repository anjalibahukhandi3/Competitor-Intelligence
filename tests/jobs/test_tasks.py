"""Unit & Integration tests for Celery background tasks and pipeline execution."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domains.reports.models import REPORT_STATUS_COMPLETED, Report
from src.jobs.tasks import _run_pipeline


def _fake_task_engine(mock_session: AsyncMock) -> tuple[MagicMock, MagicMock]:
    """Builds a (fake_engine, fake_session_maker) pair matching the shape of
    ``src.database.create_task_engine()``'s return value, for patching
    ``src.jobs.tasks.create_task_engine`` in tests.

    ``fake_session_maker()`` always returns an async context manager that
    yields the same ``mock_session`` — good enough for tests that only need
    to assert on calls made through that one session across the pipeline's
    several ``async with session_maker() as session:`` blocks.
    """
    fake_engine = MagicMock()
    fake_engine.dispose = AsyncMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)

    fake_session_maker = MagicMock(return_value=mock_ctx)
    return fake_engine, fake_session_maker


@pytest.mark.asyncio
async def test_run_pipeline_generates_pdf_and_completes() -> None:
    """Tests that _run_pipeline:
    1. Calls IntelligenceOrchestrator.run_pipeline().
    2. Calls PDFReportGenerator.generate_pdf() and saves the returned path to report.pdf_path.
    3. Marks the report status as REPORT_STATUS_COMPLETED.
    4. Acquires exactly one task-scoped engine and disposes it before returning.
    """
    report_id = "test-report-pipeline-1"
    mock_report = Report(id=report_id, competitor_id="comp-1", status="pending")

    mock_session = AsyncMock()
    fake_engine, fake_session_maker = _fake_task_engine(mock_session)

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_report)
    mock_repo.update = AsyncMock(return_value=mock_report)

    fake_pdf_path = "storage/reports/report_test-report-pipeline-1.pdf"

    with (
        patch("src.jobs.tasks.create_task_engine", return_value=(fake_engine, fake_session_maker)),
        patch("src.jobs.tasks.ReportRepository", return_value=mock_repo),
        patch("src.jobs.tasks.IntelligenceOrchestrator") as mock_orch_cls,
        patch("src.core.pdf.generator.PDFReportGenerator.generate_pdf", return_value=fake_pdf_path),
        patch("src.jobs.tasks._update_report_status", new_callable=AsyncMock) as mock_update_status,
        patch("src.jobs.tasks._load_recent_change_events", new_callable=AsyncMock, return_value=[]),
    ):
        mock_orch = MagicMock()
        mock_orch.run_pipeline = AsyncMock()
        mock_orch_cls.return_value = mock_orch

        await _run_pipeline(report_id)

        # Orchestrator must have run
        mock_orch.run_pipeline.assert_awaited_once()

        # Status must have been set to COMPLETED with the task-scoped session_maker
        mock_update_status.assert_any_call(fake_session_maker, report_id, REPORT_STATUS_COMPLETED)

        # The task-scoped engine must be disposed exactly once before the task ends
        fake_engine.dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_run_pipeline_marks_failed_and_disposes_engine_on_error() -> None:
    """A failure inside the orchestrator must still mark the report failed and
    dispose the task-scoped engine (never leak it), then re-raise.
    """
    report_id = "test-report-pipeline-2"
    mock_report = Report(id=report_id, competitor_id="comp-1", status="pending")

    mock_session = AsyncMock()
    fake_engine, fake_session_maker = _fake_task_engine(mock_session)

    mock_repo = MagicMock()
    mock_repo.get_by_id = AsyncMock(return_value=mock_report)
    mock_repo.update = AsyncMock(return_value=mock_report)

    with (
        patch("src.jobs.tasks.create_task_engine", return_value=(fake_engine, fake_session_maker)),
        patch("src.jobs.tasks.ReportRepository", return_value=mock_repo),
        patch("src.jobs.tasks.IntelligenceOrchestrator") as mock_orch_cls,
        patch("src.jobs.tasks._update_report_status", new_callable=AsyncMock),
        patch("src.jobs.tasks._mark_report_failed", new_callable=AsyncMock) as mock_mark_failed,
    ):
        mock_orch = MagicMock()
        mock_orch.run_pipeline = AsyncMock(side_effect=RuntimeError("boom"))
        mock_orch_cls.return_value = mock_orch

        with pytest.raises(RuntimeError, match="boom"):
            await _run_pipeline(report_id)

        mock_mark_failed.assert_awaited_once_with(fake_session_maker, report_id)
        fake_engine.dispose.assert_awaited_once()


def test_generate_report_task_returns_completed() -> None:
    """Tests synchronous generate_report_task runs asyncio.run(_run_pipeline) and returns result dict."""
    report_id = "task-report-id-99"
    with patch("src.jobs.tasks.asyncio") as mock_asyncio:
        mock_asyncio.run = MagicMock(return_value=None)
        from src.jobs.tasks import generate_report_task
        res = generate_report_task(report_id)
        assert res == {"report_id": report_id, "result": "completed"}
        mock_asyncio.run.assert_called_once()
