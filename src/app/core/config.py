from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_use_tls: bool = True

    email_verification_base_url: str = "http://localhost:3000/verify-email"
    email_verification_expire_hours: int = 24


@lru_cache
def get_settings() -> Settings:
    return Settings()
