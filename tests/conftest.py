"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request

from fastapi_admin_sdk.admin import AdminRegistry
from fastapi_admin_sdk.resource import Resource


@pytest.fixture
def mock_request():
    """Create a mock FastAPI Request."""
    return MagicMock(spec=Request)


@pytest.fixture
def mock_resource():
    """Create a mock Resource."""
    resource = MagicMock(spec=Resource)
    resource.name = "test_resource"
    resource.verbose_name_plural = "test resources"
    return resource


@pytest.fixture
def mock_session_factory():
    """Create a mock SessionFactory."""
    factory = AsyncMock()
    factory.__aenter__ = AsyncMock(return_value=AsyncMock())
    factory.__aexit__ = AsyncMock(return_value=None)
    return factory


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    # Ensure tests use in-memory SQLite database
    monkeypatch.setenv("ADMIN_DB_URL", "sqlite+aiosqlite:///:memory:")
    monkeypatch.setenv("ORM_TYPE", "sqlalchemy")
    yield
    # Cleanup is automatic with in-memory database


@pytest.fixture(autouse=True)
def reset_registry():
    """Reset AdminRegistry before each test."""
    AdminRegistry._registry.clear()
    yield
    AdminRegistry._registry.clear()


@pytest.fixture(autouse=True)
def reset_sqlalchemy_factory():
    """Reset SQLAlchemy factory singleton between tests to prevent hanging."""
    # Import here to avoid circular imports
    import fastapi_admin_sdk.db.sqlalchemy_factory as factory_module

    # Reset singleton before each test to ensure fresh factory
    factory_module._sqlalchemy_factory = None

    yield

    # Reset singleton after test
    factory_module._sqlalchemy_factory = None
    factory_module._sqlalchemy_factory = None
