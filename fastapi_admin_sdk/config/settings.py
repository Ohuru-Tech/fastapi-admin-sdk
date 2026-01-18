from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    admin_db_url: str = "sqlite+aiosqlite:///:memory:"
    orm_type: str = "sqlalchemy"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


settings = Settings()
