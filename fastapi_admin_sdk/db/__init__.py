from fastapi_admin_sdk.config.settings import get_settings
from fastapi_admin_sdk.db.session_factory import SessionFactory

settings = get_settings()

if settings.orm_type == "sqlalchemy":
    from fastapi_admin_sdk.db.sqlalchemy_factory import get_sqlalchemy_factory

    def get_session_factory() -> SessionFactory:
        """Get the session factory based on configured ORM type."""
        return get_sqlalchemy_factory()
else:
    raise ValueError(f"Unsupported ORM type: {settings.orm_type}")
