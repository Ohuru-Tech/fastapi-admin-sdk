"""
Integration tests for fastapi-admin-sdk.

These tests use a real database and test the full stack:
- Database models and tables
- Resources and admin classes
- HTTP endpoints
- CRUD operations, filtering, pagination, ordering
- Permissions and error handling
"""

import json
from datetime import datetime
from typing import Optional

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, EmailStr
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fastapi_admin_sdk import BaseAdmin, SQLAlchemyResource, register, router
from fastapi_admin_sdk.admin import AdminRegistry
from fastapi_admin_sdk.db import get_session_factory
from fastapi_admin_sdk.db.sqlalchemy_factory import get_sqlalchemy_factory


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# User Model (same as sample app)
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


# Pydantic Schemas
class UserCreateSchema(BaseModel):
    name: str
    email: EmailStr


class UserUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


@pytest.fixture
async def db_setup():
    """Set up database tables."""
    factory = get_sqlalchemy_factory()
    async with factory.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup - drop tables
    async with factory.engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def user_resource():
    """Create a user resource."""
    session_factory = get_session_factory()
    return SQLAlchemyResource(
        model=User,
        session_factory=session_factory,
        lookup_field="id",
    )


@pytest.fixture
def user_admin(user_resource):
    """Create and register a user admin."""
    # Clear registry first
    AdminRegistry._registry.clear()

    @register(user_resource)
    class UserAdmin(BaseAdmin):
        list_display = ["id", "name", "email", "created_at"]
        list_filter = ["name", "email"]
        search_fields = ["name", "email"]
        ordering = ["id"]

        create_form_schema = UserCreateSchema
        update_form_schema = UserUpdateSchema
        lookup_field = "id"

        async def has_create_permission(self, request: Request):
            return True

        async def has_update_permission(self, request: Request):
            return True

        async def has_delete_permission(self, request: Request):
            return True

        async def has_list_permission(self, request: Request):
            return True

        async def has_retrieve_permission(self, request: Request):
            return True

    return UserAdmin(user_resource)


@pytest.fixture
async def app(user_admin, db_setup):
    """Create a FastAPI app with admin routes."""
    app = FastAPI()
    app.include_router(router, prefix="/admin")
    yield app


