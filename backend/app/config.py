from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://healthlink:healthlink@localhost:5432/healthlink"
    secret_key: str = "dev-only-change-me"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    max_failed_logins: int = 5
    lockout_minutes: int = 15
    auto_create_tables: bool = True  # dev convenience; use Alembic migrations otherwise
    cors_origins: str = "http://localhost:5173"


settings = Settings()
