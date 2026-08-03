from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession

@dataclass
class AgentDeps:
    """Dependencies injected into PydanticAI agents during execution context."""
    db_session: AsyncSession
    competitor_id: str
    competitor_url: str
    historical_data: str | None = None
