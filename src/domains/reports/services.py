"""Report service layer — business logic for report lifecycle management.

This service orchestrates report creation and retrieval.  It remains
framework-agnostic: no FastAPI imports, no HTTP exceptions, no DB sessions
live here.  The service communicates with the outside world through:

  - Repositories     (async DB access via injected repo objects)
  - Celery tasks     (fire-and-forget via .delay(); the task runs in a
                      separate worker process and manages its own DB session)
  - ValueError       (the only exception type raised here — routers catch
                      it and convert to the appropriate HTTPException)

Architecture rule: all HTTP exceptions, FastAPI dependencies, and raw DB
sessions stay outside this layer. Only ValueError is raised here.
"""

import os
import uuid

from src.domains.competitors.repositories import CompetitorRepository
from src.domains.reports.models import Report, REPORT_STATUS_PENDING
from src.domains.reports.repositories import ReportRepository
from src.domains.reports.schemas import (
    ReportListResponse,
    ReportResponse,
    ReportTriggerResponse,
)


class ReportService:
    """Business logic for triggering, retrieving and managing AI reports.

    Depends on two repositories:
    - CompetitorRepository: used to verify the competitor exists and is
      owned by the authenticated user before any report action.
    - ReportRepository: used for all report persistence operations.
    """

    def __init__(
        self,
        report_repository: ReportRepository,
        competitor_repository: CompetitorRepository,
    ) -> None:
        self.report_repo = report_repository
        self.competitor_repo = competitor_repository

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _get_verified_competitor(self, competitor_id: str, user_id: str):
        """Loads a competitor and asserts it belongs to the requesting user.

        Centralises the two-step ownership check so every public method
        stays DRY. Raises ValueError on not-found or access violation.
        """
        competitor = await self.competitor_repo.get_by_id(competitor_id)
        if not competitor:
            raise ValueError("Competitor not found")
        if competitor.user_id != user_id:
            raise ValueError("Access denied")
        return competitor

    # ------------------------------------------------------------------
    # trigger_report
    # ------------------------------------------------------------------

    async def trigger_report(
        self, user_id: str, competitor_id: str
    ) -> ReportTriggerResponse:
        """Creates a pending Report row and enqueues the AI generation pipeline.

        Workflow
        --------
        1. Verify the competitor exists and belongs to the user.
        2. Create a new Report ORM object with status='pending'.
        3. Persist via repo (INSERT → commit → refresh).
        4. Enqueue generate_report_task.delay(report.id) — a non-blocking,
           fire-and-forget push of a JSON message to the Redis broker.
           The Celery worker picks it up independently and advances the
           status through: pending → processing → completed | failed.
        5. Return ReportTriggerResponse immediately (HTTP 202) — the client
           polls GET /reports/{report_id} to track progress.

        The import of generate_report_task is done inside the method body
        to avoid a circular import at module load time:
            celery_app  →  tasks  →  services  (cycle if imported at top level)
        """
        await self._get_verified_competitor(competitor_id, user_id)

        report = Report(
            id=str(uuid.uuid4()),
            competitor_id=competitor_id,
            status=REPORT_STATUS_PENDING,
        )
        report = await self.report_repo.create(report)

        # Enqueue the background task — fire-and-forget, non-blocking.
        # Importing here avoids the circular dependency:
        #   tasks.py imports celery_app.py which is fine at module level,
        #   but if tasks.py also imported services.py at top-level we'd have
        #   services → tasks → celery_app → (settings) [OK], but future
        #   AI integrations inside tasks may import back into services.
        from src.jobs.tasks import generate_report_task  # noqa: PLC0415
        generate_report_task.delay(report.id)

        return ReportTriggerResponse(
            report_id=report.id,
            status=report.status,
            message="Report generation started",
        )

    # ------------------------------------------------------------------
    # get_report
    # ------------------------------------------------------------------

    async def get_report(self, user_id: str, report_id: str) -> ReportResponse:
        """Retrieves a single report and enforces ownership through its competitor.

        Workflow
        --------
        1. Fetch the report by ID — raise ValueError if not found.
        2. Load the parent competitor and verify user ownership.
        3. Return a validated ReportResponse (AI fields will be None if
           the pipeline has not completed yet).
        """
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ValueError("Report not found")

        # Ownership is on the competitor, not the report directly
        await self._get_verified_competitor(report.competitor_id, user_id)

        return ReportResponse.model_validate(report)

    # ------------------------------------------------------------------
    # get_report_pdf_path
    # ------------------------------------------------------------------

    async def get_report_pdf_path(self, user_id: str, report_id: str) -> str:
        """Retrieves the file path of a generated PDF report after verifying user ownership.

        Workflow
        --------
        1. Fetch the report by ID — raise ValueError if not found.
        2. Load the parent competitor and verify user ownership.
        3. Verify pdf_path is non-null and the file exists on disk.
        4. Return pdf_path string.
        """
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ValueError("Report not found")

        await self._get_verified_competitor(report.competitor_id, user_id)

        if not report.pdf_path or not os.path.exists(report.pdf_path):
            raise ValueError("PDF report file not found")

        return report.pdf_path

    # ------------------------------------------------------------------
    # list_reports
    # ------------------------------------------------------------------

    async def list_reports(
        self,
        user_id: str,
        competitor_id: str,
        page: int = 1,
        size: int = 20,
    ) -> ReportListResponse:
        """Returns a paginated list of reports for a competitor.

        Workflow
        --------
        1. Verify the competitor belongs to the user.
        2. Fetch the total count (for pagination metadata).
        3. Slice the ordered list by page/size.
        4. Return ReportListResponse with items and total.
        """
        await self._get_verified_competitor(competitor_id, user_id)

        total = await self.report_repo.count_by_competitor(competitor_id)
        all_reports = await self.report_repo.get_by_competitor(competitor_id)

        # Apply in-Python pagination over the already-sorted result set.
        # A dedicated paginated query method can be added to the repo later
        # if the report volume per competitor grows large.
        offset = (page - 1) * size
        page_items = all_reports[offset : offset + size]

        return ReportListResponse(
            items=[ReportResponse.model_validate(r) for r in page_items],
            total=total,
        )

    # ------------------------------------------------------------------
    # update_status
    # ------------------------------------------------------------------

    async def update_status(self, report_id: str, status: str) -> ReportResponse:
        """Updates the lifecycle status of a report.

        Called exclusively by the AI worker (Celery task) as the pipeline
        progresses:  pending → processing → completed | failed

        No user_id ownership check is performed here because the caller
        is an internal trusted worker, not a user-facing HTTP request.

        Raises ValueError when the report row does not exist so the worker
        can log the error and avoid silently discarding the status update.
        """
        report = await self.report_repo.get_by_id(report_id)
        if not report:
            raise ValueError(f"Report not found: {report_id!r}")

        report.status = status
        report = await self.report_repo.update(report)
        return ReportResponse.model_validate(report)
