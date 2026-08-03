"""Unit tests for ChangeDetector — diffing, Gemini categorization, and change event persistence.

Design
------
- GeminiClient and ChangeEventRepository are fully mocked with AsyncMock.
- Tests validate: diff computation, change event creation, bulk_create call,
  handling of no-diff scenario, and Gemini failure fallback.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domains.snapshots.schemas import DetectedChangeAnalysis
from src.domains.snapshots.services import ChangeDetector


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

COMPETITOR_ID = "comp-test-uuid-001"


def _make_snapshot(
    snapshot_id: str,
    homepage: str = "",
    pricing: str = "",
) -> MagicMock:
    s = MagicMock()
    s.id = snapshot_id
    s.competitor_id = COMPETITOR_ID
    s.homepage_content = homepage
    s.pricing_content = pricing
    s.created_at = datetime(2026, 7, 30, tzinfo=timezone.utc)
    return s


def _make_gemini_analysis(
    categories: list[str] | None = None,
    impact: str = "Medium",
) -> DetectedChangeAnalysis:
    return DetectedChangeAnalysis(
        categories=categories or ["Pricing"],
        summary="Competitor lowered Pro plan price from $49 to $29/month.",
        added_highlights="• Pro: $29/month (was $49)",
        removed_highlights="• Pro: $49/month",
        impact_score=impact,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestChangeDetector:
    """Tests for ChangeDetector with mocked Gemini and repository."""

    def _make_detector(
        self,
        event_repo: AsyncMock,
        gemini: AsyncMock,
    ) -> ChangeDetector:
        return ChangeDetector(
            change_event_repository=event_repo,
            gemini_client=gemini,
        )

    @pytest.fixture
    def mock_event_repo(self) -> AsyncMock:
        repo = AsyncMock()
        repo.bulk_create.side_effect = lambda events: events
        return repo

    @pytest.fixture
    def mock_gemini(self) -> AsyncMock:
        mock = AsyncMock()
        mock.extract_structured.return_value = _make_gemini_analysis(
            categories=["Pricing"], impact="High"
        )
        return mock

    async def test_detect_changes_creates_events_for_each_category(
        self,
        mock_event_repo: AsyncMock,
        mock_gemini: AsyncMock,
    ) -> None:
        """ChangeDetector creates one ChangeEvent per detected category."""
        # Two categories returned by Gemini
        mock_gemini.extract_structured.return_value = _make_gemini_analysis(
            categories=["Pricing", "Features"], impact="High"
        )

        prev = _make_snapshot("snap-prev", homepage="Old homepage", pricing="Old pricing")
        new = _make_snapshot("snap-new", homepage="New homepage v2", pricing="New pricing v2 $29")

        detector = self._make_detector(mock_event_repo, mock_gemini)
        events = await detector.detect_and_record_changes(
            competitor_id=COMPETITOR_ID,
            previous_snapshot=prev,
            new_snapshot=new,
        )

        assert len(events) == 2
        categories = {e.category for e in events}
        assert categories == {"Pricing", "Features"}
        mock_event_repo.bulk_create.assert_awaited_once()

    async def test_detect_changes_returns_empty_when_no_diff(
        self,
        mock_event_repo: AsyncMock,
        mock_gemini: AsyncMock,
    ) -> None:
        """ChangeDetector returns [] and does NOT call Gemini when content is identical."""
        identical_content = "# Page\nNo changes at all."
        prev = _make_snapshot("snap-prev", homepage=identical_content, pricing=identical_content)
        new = _make_snapshot("snap-new", homepage=identical_content, pricing=identical_content)

        detector = self._make_detector(mock_event_repo, mock_gemini)
        events = await detector.detect_and_record_changes(
            competitor_id=COMPETITOR_ID,
            previous_snapshot=prev,
            new_snapshot=new,
        )

        assert events == []
        mock_gemini.extract_structured.assert_not_awaited()
        mock_event_repo.bulk_create.assert_not_awaited()

    async def test_detect_changes_handles_gemini_failure_gracefully(
        self,
        mock_event_repo: AsyncMock,
        mock_gemini: AsyncMock,
    ) -> None:
        """ChangeDetector returns [] and does NOT persist events if Gemini fails."""
        mock_gemini.extract_structured.side_effect = Exception("Gemini API error")

        prev = _make_snapshot("snap-prev", homepage="Old page", pricing="Old pricing")
        new = _make_snapshot("snap-new", homepage="Completely new page", pricing="New pricing tiers")

        detector = self._make_detector(mock_event_repo, mock_gemini)
        events = await detector.detect_and_record_changes(
            competitor_id=COMPETITOR_ID,
            previous_snapshot=prev,
            new_snapshot=new,
        )

        assert events == []
        mock_event_repo.bulk_create.assert_not_awaited()

    async def test_detect_changes_sets_impact_score_from_gemini(
        self,
        mock_event_repo: AsyncMock,
        mock_gemini: AsyncMock,
    ) -> None:
        """ChangeEvent.impact_score matches the value returned by Gemini."""
        mock_gemini.extract_structured.return_value = _make_gemini_analysis(
            categories=["Pricing"], impact="High"
        )

        prev = _make_snapshot("snap-prev", homepage="Old content", pricing="Old pricing")
        new = _make_snapshot("snap-new", homepage="New content", pricing="New pricing $19")

        detector = self._make_detector(mock_event_repo, mock_gemini)
        events = await detector.detect_and_record_changes(
            competitor_id=COMPETITOR_ID,
            previous_snapshot=prev,
            new_snapshot=new,
        )

        assert len(events) == 1
        assert events[0].impact_score == "High"
        assert events[0].competitor_id == COMPETITOR_ID
        assert events[0].snapshot_id == "snap-new"

    async def test_compute_diff_returns_empty_for_identical_content(
        self,
        mock_event_repo: AsyncMock,
        mock_gemini: AsyncMock,
    ) -> None:
        """_compute_diff helper returns empty string when old and new are identical."""
        detector = self._make_detector(mock_event_repo, mock_gemini)
        diff = detector._compute_diff("line one\nline two\n", "line one\nline two\n", "test")
        assert diff == ""

    async def test_compute_diff_detects_added_and_removed_lines(
        self,
        mock_event_repo: AsyncMock,
        mock_gemini: AsyncMock,
    ) -> None:
        """_compute_diff correctly identifies added and removed lines."""
        old = "line one\nline two\n"
        new = "line one\nline three\n"

        detector = self._make_detector(mock_event_repo, mock_gemini)
        diff = detector._compute_diff(old, new, "homepage")

        assert "ADDED:" in diff
        assert "REMOVED:" in diff
        assert "+ line three" in diff
        assert "- line two" in diff
