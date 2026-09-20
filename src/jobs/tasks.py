"""Celery tasks for the Competitor Intelligence background pipeline.

Process boundary problem
------------------------
Celery workers are completely separate OS processes from the FastAPI server.
They do NOT share:
  - The FastAPI lifespan context
  - The asyncpg connection pool managed by `database.py`
  - Any in-memory state (including active DB sessions)

Solution: Each task creates its own async event loop via `asyncio.run()` and
acquires a task-scoped engine + `async_sessionmaker` via
`src.database.create_task_engine()` that lives only for the duration of that
one task, then disposes it before the loop closes. This keeps the async
SQLAlchemy 2.0 stack intact without introducing a second sync driver
(psycopg2), and — critically — never lets an asyncpg connection pool created
in one event loop get reused from a different event loop. Reusing the
FastAPI process's shared `engine`/`async_session_maker` here was the root
cause of intermittent `RuntimeError: Event loop is closed` and
`AttributeError: 'NoneType' object has no attribute 'send'` failures: the
first task to touch the pool bound it to its own `asyncio.run()` loop, and
every subsequent task ran on a *new* loop that inherited a pool full of
connections tied to an already-closed one.

Extensibility contract
----------------------
`generate_report_task` is structured as a pipeline of discrete async steps
wired through `_run_pipeline()`:
  1. Mark report as processing.
  2. Run the AI orchestrator (Research, Pricing, News, Hiring agents + SWOT
     + report synthesis via Gemini) and persist the result fields.
  3. Load recently detected changes (from the existing snapshot/change
     detection pipeline) and generate the PDF.
  4. Mark the report completed.
  5. Attempt to email the PDF to the report owner — best-effort, never
     flips a completed report back to failed.

Error handling strategy
-----------------------
- `autoretry_for=RETRYABLE_PIPELINE_EXCEPTIONS`: only exceptions that can
  plausibly be transient (network blips, rate limits, DB hiccups) are
  auto-retried up to 3 times with a 60-second delay. Permanent configuration
  problems (`AIConfigurationException` — a missing/placeholder API key) are
  deliberately excluded so a bad key fails fast instead of burning three
  wasted retries.
- On permanent failure (`max_retries` exceeded, or a non-retryable
  exception) Celery invokes the `on_failure` hook defined on the base class
  below, which flips the report status to "failed" so the UI reflects the
  terminal state.
- Explicit `try/except` inside `_run_pipeline` ensures a status="failed"
  write even if the retry mechanism is bypassed (e.g. during testing).
- Email delivery failures are caught and recorded on the report's
  `email_status` field — they never re-raise into the pipeline's exception
  handling, so a broken mail provider can never undo a successful report.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import structlog

from celery import Task
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.ai.exceptions import FirecrawlException, GeminiException, TavilyException
from src.ai.orchestrator import IntelligenceOrchestrator
from src.core.pdf.generator import PDFReportGenerator
from src.core.utils.email import EmailConfigurationException, send_intelligence_report_email
from src.database import create_task_engine
from src.domains.reports.models import (
    REPORT_EMAIL_STATUS_FAILED,
    REPORT_EMAIL_STATUS_SENT,
    REPORT_STATUS_COMPLETED,
    REPORT_STATUS_FAILED,
    REPORT_STATUS_PENDING,
    REPORT_STATUS_PROCESSING,
    Report,
)
from src.domains.reports.repositories import ReportRepository
from src.jobs.celery_app import celery_app

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Retry policy — see module docstring "Error handling strategy"
# ---------------------------------------------------------------------------

#: Exceptions worth retrying: transient network/rate-limit/server errors from
#: external services. Deliberately does NOT include `AIConfigurationException`
#: (missing/placeholder API key) — retrying a bad key can never succeed.
RETRYABLE_PIPELINE_EXCEPTIONS = (
    FirecrawlException,
    TavilyException,
    GeminiException,
    ConnectionError,
    TimeoutError,
    OSError,
)


# ---------------------------------------------------------------------------
# Task-scoped database access — see module docstring "Process boundary problem"
# ---------------------------------------------------------------------------


@asynccontextmanager
async def _task_db_session_maker() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Yields an `async_sessionmaker` bound to a fresh engine scoped to THIS call's event loop.

    Must be entered from inside the coroutine passed to `asyncio.run()` (i.e. after
    the event loop already exists) and must not be held open past that loop's
    lifetime. The engine is always disposed on exit, success or failure.
    """
    task_engine, task_session_maker = create_task_engine()
    try:
        yield task_session_maker
    finally:
        await task_engine.dispose()


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
        """Called by Celery when all retries are exhausted or a non-retryable
        exception escapes the task function.

        We run a separate asyncio loop here because `on_failure` is a
        synchronous Celery callback and we need to write to the async DB —
        and, per the module docstring, that loop gets its own task-scoped
        engine rather than touching any engine from a previous task.
        """
        report_id: str | None = args[0] if args else kwargs.get("report_id")
        if report_id:
            logger.error(
                "report_pipeline_failed",
                report_id=report_id,
                task_id=task_id,
                exc=str(exc),
            )
            asyncio.run(_mark_report_failed_isolated(report_id))
        super().on_failure(exc, task_id, args, kwargs, einfo)


