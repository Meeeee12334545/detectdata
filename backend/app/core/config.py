from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "EDS Data Platform"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+psycopg2://eds:eds@localhost:5432/eds"

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_database_url(cls, v: str) -> str:
        # Render and Heroku provide postgres:// or postgresql:// which need the
        # explicit psycopg2 driver suffix for SQLAlchemy 2.x
        if not isinstance(v, str):
            return v
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
        return v

    detectdata_base_url: str = "https://www.detecdata-en.com"
    detectdata_username: str = ""
    detectdata_password: str = ""
    detectdata_login_path: str = "/"

    scheduler_enabled: bool = True

    frontend_url: str = "http://localhost:5173"

    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
