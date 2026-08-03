"""End-to-end integration tests for the Reports API router.

Full lifecycle tested
---------------------
1. Register a new user            POST /auth/register
2. Login and obtain JWT           POST /auth/login
3. Create a competitor            POST /competitors/
4. Trigger an AI report           POST /reports/trigger/{competitor_id}
5. Get the report by ID           GET  /reports/{report_id}
6. List reports for competitor    GET  /reports/{competitor_id}/list
7. Update report status           PATCH /reports/{report_id}/status

Guard-rail tests
----------------
- Trigger report for unknown competitor  → 404
- Trigger report without auth token      → 401
- Get non-existent report                → 404
- List reports with invalid pagination   → 422
"""

import pytest
import pytest_asyncio
import uuid
from httpx import AsyncClient, ASGITransport

from src.main import app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def unique_email() -> str:
    """Generates a unique email so parallel runs don't collide."""
    return f"test_{uuid.uuid4().hex[:8]}@example.com"


async def register_and_login(client: AsyncClient) -> tuple[dict, str]:
    """Creates a user and returns (user_data, bearer_token)."""
    email = unique_email()
    password = "SecurePass123!"

    reg_resp = await client.post(
        "/auth/register",
        json={"email": email, "password": password},
    )
    assert reg_resp.status_code == 201, f"Register failed: {reg_resp.text}"
    user = reg_resp.json()

    login_resp = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token = login_resp.json()["access_token"]

    return user, token


