"""Regression coverage for monitoring ownership and crawl target checks."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domains.snapshots.services import MonitoringService, SnapshotService


@pytest.mark.asyncio
async def test_manual_monitoring_rejects_competitors_owned_by_another_user():
    competitors = AsyncMock()
    competitors.get_by_user.return_value = []
    service = MonitoringService(
        snapshot_repository=AsyncMock(),
        change_event_repository=AsyncMock(),
        report_repository=AsyncMock(),
        competitor_repository=competitors,
    )

    with pytest.raises(ValueError, match="Competitor not found"):
        await service.run_monitoring("user-a", ["competitor-owned-by-user-b"])


@pytest.mark.asyncio
async def test_manual_monitoring_defaults_to_only_callers_active_competitors():
    competitor = MagicMock(id="owned-competitor")
    competitors = AsyncMock()
    competitors.get_active_by_user.return_value = [competitor]
    service = MonitoringService(
        snapshot_repository=AsyncMock(),
        change_event_repository=AsyncMock(),
        report_repository=AsyncMock(),
        competitor_repository=competitors,
    )

    with patch("src.jobs.tasks.run_competitor_monitoring_task.delay") as enqueue:
        result = await service.run_monitoring("user-a")

    assert result.competitor_ids == ["owned-competitor"]
    competitors.get_active_by_user.assert_awaited_once_with("user-a")
    competitors.get_all_active.assert_not_awaited()
    enqueue.assert_called_once_with("owned-competitor")


@pytest.mark.asyncio
async def test_crawler_rejects_private_ip_destinations():
    with patch(
        "src.domains.snapshots.services.socket.getaddrinfo",
        return_value=[(None, None, None, None, ("127.0.0.1", 443))],
    ):
        with pytest.raises(ValueError, match="public IP"):
            await SnapshotService._validate_public_target("https://competitor.example")


@pytest.mark.asyncio
async def test_crawler_rejects_localhost_without_dns_lookup():
    with patch("src.domains.snapshots.services.socket.getaddrinfo") as resolver:
        with pytest.raises(ValueError, match="Local network"):
            await SnapshotService._validate_public_target("http://localhost:8000")
    resolver.assert_not_called()
