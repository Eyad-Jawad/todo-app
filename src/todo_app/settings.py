from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    secret_key: SecretStr
    algorithm: str = "HS256"

    access_token_expire_time_in_minutes: int = 30
    refresh_token_expire_time_in_days: int = 15

    max_password_length: int = 512


settings = Settings()