# ---------------------------------------------------------------------------
# Async helpers — run inside asyncio.run() from within Celery tasks
# ---------------------------------------------------------------------------


async def _update_report_status(
    session_maker: async_sessionmaker[AsyncSession], report_id: str, new_status: str
) -> None:
    """Opens a one-shot DB session, updates report status, and closes.

    Each call is a complete unit of work: open → update → commit → close,
    using the task-scoped `session_maker` passed in by the caller (never the
    FastAPI process's global `async_session_maker`).
    """
    async with session_maker() as session:
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


async def _mark_report_failed(
    session_maker: async_sessionmaker[AsyncSession], report_id: str
) -> None:
    """Convenience wrapper — sets status to 'failed'."""
    await _update_report_status(session_maker, report_id, REPORT_STATUS_FAILED)


async def _mark_report_failed_isolated(report_id: str) -> None:
    """Same as `_mark_report_failed`, but acquires its own task-scoped engine.

    Used from `_ReportTaskBase.on_failure`, which runs in a fresh
    `asyncio.run()` call outside of `_run_pipeline`'s own engine lifetime.
    """
    async with _task_db_session_maker() as session_maker:
        await _mark_report_failed(session_maker, report_id)


async def _load_recent_change_events(
    session: AsyncSession, competitor_id: str, log: "structlog.BoundLogger"
) -> list:
    """Loads recently detected changes for a competitor to embed in the report/PDF.

    This reuses the existing, already-tested change-detection pipeline's output
    (`ChangeEvent` rows written by `run_competitor_monitoring_task` /
    `ChangeDetector`) rather than re-running detection — `generate_report_task`
    stays a consumer of that data, not a second implementation of it.
    """
    try:
        from src.domains.snapshots.repositories import ChangeEventRepository  # noqa: PLC0415

        change_repo = ChangeEventRepository(session)
        events = await change_repo.get_by_competitor(competitor_id, limit=10)
        log.info("change_detection_completed", change_count=len(events), source="existing_snapshots")
        return events
    except Exception as exc:  # noqa: BLE001 - never let a lookup failure break the report
        log.warning("change_detection_lookup_failed", error=str(exc))
        return []


