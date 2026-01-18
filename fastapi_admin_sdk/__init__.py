"""FastAPI Admin SDK - A FastAPI admin SDK for building admin interfaces."""

from fastapi_admin_sdk.admin import AdminRegistry, BaseAdmin, register
from fastapi_admin_sdk.config import Settings, settings
from fastapi_admin_sdk.db import SessionFactory, get_session_factory
from fastapi_admin_sdk.forms import (
    BaseFormField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    FileField,
    FloatField,
    ImageField,
    IntegerField,
    SelectField,
    TextField,
    URLField,
)
from fastapi_admin_sdk.resource import Resource, SQLAlchemyResource
from fastapi_admin_sdk.routes import router
from fastapi_admin_sdk.services import AdminService

__version__ = "0.1.0"

__all__ = [
    "BaseAdmin",
    "AdminRegistry",
    "register",
    "Resource",
    "SQLAlchemyResource",
    "router",
    "AdminService",
    "Settings",
    "settings",
    "get_session_factory",
    "SessionFactory",
    "BaseFormField",
    "TextField",
    "CharField",
    "DateField",
    "DateTimeField",
    "ImageField",
    "FileField",
    "EmailField",
    "IntegerField",
    "FloatField",
    "BooleanField",
    "SelectField",
    "URLField",
]
