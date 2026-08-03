"""Snapshots domain — business logic services.

This module contains three service classes:
  - SnapshotService:  Crawls competitor websites, hashes content, stores snapshots.
  - ChangeDetector:   Diffs consecutive snapshots, uses Gemini to categorize changes.
  - TimelineService:  Collates snapshots, changes, and reports into a unified timeline.

Architecture rules
------------------
- No FastAPI imports. No HTTP exceptions. Raise ValueError only.
- DB access only via injected repositories (Clean Architecture / DI).
- All async — compatible with SQLAlchemy 2.0 AsyncSession.
"""

from __future__ import annotations

import hashlib
import uuid

import structlog

from src.ai.clients.firecrawl import FirecrawlClient
from src.ai.clients.gemini import GeminiClient
from src.domains.competitors.repositories import CompetitorRepository
from src.domains.reports.repositories import ReportRepository
from src.domains.snapshots.models import ChangeEvent, CompetitorSnapshot
from src.domains.snapshots.repositories import ChangeEventRepository, SnapshotRepository
from src.domains.snapshots.schemas import (
    ChangeEventResponse,
    DetectedChangeAnalysis,
    MonitoringRunResult,
    SnapshotResponse,
    TimelineItemResponse,
    TimelineResponse,
)

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# SnapshotService
# ---------------------------------------------------------------------------


class SnapshotService:
    """Crawls competitor websites and stores content snapshots.

    Duplicate prevention: if the SHA256 of (homepage_content + pricing_content)
    matches the latest snapshot hash, the run is skipped without persisting a new row.
    """

    def __init__(
        self,
        snapshot_repository: SnapshotRepository,
        competitor_repository: CompetitorRepository,
        firecrawl_client: FirecrawlClient | None = None,
    ) -> None:
        self.snapshot_repo = snapshot_repository
        self.competitor_repo = competitor_repository
        self.firecrawl = firecrawl_client or FirecrawlClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def take_snapshot(
        self, competitor_id: str
    ) -> tuple[CompetitorSnapshot, bool]:
        """Crawls a competitor's website and stores a new snapshot if content changed.

        Parameters
        ----------
        competitor_id : str
            UUID of the competitor to snapshot.

        Returns
        -------
        (CompetitorSnapshot, is_new: bool)
            The snapshot (either newly created or the existing duplicate) and a
            boolean indicating whether a new row was persisted.

        Raises
        ------
        ValueError
            When the competitor does not exist.
        """
        log = logger.bind(competitor_id=competitor_id)

        competitor = await self.competitor_repo.get_by_id(competitor_id)
        if not competitor:
            raise ValueError(f"Competitor not found: {competitor_id!r}")

        website = competitor.website.rstrip("/")
        log.info("Taking snapshot", website=website)

        # Crawl homepage
        homepage_md = ""
        try:
            result = await self.firecrawl.scrape(website)
            homepage_md = result.get("markdown", "") or ""
        except Exception as exc:
            log.warning("Homepage crawl failed", error=str(exc))

        # Crawl pricing page
        pricing_md = ""
        try:
            pricing_url = f"{website}/pricing"
            result = await self.firecrawl.scrape(pricing_url)
            pricing_md = result.get("markdown", "") or ""
        except Exception as exc:
            log.warning("Pricing page crawl failed", error=str(exc))

        # Compute content hash
        raw = (homepage_md + pricing_md).encode("utf-8")
        content_hash = hashlib.sha256(raw).hexdigest()

        # Duplicate detection
        is_duplicate = await self.snapshot_repo.exists_with_hash(competitor_id, content_hash)
        if is_duplicate:
            log.info("Snapshot skipped — content unchanged", content_hash=content_hash[:12])
            existing = await self.snapshot_repo.get_latest_by_competitor(competitor_id)
            # Return the latest snapshot if hash matches (should always exist)
            if existing:
                return existing, False

        # Persist new snapshot
        snapshot = CompetitorSnapshot(
            id=str(uuid.uuid4()),
            competitor_id=competitor_id,
            content_hash=content_hash,
            homepage_content=homepage_md or None,
            pricing_content=pricing_md or None,
        )
        snapshot = await self.snapshot_repo.create(snapshot)
        log.info("Snapshot created", snapshot_id=snapshot.id, hash=content_hash[:12])
        return snapshot, True

    async def get_snapshot(self, snapshot_id: str) -> SnapshotResponse:
        """Returns a single snapshot by ID. Raises ValueError if not found."""
        snapshot = await self.snapshot_repo.get_by_id(snapshot_id)
        if not snapshot:
            raise ValueError(f"Snapshot not found: {snapshot_id!r}")
        return SnapshotResponse.model_validate(snapshot)


# ---------------------------------------------------------------------------
# ChangeDetector
# ---------------------------------------------------------------------------


