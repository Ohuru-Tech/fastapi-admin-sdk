from functools import lru_cache
from typing import Any, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict

_runtime_overrides: Dict[str, Any] = {}


class AdminSDKSettings(BaseSettings):
    admin_db_url: str = "sqlite+aiosqlite:///:memory:"
    orm_type: str = "sqlalchemy"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


def configure_settings(**kwargs):
    global _runtime_overrides

    _runtime_overrides.update(kwargs)

    get_settings.cache_clear()


@lru_cache
def get_settings():
    base_settings = AdminSDKSettings(**_runtime_overrides)
    return base_settings
