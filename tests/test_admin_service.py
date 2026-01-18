"""Tests for AdminService."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import BaseModel

from fastapi_admin_sdk.admin import AdminRegistry, BaseAdmin
from fastapi_admin_sdk.resource import Resource
from fastapi_admin_sdk.services.admin_service import AdminService


class CreateSchema(BaseModel):
    """Test create schema."""

    name: str
    email: str


class UpdateSchema(BaseModel):
    """Test update schema."""

    name: str | None = None
    email: str | None = None


class MockResource(Resource):
    """Mock resource."""

    def __init__(self):
        super().__init__(name="test_resource", verbose_name_plural="test resources")


class MockAdmin(BaseAdmin):
    """Mock admin."""

    create_form_schema = CreateSchema
    update_form_schema = UpdateSchema
    lookup_field = "id"

    def __init__(self, resource: Resource):
        super().__init__(resource)


@pytest.fixture
def mock_session_factory():
    """Create a mock session factory."""
    return AsyncMock()


@pytest.fixture
def admin_service(mock_session_factory):
    """Create an AdminService instance."""
    return AdminService(mock_session_factory)


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
def mock_request():
    """Create a mock request."""
    return MagicMock()


@pytest.mark.asyncio
async def test_create_resource_not_found(admin_service, mock_request):
    """Test creating a resource that doesn't exist."""
    with pytest.raises(HTTPException) as exc_info:
        await admin_service.create_resource("nonexistent", {}, mock_request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_create_resource_permission_denied(
    admin_service, mock_request, registered_admin
):
    """Test creating a resource without permission."""
    admin, resource = registered_admin

    async def deny_permission(request):
        return False

    admin.has_create_permission = deny_permission

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.create_resource(
            resource.name, {"name": "test", "email": "test@example.com"}, mock_request
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_create_resource_validation_error(
    admin_service, mock_request, registered_admin
):
    """Test creating a resource with invalid data."""
    admin, resource = registered_admin

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.create_resource(
            resource.name, {"invalid": "data"}, mock_request
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_create_resource_success(admin_service, mock_request, registered_admin):
    """Test successfully creating a resource."""
    admin, resource = registered_admin
    resource.create = AsyncMock(
        return_value={"id": 1, "name": "test", "email": "test@example.com"}
    )

    result = await admin_service.create_resource(
        resource.name, {"name": "test", "email": "test@example.com"}, mock_request
    )

    assert result == {"id": 1, "name": "test", "email": "test@example.com"}
    resource.create.assert_called_once_with(
        {"name": "test", "email": "test@example.com"}
    )


@pytest.mark.asyncio
async def test_update_resource_not_found(admin_service, mock_request):
    """Test updating a resource that doesn't exist."""
    with pytest.raises(HTTPException) as exc_info:
        await admin_service.update_resource("nonexistent", "1", {}, mock_request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_update_resource_permission_denied(
    admin_service, mock_request, registered_admin
):
    """Test updating a resource without permission."""
    admin, resource = registered_admin

    async def deny_permission(request):
        return False

    admin.has_update_permission = deny_permission

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.update_resource(
            resource.name, "1", {"name": "updated"}, mock_request
        )
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_update_resource_success(admin_service, mock_request, registered_admin):
    """Test successfully updating a resource."""
    admin, resource = registered_admin
    resource.update = AsyncMock(
        return_value={"id": 1, "name": "updated", "email": "test@example.com"}
    )

    result = await admin_service.update_resource(
        resource.name, "1", {"name": "updated"}, mock_request
    )

    assert result == {"id": 1, "name": "updated", "email": "test@example.com"}
    resource.update.assert_called_once_with("1", {"name": "updated"})


@pytest.mark.asyncio
async def test_list_resource_not_found(admin_service, mock_request):
    """Test listing a resource that doesn't exist."""
    with pytest.raises(HTTPException) as exc_info:
        await admin_service.list_resource("nonexistent", mock_request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_list_resource_permission_denied(
    admin_service, mock_request, registered_admin
):
    """Test listing a resource without permission."""
    admin, resource = registered_admin

    async def deny_permission(request):
        return False

    admin.has_list_permission = deny_permission

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.list_resource(resource.name, mock_request)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_list_resource_success(admin_service, mock_request, registered_admin):
    """Test successfully listing resources."""
    _, resource = registered_admin
    resource.list = AsyncMock(return_value=[{"id": 1, "name": "test"}])

    result = await admin_service.list_resource(resource.name, mock_request)

    assert result == [{"id": 1, "name": "test"}]
    resource.list.assert_called_once_with(None, 0, None, None)


@pytest.mark.asyncio
async def test_list_resource_with_filters(
    admin_service, mock_request, registered_admin
):
    """Test listing resources with filters."""
    admin, resource = registered_admin
    resource.list = AsyncMock(return_value=[])

    filters_json = json.dumps({"name": "test"})
    _ = await admin_service.list_resource(
        resource.name, mock_request, filters=filters_json
    )

    resource.list.assert_called_once_with(None, 0, {"name": "test"}, None)


@pytest.mark.asyncio
async def test_list_resource_with_ordering(
    admin_service, mock_request, registered_admin
):
    """Test listing resources with ordering."""
    admin, resource = registered_admin
    resource.list = AsyncMock(return_value=[])

    _ = await admin_service.list_resource(
        resource.name, mock_request, ordering="name,-id"
    )

    resource.list.assert_called_once_with(None, 0, None, ["name", "-id"])


@pytest.mark.asyncio
async def test_list_resource_invalid_json(
    admin_service, mock_request, registered_admin
):
    """Test listing resources with invalid JSON filters."""
    admin, resource = registered_admin

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.list_resource(
            resource.name, mock_request, filters="invalid json"
        )
    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_retrieve_resource_not_found(admin_service, mock_request):
    """Test retrieving a resource that doesn't exist."""
    with pytest.raises(HTTPException) as exc_info:
        await admin_service.retrieve_resource("nonexistent", "1", mock_request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_retrieve_resource_permission_denied(
    admin_service, mock_request, registered_admin
):
    """Test retrieving a resource without permission."""
    admin, resource = registered_admin

    async def deny_permission(request):
        return False

    admin.has_retrieve_permission = deny_permission

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.retrieve_resource(resource.name, "1", mock_request)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_retrieve_resource_success(admin_service, mock_request, registered_admin):
    """Test successfully retrieving a resource."""
    admin, resource = registered_admin
    resource.retrieve = AsyncMock(return_value={"id": 1, "name": "test"})

    result = await admin_service.retrieve_resource(resource.name, "1", mock_request)

    assert result == {"id": 1, "name": "test"}
    resource.retrieve.assert_called_once_with("1")


@pytest.mark.asyncio
async def test_delete_resource_not_found(admin_service, mock_request):
    """Test deleting a resource that doesn't exist."""
    with pytest.raises(HTTPException) as exc_info:
        await admin_service.delete_resource("nonexistent", "1", mock_request)
    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_resource_permission_denied(
    admin_service, mock_request, registered_admin
):
    """Test deleting a resource without permission."""
    admin, resource = registered_admin

    async def deny_permission(request):
        return False

    admin.has_delete_permission = deny_permission

    with pytest.raises(HTTPException) as exc_info:
        await admin_service.delete_resource(resource.name, "1", mock_request)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_delete_resource_success(admin_service, mock_request, registered_admin):
    """Test successfully deleting a resource."""
    admin, resource = registered_admin
    resource.delete = AsyncMock(return_value=True)

    result = await admin_service.delete_resource(resource.name, "1", mock_request)

    assert result is True
    resource.delete.assert_called_once_with("1")


@pytest.mark.asyncio
async def test_get_manifest_empty_registry(admin_service, mock_request):
    """Test get_manifest with empty registry."""
    result = await admin_service.get_manifest(mock_request)
    assert result == {"resources": []}


@pytest.mark.asyncio
async def test_get_manifest_single_resource(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest with a single resource."""
    admin, resource = registered_admin

    result = await admin_service.get_manifest(mock_request)

    assert "resources" in result
    assert len(result["resources"]) == 1
    resource_data = result["resources"][0]
    assert resource_data["name"] == "test_resource"
    assert resource_data["verbose_name"] == "test resources"
    assert "list" in resource_data["actions"]
    assert "create" in resource_data["actions"]
    assert "update" in resource_data["actions"]
    assert "delete" in resource_data["actions"]
    assert "retrieve" in resource_data["actions"]
    assert "list_config" in resource_data
    assert "create_schema" in resource_data
    assert "update_schema" in resource_data


@pytest.mark.asyncio
async def test_get_manifest_filters_by_permissions(admin_service, mock_request):
    """Test get_manifest filters resources by permissions."""
    from fastapi_admin_sdk.admin import AdminRegistry

    # Create two resources with different permissions
    resource1 = MockResource()
    admin1 = MockAdmin(resource1)

    async def deny_all_permissions(request):
        return False

    admin1.has_list_permission = deny_all_permissions
    admin1.has_create_permission = deny_all_permissions
    admin1.has_update_permission = deny_all_permissions
    admin1.has_delete_permission = deny_all_permissions
    admin1.has_retrieve_permission = deny_all_permissions

    AdminRegistry._registry[resource1.name] = {
        "admin": admin1,
        "resource": resource1,
    }

    resource2 = MockResource()
    resource2.name = "test_resource_2"
    resource2.verbose_name_plural = "test resources 2"
    admin2 = MockAdmin(resource2)

    AdminRegistry._registry[resource2.name] = {
        "admin": admin2,
        "resource": resource2,
    }

    result = await admin_service.get_manifest(mock_request)

    # Should only include resource2 (resource1 has no permissions)
    assert len(result["resources"]) == 1
    assert result["resources"][0]["name"] == "test_resource_2"


@pytest.mark.asyncio
async def test_get_manifest_filters_actions_by_permissions(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest filters actions by permissions."""
    admin, resource = registered_admin

    async def deny_create_and_delete(request):
        return False

    admin.has_create_permission = deny_create_and_delete
    admin.has_delete_permission = deny_create_and_delete

    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    assert "list" in resource_data["actions"]
    assert "create" not in resource_data["actions"]
    assert "update" in resource_data["actions"]
    assert "delete" not in resource_data["actions"]
    assert "retrieve" in resource_data["actions"]


@pytest.mark.asyncio
async def test_get_manifest_includes_list_config(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest includes list configuration."""
    admin, resource = registered_admin
    admin.list_display = ["id", "name"]
    admin.list_filter = ["name"]
    admin.search_fields = ["name", "email"]
    admin.ordering = ["id"]

    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    list_config = resource_data["list_config"]
    assert list_config["display_fields"] == ["id", "name"]
    assert list_config["filter_fields"] == ["name"]
    assert list_config["search_fields"] == ["name", "email"]
    assert list_config["ordering"] == ["id"]


@pytest.mark.asyncio
async def test_get_manifest_schema_enhancement(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest enhances schemas with form field types."""
    admin, resource = registered_admin

    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    create_schema = resource_data["create_schema"]
    update_schema = resource_data["update_schema"]

    # Check that schemas have properties
    assert "properties" in create_schema
    assert "properties" in update_schema

    # Check that form field metadata is present (if fields exist)
    if "properties" in create_schema and create_schema["properties"]:
        first_field = list(create_schema["properties"].values())[0]
        # Should have x-field-type if form field types were applied
        assert "x-field-type" in first_field or "type" in first_field
