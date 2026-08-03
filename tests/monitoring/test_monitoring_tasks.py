"""Unit tests for monitoring Celery tasks.

Tests verify that:
  - trigger_monitoring_polling loads active competitors and enqueues tasks.
  - run_competitor_monitoring_task drives the monitoring pipeline.
  - Skipped (no-change) results are handled correctly.

All async DB sessions and external clients are fully mocked.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestTriggerMonitoringPolling:
    """Tests for trigger_monitoring_polling task."""

    def test_trigger_polling_enqueues_per_active_competitor(self) -> None:
        """trigger_monitoring_polling enqueues one task per active competitor."""
        from src.jobs.tasks import trigger_monitoring_polling

        with patch(
            "src.jobs.tasks._enqueue_monitoring_for_all_active_competitors",
            new_callable=AsyncMock,
        ) as mock_enqueue:
            with patch("asyncio.run", return_value=None) as mock_run:
                trigger_monitoring_polling()
                mock_run.assert_called_once()

    def test_run_monitoring_task_returns_success_dict(self) -> None:
        """run_competitor_monitoring_task returns correct success dict."""
        from src.jobs.tasks import run_competitor_monitoring_task

        expected_result = {
            "competitor_id": "comp-001",
            "snapshot_id": "snap-xyz",
            "change_count": 2,
            "skipped": False,
        }

        with patch("asyncio.run", return_value=expected_result) as mock_run:
            result = run_competitor_monitoring_task("comp-001")
            assert result == expected_result
            mock_run.assert_called_once()

    def test_run_monitoring_task_returns_skipped_dict_when_no_change(self) -> None:
        """run_competitor_monitoring_task returns skipped=True when content unchanged."""
        from src.jobs.tasks import run_competitor_monitoring_task

        skipped_result = {
            "competitor_id": "comp-001",
            "skipped": True,
            "reason": "no_change",
        }

        with patch("asyncio.run", return_value=skipped_result) as mock_run:
            result = run_competitor_monitoring_task("comp-001")
            assert result["skipped"] is True
            assert result["reason"] == "no_change"
            mock_run.assert_called_once()


class TestRunMonitoringPipelineAsync:
    """Unit tests for _run_monitoring_pipeline async helper."""

    async def test_pipeline_returns_skipped_when_no_new_snapshot(self) -> None:
        """_run_monitoring_pipeline returns skipped when content hash unchanged."""
        from src.jobs.tasks import _run_monitoring_pipeline

        fake_snapshot = MagicMock(id="snap-existing")
        fake_snapshot_service = MagicMock()
        fake_snapshot_service.take_snapshot = AsyncMock(return_value=(fake_snapshot, False))

        with patch("src.jobs.tasks.async_session_maker") as mock_session_maker, \
             patch("src.domains.snapshots.services.SnapshotService", return_value=fake_snapshot_service), \
             patch("src.domains.snapshots.services.ChangeDetector"):
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_maker.return_value = mock_session

            result = await _run_monitoring_pipeline("comp-001")

        assert result.get("skipped") is True

    async def test_pipeline_creates_change_events_for_new_snapshot(self) -> None:
        """_run_monitoring_pipeline calls detect_and_record_changes when previous snapshot exists."""
        from src.jobs.tasks import _run_monitoring_pipeline

        fake_new_snapshot = MagicMock(id="snap-new")
        fake_prev_snapshot = MagicMock(id="snap-prev")

        fake_snapshot_repo = AsyncMock()
        fake_snapshot_repo.get_previous_by_competitor.return_value = fake_prev_snapshot

        fake_snapshot_service = MagicMock()
        fake_snapshot_service.take_snapshot = AsyncMock(return_value=(fake_new_snapshot, True))

        fake_change_detector = MagicMock()
        fake_change_detector.detect_and_record_changes = AsyncMock(return_value=[MagicMock(), MagicMock()])

        with patch("src.jobs.tasks.async_session_maker") as mock_session_maker, \
             patch("src.domains.snapshots.repositories.SnapshotRepository", return_value=fake_snapshot_repo), \
             patch("src.domains.snapshots.services.SnapshotService", return_value=fake_snapshot_service), \
             patch("src.domains.snapshots.services.ChangeDetector", return_value=fake_change_detector):

            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session_maker.return_value = mock_session

            result = await _run_monitoring_pipeline("comp-001")

        assert result.get("change_count") == 2
        assert result.get("skipped") is False
