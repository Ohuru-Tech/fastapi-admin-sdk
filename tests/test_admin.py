"""Tests for admin module."""

import pytest
from pydantic import BaseModel

from fastapi_admin_sdk.admin import AdminRegistry, BaseAdmin, register
from fastapi_admin_sdk.resource import Resource


class MockResource(Resource):
    """Mock resource for testing."""

    def __init__(self):
        super().__init__(name="test", verbose_name_plural="tests")


class CreateSchema(BaseModel):
    """Test create schema."""

    name: str


class UpdateSchema(BaseModel):
    """Test update schema."""

    name: str | None = None


class MockAdmin(BaseAdmin):
    """Mock admin class."""

    list_display = ["id", "name"]
    list_filter = ["name"]
    search_fields = ["name"]
    ordering = ["id"]
    create_form_schema = CreateSchema
    update_form_schema = UpdateSchema
    lookup_field = "id"

    def __init__(self, resource: Resource):
        super().__init__(resource)


def test_base_admin_initialization(mock_resource):
    """Test BaseAdmin initialization."""
    admin = BaseAdmin(mock_resource)
    assert admin.resource == mock_resource
    assert admin.list_display == []
    assert admin.lookup_field == "id"


@pytest.mark.asyncio
async def test_base_admin_permissions_async(mock_resource, mock_request):
    """Test BaseAdmin permission methods are async."""
    admin = BaseAdmin(mock_resource)

    result = await admin.has_create_permission(mock_request)
    assert result is True


def test_admin_registry():
    """Test AdminRegistry is empty initially."""
    assert AdminRegistry._registry == {}


def test_register_decorator():
    """Test register decorator."""
    resource = MockResource()

    @register(resource)
    class MyAdmin(MockAdmin):
        pass

    assert "test" in AdminRegistry._registry
    assert AdminRegistry._registry["test"]["resource"] == resource
    # The decorator stores the class itself, not an instance
    # The registry now stores an instance, not the class
    assert isinstance(AdminRegistry._registry["test"]["admin"], MyAdmin)


def test_register_decorator_multiple_resources():
    """Test registering multiple resources."""
    resource1 = MockResource()
    resource2 = Resource(name="other", verbose_name_plural="others")

    @register(resource1)
    class Admin1(MockAdmin):
        pass

    @register(resource2)
    class Admin2(MockAdmin):
        pass

    assert len(AdminRegistry._registry) == 2
    assert "test" in AdminRegistry._registry
    assert "other" in AdminRegistry._registry
