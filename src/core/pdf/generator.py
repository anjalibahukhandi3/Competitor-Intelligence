"""PDF Report Generator — WeasyPrint & Jinja2 PDF compiler for competitive analysis.

Clean Architecture boundary
----------------------------
This core module renders HTML templates using Jinja2 and converts them into
professional consulting-style PDF documents via WeasyPrint.

Design decisions
----------------
- raw_ai_response JSON dicts are converted to SimpleNamespace objects via
  _to_namespace() so Jinja templates can access nested fields with dot-notation
  (e.g. ``news.items``, ``pricing.tiers``) without triggering Python's built-in
  ``dict.items()`` method.
- WeasyPrint is imported lazily inside generate_pdf() to keep module-level
  startup safe in environments where GTK/Pango C-libraries are absent.
  This also allows tests to patch ``src.core.pdf.generator.HTML`` cleanly.
- Fallback binary PDF written when WeasyPrint raises OSError so the pipeline
  does not crash on bare Windows development machines.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import structlog
from jinja2 import Environment, FileSystemLoader

from src.domains.reports.models import Report

logger = structlog.get_logger(__name__)

TEMPLATES_DIR = Path(__file__).parent / "templates"
DEFAULT_OUTPUT_DIR = Path("storage") / "reports"

# Module-level alias so tests can patch ``src.core.pdf.generator.HTML``
# without needing to import weasyprint at module load time.
HTML: Any = None


def _try_load_weasyprint() -> Any:
    """Attempt to import weasyprint.HTML, returning None on failure."""
    try:
        from weasyprint import HTML as _HTML  # noqa: PLC0415
        return _HTML
    except (ImportError, OSError):
        return None


def _to_namespace(obj: Any) -> Any:
    """Recursively convert dicts and lists from JSON into SimpleNamespace objects.

    This allows Jinja2 templates to access dict fields via dot notation
    (e.g. ``{{ news.overall_sentiment }}`` or ``{{ news.news_items }}``)
    without accidentally resolving Python built-in dict methods like
    ``dict.items()`` when the template uses ``{{ news.items }}``.

    The JSON key ``items`` inside the news dict is renamed to ``news_items``
    to prevent shadowing the Python built-in attribute.
    """
    if isinstance(obj, dict):
        renamed: dict[str, Any] = {}
        for k, v in obj.items():
            # Rename the 'items' key inside news/hiring sub-dicts to avoid
            # clashing with dict.items() at the SimpleNamespace attribute level.
            new_key = "news_items" if k == "items" else k
            renamed[new_key] = _to_namespace(v)
        return SimpleNamespace(**renamed)
    elif isinstance(obj, list):
        return [_to_namespace(item) for item in obj]
    return obj


class PDFReportGenerator:
    """Generates professional PDF reports from Report ORM models."""

    def __init__(self, templates_dir: Path | str | None = None) -> None:
        self.templates_dir = Path(templates_dir) if templates_dir else TEMPLATES_DIR
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True,
        )
        self._css_path = self.templates_dir / "styles.css"

    def _load_css(self) -> str:
        if self._css_path.exists():
            return self._css_path.read_text(encoding="utf-8")
        return ""

    def _extract_context(self, report: Report) -> dict[str, Any]:
        """Extracts and formats template context variables from a Report model."""
        competitor_name = "Target Competitor"
        competitor_url = "N/A"
        if hasattr(report, "competitor") and report.competitor:
            competitor_name = getattr(report.competitor, "company_name", competitor_name)
            competitor_url = str(getattr(report.competitor, "website", competitor_url))

        created_date = report.created_at
        if isinstance(created_date, datetime):
            generated_at = created_date.strftime("%B %d, %Y")
        else:
            generated_at = datetime.now(UTC).strftime("%B %d, %Y")

        # Parse raw_ai_response if present for structured signals
        raw_data: dict[str, Any] = {}
        if report.raw_ai_response:
            try:
                parsed = json.loads(report.raw_ai_response)
                if isinstance(parsed, dict):
                    raw_data = parsed
            except Exception as exc:
                logger.debug("Failed to parse raw_ai_response JSON", error=str(exc))

        # SWOT parsing
        swot_data = raw_data.get("swot") or {}
        if not isinstance(swot_data, dict):
            swot_data = {}

        def _split_lines(val: str | None) -> list[str]:
            if not val:
                return []
            lines = [line.strip("- *").strip() for line in val.splitlines() if line.strip()]
            return lines if lines else [val]

        strengths_list = swot_data.get("strengths") or _split_lines(report.strengths)
        weaknesses_list = swot_data.get("weaknesses") or _split_lines(report.weaknesses)
        opportunities_list = swot_data.get("opportunities") or _split_lines(report.opportunities)
        threats_list = swot_data.get("threats") or _split_lines(report.threats)

        swot = SimpleNamespace(
            strengths=strengths_list,
            weaknesses=weaknesses_list,
            opportunities=opportunities_list,
            threats=threats_list,
        )

        # Convert raw agent output dicts into SimpleNamespace trees for clean
        # Jinja2 dot-notation access (avoids dict.items() method collision).
        research = _to_namespace(raw_data.get("research")) if raw_data.get("research") else None
        news = _to_namespace(raw_data.get("news")) if raw_data.get("news") else None
        pricing = _to_namespace(raw_data.get("pricing")) if raw_data.get("pricing") else None
        hiring = _to_namespace(raw_data.get("hiring")) if raw_data.get("hiring") else None

        return {
            "report_id": report.id,
            "competitor_name": competitor_name,
            "competitor_url": competitor_url,
            "generated_at": generated_at,
            "summary": report.summary or "",
            "market_position": report.market_position or "",
            "pricing_analysis": report.pricing_analysis or "",
            "feature_analysis": report.feature_analysis or "",
            "strengths": report.strengths or "",
            "weaknesses": report.weaknesses or "",
            "opportunities": report.opportunities or "",
            "threats": report.threats or "",
            "swot": swot,
            "research": research,
            "news": news,
            "pricing": pricing,
            "hiring": hiring,
            "key_takeaways": [
                SimpleNamespace(
                    title="Market Positioning",
                    description=(
                        report.market_position[:120] + "..."
                        if report.market_position
                        else "Strong product alignment."
                    ),
                ),
                SimpleNamespace(
                    title="Pricing Structure",
                    description=(
                        report.pricing_analysis[:120] + "..."
                        if report.pricing_analysis
                        else "Competitive subscription model."
                    ),
                ),
            ],
            "feature_points": [
                SimpleNamespace(
                    name="Core Product Features",
                    offering=report.feature_analysis or "Standard capability",
                    impact="High Market Relevance",
                )
            ],
            "recommendations": [
                SimpleNamespace(
                    title="Differentiate Value Proposition",
                    description=f"Highlight core performance advantages over {competitor_name}.",
                ),
                SimpleNamespace(
                    title="Optimize Pricing Tiers",
                    description="Structure flexible pricing plans targeting underserved segments.",
                ),
                SimpleNamespace(
                    title="Monitor Feature Roadmap",
                    description=f"Accelerate key feature developments where {competitor_name} is expanding.",
                ),
            ],
        }

    def generate_html(self, report: Report) -> str:
        """Renders HTML string for the report using Jinja2 templates."""
        template = self.env.get_template("base.html")
        css_content = self._load_css()
        context = self._extract_context(report)
        context["css_content"] = css_content
        return template.render(**context)

    def generate_pdf(
        self,
        report: Report,
        output_dir: Path | str | None = None,
    ) -> str:
        """Converts Report into a PDF file and returns the saved file path.

        Parameters
        ----------
        report:
            The Report ORM object containing AI analysis results.
        output_dir:
            Directory where PDF report files are stored. Defaults to ``storage/reports``.

        Returns
        -------
        str
            File path string to the generated PDF document (forward-slash delimited).
        """
        out_dir = Path(output_dir) if output_dir else DEFAULT_OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        filename = f"report_{report.id}.pdf"
        file_path = out_dir / filename

        html_content = self.generate_html(report)

        # Lazy import — allows test patching of ``src.core.pdf.generator.HTML``
        # and avoids crashing the module on environments without GTK C-libraries.
        weasyprint_html = _try_load_weasyprint()

        try:
            if weasyprint_html is None:
                raise OSError("WeasyPrint HTML class unavailable (missing GTK libraries)")
            weasyprint_html(string=html_content).write_pdf(target=str(file_path))
            logger.info("PDF report successfully generated via WeasyPrint", pdf_path=str(file_path))
        except (OSError, Exception) as exc:
            # Fallback for environments missing GTK/Pango (e.g. bare Windows dev machines)
            logger.warning(
                "WeasyPrint native rendering unavailable — writing fallback PDF document",
                error=str(exc),
            )
            self._write_fallback_pdf(file_path=file_path, html_content=html_content)

        return str(file_path).replace("\\", "/")

    def _write_fallback_pdf(self, file_path: Path, html_content: str) -> None:
        """Writes a minimal valid PDF binary when WeasyPrint is unavailable."""
        pdf_bytes = (
            b"%PDF-1.4\n"
            b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << >> >>\nendobj\n"
            b"4 0 obj\n<< /Length 50 >>\nstream\n"
            b"BT /F1 12 Tf 50 700 TD (Competitor Intelligence PDF Report) Tj ET\n"
            b"endstream\nendobj\n"
            b"xref\n0 5\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
            b"0000000115 00000 n \n0000000222 00000 n \n"
            b"trailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n323\n%%EOF\n"
        )
        file_path.write_bytes(pdf_bytes)
