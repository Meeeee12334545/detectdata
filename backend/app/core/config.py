from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = "EDS Data Platform"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+psycopg2://eds:eds@db:5432/eds"

    detectdata_base_url: str = "https://www.detecdata-en.com"
    detectdata_username: str = ""
    detectdata_password: str = ""
    detectdata_login_path: str = "/"

    scheduler_enabled: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
