from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest

from src.domains.users.models import User
from src.domains.competitors.models import Competitor
from src.domains.reports.models import Report, REPORT_STATUS_COMPLETED, REPORT_STATUS_PENDING
from src.domains.reports.services import ReportService
from src.domains.reports.schemas import ReportTriggerResponse, ReportResponse, ReportListResponse


@pytest.mark.asyncio
async def test_trigger_report_success():
    report_repo = MagicMock()
    competitor_repo = MagicMock()

    # Mock competitor ownership verification
    competitor = MagicMock()
    competitor.user_id = "user_123"
    competitor_repo.get_by_id = AsyncMock(return_value=competitor)

    # Mock report creation
    created_report = Report(id="report_456", competitor_id="comp_789", status=REPORT_STATUS_PENDING, created_at=datetime.now(timezone.utc))
    report_repo.create = AsyncMock(return_value=created_report)

    service = ReportService(report_repository=report_repo, competitor_repository=competitor_repo)

    response = await service.trigger_report(user_id="user_123", competitor_id="comp_789")

    assert isinstance(response, ReportTriggerResponse)
    assert response.report_id == "report_456"
    assert response.status == REPORT_STATUS_PENDING
    assert response.message == "Report generation started"
    competitor_repo.get_by_id.assert_called_once_with("comp_789")
    report_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_trigger_report_competitor_not_found():
    report_repo = MagicMock()
    competitor_repo = MagicMock()
    competitor_repo.get_by_id = AsyncMock(return_value=None)

    service = ReportService(report_repository=report_repo, competitor_repository=competitor_repo)

    with pytest.raises(ValueError, match="Competitor not found"):
        await service.trigger_report(user_id="user_123", competitor_id="nonexistent")


@pytest.mark.asyncio
async def test_trigger_report_access_denied():
    report_repo = MagicMock()
    competitor_repo = MagicMock()

    competitor = MagicMock()
    competitor.user_id = "other_user"
    competitor_repo.get_by_id = AsyncMock(return_value=competitor)

    service = ReportService(report_repository=report_repo, competitor_repository=competitor_repo)

    with pytest.raises(ValueError, match="Access denied"):
        await service.trigger_report(user_id="user_123", competitor_id="comp_789")


@pytest.mark.asyncio
async def test_get_report_success():
    report_repo = MagicMock()
    competitor_repo = MagicMock()

    report = Report(id="report_123", competitor_id="comp_789", status=REPORT_STATUS_PENDING, created_at=datetime.now(timezone.utc))
    report_repo.get_by_id = AsyncMock(return_value=report)

    competitor = MagicMock()
    competitor.user_id = "user_123"
    competitor_repo.get_by_id = AsyncMock(return_value=competitor)

    service = ReportService(report_repository=report_repo, competitor_repository=competitor_repo)

    res = await service.get_report(user_id="user_123", report_id="report_123")
    assert isinstance(res, ReportResponse)
    assert res.id == "report_123"
    assert res.status == REPORT_STATUS_PENDING


@pytest.mark.asyncio
async def test_list_reports_success():
    report_repo = MagicMock()
    competitor_repo = MagicMock()

    competitor = MagicMock()
    competitor.user_id = "user_123"
    competitor_repo.get_by_id = AsyncMock(return_value=competitor)

    r1 = Report(id="rep_1", competitor_id="comp_789", status=REPORT_STATUS_PENDING, created_at=datetime.now(timezone.utc))
    r2 = Report(id="rep_2", competitor_id="comp_789", status=REPORT_STATUS_COMPLETED, created_at=datetime.now(timezone.utc))
    report_repo.count_by_competitor = AsyncMock(return_value=2)
    report_repo.get_by_competitor = AsyncMock(return_value=[r1, r2])

    service = ReportService(report_repository=report_repo, competitor_repository=competitor_repo)

    res = await service.list_reports(user_id="user_123", competitor_id="comp_789", page=1, size=10)
    assert isinstance(res, ReportListResponse)
    assert res.total == 2
    assert len(res.items) == 2


@pytest.mark.asyncio
async def test_update_status_success():
    report_repo = MagicMock()
    competitor_repo = MagicMock()

    report = Report(id="report_123", competitor_id="comp_789", status=REPORT_STATUS_PENDING, created_at=datetime.now(timezone.utc))
    report_repo.get_by_id = AsyncMock(return_value=report)
    
    updated_report = Report(id="report_123", competitor_id="comp_789", status=REPORT_STATUS_COMPLETED, created_at=datetime.now(timezone.utc))
    report_repo.update = AsyncMock(return_value=updated_report)

    service = ReportService(report_repository=report_repo, competitor_repository=competitor_repo)

    res = await service.update_status(report_id="report_123", status=REPORT_STATUS_COMPLETED)
    assert isinstance(res, ReportResponse)
    assert res.status == REPORT_STATUS_COMPLETED
