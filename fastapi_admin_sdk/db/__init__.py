from fastapi_admin_sdk.config.settings import settings
from fastapi_admin_sdk.db.session_factory import SessionFactory

if settings.orm_type == "sqlalchemy":
    from fastapi_admin_sdk.db.sqlalchemy_factory import get_sqlalchemy_factory

    def get_session_factory() -> SessionFactory:
        """Get the session factory based on configured ORM type."""
        return get_sqlalchemy_factory()
else:
    raise ValueError(f"Unsupported ORM type: {settings.orm_type}")
