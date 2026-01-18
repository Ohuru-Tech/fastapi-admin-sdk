"""Tests for resource module."""

import pytest

from fastapi_admin_sdk.resource import Resource


def test_resource_initialization():
    """Test Resource initialization."""
    resource = Resource(name="test", verbose_name_plural="tests")
    assert resource.name == "test"
    assert resource.verbose_name_plural == "tests"


@pytest.mark.asyncio
async def test_resource_create():
    """Test Resource create method."""
    resource = Resource(name="test", verbose_name_plural="tests")
    result = await resource.create({"name": "test"})
    assert result is None  # Base implementation returns None


@pytest.mark.asyncio
async def test_resource_update():
    """Test Resource update method."""
    resource = Resource(name="test", verbose_name_plural="tests")
    result = await resource.update("1", {"name": "updated"})
    assert result is None  # Base implementation returns None


@pytest.mark.asyncio
async def test_resource_delete():
    """Test Resource delete method."""
    resource = Resource(name="test", verbose_name_plural="tests")
    result = await resource.delete("1")
    assert result is None  # Base implementation returns None


@pytest.mark.asyncio
async def test_resource_list():
    """Test Resource list method."""
    resource = Resource(name="test", verbose_name_plural="tests")
    result = await resource.list()
    assert result is None  # Base implementation returns None


@pytest.mark.asyncio
async def test_resource_list_with_params():
    """Test Resource list method with parameters."""
    resource = Resource(name="test", verbose_name_plural="tests")
    result = await resource.list(
        limit=10, offset=0, filters={"name": "test"}, ordering=["id"]
    )
    assert result is None  # Base implementation returns None


@pytest.mark.asyncio
async def test_resource_retrieve():
    """Test Resource retrieve method."""
    resource = Resource(name="test", verbose_name_plural="tests")
    result = await resource.retrieve("1")
    assert result is None  # Base implementation returns None
