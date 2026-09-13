from app.config import Settings


def test_hosted_postgres_url_is_normalized_for_psycopg() -> None:
    settings = Settings(
        DATABASE_URL="postgres://user:password@db.example.com:5432/foodbridge",
        SECRET_KEY="test-secret",
        _env_file=None,
    )

    assert settings.sqlalchemy_database_url == "postgresql+psycopg://user:password@db.example.com:5432/foodbridge"


def test_postgresql_url_is_normalized_for_psycopg() -> None:
    settings = Settings(
        DATABASE_URL="postgresql://user:password@localhost:5432/foodbridge",
        SECRET_KEY="test-secret",
        _env_file=None,
    )

    assert settings.sqlalchemy_database_url == "postgresql+psycopg://user:password@localhost:5432/foodbridge"


def test_cors_allowed_origins_alias_is_supported() -> None:
    settings = Settings(
        DATABASE_URL="sqlite:///./test.db",
        SECRET_KEY="test-secret",
        CORS_ALLOWED_ORIGINS="https://foodbridge.example, https://www.foodbridge.example",
        _env_file=None,
    )

    assert settings.cors_origins == ["https://foodbridge.example", "https://www.foodbridge.example"]
