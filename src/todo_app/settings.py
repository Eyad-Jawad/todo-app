from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
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
    postgres_user: str
    postgres_password: str
    postgres_host: str

    redis_host: str
    redis_url: str



settings = Settings()