class ChangeDetector:
    """Diffs two consecutive competitor snapshots and records detected changes.

    Uses a simple line-diff to find added/removed content, then invokes
    GeminiClient to classify changes and assess business impact.

    Change categories: Pricing | Features | Homepage | Hiring | Marketing |
                       Product | Documentation
    """

    def __init__(
        self,
        change_event_repository: ChangeEventRepository,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.event_repo = change_event_repository
        self.gemini = gemini_client or GeminiClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def detect_and_record_changes(
        self,
        competitor_id: str,
        previous_snapshot: CompetitorSnapshot,
        new_snapshot: CompetitorSnapshot,
    ) -> list[ChangeEvent]:
        """Diffs the two snapshots, classifies changes with Gemini, and persists events.

        Returns
        -------
        list[ChangeEvent]
            The persisted ChangeEvent rows (may be empty if no significant changes).
        """
        log = logger.bind(
            competitor_id=competitor_id,
            prev_id=previous_snapshot.id,
            new_id=new_snapshot.id,
        )

        homepage_diff = self._compute_diff(
            previous_snapshot.homepage_content or "",
            new_snapshot.homepage_content or "",
            label="homepage",
        )
        pricing_diff = self._compute_diff(
            previous_snapshot.pricing_content or "",
            new_snapshot.pricing_content or "",
            label="pricing",
        )

        combined_diff = "\n\n".join(filter(None, [homepage_diff, pricing_diff]))
        if not combined_diff.strip():
            log.info("No textual diff detected between snapshots")
            return []

        # Gemini classification
        analysis = await self._classify_with_gemini(
            competitor_id=competitor_id,
            diff_text=combined_diff,
        )
        if not analysis:
            log.warning("Gemini classification returned no result — skipping event creation")
            return []

        log.info(
            "Changes classified",
            categories=analysis.categories,
            impact=analysis.impact_score,
        )

        # Create one ChangeEvent per detected category
        events: list[ChangeEvent] = []
        for category in analysis.categories:
            event = ChangeEvent(
                id=str(uuid.uuid4()),
                competitor_id=competitor_id,
                snapshot_id=new_snapshot.id,
                category=category,
                summary=analysis.summary,
                added_content=analysis.added_highlights,
                removed_content=analysis.removed_highlights,
                impact_score=analysis.impact_score,
            )
            events.append(event)

        if events:
            events = await self.event_repo.bulk_create(events)
            log.info("Change events persisted", count=len(events))

        return events

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _compute_diff(self, old: str, new: str, label: str) -> str:
        """Returns a compact unified-style diff string between two texts.

        Only added (+) and removed (-) lines are included. Unchanged lines
        are omitted to keep the prompt concise.
        """
        old_lines = set(old.splitlines())
        new_lines = set(new.splitlines())

        added = [line for line in new.splitlines() if line not in old_lines and line.strip()]
        removed = [line for line in old.splitlines() if line not in new_lines and line.strip()]

        if not added and not removed:
            return ""

        parts = [f"=== {label.upper()} CHANGES ==="]
        if added:
            parts.append("ADDED:")
            parts.extend(f"+ {line}" for line in added[:100])
        if removed:
            parts.append("REMOVED:")
            parts.extend(f"- {line}" for line in removed[:100])

        return "\n".join(parts)

    async def _classify_with_gemini(
        self,
        competitor_id: str,
        diff_text: str,
    ) -> DetectedChangeAnalysis | None:
        """Sends the diff to Gemini and parses the structured classification."""
        prompt = (
            f"A competitor's website has changed. Analyze the diff below and classify what changed.\n\n"
            f"Diff:\n{diff_text[:8000]}\n\n"
            f"Identify: change categories, a concise human-readable summary, key additions, "
            f"key removals, and business impact level."
        )
        system_prompt = (
            "You are a competitive intelligence analyst. "
            "Examine website content diffs and classify what changed, summarize the business implications, "
            "and rate the impact on a competitor's strategic position."
        )
        try:
            return await self.gemini.extract_structured(
                prompt=prompt,
                schema_class=DetectedChangeAnalysis,
                system_prompt=system_prompt,
            )
        except Exception as exc:
            logger.warning("Gemini change classification failed", error=str(exc))
            return None


# ---------------------------------------------------------------------------
# TimelineService
# ---------------------------------------------------------------------------


class TimelineService:
    """Aggregates snapshots, change events, and reports into a unified timeline."""

    def __init__(
        self,
        snapshot_repository: SnapshotRepository,
        change_event_repository: ChangeEventRepository,
        report_repository: ReportRepository,
        competitor_repository: CompetitorRepository,
    ) -> None:
        self.snapshot_repo = snapshot_repository
        self.event_repo = change_event_repository
        self.report_repo = report_repository
        self.competitor_repo = competitor_repository

    async def get_timeline(
        self, competitor_id: str, user_id: str, limit: int = 50
    ) -> TimelineResponse:
        """Returns a unified chronological timeline for a competitor.

        Raises
        ------
        ValueError
            If the competitor does not exist or does not belong to the user.
        """
        competitor = await self.competitor_repo.get_by_id(competitor_id)
        if not competitor:
            raise ValueError("Competitor not found")
        if competitor.user_id != user_id:
            raise ValueError("Access denied")

        items: list[TimelineItemResponse] = []

        # Snapshots
        snapshots = await self.snapshot_repo.get_by_competitor(competitor_id, limit=limit)
        for s in snapshots:
            items.append(
                TimelineItemResponse(
                    event_type="snapshot",
                    event_id=s.id,
                    competitor_id=competitor_id,
                    title="Website Snapshot Taken",
                    description=f"Content hash: {s.content_hash[:12]}…",
                    created_at=s.created_at,
                )
            )

        # Change events
        events = await self.event_repo.get_by_competitor(competitor_id, limit=limit)
        for e in events:
            items.append(
                TimelineItemResponse(
                    event_type="change",
                    event_id=e.id,
                    competitor_id=competitor_id,
                    title=f"{e.category} Change Detected",
                    description=e.summary,
                    category=e.category,
                    impact_score=e.impact_score,
                    created_at=e.created_at,
                )
            )

        # Reports
        reports = await self.report_repo.get_by_competitor(competitor_id)
        for r in reports:
            items.append(
                TimelineItemResponse(
                    event_type="report",
                    event_id=r.id,
                    competitor_id=competitor_id,
                    title="AI Intelligence Report Generated",
                    description=f"Status: {r.status}",
                    created_at=r.created_at,
                )
            )

        # Sort by timestamp descending, take `limit` most recent
        items.sort(key=lambda x: x.created_at, reverse=True)
        items = items[:limit]

        return TimelineResponse(
            competitor_id=competitor_id,
            items=items,
            total=len(items),
        )

    # ------------------------------------------------------------------
    # Monitoring run orchestration
    # ------------------------------------------------------------------

    async def run_monitoring_for_competitor(
        self,
        competitor_id: str,
        snapshot_service: SnapshotService,
        change_detector: ChangeDetector,
    ) -> dict:
        """Runs the full snapshot + change detection pipeline for a single competitor.

        Returns a summary dict with snapshot_id and change_count.
        """
        log = logger.bind(competitor_id=competitor_id)
        try:
            snapshot, is_new = await snapshot_service.take_snapshot(competitor_id)
            if not is_new:
                return {"competitor_id": competitor_id, "skipped": True, "reason": "no_change"}

            # Get the previous snapshot for diffing
            previous = await self.snapshot_repo.get_previous_by_competitor(
                competitor_id, snapshot.id
            )

            change_count = 0
            if previous:
                events = await change_detector.detect_and_record_changes(
                    competitor_id=competitor_id,
                    previous_snapshot=previous,
                    new_snapshot=snapshot,
                )
                change_count = len(events)
            else:
                log.info("First snapshot for competitor — no previous to diff against")

            return {
                "competitor_id": competitor_id,
                "snapshot_id": snapshot.id,
                "change_count": change_count,
                "skipped": False,
            }
        except Exception as exc:
            log.error("Monitoring run failed for competitor", error=str(exc))
            return {"competitor_id": competitor_id, "error": str(exc), "skipped": False}


# ---------------------------------------------------------------------------
# MonitoringService  (coordinates bulk runs, called by Celery task & API)
# ---------------------------------------------------------------------------


class MonitoringService:
    """Coordinates bulk monitoring runs across multiple active competitors."""

    def __init__(
        self,
        snapshot_repository: SnapshotRepository,
        change_event_repository: ChangeEventRepository,
        report_repository: ReportRepository,
        competitor_repository: CompetitorRepository,
        firecrawl_client: FirecrawlClient | None = None,
        gemini_client: GeminiClient | None = None,
    ) -> None:
        self.snapshot_repo = snapshot_repository
        self.event_repo = change_event_repository
        self.report_repo = report_repository
        self.competitor_repo = competitor_repository
        self.firecrawl = firecrawl_client or FirecrawlClient()
        self.gemini = gemini_client or GeminiClient()

    async def run_monitoring(
        self, competitor_ids: list[str] | None = None
    ) -> MonitoringRunResult:
        """Enqueues monitoring tasks for the given competitor IDs.

        If competitor_ids is None or empty, targets ALL active competitors.
        Returns a result summary immediately — actual monitoring runs as background task.
        """
        if not competitor_ids:
            competitors = await self.competitor_repo.get_all_active()
            competitor_ids = [c.id for c in competitors]

        if not competitor_ids:
            return MonitoringRunResult(
                enqueued=0,
                competitor_ids=[],
                message="No active competitors found to monitor",
            )

        # Enqueue one Celery task per competitor (fire-and-forget)
        from src.jobs.tasks import run_competitor_monitoring_task  # noqa: PLC0415
        for cid in competitor_ids:
            run_competitor_monitoring_task.delay(cid)

        logger.info("Monitoring tasks enqueued", count=len(competitor_ids))
        return MonitoringRunResult(
            enqueued=len(competitor_ids),
            competitor_ids=competitor_ids,
            message=f"Monitoring enqueued for {len(competitor_ids)} competitor(s)",
        )
