import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )
    secret_str: SecretStr
    algorithm: str = "HS256"

    access_token_expire_time_in_minutes: int = 30
    refresh_token_expire_time_in_days: int = 15

    max_password_length: int = 512

    db_url: str = "sqlite+aiosqlite:///todo_app.db"
    db_name: str = "todo"

    postgres_ssl: str = "false"
    postgres_user: str | None = None
    postgres_wwpassword: str | None = None
    postgres_host: str | None = None

    redis_url: str = "redis://localhost:6380"
    redis_host: str = "localhost"



settings = Settings()
