import asyncio
import uuid
from datetime import datetime, timedelta
from src.database import get_db
from src.domains.reports.models import Report, REPORT_STATUS_COMPLETED
from src.domains.competitors.models import Competitor
from src.domains.users.models import User
from src.core.pdf.generator import PDFReportGenerator
from sqlalchemy import select

async def regenerate_pdfs():
    async for db in get_db():
        target_user_id = 'ec8fc7a5-46f0-4f68-8ae0-0cdd9e3307fb'
        result = await db.execute(select(Competitor).where(Competitor.user_id == target_user_id))
        comps = result.scalars().all()

        generator = PDFReportGenerator()
        for comp in comps:
            report_result = await db.execute(select(Report).where(Report.competitor_id == comp.id))
            report = report_result.scalar_one_or_none()
            if report:
                print(f"Regenerating PDF for {comp.company_name}...")
                pdf_path = generator.generate_pdf(report=report)
                report.pdf_path = pdf_path
                print(f"  -> {pdf_path}")
        await db.commit()
        print("All PDFs regenerated!")
        break

asyncio.run(regenerate_pdfs())