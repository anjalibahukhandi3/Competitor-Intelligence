"""Unit tests for SnapshotService — snapshot creation, hashing, and duplicate prevention.

Design
------
- All external clients (FirecrawlClient) are fully mocked with AsyncMock.
- All repositories are mocked with AsyncMock.
- No database or network calls are made.
- Tests run in milliseconds.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.domains.snapshots.services import SnapshotService


# ---------------------------------------------------------------------------
# Shared fixtures & helpers
# ---------------------------------------------------------------------------

COMPETITOR_ID = "comp-test-uuid-1234"
HOMEPAGE_MD = "# AcmeCorp\nWelcome to AcmeCorp. We provide the best solution."
PRICING_MD = "# Pricing\nPro: $29/month. Enterprise: $99/month."


def _make_hash(homepage: str, pricing: str) -> str:
    raw = (homepage + pricing).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _make_fake_competitor(competitor_id: str = COMPETITOR_ID) -> MagicMock:
    c = MagicMock()
    c.id = competitor_id
    c.website = "https://acmecorp.example.com"
    return c


def _make_fake_snapshot(
    snapshot_id: str = "snap-001",
    competitor_id: str = COMPETITOR_ID,
    homepage: str = HOMEPAGE_MD,
    pricing: str = PRICING_MD,
) -> MagicMock:
    s = MagicMock()
    s.id = snapshot_id
    s.competitor_id = competitor_id
    s.content_hash = _make_hash(homepage, pricing)
    s.homepage_content = homepage
    s.pricing_content = pricing
    s.created_at = datetime(2026, 7, 30, 2, 0, 0, tzinfo=timezone.utc)
    return s


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestSnapshotService:
    """Tests for SnapshotService with fully mocked dependencies."""

    def _make_service(
        self,
        snapshot_repo: AsyncMock,
        competitor_repo: AsyncMock,
        firecrawl: AsyncMock,
    ) -> SnapshotService:
        return SnapshotService(
            snapshot_repository=snapshot_repo,
            competitor_repository=competitor_repo,
            firecrawl_client=firecrawl,
        )

    @pytest.fixture
    def mock_firecrawl(self) -> AsyncMock:
        mock = AsyncMock()
        mock.scrape.side_effect = [
            {"markdown": HOMEPAGE_MD, "title": "AcmeCorp", "description": ""},
            {"markdown": PRICING_MD, "title": "Pricing", "description": ""},
        ]
        return mock

    @pytest.fixture
    def mock_snapshot_repo(self) -> AsyncMock:
        repo = AsyncMock()
        repo.exists_with_hash.return_value = False  # no duplicate by default
        repo.create.side_effect = lambda snap: snap
        return repo

    @pytest.fixture
    def mock_competitor_repo(self) -> AsyncMock:
        repo = AsyncMock()
        repo.get_by_id.return_value = _make_fake_competitor()
        return repo

    async def test_take_snapshot_creates_new_when_no_duplicate(
        self,
        mock_firecrawl: AsyncMock,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """SnapshotService creates a new snapshot when content hash is new."""
        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, mock_firecrawl)

        snapshot, is_new = await service.take_snapshot(COMPETITOR_ID)

        assert is_new is True
        assert snapshot.competitor_id == COMPETITOR_ID
        assert snapshot.content_hash == _make_hash(HOMEPAGE_MD, PRICING_MD)
        assert snapshot.homepage_content == HOMEPAGE_MD
        assert snapshot.pricing_content == PRICING_MD
        mock_snapshot_repo.create.assert_awaited_once()

    async def test_take_snapshot_skips_duplicate_when_hash_matches(
        self,
        mock_firecrawl: AsyncMock,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """SnapshotService skips creation when content hash already exists (no change)."""
        mock_snapshot_repo.exists_with_hash.return_value = True
        existing = _make_fake_snapshot()
        mock_snapshot_repo.get_latest_by_competitor.return_value = existing

        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, mock_firecrawl)
        snapshot, is_new = await service.take_snapshot(COMPETITOR_ID)

        assert is_new is False
        assert snapshot.id == "snap-001"
        mock_snapshot_repo.create.assert_not_awaited()

    async def test_take_snapshot_raises_when_competitor_not_found(
        self,
        mock_firecrawl: AsyncMock,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """SnapshotService raises ValueError when competitor is not found."""
        mock_competitor_repo.get_by_id.return_value = None

        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, mock_firecrawl)

        with pytest.raises(ValueError, match="Competitor not found"):
            await service.take_snapshot("nonexistent-competitor")

    async def test_take_snapshot_handles_crawl_failure_gracefully(
        self,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """SnapshotService still creates a snapshot with empty content if crawl fails."""
        failing_firecrawl = AsyncMock()
        failing_firecrawl.scrape.side_effect = Exception("Connection timeout")

        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, failing_firecrawl)
        snapshot, is_new = await service.take_snapshot(COMPETITOR_ID)

        # Should still create a snapshot, but with empty content
        assert is_new is True
        assert snapshot.homepage_content is None
        assert snapshot.pricing_content is None
        mock_snapshot_repo.create.assert_awaited_once()

    async def test_get_snapshot_returns_schema_when_found(
        self,
        mock_firecrawl: AsyncMock,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """get_snapshot returns a SnapshotResponse when the snapshot exists."""
        existing = _make_fake_snapshot()
        mock_snapshot_repo.get_by_id.return_value = existing

        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, mock_firecrawl)
        result = await service.get_snapshot("snap-001")

        assert result.id == "snap-001"
        assert result.competitor_id == COMPETITOR_ID

    async def test_get_snapshot_raises_when_not_found(
        self,
        mock_firecrawl: AsyncMock,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """get_snapshot raises ValueError when snapshot is not found."""
        mock_snapshot_repo.get_by_id.return_value = None

        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, mock_firecrawl)

        with pytest.raises(ValueError, match="Snapshot not found"):
            await service.get_snapshot("missing-id")

    async def test_content_hash_is_sha256_of_combined_content(
        self,
        mock_firecrawl: AsyncMock,
        mock_snapshot_repo: AsyncMock,
        mock_competitor_repo: AsyncMock,
    ) -> None:
        """Verifies that the content_hash on the created snapshot is the expected SHA256."""
        service = self._make_service(mock_snapshot_repo, mock_competitor_repo, mock_firecrawl)
        snapshot, _ = await service.take_snapshot(COMPETITOR_ID)

        expected_hash = _make_hash(HOMEPAGE_MD, PRICING_MD)
        assert snapshot.content_hash == expected_hash
        assert len(snapshot.content_hash) == 64  # SHA256 hex = 64 chars