async def create_competitor(client: AsyncClient, token: str) -> dict:
    """Creates and returns a competitor owned by the authenticated user."""
    resp = await client.post(
        "/competitors/",
        json={
            "company_name": f"Acme Corp {uuid.uuid4().hex[:4]}",
            "website": "https://acme.example.com",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Create competitor failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture()
async def async_client():
    """Provides an async HTTP client bound to the FastAPI app."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest_asyncio.fixture()
async def auth_context(async_client: AsyncClient):
    """Returns (client, user, token, competitor) for authenticated test flows."""
    user, token = await register_and_login(async_client)
    competitor = await create_competitor(async_client, token)
    return async_client, user, token, competitor


# ---------------------------------------------------------------------------
# Happy-path lifecycle test
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_full_report_lifecycle(auth_context):
    """
    Complete end-to-end lifecycle:
      Register → Login → Create Competitor → Trigger Report →
      Get Report → List Reports → Update Status
    """
    client, user, token, competitor = auth_context
    headers = {"Authorization": f"Bearer {token}"}
    competitor_id = competitor["id"]

    # ── Step 4: Trigger report ──────────────────────────────────────────────
    trigger_resp = await client.post(
        f"/reports/trigger/{competitor_id}",
        headers=headers,
    )
    assert trigger_resp.status_code == 202, f"Trigger failed: {trigger_resp.text}"

    trigger_data = trigger_resp.json()
    assert "report_id" in trigger_data
    assert trigger_data["status"] == "pending"
    assert "message" in trigger_data

    report_id = trigger_data["report_id"]

    # ── Step 5: Get report by ID ────────────────────────────────────────────
    get_resp = await client.get(
        f"/reports/{report_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200, f"Get report failed: {get_resp.text}"

    report = get_resp.json()
    assert report["id"] == report_id
    assert report["competitor_id"] == competitor_id
    assert report["status"] == "pending"
    # AI fields are None until the background worker runs
    assert report["summary"] is None
    assert report["strengths"] is None

    # ── Step 6: List reports for competitor ────────────────────────────────
    list_resp = await client.get(
        f"/reports/{competitor_id}/list",
        headers=headers,
    )
    assert list_resp.status_code == 200, f"List reports failed: {list_resp.text}"

    list_data = list_resp.json()
    assert "items" in list_data
    assert "total" in list_data
    assert list_data["total"] >= 1
    assert any(r["id"] == report_id for r in list_data["items"])

    # ── Step 7: Update report status ───────────────────────────────────────
    patch_resp = await client.patch(
        f"/reports/{report_id}/status",
        json={"status": "processing"},
        headers=headers,
    )
    assert patch_resp.status_code == 200, f"Status update failed: {patch_resp.text}"

    updated = patch_resp.json()
    assert updated["id"] == report_id
    assert updated["status"] == "processing"


# ---------------------------------------------------------------------------
# Guard-rail tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trigger_report_unknown_competitor(async_client: AsyncClient):
    """Triggering a report for a non-existent competitor returns 404."""
    _, token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())

    resp = await async_client.post(f"/reports/trigger/{fake_id}", headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_report_unauthenticated(async_client: AsyncClient):
    """Triggering a report without a JWT token returns 401."""
    fake_id = str(uuid.uuid4())
    resp = await async_client.post(f"/reports/trigger/{fake_id}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_report_not_found(async_client: AsyncClient):
    """Getting a report with a non-existent ID returns 404."""
    _, token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())

    resp = await async_client.get(f"/reports/{fake_id}", headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_reports_invalid_pagination(async_client: AsyncClient):
    """Invalid pagination params return 422 Unprocessable Entity from FastAPI."""
    _, token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())

    resp = await async_client.get(
        f"/reports/{fake_id}/list",
        params={"page": 0, "size": 200},   # page<1, size>100 both invalid
        headers=headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_status_missing_body(async_client: AsyncClient):
    """PATCH without a `status` key in the body returns 400."""
    _, token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())

    resp = await async_client.patch(
        f"/reports/{fake_id}/status",
        json={},           # no status field
        headers=headers,
    )
    # Could be 404 (report not found hit first) or 400 (missing status field)
    # Either is a correct failure — we just assert it's not 2xx
    assert resp.status_code in (400, 404)


@pytest.mark.asyncio
async def test_report_ownership_isolation(async_client: AsyncClient):
    """User A cannot access a report triggered by User B."""
    # User A creates competitor and triggers a report
    _, token_a = await register_and_login(async_client)
    competitor_a = await create_competitor(async_client, token_a)

    trigger_resp = await async_client.post(
        f"/reports/trigger/{competitor_a['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert trigger_resp.status_code == 202
    report_id = trigger_resp.json()["report_id"]

    # User B tries to access the same report
    _, token_b = await register_and_login(async_client)
    get_resp = await async_client.get(
        f"/reports/{report_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Should be 403 (access denied) or 404, never 200
    assert get_resp.status_code in (403, 404)


@pytest.mark.asyncio
async def test_list_reports_returns_empty_for_new_competitor(auth_context):
    """A freshly created competitor with no reports returns total=0."""
    client, user, token, competitor = auth_context
    headers = {"Authorization": f"Bearer {token}"}

    # Create a SECOND competitor — no reports for it yet
    second = await create_competitor(client, token)

    list_resp = await client.get(
        f"/reports/{second['id']}/list",
        headers=headers,
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_trigger_multiple_reports(auth_context):
    """Multiple triggers for the same competitor creates multiple report rows."""
    client, user, token, competitor = auth_context
    headers = {"Authorization": f"Bearer {token}"}
    competitor_id = competitor["id"]

    # Trigger 3 times
    for _ in range(3):
        resp = await client.post(f"/reports/trigger/{competitor_id}", headers=headers)
        assert resp.status_code == 202

    list_resp = await client.get(
        f"/reports/{competitor_id}/list",
        headers=headers,
    )
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 3
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_download_pdf_report_not_found(async_client: AsyncClient):
    """Downloading a non-existent report returns 404 Not Found."""
    _, token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}
    fake_id = str(uuid.uuid4())

    resp = await async_client.get(f"/reports/{fake_id}/download", headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_download_pdf_report_missing_file(auth_context):
    """Downloading a report that has no PDF generated on disk returns 404 Not Found."""
    client, user, token, competitor = auth_context
    headers = {"Authorization": f"Bearer {token}"}

    trigger_resp = await client.post(
        f"/reports/trigger/{competitor['id']}",
        headers=headers,
    )
    report_id = trigger_resp.json()["report_id"]

    # At trigger time, pdf_path is None
    resp = await client.get(f"/reports/{report_id}/download", headers=headers)
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_download_pdf_report_success(auth_context, tmp_path):
    """Downloading a report with a valid pdf_path on disk returns 200 OK and PDF content."""
    client, user, token, competitor = auth_context
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger report
    trigger_resp = await client.post(
        f"/reports/trigger/{competitor['id']}",
        headers=headers,
    )
    report_id = trigger_resp.json()["report_id"]

    # Create a dummy PDF file on disk and set pdf_path via direct DB session or API patch
    fake_pdf = tmp_path / f"report_{report_id}.pdf"
    fake_pdf.write_bytes(b"%PDF-1.4 sample pdf content")

    # Access database session from app container or test session to update report.pdf_path directly
    from src.database import async_session_maker
    from src.domains.reports.repositories import ReportRepository

    async with async_session_maker() as session:
        repo = ReportRepository(session)
        report = await repo.get_by_id(report_id)
        if report:
            report.pdf_path = str(fake_pdf)
            await repo.update(report)

    # Now download the PDF
    download_resp = await client.get(
        f"/reports/{report_id}/download",
        headers=headers,
    )
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"] == "application/pdf"
    assert b"%PDF-1.4" in download_resp.content


@pytest.mark.asyncio
async def test_download_pdf_report_forbidden(async_client: AsyncClient, tmp_path):
    """User B cannot download User A's PDF report."""
    # User A creates report
    user_a, token_a = await register_and_login(async_client)
    competitor_a = await create_competitor(async_client, token_a)
    trigger_resp = await async_client.post(
        f"/reports/trigger/{competitor_a['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    report_id = trigger_resp.json()["report_id"]

    # User B attempts download
    _, token_b = await register_and_login(async_client)
    resp = await async_client.get(
        f"/reports/{report_id}/download",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code in (403, 404)

