from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cannabis_intel"
    sync_database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/cannabis_intel"
    redis_url: str = "redis://localhost:6379/0"

    secret_key: str = "changeme-use-a-real-secret-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    reset_token_expire_minutes: int = 60
    invite_token_expire_days: int = 7

    admin_email: str = "admin@cannabisintel.com"
    admin_password: str = "Admin2026!"
    admin_name: str = "Platform Admin"

    resend_api_key: str = ""
    email_from: str = "noreply@cannabisintel.com"
    email_from_name: str = "NJ Cannabis Intel"

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    google_maps_api_key: str = ""
    frontend_url: str = "http://localhost:3000"
    environment: str = "development"

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
