from typing import Dict, List, Optional, Type, get_args, get_origin

from fastapi import Request
from pydantic import BaseModel, EmailStr
from typing_extensions import Dict as TypingDict

from fastapi_admin_sdk.forms import (
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    EmailField,
    FloatField,
    IntegerField,
    TextField,
)
from fastapi_admin_sdk.forms.base import BaseFormField
from fastapi_admin_sdk.resource import Resource


class BaseAdmin:
    list_display: List[str] = []
    list_filter: List[str] = []
    search_fields: List[str] = []
    ordering: List[str] = []

    create_form_schema: BaseModel
    update_form_schema: BaseModel
    lookup_field: str = "id"
    form_field_types: Optional[Dict[str, BaseFormField]] = None

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

    def __init__(self, resource: Resource):
        self.resource = resource

    def _detect_field_type(self, field_name: str, field_info) -> BaseFormField:
        """
        Auto-detect form field type from Pydantic field.

        Args:
            field_name: Name of the field
            field_info: Pydantic FieldInfo object

        Returns:
            BaseFormField instance
        """
        annotation = field_info.annotation
        is_optional = False

        # Check if Optional or Union with None
        origin = get_origin(annotation)
        if origin is not None:
            args = get_args(annotation)
            if type(None) in args:
                is_optional = True
                # Get the non-None type
                annotation = next(
                    (arg for arg in args if arg is not type(None)), annotation
                )

        # Handle EmailStr
        try:
            if annotation is EmailStr or (
                hasattr(EmailStr, "__name__")
                and getattr(annotation, "__name__", None) == "EmailStr"
            ):
                return EmailField(required=not is_optional)
        except (TypeError, AttributeError):
            pass

        # Check if it's EmailStr by string representation (for cases where it's wrapped)
        if str(annotation).startswith("EmailStr") or "EmailStr" in str(annotation):
            return EmailField(required=not is_optional)

        # Handle basic types
        if annotation is str:
            # Check field name hints for text vs char
            if (
                "description" in field_name.lower()
                or "content" in field_name.lower()
                or "body" in field_name.lower()
            ):
                return TextField(required=not is_optional)
            return CharField(required=not is_optional)

        if annotation is int:
            return IntegerField(required=not is_optional)

        if annotation is float:
            return FloatField(required=not is_optional)

        if annotation is bool:
            return BooleanField(required=not is_optional)

        # Handle datetime types
        if hasattr(annotation, "__name__"):
            if annotation.__name__ == "date":
                return DateField(required=not is_optional)
            if annotation.__name__ == "datetime":
                return DateTimeField(required=not is_optional)

        # Default to CharField for unknown types
        return CharField(required=not is_optional)

    def get_form_field_types(self, schema: Type[BaseModel]) -> Dict[str, BaseFormField]:
        """
        Get form field types for a schema, using explicit types or auto-detection.

        Args:
            schema: Pydantic model class

        Returns:
            Dictionary mapping field names to FormField instances
        """
        if self.form_field_types is not None:
            return self.form_field_types

        # Auto-detect from schema
        field_types = {}
        if hasattr(schema, "model_fields"):
            for field_name, field_info in schema.model_fields.items():
                field_types[field_name] = self._detect_field_type(
                    field_name, field_info
                )

        return field_types


class AdminRegistry:
    _registry: TypingDict[str, TypingDict[str, BaseAdmin | Resource]] = {}


def register(resource: Resource):
    def decorator(admin_class: type[BaseAdmin]):
        # Instantiate the admin class with the resource
        admin_instance = admin_class(resource)
        AdminRegistry._registry[resource.name] = {
            "admin": admin_instance,
            "resource": resource,
        }
        return admin_class

    return decorator
