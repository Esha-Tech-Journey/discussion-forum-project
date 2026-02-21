from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    SQL_ECHO: bool = False
    REDIS_URL: str = "redis://localhost:6379"
    BOOTSTRAP_ADMIN_EMAIL: str = "admin@discussionforum.com"
    BOOTSTRAP_ADMIN_PASSWORD: str = "Admin@12345"
    BOOTSTRAP_ADMIN_NAME: str = "Bootstrap Admin"
    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[2] / ".env"),
        env_file_encoding="utf-8",
    )


settings = Settings()
