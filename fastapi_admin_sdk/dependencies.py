from fastapi import Depends

from fastapi_admin_sdk.db import get_session_factory
from fastapi_admin_sdk.db.session_factory import SessionFactory
from fastapi_admin_sdk.services.admin_service import AdminService


def get_session_factory_dependency() -> SessionFactory:
    """Dependency to get the session factory."""
    return get_session_factory()


def get_admin_service(
    session_factory: SessionFactory = Depends(get_session_factory_dependency),
) -> AdminService:
    """Dependency to get the admin service with injected session factory."""
    return AdminService(session_factory)
