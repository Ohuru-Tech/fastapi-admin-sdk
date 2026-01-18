"""Tests for routes module."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from fastapi_admin_sdk.admin import AdminRegistry, BaseAdmin
from fastapi_admin_sdk.resource import Resource
from fastapi_admin_sdk.routes import router
from fastapi_admin_sdk.services.admin_service import AdminService


class CreateSchema:
    """Mock create schema."""

    def __init__(self, **kwargs):
        pass


class UpdateSchema:
    """Mock update schema."""

    def __init__(self, **kwargs):
        pass


class MockResource(Resource):
    """Test resource."""

    def __init__(self):
        super().__init__(name="test_resource", verbose_name_plural="test resources")


class MockAdmin(BaseAdmin):
    """Test admin."""

    create_form_schema = CreateSchema
    update_form_schema = UpdateSchema
    lookup_field = "id"

    def __init__(self, resource: Resource):
        super().__init__(resource)


@pytest.fixture
def app():
    """Create a test FastAPI app."""
    app = FastAPI()
    app.include_router(router, prefix="/admin")
    return app


@pytest.fixture
async def client(app):
    """Create a test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def registered_admin():
    """Register a test admin."""
    resource = MockResource()
    admin = MockAdmin(resource)
    AdminRegistry._registry[resource.name] = {
        "admin": admin,
        "resource": resource,
    }
    return admin, resource


@pytest.fixture
def mock_admin_service():
    """Create a mock admin service."""
    service = MagicMock(spec=AdminService)
    service.create_resource = AsyncMock(return_value={"id": 1, "name": "test"})
    service.update_resource = AsyncMock(return_value={"id": 1, "name": "updated"})
    service.list_resource = AsyncMock(return_value=[{"id": 1, "name": "test"}])
    service.retrieve_resource = AsyncMock(return_value={"id": 1, "name": "test"})
    service.delete_resource = AsyncMock(return_value=True)
    return service


@pytest.mark.asyncio
async def test_create_resource_endpoint(
    client, app, registered_admin, mock_admin_service
):
    """Test create resource endpoint."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.post(
            "/admin/test_resource/create", json={"name": "test"}
        )
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "test"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_update_resource_endpoint(
    client, app, registered_admin, mock_admin_service
):
    """Test update resource endpoint."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.patch(
            "/admin/test_resource/1/update", json={"name": "updated"}
        )
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "updated"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_resource_endpoint(
    client, app, registered_admin, mock_admin_service
):
    """Test list resource endpoint."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.get("/admin/test_resource/list")
        assert response.status_code == 200
        assert response.json() == [{"id": 1, "name": "test"}]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_resource_endpoint_with_params(
    client, app, registered_admin, mock_admin_service
):
    """Test list resource endpoint with query parameters."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.get("/admin/test_resource/list?limit=5&offset=10")
        assert response.status_code == 200
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_retrieve_resource_endpoint(
    client, app, registered_admin, mock_admin_service
):
    """Test retrieve resource endpoint."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.get("/admin/test_resource/1/retrieve")
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "test"}
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_delete_resource_endpoint(
    client, app, registered_admin, mock_admin_service
):
    """Test delete resource endpoint."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.delete("/admin/test_resource/1/delete")
        assert response.status_code == 200
        assert response.json() is True
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_manifest_endpoint(client, app, registered_admin, mock_admin_service):
    """Test GET /admin/manifest endpoint."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    # Mock the manifest response
    mock_admin_service.get_manifest = AsyncMock(
        return_value={
            "resources": [
                {
                    "name": "test_resource",
                    "verbose_name": "test resources",
                    "actions": ["list", "create", "update", "delete", "retrieve"],
                    "list_config": {
                        "display_fields": [],
                        "filter_fields": [],
                        "search_fields": [],
                        "ordering": [],
                    },
                    "create_schema": {"type": "object", "properties": {}},
                    "update_schema": {"type": "object", "properties": {}},
                }
            ]
        }
    )

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.get("/admin/manifest")
        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert len(data["resources"]) == 1
        assert data["resources"][0]["name"] == "test_resource"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_get_manifest_endpoint_empty(client, app, mock_admin_service):
    """Test GET /admin/manifest endpoint with empty registry."""
    from fastapi_admin_sdk.dependencies import get_admin_service

    mock_admin_service.get_manifest = AsyncMock(return_value={"resources": []})

    app.dependency_overrides[get_admin_service] = lambda: mock_admin_service
    try:
        response = await client.get("/admin/manifest")
        assert response.status_code == 200
        data = response.json()
        assert data == {"resources": []}
    finally:
        app.dependency_overrides.clear()
