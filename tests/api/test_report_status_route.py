"""The report lifecycle status is managed by background workers only."""

from src.main import app


def test_report_status_mutation_is_not_a_public_route():
    assert "/reports/{report_id}/status" not in app.openapi()["paths"]
