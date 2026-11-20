from urllib.parse import urlsplit

from pydantic import Field, model_validator
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
    secret_key: str = Field(default="development_only_change_this_jwt_secret_key", alias="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

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
    cors_allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="CORS_ALLOWED_ORIGINS",
    )
    
    # Subgroup configurations instantiated on demand
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    external: ExternalApiSettings = Field(default_factory=ExternalApiSettings)

    @model_validator(mode="after")
    def validate_deployment_secrets(self):
        """Reject unsafe configuration when running outside development."""
        if self.env.lower() not in {"development", "dev", "local"}:
            key = self.security.secret_key
            lowered_key = key.strip().lower()
            if (
                len(key) < 32
                or any(
                    marker in lowered_key
                    for marker in (
                        "change_this",
                        "placeholder",
                        "your_",
                        "development",
                        "local_",
                        "replace",
                        "example",
                    )
                )
            ):
                raise ValueError("JWT_SECRET_KEY must be a unique secret of at least 32 characters outside development")
            if self.debug:
                raise ValueError("DEBUG must be false outside development")
            if self.security.algorithm != "HS256":
                raise ValueError("JWT_ALGORITHM must be HS256")
            if self.security.access_token_expire_minutes <= 0:
                raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be positive")

            origins = [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
            if not origins or "*" in origins:
                raise ValueError("CORS_ALLOWED_ORIGINS must list explicit production origins")
            for origin in origins:
                parsed = urlsplit(origin)
                if parsed.scheme != "https" or not parsed.netloc or parsed.path not in {"", "/"}:
                    raise ValueError("Production CORS origins must be HTTPS origins without paths")
        return self

settings = Settings()


