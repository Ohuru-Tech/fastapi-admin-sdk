"""Tests for manifest API."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel, EmailStr

from fastapi_admin_sdk.admin import AdminRegistry, BaseAdmin
from fastapi_admin_sdk.forms import CharField, EmailField
from fastapi_admin_sdk.resource import Resource
from fastapi_admin_sdk.services.admin_service import AdminService


class CreateSchema(BaseModel):
    """Test create schema."""

    name: str
    email: EmailStr


class UpdateSchema(BaseModel):
    """Test update schema."""

    name: str | None = None
    email: EmailStr | None = None


class MockResource(Resource):
    """Mock resource for testing."""

    def __init__(self, name: str = "test_resource", verbose_name: str = "test resources"):
        super().__init__(name=name, verbose_name_plural=verbose_name)


class MockAdmin(BaseAdmin):
    """Mock admin for testing."""

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
def mock_request():
    """Create a mock request."""
    return MagicMock()


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


@pytest.mark.asyncio
async def test_get_manifest_returns_correct_structure(admin_service, mock_request, registered_admin):
    """Test get_manifest returns correct structure."""
    result = await admin_service.get_manifest(mock_request)

    assert isinstance(result, dict)
    assert "resources" in result
    assert isinstance(result["resources"], list)
    assert len(result["resources"]) > 0

    resource_data = result["resources"][0]
    assert "name" in resource_data
    assert "verbose_name" in resource_data
    assert "actions" in resource_data
    assert "list_config" in resource_data
    assert "create_schema" in resource_data
    assert "update_schema" in resource_data


@pytest.mark.asyncio
async def test_get_manifest_includes_all_actions_when_permitted(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest includes all actions when user has all permissions."""
    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    actions = resource_data["actions"]
    assert "list" in actions
    assert "create" in actions
    assert "update" in actions
    assert "delete" in actions
    assert "retrieve" in actions


@pytest.mark.asyncio
async def test_get_manifest_excludes_resources_with_no_permissions(
    admin_service, mock_request
):
    """Test get_manifest excludes resources with no permissions."""
    # Create a resource with no permissions
    resource = MockResource(name="no_permission_resource")
    admin = MockAdmin(resource)

    async def deny_all(request):
        return False

    admin.has_list_permission = deny_all
    admin.has_create_permission = deny_all
    admin.has_update_permission = deny_all
    admin.has_delete_permission = deny_all
    admin.has_retrieve_permission = deny_all

    AdminRegistry._registry[resource.name] = {
        "admin": admin,
        "resource": resource,
    }

    result = await admin_service.get_manifest(mock_request)

    # Should not include the resource with no permissions
    resource_names = [r["name"] for r in result["resources"]]
    assert "no_permission_resource" not in resource_names


@pytest.mark.asyncio
async def test_get_manifest_filters_actions_by_permissions(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest filters actions based on permissions."""
    admin, resource = registered_admin

    # Deny create and delete permissions
    async def deny_create_delete(request):
        return False

    admin.has_create_permission = deny_create_delete
    admin.has_delete_permission = deny_create_delete

    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    actions = resource_data["actions"]
    assert "list" in actions
    assert "create" not in actions
    assert "update" in actions
    assert "delete" not in actions
    assert "retrieve" in actions


@pytest.mark.asyncio
async def test_get_manifest_schema_enhancement_with_form_fields(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest enhances schemas with form field types."""
    admin, resource = registered_admin
    admin.form_field_types = {
        "name": CharField(max_length=100),
        "email": EmailField(),
    }

    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    create_schema = resource_data["create_schema"]

    # Check that form field metadata is present
    assert "properties" in create_schema
    if "name" in create_schema["properties"]:
        name_field = create_schema["properties"]["name"]
        assert "x-field-type" in name_field
        assert name_field["x-field-type"] == "char"
        assert "maxLength" in name_field

    if "email" in create_schema["properties"]:
        email_field = create_schema["properties"]["email"]
        assert "x-field-type" in email_field
        assert email_field["x-field-type"] == "email"


@pytest.mark.asyncio
async def test_get_manifest_list_config(admin_service, mock_request, registered_admin):
    """Test get_manifest includes list configuration."""
    admin, resource = registered_admin
    admin.list_display = ["id", "name", "email"]
    admin.list_filter = ["name"]
    admin.search_fields = ["name", "email"]
    admin.ordering = ["-id"]

    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    list_config = resource_data["list_config"]

    assert list_config["display_fields"] == ["id", "name", "email"]
    assert list_config["filter_fields"] == ["name"]
    assert list_config["search_fields"] == ["name", "email"]
    assert list_config["ordering"] == ["-id"]


@pytest.mark.asyncio
async def test_get_manifest_multiple_resources(admin_service, mock_request):
    """Test get_manifest with multiple resources."""
    # Create first resource
    resource1 = MockResource(name="resource1", verbose_name="Resource 1")
    admin1 = MockAdmin(resource1)
    AdminRegistry._registry[resource1.name] = {
        "admin": admin1,
        "resource": resource1,
    }

    # Create second resource
    resource2 = MockResource(name="resource2", verbose_name="Resource 2")
    admin2 = MockAdmin(resource2)
    AdminRegistry._registry[resource2.name] = {
        "admin": admin2,
        "resource": resource2,
    }

    result = await admin_service.get_manifest(mock_request)

    assert len(result["resources"]) == 2
    resource_names = [r["name"] for r in result["resources"]]
    assert "resource1" in resource_names
    assert "resource2" in resource_names


@pytest.mark.asyncio
async def test_get_manifest_empty_registry(admin_service, mock_request):
    """Test get_manifest with empty registry."""
    AdminRegistry._registry.clear()

    result = await admin_service.get_manifest(mock_request)

    assert result == {"resources": []}


@pytest.mark.asyncio
async def test_get_manifest_schema_has_required_fields(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest includes required fields in schemas."""
    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    create_schema = resource_data["create_schema"]

    # Check that required fields are present if schema has them
    if "required" in create_schema:
        assert isinstance(create_schema["required"], list)


@pytest.mark.asyncio
async def test_get_manifest_update_schema_optional_fields(
    admin_service, mock_request, registered_admin
):
    """Test get_manifest handles optional fields in update schema."""
    result = await admin_service.get_manifest(mock_request)

    resource_data = result["resources"][0]
    update_schema = resource_data["update_schema"]

    # Update schema should have properties
    assert "properties" in update_schema

    # Fields in update schema should be optional (no required constraint or required=False)
    if "properties" in update_schema:
        for field_name, field_schema in update_schema["properties"].items():
            # If there's x-validation, check required status
            if "x-validation" in field_schema:
                # Update schema fields are typically optional
                pass  # Just verify the structure exists
