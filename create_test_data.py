import asyncio
import uuid
from datetime import datetime, timedelta
from src.database import get_db
from src.domains.reports.models import Report, REPORT_STATUS_COMPLETED
from src.domains.competitors.models import Competitor
from src.domains.users.models import User
from src.core.pdf.generator import PDFReportGenerator
from sqlalchemy import select, delete

async def create_test_data():
    async for db in get_db():
        target_user_id = 'ec8fc7a5-46f0-4f68-8ae0-0cdd9e3307fb'
        result = await db.execute(select(User).where(User.id == target_user_id))
        user = result.scalar_one_or_none()
        if not user:
            print(f'User {target_user_id} not found')
            return
        print(f'Found user: {user.email}')

        # Delete existing competitors for this user
        existing = await db.execute(select(Competitor).where(Competitor.user_id == target_user_id))
        for comp in existing.scalars().all():
            print(f'Deleting existing: {comp.company_name}')
            await db.execute(delete(Report).where(Report.competitor_id == comp.id))
            await db.delete(comp)
        await db.flush()

        test_companies = [
            {
                'name': 'OpenAI',
                'website': 'https://openai.com',
                'description': 'AI research and deployment company, creator of ChatGPT and DALL-E',
                'industry': 'Artificial Intelligence',
                'country': 'United States',
            },
            {
                'name': 'Anthropic',
                'website': 'https://anthropic.com',
                'description': 'AI safety company, creator of Claude AI assistant',
                'industry': 'Artificial Intelligence',
                'country': 'United States',
            },
            {
                'name': 'Google DeepMind',
                'website': 'https://deepmind.google',
                'description': 'AI research subsidiary of Alphabet, creator of Gemini',
                'industry': 'Artificial Intelligence',
                'country': 'United Kingdom',
            },
            {
                'name': 'Perplexity AI',
                'website': 'https://perplexity.ai',
                'description': 'AI-powered answer engine, competitor to Google Search',
                'industry': 'Artificial Intelligence',
                'country': 'United States',
            },
        ]

        for company in test_companies:
            comp_id = str(uuid.uuid4())
            competitor = Competitor(
                id=comp_id,
                user_id=target_user_id,
                company_name=company['name'],
                website=company['website'],
                industry=company['industry'],
                country=company['country'],
                description=company['description'],
                is_active=True,
                created_at=datetime.utcnow() - timedelta(days=30),
            )
            db.add(competitor)
            await db.flush()

            report_id = str(uuid.uuid4())
            report = Report(
                id=report_id,
                competitor_id=comp_id,
                status=REPORT_STATUS_COMPLETED,
                summary=f"{company['name']} is a leading AI company with strong market position. They have innovative products and growing user base, but face intense competition from larger tech giants.",
                strengths='Strong brand recognition, cutting-edge AI research, large user base, venture funding',
                weaknesses='Limited monetization compared to competitors, slower enterprise adoption, ethical concerns',
                opportunities='Enterprise AI market expansion, international growth, API ecosystem',
                threats='Big tech competition (Google, Microsoft), regulatory scrutiny, open-source alternatives',
                pricing_analysis='Freemium model with premium tiers. OpenAI: $20/mo for ChatGPT Plus. Anthropic: tiered API pricing. Perplexity: free + Pro $20/mo.',
                feature_analysis='Core AI capabilities, chat interfaces, API access. Differentiation in model quality and safety features.',
                market_position='Leading AI company with strong developer adoption. Facing competition from established tech giants.',
                raw_ai_response='mock data for testing',
                email_status='pending',
                created_at=datetime.utcnow() - timedelta(days=5),
            )
            db.add(report)
            await db.flush()

            try:
                generator = PDFReportGenerator()
                pdf_path = generator.generate_pdf(report=report)
                report.pdf_path = pdf_path
                print(f"Created {company['name']} with report {report_id[:8]}...")
            except Exception as e:
                print(f"PDF generation failed for {company['name']}: {e}")

        await db.commit()
        print('All test companies created successfully!')
        break

asyncio.run(create_test_data())