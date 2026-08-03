"""Celery tasks for the Competitor Intelligence background pipeline.

Process boundary problem
------------------------
Celery workers are completely separate OS processes from the FastAPI server.
They do NOT share:
  - The FastAPI lifespan context
  - The asyncpg connection pool managed by `database.py`
  - Any in-memory state (including active DB sessions)

Solution: Each task creates its own async event loop via `asyncio.run()` and
opens a fresh `async_session_maker()` session that lives only for the duration
of that one task. This keeps the async SQLAlchemy 2.0 stack intact without
introducing a second sync driver (psycopg2).

Extensibility contract
----------------------
`generate_report_task` is intentionally structured as a pipeline of discrete
async steps wired through `_run_pipeline()`. Adding Firecrawl, Tavily, or
Anthropic Claude in a future milestone means:
  1. Create `src/ai/pipeline.py` (or similar) with the real AI calls.
  2. Replace `_simulate_analysis()` with `await ai_pipeline.run(report_id)`.
  3. Zero changes to the service layer, router, or Celery config.

Error handling strategy
-----------------------
- `autoretry_for=(Exception,)` + `max_retries=3` + `countdown=60`:
  Any transient failure (network blip, DB timeout) is automatically retried
  up to 3 times with a 60-second delay between attempts.
- On permanent failure (`max_retries` exceeded) Celery raises `MaxRetriesExceededError`.
  The `on_failure` hook (defined on the base class below) catches this and
  flips the report status to "failed" so the UI reflects the terminal state.
- Explicit `try/except` inside `_run_pipeline` ensures a status="failed"
  write even if the retry mechanism is bypassed (e.g. during testing).
"""

import asyncio
import structlog

from celery import Task

from src.ai.orchestrator import IntelligenceOrchestrator
from src.database import async_session_maker
from src.domains.reports.models import (
    REPORT_STATUS_COMPLETED,
    REPORT_STATUS_FAILED,
    REPORT_STATUS_PROCESSING,
)
from src.domains.reports.repositories import ReportRepository
from src.jobs.celery_app import celery_app

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Base task class — shared retry / failure behaviour
# ---------------------------------------------------------------------------

