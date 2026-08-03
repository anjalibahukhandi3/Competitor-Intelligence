from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class BaseAppSettings(BaseSettings):
    """Shared base settings class that reads from .env."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

class DatabaseSettings(BaseAppSettings):
    """Database configuration variables."""
    url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/competitor_intel",
        alias="DATABASE_URL"
    )
    pool_size: int = Field(default=20, alias="DB_POOL_SIZE")
    max_overflow: int = Field(default=10, alias="DB_MAX_OVERFLOW")
    pool_timeout: float = Field(default=30.0, alias="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=1800, alias="DB_POOL_RECYCLE")

class SecuritySettings(BaseAppSettings):
    """Security configuration variables (JWT)."""
    secret_key: str = Field(default="placeholder_secret_key", alias="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

class RedisSettings(BaseAppSettings):
    """Redis cache and broker configuration variables."""
    url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")

class AISettings(BaseAppSettings):
    """Google Gemini & Agent configuration variables."""
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.0-flash", alias="GEMINI_MODEL")
    agent_temperature: float = Field(default=0.2, alias="AGENT_TEMPERATURE")
    
    # MCP server configurations
    firecrawl_mcp_server_command: str = Field(default="npx", alias="FIRECRAWL_MCP_SERVER_COMMAND")
    firecrawl_mcp_server_args: str = Field(default="-y,@modelcontextprotocol/server-firecrawl", alias="FIRECRAWL_MCP_SERVER_ARGS")
    tavily_mcp_server_command: str = Field(default="npx", alias="TAVILY_MCP_SERVER_COMMAND")
    tavily_mcp_server_args: str = Field(default="-y,@modelcontextprotocol/server-tavily", alias="TAVILY_MCP_SERVER_ARGS")

class ExternalApiSettings(BaseAppSettings):
    """APIs for intelligence gathering."""
    tavily_api_key: str | None = Field(default=None, alias="TAVILY_API_KEY")
    firecrawl_api_key: str | None = Field(default=None, alias="FIRECRAWL_API_KEY")
    resend_api_key: str | None = Field(default=None, alias="RESEND_API_KEY")
    sender_email: str = Field(default="alerts@yourdomain.com", alias="SENDER_EMAIL")

class Settings(BaseAppSettings):
    """Master Application Settings combining child subgroups."""
    project_name: str = Field(default="Competitor Intelligence AI Agent", alias="PROJECT_NAME")
    env: str = Field(default="development", alias="ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    port: int = Field(default=8000, alias="PORT")
    
    # Subgroup configurations instantiated on demand
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    external: ExternalApiSettings = Field(default_factory=ExternalApiSettings)

settings = Settings()