@pytest.fixture
async def client(app):
    """Create a test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# Test CRUD Operations


@pytest.mark.asyncio
async def test_create_user_success(client):
    """Test creating a user successfully."""
    response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_user_invalid_data(client):
    """Test creating a user with invalid data."""
    # Missing required field
    response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe"},
    )
    assert response.status_code == 400

    # Invalid email format
    response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "invalid-email"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_create_user_duplicate_email(client):
    """Test creating a user with duplicate email."""
    # Create first user
    response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert response.status_code == 200

    # Try to create another user with same email
    response = await client.post(
        "/admin/users/create",
        json={"name": "Jane Doe", "email": "john@example.com"},
    )
    # Should fail due to unique constraint (database error will be raised)
    # FastAPI will convert it to 500, or it might be caught and converted to 400
    assert response.status_code in [
        400,
        500,
        422,
    ]  # Database constraint violation or validation error


@pytest.mark.asyncio
async def test_list_users_empty(client):
    """Test listing users when database is empty."""
    response = await client.get("/admin/users/list")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_users_with_data(client):
    """Test listing users with data."""
    # Create multiple users
    users_data = [
        {"name": "Alice", "email": "alice@example.com"},
        {"name": "Bob", "email": "bob@example.com"},
        {"name": "Charlie", "email": "charlie@example.com"},
    ]

    created_ids = []
    for user_data in users_data:
        response = await client.post("/admin/users/create", json=user_data)
        assert response.status_code == 200
        created_ids.append(response.json()["id"])

    # List all users
    response = await client.get("/admin/users/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert all("id" in item for item in data)
    assert all("name" in item for item in data)
    assert all("email" in item for item in data)


@pytest.mark.asyncio
async def test_list_users_with_pagination(client):
    """Test listing users with pagination."""
    # Create 5 users
    for i in range(5):
        await client.post(
            "/admin/users/create",
            json={"name": f"User {i}", "email": f"user{i}@example.com"},
        )

    # Test limit
    response = await client.get("/admin/users/list?limit=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    # Test offset
    response = await client.get("/admin/users/list?limit=2&offset=2")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_list_users_with_filters(client):
    """Test listing users with filters."""
    # Create users
    await client.post(
        "/admin/users/create",
        json={"name": "Alice", "email": "alice@example.com"},
    )
    await client.post(
        "/admin/users/create",
        json={"name": "Bob", "email": "bob@example.com"},
    )

    # Filter by name
    filters = json.dumps({"name": "Alice"})
    response = await client.get(f"/admin/users/list?filters={filters}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Alice"


@pytest.mark.asyncio
async def test_list_users_with_ordering(client):
    """Test listing users with ordering."""
    # Create users in specific order
    names = ["Charlie", "Alice", "Bob"]
    for name in names:
        await client.post(
            "/admin/users/create",
            json={"name": name, "email": f"{name.lower()}@example.com"},
        )

    # Order by name ascending
    response = await client.get("/admin/users/list?ordering=name")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Alice"
    assert data[1]["name"] == "Bob"
    assert data[2]["name"] == "Charlie"

    # Order by name descending
    response = await client.get("/admin/users/list?ordering=-name")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["name"] == "Charlie"
    assert data[1]["name"] == "Bob"
    assert data[2]["name"] == "Alice"


@pytest.mark.asyncio
async def test_list_users_invalid_filters(client):
    """Test listing users with invalid JSON filters."""
    response = await client.get("/admin/users/list?filters=invalid json")
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_retrieve_user_success(client):
    """Test retrieving a user successfully."""
    # Create a user
    create_response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Retrieve the user
    response = await client.get(f"/admin/users/{user_id}/retrieve")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == user_id
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_retrieve_user_not_found(client):
    """Test retrieving a non-existent user."""
    response = await client.get("/admin/users/999/retrieve")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_success(client):
    """Test updating a user successfully."""
    # Create a user
    create_response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Update the user
    response = await client.patch(
        f"/admin/users/{user_id}/update",
        json={"name": "Jane Doe"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Jane Doe"
    assert data["email"] == "john@example.com"  # Email unchanged

    # Update email
    response = await client.patch(
        f"/admin/users/{user_id}/update",
        json={"email": "jane@example.com"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "jane@example.com"


@pytest.mark.asyncio
async def test_update_user_not_found(client):
    """Test updating a non-existent user."""
    response = await client.patch(
        "/admin/users/999/update",
        json={"name": "Updated Name"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_user_invalid_data(client):
    """Test updating a user with invalid data."""
    # Create a user
    create_response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Try to update with invalid email
    response = await client.patch(
        f"/admin/users/{user_id}/update",
        json={"email": "invalid-email"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_user_success(client):
    """Test deleting a user successfully."""
    # Create a user
    create_response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Delete the user
    response = await client.delete(f"/admin/users/{user_id}/delete")
    assert response.status_code == 200
    assert response.json() is True

    # Verify user is deleted
    response = await client.get(f"/admin/users/{user_id}/retrieve")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(client):
    """Test deleting a non-existent user."""
    response = await client.delete("/admin/users/999/delete")
    assert response.status_code == 404


# Test Error Cases


@pytest.mark.asyncio
async def test_resource_not_found(client):
    """Test accessing a non-existent resource."""
    response = await client.get("/admin/nonexistent/list")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_permission_denied(client, user_admin):
    """Test permission denied scenario."""

    # Override permission to deny on the instance in the registry
    async def deny_permission(request: Request):
        return False

    # Get the admin instance from the registry and modify it
    admin_instance = AdminRegistry._registry["users"]["admin"]
    admin_instance.has_list_permission = deny_permission

    response = await client.get("/admin/users/list")
    assert response.status_code == 403
    assert "permission" in response.json()["detail"].lower()


# Test Edge Cases


@pytest.mark.asyncio
async def test_list_with_zero_limit(client):
    """Test listing with zero limit."""
    # Create a user
    await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )

    # List with limit=0 (should return empty or all, depending on implementation)
    response = await client.get("/admin/users/list?limit=0")
    # Should handle gracefully (either empty list or validation error)
    assert response.status_code in [200, 400, 422]  # 422 is validation error


@pytest.mark.asyncio
async def test_list_with_negative_offset(client):
    """Test listing with negative offset."""
    response = await client.get("/admin/users/list?offset=-1")
    # Should validate and return validation error or handle gracefully
    assert response.status_code in [200, 400, 422]  # 422 is validation error


@pytest.mark.asyncio
async def test_update_with_empty_data(client):
    """Test updating with empty data."""
    # Create a user
    create_response = await client.post(
        "/admin/users/create",
        json={"name": "John Doe", "email": "john@example.com"},
    )
    assert create_response.status_code == 200
    user_id = create_response.json()["id"]

    # Update with empty dict (should be valid - no changes)
    response = await client.patch(
        f"/admin/users/{user_id}/update",
        json={},
    )
    # Should succeed (no-op update)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_manifest_integration(client):
    """Test GET /admin/manifest endpoint with real database and models."""
    response = await client.get("/admin/manifest")
    assert response.status_code == 200

    data = response.json()
    assert "resources" in data
    assert isinstance(data["resources"], list)

    # Should include the users resource
    resource_names = [r["name"] for r in data["resources"]]
    assert "users" in resource_names

    # Find the users resource
    users_resource = next(r for r in data["resources"] if r["name"] == "users")
    assert users_resource["verbose_name"] == "users"
    assert "actions" in users_resource
    assert "list" in users_resource["actions"]
    assert "create" in users_resource["actions"]
    assert "update" in users_resource["actions"]
    assert "delete" in users_resource["actions"]
    assert "retrieve" in users_resource["actions"]

    # Check list_config
    assert "list_config" in users_resource
    list_config = users_resource["list_config"]
    assert "display_fields" in list_config
    assert "filter_fields" in list_config
    assert "search_fields" in list_config
    assert "ordering" in list_config

    # Check schemas
    assert "create_schema" in users_resource
    assert "update_schema" in users_resource

    create_schema = users_resource["create_schema"]
    assert "properties" in create_schema
    assert "name" in create_schema["properties"]
    assert "email" in create_schema["properties"]

    # Check that form field metadata is present
    name_field = create_schema["properties"]["name"]
    assert "x-field-type" in name_field or "type" in name_field

    email_field = create_schema["properties"]["email"]
    assert "x-field-type" in email_field or "type" in email_field


@pytest.mark.asyncio
async def test_get_manifest_respects_permissions(client, user_admin):
    """Test GET /admin/manifest respects permission checks."""

    # Deny some permissions
    async def deny_create_delete(request: Request):
        return False

    admin_instance = AdminRegistry._registry["users"]["admin"]
    admin_instance.has_create_permission = deny_create_delete
    admin_instance.has_delete_permission = deny_create_delete

    # Get manifest again
    response = await client.get("/admin/manifest")
    assert response.status_code == 200
    data = response.json()
    users_resource = next(r for r in data["resources"] if r["name"] == "users")
    new_actions = set(users_resource["actions"])

    # Should have fewer actions
    assert "create" not in new_actions
    assert "delete" not in new_actions
    assert "list" in new_actions
    assert "update" in new_actions
    assert "retrieve" in new_actions