class _ReportTaskBase(Task):
    """Custom Celery Task base that writes status='failed' on permanent failure.

    Subclassing Task and setting `abstract = True` means Celery does NOT
    register this class itself as a task; it is purely a mixin for the
    concrete tasks below.
    """

    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called by Celery when all retries are exhausted or an unhandled
        exception escapes the task function.

        We run a separate asyncio loop here because `on_failure` is a
        synchronous Celery callback and we need to write to the async DB.
        """
        report_id: str | None = args[0] if args else kwargs.get("report_id")
        if report_id:
            logger.error(
                "Report pipeline permanently failed",
                report_id=report_id,
                task_id=task_id,
                exc=str(exc),
            )
            asyncio.run(_mark_report_failed(report_id))
        super().on_failure(exc, task_id, args, kwargs, einfo)


# ---------------------------------------------------------------------------
# Async helpers — run inside asyncio.run() from within Celery tasks
# ---------------------------------------------------------------------------

async def _update_report_status(report_id: str, new_status: str) -> None:
    """Opens a one-shot DB session, updates report status, and closes.

    Each call is a complete unit of work:  open → update → commit → close.
    This is deliberate: tasks run in separate processes that do not share
    the FastAPI session lifecycle.
    """
    async with async_session_maker() as session:
        repo = ReportRepository(session)
        report = await repo.get_by_id(report_id)
        if report is None:
            logger.warning("_update_report_status: report not found", report_id=report_id)
            return
        report.status = new_status
        await repo.update(report)
        logger.info(
            "Report status updated",
            report_id=report_id,
            status=new_status,
        )


async def _mark_report_failed(report_id: str) -> None:
    """Convenience wrapper — sets status to 'failed'."""
    await _update_report_status(report_id, REPORT_STATUS_FAILED)


async def _run_pipeline(report_id: str) -> None:
    """Orchestrates the full report generation pipeline as async steps.

    Steps
    -----
    1. pending  → processing  (immediately on task pick-up)
    2. Run IntelligenceOrchestrator pipeline (all AI agents)
    3. processing → completed (on success) | failed (on exception)

    The orchestrator receives a dedicated DB session scoped to the full
    pipeline run — separate from the status-update sessions so that a
    failure inside the orchestrator does not roll back the status write.
    """
    try:
        # Step 1: Mark as processing
        await _update_report_status(report_id, REPORT_STATUS_PROCESSING)

        # Step 2: Run AI orchestration pipeline
        async with async_session_maker() as session:
            repository = ReportRepository(session)
            orchestrator = IntelligenceOrchestrator(
                report_id=report_id,
                repository=repository,
            )
            await orchestrator.run_pipeline()

        # Step 3: Generate PDF report and update report record with pdf_path
        async with async_session_maker() as session:
            repository = ReportRepository(session)
            report = await repository.get_by_id(report_id)
            if report:
                from src.core.pdf.generator import PDFReportGenerator  # noqa: PLC0415
                pdf_generator = PDFReportGenerator()
                pdf_path = pdf_generator.generate_pdf(report)
                report.pdf_path = pdf_path
                await repository.update(report)
                logger.info(
                    "Generated PDF report artifact",
                    report_id=report_id,
                    pdf_path=pdf_path,
                )

        # Step 4: Mark as completed
        await _update_report_status(report_id, REPORT_STATUS_COMPLETED)

    except Exception as exc:
        # Write failed status so the UI doesn't show "processing" indefinitely
        logger.error(
            "Pipeline error — marking report failed",
            report_id=report_id,
            exc=str(exc),
        )
        await _mark_report_failed(report_id)
        raise  # re-raise so Celery can apply its retry / failure logic


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@celery_app.task(
    name="tasks.generate_report_task",
    base=_ReportTaskBase,
    bind=True,                        # `self` gives access to retry(), request etc.
    autoretry_for=(Exception,),       # retry on ANY exception automatically
    max_retries=3,                    # up to 3 retries beyond the first attempt
    default_retry_delay=60,           # wait 60 s between retries
    time_limit=600,                   # hard kill the task after 10 minutes
    soft_time_limit=540,              # SIGTERM warning 1 minute before hard kill
)
def generate_report_task(self, report_id: str) -> dict:
    """Entry point for the Competitor Intelligence AI pipeline.

    Called by `ReportService.trigger_report()` via `.delay(report_id)`.

    Parameters
    ----------
    report_id : str
        UUID of the report row that was created (status='pending') by the
        service layer before this task was enqueued.

    Returns
    -------
    dict
        A JSON-serialisable summary written to the Celery result backend.
        The canonical source of truth is the `reports` DB table — this
        return value is secondary and used for debugging / monitoring only.
    """
    logger.info(
        "generate_report_task received",
        report_id=report_id,
        celery_task_id=self.request.id,
    )

    # Celery tasks are sync functions; we drive the async pipeline with
    # asyncio.run() which creates + closes a dedicated event loop per call.
    asyncio.run(_run_pipeline(report_id))

    logger.info(
        "generate_report_task completed",
        report_id=report_id,
        celery_task_id=self.request.id,
    )
    return {"report_id": report_id, "result": "completed"}


@celery_app.task(name="tasks.trigger_monitoring_polling")
def trigger_monitoring_polling() -> None:
    """Celery Beat cron task — runs daily at 02:00 UTC.

    Fetches all active competitors and enqueues an individual
    ``run_competitor_monitoring_task`` for each one so that monitoring
    work is parallelized across available workers.
    """
    logger.info("Daily competitor monitoring polling triggered — loading active competitors")
    asyncio.run(_enqueue_monitoring_for_all_active_competitors())


async def _enqueue_monitoring_for_all_active_competitors() -> None:
    """Fetches all active competitors and enqueues monitoring tasks."""
    from src.domains.competitors.repositories import CompetitorRepository  # noqa: PLC0415
    async with async_session_maker() as session:
        repo = CompetitorRepository(session)
        competitors = await repo.get_all_active()
        logger.info("Enqueuing monitoring tasks", count=len(competitors))
        for competitor in competitors:
            run_competitor_monitoring_task.delay(competitor.id)


@celery_app.task(
    name="tasks.run_competitor_monitoring_task",
    autoretry_for=(Exception,),
    max_retries=2,
    default_retry_delay=120,
    time_limit=300,
    soft_time_limit=270,
)
def run_competitor_monitoring_task(competitor_id: str) -> dict:
    """Runs the full snapshot + change detection pipeline for a single competitor.

    Workflow
    --------
    1. SnapshotService crawls homepage + pricing via Firecrawl.
    2. SHA256 hash is compared against the latest stored snapshot.
    3. If content changed → new CompetitorSnapshot is persisted.
    4. ChangeDetector diffs previous vs. new snapshot via Gemini.
    5. ChangeEvent rows are persisted for each detected change category.
    6. Returns a summary dict for observability.
    """
    logger.info("run_competitor_monitoring_task received", competitor_id=competitor_id)
    result = asyncio.run(_run_monitoring_pipeline(competitor_id))
    logger.info("run_competitor_monitoring_task completed", competitor_id=competitor_id, result=result)
    return result


async def _run_monitoring_pipeline(competitor_id: str) -> dict:
    """Async monitoring pipeline — runs inside a dedicated asyncio event loop."""
    from src.domains.competitors.repositories import CompetitorRepository  # noqa: PLC0415
    from src.domains.snapshots.repositories import ChangeEventRepository, SnapshotRepository  # noqa: PLC0415
    from src.domains.snapshots.services import ChangeDetector, SnapshotService  # noqa: PLC0415

    async with async_session_maker() as session:
        snapshot_repo = SnapshotRepository(session)
        event_repo = ChangeEventRepository(session)
        competitor_repo = CompetitorRepository(session)

        snapshot_service = SnapshotService(
            snapshot_repository=snapshot_repo,
            competitor_repository=competitor_repo,
        )
        change_detector = ChangeDetector(change_event_repository=event_repo)

        # Take snapshot (skips if content unchanged)
        snapshot, is_new = await snapshot_service.take_snapshot(competitor_id)
        if not is_new:
            logger.info("Monitoring skipped — content unchanged", competitor_id=competitor_id)
            return {"competitor_id": competitor_id, "skipped": True, "reason": "no_change"}

        # Get the previous snapshot for diffing
        previous = await snapshot_repo.get_previous_by_competitor(competitor_id, snapshot.id)
        change_count = 0
        if previous:
            events = await change_detector.detect_and_record_changes(
                competitor_id=competitor_id,
                previous_snapshot=previous,
                new_snapshot=snapshot,
            )
            change_count = len(events)
        else:
            logger.info("First snapshot — no previous to diff", competitor_id=competitor_id)

    return {
        "competitor_id": competitor_id,
        "snapshot_id": snapshot.id,
        "change_count": change_count,
        "skipped": False,
    }


@celery_app.task(name="tasks.execute_competitor_analysis_pipeline")
def execute_competitor_analysis_pipeline(competitor_id: str) -> str:
    """Legacy task stub — kept for backward compatibility with existing tests.

    Superseded by ``generate_report_task`` which operates on report IDs.
    """
    logger.info("Competitor analysis pipeline triggered", competitor_id=competitor_id)
    return f"Completed analysis for {competitor_id}"

