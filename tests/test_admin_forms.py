"""Tests for BaseAdmin form field integration."""

from datetime import date, datetime
from typing import Optional

import pytest
from pydantic import BaseModel, EmailStr

from fastapi_admin_sdk.admin import BaseAdmin
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
from fastapi_admin_sdk.resource import Resource


class MockResource(Resource):
    """Mock resource for testing."""

    def __init__(self):
        super().__init__(name="test", verbose_name_plural="tests")


class TestExplicitFormFieldTypes:
    """Tests for explicit form_field_types assignment."""

    def test_explicit_form_field_types(self):
        """Test setting form_field_types explicitly."""
        class CreateSchema(BaseModel):
            name: str
            email: str

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema
        admin.form_field_types = {
            "name": CharField(max_length=100),
            "email": EmailField(),
        }

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["name"], CharField)
        assert isinstance(field_types["email"], EmailField)
        assert field_types["name"].max_length == 100

    def test_explicit_form_field_types_override_auto_detection(self):
        """Test explicit form_field_types override auto-detection."""
        class CreateSchema(BaseModel):
            name: str  # Would auto-detect as CharField

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema
        admin.form_field_types = {
            "name": TextField(),  # Explicitly set as TextField
        }

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["name"], TextField)


class TestAutoDetection:
    """Tests for auto-detection of field types."""

    def test_auto_detect_str_as_char_field(self):
        """Test auto-detection of str as CharField."""
        class CreateSchema(BaseModel):
            name: str

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["name"], CharField)
        assert field_types["name"].required is True

    def test_auto_detect_str_as_text_field(self):
        """Test auto-detection of str as TextField for description/content/body fields."""
        class CreateSchema(BaseModel):
            description: str
            content: str
            body: str

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["description"], TextField)
        assert isinstance(field_types["content"], TextField)
        assert isinstance(field_types["body"], TextField)

    def test_auto_detect_email_str(self):
        """Test auto-detection of EmailStr as EmailField."""
        class CreateSchema(BaseModel):
            email: EmailStr

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["email"], EmailField)
        assert field_types["email"].required is True

    def test_auto_detect_int(self):
        """Test auto-detection of int as IntegerField."""
        class CreateSchema(BaseModel):
            age: int

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["age"], IntegerField)
        assert field_types["age"].required is True

    def test_auto_detect_float(self):
        """Test auto-detection of float as FloatField."""
        class CreateSchema(BaseModel):
            price: float

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["price"], FloatField)
        assert field_types["price"].required is True

    def test_auto_detect_bool(self):
        """Test auto-detection of bool as BooleanField."""
        class CreateSchema(BaseModel):
            is_active: bool

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["is_active"], BooleanField)
        assert field_types["is_active"].required is True

    def test_auto_detect_datetime(self):
        """Test auto-detection of datetime as DateTimeField."""
        class CreateSchema(BaseModel):
            created_at: datetime

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["created_at"], DateTimeField)
        assert field_types["created_at"].required is True

    def test_auto_detect_date(self):
        """Test auto-detection of date as DateField."""
        class CreateSchema(BaseModel):
            birth_date: date

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["birth_date"], DateField)
        assert field_types["birth_date"].required is True

    def test_auto_detect_optional_str(self):
        """Test auto-detection of Optional[str] as CharField with required=False."""
        class UpdateSchema(BaseModel):
            name: Optional[str] = None

        admin = BaseAdmin(MockResource())
        admin.update_form_schema = UpdateSchema

        field_types = admin.get_form_field_types(UpdateSchema)
        assert isinstance(field_types["name"], CharField)
        assert field_types["name"].required is False

    def test_auto_detect_optional_email(self):
        """Test auto-detection of Optional[EmailStr] as EmailField with required=False."""
        class UpdateSchema(BaseModel):
            email: Optional[EmailStr] = None

        admin = BaseAdmin(MockResource())
        admin.update_form_schema = UpdateSchema

        field_types = admin.get_form_field_types(UpdateSchema)
        assert isinstance(field_types["email"], EmailField)
        assert field_types["email"].required is False

    def test_auto_detect_optional_int(self):
        """Test auto-detection of Optional[int] as IntegerField with required=False."""
        class UpdateSchema(BaseModel):
            age: Optional[int] = None

        admin = BaseAdmin(MockResource())
        admin.update_form_schema = UpdateSchema

        field_types = admin.get_form_field_types(UpdateSchema)
        assert isinstance(field_types["age"], IntegerField)
        assert field_types["age"].required is False

    def test_auto_detect_mixed_schema(self):
        """Test auto-detection with mixed field types."""
        class CreateSchema(BaseModel):
            name: str
            email: EmailStr
            age: int
            price: float
            is_active: bool
            description: str
            created_at: datetime

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        assert isinstance(field_types["name"], CharField)
        assert isinstance(field_types["email"], EmailField)
        assert isinstance(field_types["age"], IntegerField)
        assert isinstance(field_types["price"], FloatField)
        assert isinstance(field_types["is_active"], BooleanField)
        assert isinstance(field_types["description"], TextField)
        assert isinstance(field_types["created_at"], DateTimeField)

    def test_auto_detect_unknown_type_defaults_to_char_field(self):
        """Test that unknown types default to CharField."""
        class CreateSchema(BaseModel):
            custom_field: list  # Not a standard type

        admin = BaseAdmin(MockResource())
        admin.create_form_schema = CreateSchema

        field_types = admin.get_form_field_types(CreateSchema)
        # Should default to CharField for unknown types
        assert isinstance(field_types["custom_field"], CharField)
