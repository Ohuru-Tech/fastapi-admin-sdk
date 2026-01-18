"""
Sample FastAPI application demonstrating fastapi-admin-sdk usage.

This example shows how to:
- Define SQLAlchemy models
- Create resources and admin classes
- Set up a FastAPI app with admin routes
- Use CRUD operations, filtering, pagination, and permissions
"""

import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from fastapi_admin_sdk import BaseAdmin, SQLAlchemyResource, register, router
from fastapi_admin_sdk.db import get_session_factory

# Set up database URL (defaults to SQLite for this example)
os.environ.setdefault("ADMIN_DB_URL", "sqlite+aiosqlite:///./sample.db")
os.environ.setdefault("ORM_TYPE", "sqlalchemy")


# SQLAlchemy Base
class Base(DeclarativeBase):
    pass


# User Model
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', email='{self.email}')>"


# Pydantic Schemas
class UserCreateSchema(BaseModel):
    name: str
    email: EmailStr


class UserUpdateSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


# Create Resource
session_factory = get_session_factory()
user_resource = SQLAlchemyResource(
    model=User,
    session_factory=session_factory,
    lookup_field="id",
)


# Create Admin Class
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
        # Example: Allow all users to create
        return True

    async def has_update_permission(self, request: Request):
        # Example: Allow all users to update
        return True

    async def has_delete_permission(self, request: Request):
        # Example: Allow all users to delete
        return True

    async def has_list_permission(self, request: Request):
        # Example: Allow all users to list
        return True

    async def has_retrieve_permission(self, request: Request):
        # Example: Allow all users to retrieve
        return True


# FastAPI App
app = FastAPI(
    title="FastAPI Admin SDK Sample App",
    description="A sample application demonstrating fastapi-admin-sdk",
    version="1.0.0",
)

# Include admin router
app.include_router(router, prefix="/admin", tags=["admin"])


@app.on_event("startup")
async def startup_event():
    """Create database tables on startup."""
    from fastapi_admin_sdk.db.sqlalchemy_factory import get_sqlalchemy_factory

    factory = get_sqlalchemy_factory()
    async with factory.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up database connections on shutdown."""
    from fastapi_admin_sdk.db.sqlalchemy_factory import get_sqlalchemy_factory

    factory = get_sqlalchemy_factory()
    await factory.close()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "FastAPI Admin SDK Sample App",
        "admin_endpoints": {
            "create": "POST /admin/users/create",
            "list": "GET /admin/users/list",
            "retrieve": "GET /admin/users/{id}/retrieve",
            "update": "PATCH /admin/users/{id}/update",
            "delete": "DELETE /admin/users/{id}/delete",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
