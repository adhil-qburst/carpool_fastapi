from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str

    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    smtp_from: str
    smtp_use_tls: bool

    email_verification_base_url: str
    email_verification_expire_hours: int
    email_verification_success_url: str

    jwt_secret: str
    jwt_refresh_secret: str
    jwt_algorithm: str


@lru_cache
def get_settings() -> Settings:
    return Settings()