async def _run_pipeline(report_id: str) -> None:
    """Orchestrates the full report generation pipeline as async steps.

    Steps
    -----
    1. pending  → processing  (immediately on task pick-up)
    2. Run IntelligenceOrchestrator pipeline (Research/Pricing/News/Hiring
       agents, then SWOT + report synthesis via Gemini)
    3. Load recent detected changes + generate the PDF
    4. processing → completed (on success) | failed (on exception)
    5. Best-effort email delivery — never affects report/PDF status above

    All DB work in this function goes through ONE task-scoped
    `async_sessionmaker`, acquired once at the top and disposed at the
    bottom, so every step in a single task run shares the same
    event-loop-bound engine (see module docstring).
    """
    async with _task_db_session_maker() as session_maker:
        log = logger.bind(report_id=report_id)
        log.info("report_pipeline_started")

        try:
            # Step 1: Mark as processing
            await _update_report_status(session_maker, report_id, REPORT_STATUS_PROCESSING)

            # Step 2: Run AI orchestration pipeline (agents + SWOT + report synthesis)
            async with session_maker() as session:
                repository = ReportRepository(session)
                orchestrator = IntelligenceOrchestrator(
                    report_id=report_id,
                    repository=repository,
                )
                await orchestrator.run_pipeline()
            log.info("swot_generation_completed", report_id=report_id)
            log.info("report_generation_completed", report_id=report_id)

            # Step 3: Load detected changes + generate PDF report artifact
            async with session_maker() as session:
                repository = ReportRepository(session)
                report = await repository.get_by_id(report_id)
                if report is None:
                    raise ValueError(f"Report not found after generation: {report_id}")

                change_events = await _load_recent_change_events(session, report.competitor_id, log)

                pdf_generator = PDFReportGenerator()
                pdf_path = pdf_generator.generate_pdf(report, changes=change_events)
                report.pdf_path = pdf_path
                await repository.update(report)
                log.info("pdf_generation_completed", pdf_path=pdf_path)

            # Step 4: Mark as completed
            await _update_report_status(session_maker, report_id, REPORT_STATUS_COMPLETED)
            log.info("report_pipeline_completed", status=REPORT_STATUS_COMPLETED)

        except Exception as exc:
            # Write failed status so the UI doesn't show "processing" indefinitely
            log.error("report_pipeline_failed", error=str(exc))
            await _mark_report_failed(session_maker, report_id)
            raise  # re-raise so Celery can apply its retry / failure logic

        # Step 5: Best-effort email delivery. Only reached when the try block
        # above completed without raising — a failed pipeline never attempts
        # to email a report that doesn't exist / has no PDF. Errors here are
        # fully contained inside `_deliver_report_email` and never propagate.
        await _deliver_report_email(session_maker, report_id, log)


