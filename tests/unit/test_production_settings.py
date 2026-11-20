import pytest

from src.config import Settings


def _settings(monkeypatch, **overrides):
    values = {
        "ENV": "production",
        "DEBUG": "false",
        "JWT_SECRET_KEY": "a" * 64,
        "JWT_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "CORS_ALLOWED_ORIGINS": "https://app.example.com",
    }
    values.update(overrides)
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return Settings(_env_file=None)


def test_production_configuration_accepts_secure_values(monkeypatch):
    settings = _settings(monkeypatch)

    assert settings.env == "production"
    assert settings.debug is False
    assert settings.cors_allowed_origins == "https://app.example.com"


@pytest.mark.parametrize(
    "overrides",
    [
        {"DEBUG": "true"},
        {"JWT_SECRET_KEY": "local_development_only_replace_with_random_secret"},
        {"JWT_ALGORITHM": "none"},
        {"ACCESS_TOKEN_EXPIRE_MINUTES": "0"},
        {"CORS_ALLOWED_ORIGINS": "*"},
        {"CORS_ALLOWED_ORIGINS": "http://app.example.com"},
    ],
)
def test_production_configuration_rejects_unsafe_values(monkeypatch, overrides):
    with pytest.raises(ValueError):
        _settings(monkeypatch, **overrides)
