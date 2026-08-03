"""Unit tests for monitoring API endpoints.

Design
------
- Uses FastAPI TestClient with full dependency override pattern.
- All external services (SnapshotService, ChangeDetector, MonitoringService, TimelineService)
  are mocked entirely — no DB, no network.
- Tests validate HTTP status codes, response shapes, and error propagation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.domains.snapshots.schemas import (
    ChangeEventListResponse,
    ChangeEventResponse,
    MonitoringRunResult,
    SnapshotResponse,
    TimelineItemResponse,
    TimelineResponse,
)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

COMPETITOR_ID = "comp-test-uuid-1234"
SNAPSHOT_ID = "snap-test-uuid-5678"
NOW = datetime(2026, 7, 30, 2, 0, 0, tzinfo=timezone.utc)

FAKE_SNAPSHOT = SnapshotResponse(
    id=SNAPSHOT_ID,
    competitor_id=COMPETITOR_ID,
    content_hash="abc123" * 10 + "ab",  # 64 chars
    homepage_content="# AcmeCorp\nWelcome",
    pricing_content="# Pricing\nPro: $29",
    created_at=NOW,
)

FAKE_CHANGE_EVENT = ChangeEventResponse(
    id="change-event-001",
    competitor_id=COMPETITOR_ID,
    snapshot_id=SNAPSHOT_ID,
    category="Pricing",
    summary="Competitor lowered price.",
    added_content="• $29/month",
    removed_content="• $49/month",
    impact_score="High",
    created_at=NOW,
)

FAKE_TIMELINE = TimelineResponse(
    competitor_id=COMPETITOR_ID,
    items=[
        TimelineItemResponse(
            event_type="snapshot",
            event_id=SNAPSHOT_ID,
            competitor_id=COMPETITOR_ID,
            title="Website Snapshot Taken",
            description="Content hash: abc123…",
            created_at=NOW,
        ),
        TimelineItemResponse(
            event_type="change",
            event_id="change-event-001",
            competitor_id=COMPETITOR_ID,
            title="Pricing Change Detected",
            description="Competitor lowered price.",
            category="Pricing",
            impact_score="High",
            created_at=NOW,
        ),
    ],
    total=2,
)


# ---------------------------------------------------------------------------
# Test class using FastAPI TestClient
# ---------------------------------------------------------------------------

class TestMonitoringAPI:
    """Integration-style tests for the monitoring API endpoints using TestClient."""

    @pytest.fixture
    def app_client(self):
        """Provides a FastAPI TestClient with mocked auth and DB dependencies."""
        from src.main import app
        from src.api.dependencies import get_current_user
        from src.database import get_db

        # Mock authenticated user
        fake_user = MagicMock()
        fake_user.id = "user-test-001"
        fake_user.email = "test@example.com"
        fake_user.is_active = True

        app.dependency_overrides[get_current_user] = lambda: fake_user
        app.dependency_overrides[get_db] = lambda: AsyncMock()

        with TestClient(app, raise_server_exceptions=False) as client:
            yield client

        app.dependency_overrides.clear()

    # ------------------------------------------------------------------
    # GET /snapshots/{snapshot_id}
    # ------------------------------------------------------------------

    def test_get_snapshot_returns_200_when_found(self, app_client) -> None:
        """GET /snapshots/{id} returns 200 and snapshot data when snapshot exists."""
        with patch(
            "src.domains.snapshots.services.SnapshotService.get_snapshot",
            new_callable=AsyncMock,
            return_value=FAKE_SNAPSHOT,
        ):
            response = app_client.get(f"/snapshots/{SNAPSHOT_ID}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == SNAPSHOT_ID
            assert data["competitor_id"] == COMPETITOR_ID
            assert "content_hash" in data

    def test_get_snapshot_returns_404_when_not_found(self, app_client) -> None:
        """GET /snapshots/{id} returns 404 when snapshot does not exist."""
        with patch(
            "src.domains.snapshots.services.SnapshotService.get_snapshot",
            new_callable=AsyncMock,
            side_effect=ValueError("Snapshot not found"),
        ):
            response = app_client.get("/snapshots/nonexistent-snap")
            assert response.status_code == 404

    # ------------------------------------------------------------------
    # GET /competitors/{id}/timeline
    # ------------------------------------------------------------------

    def test_get_timeline_returns_200_with_items(self, app_client) -> None:
        """GET /competitors/{id}/timeline returns 200 and unified timeline."""
        with patch(
            "src.domains.snapshots.services.TimelineService.get_timeline",
            new_callable=AsyncMock,
            return_value=FAKE_TIMELINE,
        ):
            response = app_client.get(f"/competitors/{COMPETITOR_ID}/timeline")
            assert response.status_code == 200
            data = response.json()
            assert data["competitor_id"] == COMPETITOR_ID
            assert data["total"] == 2
            assert len(data["items"]) == 2

    def test_get_timeline_returns_404_for_unknown_competitor(self, app_client) -> None:
        """GET /competitors/{id}/timeline returns 404 when competitor not found."""
        with patch(
            "src.domains.snapshots.services.TimelineService.get_timeline",
            new_callable=AsyncMock,
            side_effect=ValueError("Competitor not found"),
        ):
            response = app_client.get("/competitors/unknown-id/timeline")
            assert response.status_code == 404

    def test_get_timeline_returns_403_for_unauthorized(self, app_client) -> None:
        """GET /competitors/{id}/timeline returns 403 when access is denied."""
        with patch(
            "src.domains.snapshots.services.TimelineService.get_timeline",
            new_callable=AsyncMock,
            side_effect=ValueError("Access denied"),
        ):
            response = app_client.get(f"/competitors/{COMPETITOR_ID}/timeline")
            assert response.status_code == 403

    # ------------------------------------------------------------------
    # POST /monitor/run
    # ------------------------------------------------------------------

    def test_trigger_monitoring_returns_202_with_run_result(self, app_client) -> None:
        """POST /monitor/run returns 202 and enqueue summary."""
        expected = MonitoringRunResult(
            enqueued=2,
            competitor_ids=[COMPETITOR_ID, "comp-002"],
            message="Monitoring enqueued for 2 competitor(s)",
        )
        with patch(
            "src.domains.snapshots.services.MonitoringService.run_monitoring",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            response = app_client.post("/monitor/run", json={"competitor_ids": [COMPETITOR_ID, "comp-002"]})
            assert response.status_code == 202
            data = response.json()
            assert data["enqueued"] == 2
            assert COMPETITOR_ID in data["competitor_ids"]

    def test_trigger_monitoring_with_empty_body_monitors_all(self, app_client) -> None:
        """POST /monitor/run with empty body enqueues all active competitors."""
        expected = MonitoringRunResult(
            enqueued=0,
            competitor_ids=[],
            message="No active competitors found to monitor",
        )
        with patch(
            "src.domains.snapshots.services.MonitoringService.run_monitoring",
            new_callable=AsyncMock,
            return_value=expected,
        ):
            response = app_client.post("/monitor/run", json={})
            assert response.status_code == 202
            data = response.json()
            assert data["enqueued"] == 0

    # ------------------------------------------------------------------
    # GET /changes
    # ------------------------------------------------------------------

    def test_get_changes_returns_200_with_events(self, app_client) -> None:
        """GET /changes returns 200 and change event list."""
        with patch(
            "src.domains.snapshots.repositories.ChangeEventRepository.get_all_recent",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = app_client.get("/changes")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data

    def test_get_changes_supports_category_filter(self, app_client) -> None:
        """GET /changes?category=Pricing is accepted and returns 200."""
        with patch(
            "src.domains.snapshots.repositories.ChangeEventRepository.get_all_recent",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = app_client.get("/changes?category=Pricing")
            assert response.status_code == 200

    def test_get_changes_supports_impact_filter(self, app_client) -> None:
        """GET /changes?impact=High is accepted and returns 200."""
        with patch(
            "src.domains.snapshots.repositories.ChangeEventRepository.get_all_recent",
            new_callable=AsyncMock,
            return_value=[],
        ):
            response = app_client.get("/changes?impact=High")
            assert response.status_code == 200