async def _deliver_report_email(
    session_maker: async_sessionmaker[AsyncSession], report_id: str, log: "structlog.BoundLogger"
) -> None:
    """Emails the generated PDF to the report owner. Best-effort — never raises.

    On any failure (missing recipient, unreadable PDF, Resend configuration
    or delivery error) this records `email_status='failed'` on the report and
    logs the reason, but leaves the report and its PDF exactly as they are.
    The report's `status` field (pending/processing/completed/failed) is
    never touched here — email delivery is a separate concern.
    """
    async with session_maker() as session:
        repository = ReportRepository(session)
        report = await repository.get_by_id(report_id)

        if report is None or not report.pdf_path:
            log.warning("report_email_skipped", reason="missing_report_or_pdf")
            return

        recipient = None
        if report.competitor is not None and report.competitor.user is not None:
            recipient = report.competitor.user.email

        if not recipient:
            log.warning("report_email_failed", reason="no_recipient_email")
            report.email_status = REPORT_EMAIL_STATUS_FAILED
            await repository.update(report)
            return

        try:
            pdf_bytes = Path(report.pdf_path).read_bytes()
        except OSError as exc:
            log.error("report_email_failed", reason="pdf_read_error", error=str(exc))
            report.email_status = REPORT_EMAIL_STATUS_FAILED
            await repository.update(report)
            return

        competitor_name = report.competitor.company_name if report.competitor else "the competitor"
        subject = f"Competitor Intelligence Report — {competitor_name}"
        generated_at = (
            report.created_at.strftime("%B %d, %Y at %H:%M UTC") if report.created_at else "just now"
        )
        text_summary = (
            "Your competitor intelligence report is ready.\n\n"
            f"Competitor:\n{competitor_name}\n\n"
            f"Report generated:\n{generated_at}\n\n"
            "The attached PDF contains:\n"
            "- Executive Summary\n"
            "- Competitor Analysis\n"
            "- Pricing Analysis\n"
            "- News & Updates\n"
            "- Hiring Signals\n"
            "- Change Detection\n"
            "- SWOT Analysis\n"
            "- Strategic Insights\n"
        )
        safe_filename = "".join(c if c.isalnum() else "_" for c in competitor_name).strip("_") or "report"

        try:
            await send_intelligence_report_email(
                to_email=recipient,
                subject=subject,
                pdf_bytes=pdf_bytes,
                text_summary=text_summary,
                pdf_filename=f"{safe_filename}_intelligence_report.pdf",
            )
            report.email_status = REPORT_EMAIL_STATUS_SENT
            await repository.update(report)
            log.info("report_email_sent", report_id=report_id)
        except EmailConfigurationException as exc:
            log.warning("report_email_failed", reason="configuration", error=str(exc))
            report.email_status = REPORT_EMAIL_STATUS_FAILED
            await repository.update(report)
        except Exception as exc:  # noqa: BLE001 - email failures must never bubble up
            log.error("report_email_failed", reason="delivery", error=str(exc))
            report.email_status = REPORT_EMAIL_STATUS_FAILED
            await repository.update(report)


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@celery_app.task(
    name="tasks.generate_report_task",
    base=_ReportTaskBase,
    bind=True,                              # `self` gives access to retry(), request etc.
    autoretry_for=RETRYABLE_PIPELINE_EXCEPTIONS,  # retry only plausibly-transient errors
    max_retries=3,                          # up to 3 retries beyond the first attempt
    default_retry_delay=60,                 # wait 60 s between retries
    time_limit=600,                         # hard kill the task after 10 minutes
    soft_time_limit=540,                    # SIGTERM warning 1 minute before hard kill
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

    async with _task_db_session_maker() as session_maker:
        async with session_maker() as session:
            repo = CompetitorRepository(session)
            competitors = await repo.get_all_active()
            logger.info("Enqueuing monitoring tasks", count=len(competitors))
            for competitor in competitors:
                run_competitor_monitoring_task.delay(competitor.id)


@celery_app.task(name="tasks.trigger_weekly_report_emails")
def trigger_weekly_report_emails() -> None:
    """Celery Beat task — runs every 7 days (see `timedelta(days=7)` in celery_app.py).

    For every active competitor, creates a fresh pending Report row and
    enqueues `generate_report_task` for it — the exact same pipeline used by
    `POST /reports/trigger/{competitor_id}` (agents -> SWOT -> PDF -> email).
    Each competitor's owner automatically receives the PDF report by email
    once their report finishes, with no manual trigger required.
    """
    logger.info("Weekly report email delivery triggered — loading active competitors")
    asyncio.run(_enqueue_weekly_reports_for_all_active_competitors())


async def _enqueue_weekly_reports_for_all_active_competitors() -> None:
    """Creates a pending Report row per active competitor and enqueues generation."""
    from src.domains.competitors.repositories import CompetitorRepository  # noqa: PLC0415

    async with _task_db_session_maker() as session_maker:
        async with session_maker() as session:
            competitor_repo = CompetitorRepository(session)
            report_repo = ReportRepository(session)
            competitors = await competitor_repo.get_all_active()
            logger.info("Enqueuing weekly reports", count=len(competitors))
            for competitor in competitors:
                report = Report(
                    id=str(uuid.uuid4()),
                    competitor_id=competitor.id,
                    status=REPORT_STATUS_PENDING,
                )
                report = await report_repo.create(report)
                generate_report_task.delay(report.id)


@celery_app.task(
    name="tasks.run_competitor_monitoring_task",
    autoretry_for=RETRYABLE_PIPELINE_EXCEPTIONS,
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

    async with _task_db_session_maker() as session_maker:
        async with session_maker() as session:
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
