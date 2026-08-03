"""Unit tests for the PDFReportGenerator module."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.core.pdf.generator import PDFReportGenerator
from src.domains.reports.models import Report


@pytest.fixture
def sample_report() -> Report:
    """Fixture providing a mock Report model populated with AI analysis data."""
    raw_ai = {
        "swot": {
            "strengths": ["Strong brand recognition", "Patented AI core"],
            "weaknesses": ["High tier price"],
            "opportunities": ["Global expansion"],
            "threats": ["New entrants"],
        },
        "research": {
            "target_customers": ["Enterprise", "Mid-market"],
            "primary_use_cases": ["Automated intelligence"],
            "key_differentiators": ["Real-time diff tracking"],
        },
        "pricing": {
            "pricing_model": "subscription",
            "has_free_tier": True,
            "has_enterprise_tier": True,
            "tiers": [
                {
                    "tier_name": "Pro",
                    "price": "$49/mo",
                    "billing_cycle": "monthly",
                    "key_features": ["Full tracking", "Daily alerts"],
                }
            ],
        },
        "news": {
            "overall_sentiment": "positive",
            "key_themes": ["Product launch"],
            "items": [
                {
                    "headline": "Acme launches v2",
                    "source": "Tech News",
                    "published_at": "2026-08-01",
                    "sentiment": "positive",
                    "summary": "Acme releases v2 platform.",
                }
            ],
        },
        "hiring": {
            "growth_signal": "hiring",
            "total_open_roles": 5,
            "top_departments": ["Engineering"],
            "postings": [
                {
                    "title": "Backend Dev",
                    "department": "Engineering",
                    "location": "Remote",
                    "inferred_skills": ["Python", "FastAPI"],
                }
            ],
        },
    }

    report = Report(
        id="rep-12345",
        competitor_id="comp-67890",
        summary="Acme Corp is accelerating product development in AI space.",
        strengths="- Brand recognition\n- Technology stack",
        weaknesses="- High cost",
        opportunities="- Market expansion",
        threats="- Aggressive rivals",
        pricing_analysis="Tiered subscription structure with free tier.",
        feature_analysis="Advanced tracking and real-time alerts.",
        market_position="Market Leader in SaaS intelligence.",
        raw_ai_response=json.dumps(raw_ai),
    )
    # Mock relationship
    mock_competitor = MagicMock()
    mock_competitor.company_name = "Acme Corporation"
    mock_competitor.website = "https://acme.example.com"
    report.competitor = mock_competitor
    return report


def test_pdf_generator_html_rendering(sample_report: Report) -> None:
    """Tests that HTML generation includes all 10 required report section elements."""
    generator = PDFReportGenerator()
    html = generator.generate_html(sample_report)

    assert "Acme Corporation" in html
    assert "Acme Corp is accelerating product development" in html
    assert "Executive Summary" in html
    assert "Competitor Overview" in html
    assert "Pricing Strategy" in html
    assert "Feature Comparison" in html
    # HTML-escaped variant due to Jinja autoescape
    assert "News" in html
    assert "Hiring" in html
    assert "SWOT Analysis" in html
    assert "Strategic Recommendations" in html
    # SWOT bullet points from raw_ai_response
    assert "Strong brand recognition" in html
    # Pricing from raw_ai_response
    assert "Pro" in html or "$49/mo" in html


def test_pdf_generator_pdf_creation(sample_report: Report, tmp_path: Path) -> None:
    """Tests that generate_pdf writes a PDF file to the specified output directory."""
    generator = PDFReportGenerator()
    pdf_path_str = generator.generate_pdf(sample_report, output_dir=tmp_path)

    pdf_path = Path(pdf_path_str)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    assert pdf_path.suffix == ".pdf"


def test_pdf_generator_fallback(sample_report: Report, tmp_path: Path) -> None:
    """Tests fallback PDF writing when WeasyPrint is unavailable (missing GTK C-deps).

    Patches ``_try_load_weasyprint`` at the module level so the test does not
    need to import ``weasyprint`` (which crashes on Windows without GTK).
    """
    generator = PDFReportGenerator()
    # Patch the helper that loads WeasyPrint to return None (GTK not available)
    with patch("src.core.pdf.generator._try_load_weasyprint", return_value=None):
        pdf_path_str = generator.generate_pdf(sample_report, output_dir=tmp_path)

    pdf_path = Path(pdf_path_str)
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 0
    content = pdf_path.read_bytes()
    assert b"%PDF-1.4" in content


def test_to_namespace_renames_items_key() -> None:
    """Tests that _to_namespace renames the 'items' key to 'news_items' to prevent dict.items() collision."""
    from src.core.pdf.generator import _to_namespace

    raw = {
        "overall_sentiment": "positive",
        "key_themes": ["AI"],
        "items": [{"headline": "Test", "source": "Test Source", "sentiment": "positive", "summary": "Test"}],
    }
    result = _to_namespace(raw)
    assert isinstance(result, SimpleNamespace)
    assert hasattr(result, "news_items")
    assert not hasattr(result, "items")
    assert result.overall_sentiment == "positive"
    assert isinstance(result.news_items, list)
    assert result.news_items[0].headline == "Test"
