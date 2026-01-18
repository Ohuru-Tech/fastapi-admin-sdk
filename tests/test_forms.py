"""Tests for form field types."""

import pytest

from fastapi_admin_sdk.forms import (
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


class TestBaseFormField:
    """Tests for BaseFormField base class."""

    def test_base_formfield_initialization(self):
        """Test BaseFormField initialization with all parameters."""
        from fastapi_admin_sdk.forms.base import BaseFormField

        # Create a concrete subclass for testing
        class TestField(BaseFormField):
            def to_json_schema(self, field_name: str):
                return self._base_json_schema(field_name, "string")

        field = TestField(
            field_type="test",
            required=True,
            label="Test Field",
            help_text="This is a test field",
            default="default_value",
            extra_option="extra",
        )
        assert field.field_type == "test"
        assert field.required is True
        assert field.label == "Test Field"
        assert field.help_text == "This is a test field"
        assert field.default == "default_value"
        assert field.extra_options["extra_option"] == "extra"

    def test_base_formfield_optional(self):
        """Test BaseFormField initialization as optional."""
        from fastapi_admin_sdk.forms.base import BaseFormField

        # Create a concrete subclass for testing
        class TestField(BaseFormField):
            def to_json_schema(self, field_name: str):
                return self._base_json_schema(field_name, "string")

        field = TestField(field_type="test", required=False)
        assert field.required is False


class TestTextField:
    """Tests for TextField."""

    def test_text_field_initialization(self):
        """Test TextField initialization."""
        field = TextField(min_length=10, max_length=100, pattern="^[A-Z]")
        assert field.min_length == 10
        assert field.max_length == 100
        assert field.pattern == "^[A-Z]"

    def test_text_field_to_json_schema(self):
        """Test TextField JSON Schema conversion."""
        field = TextField(min_length=10, max_length=100, required=True)
        schema = field.to_json_schema("description")
        assert schema["type"] == "string"
        assert schema["x-field-type"] == "text"
        assert schema["x-input-type"] == "textarea"
        assert schema["minLength"] == 10
        assert schema["maxLength"] == 100
        assert schema["x-validation"]["required"] is True

    def test_text_field_optional(self):
        """Test TextField as optional."""
        field = TextField(required=False)
        schema = field.to_json_schema("description")
        assert schema["x-validation"]["required"] is False

    def test_text_field_with_label_and_help(self):
        """Test TextField with label and help text."""
        field = TextField(label="Description", help_text="Enter a description")
        schema = field.to_json_schema("description")
        assert schema["title"] == "Description"
        assert schema["description"] == "Enter a description"


class TestCharField:
    """Tests for CharField."""

    def test_char_field_initialization(self):
        """Test CharField initialization."""
        field = CharField(max_length=255, min_length=5)
        assert field.max_length == 255
        assert field.min_length == 5

    def test_char_field_to_json_schema(self):
        """Test CharField JSON Schema conversion."""
        field = CharField(max_length=255, required=True)
        schema = field.to_json_schema("name")
        assert schema["type"] == "string"
        assert schema["x-field-type"] == "char"
        assert schema["x-input-type"] == "text"
        assert schema["maxLength"] == 255
        assert schema["x-validation"]["required"] is True

    def test_char_field_with_pattern(self):
        """Test CharField with pattern validation."""
        field = CharField(pattern="^[A-Za-z]+$")
        schema = field.to_json_schema("name")
        assert schema["pattern"] == "^[A-Za-z]+$"
        assert "pattern" in schema["x-validation"]


class TestEmailField:
    """Tests for EmailField."""

    def test_email_field_initialization(self):
        """Test EmailField initialization."""
        field = EmailField(max_length=255)
        assert field.max_length == 255

    def test_email_field_to_json_schema(self):
        """Test EmailField JSON Schema conversion."""
        field = EmailField(required=True)
        schema = field.to_json_schema("email")
        assert schema["type"] == "string"
        assert schema["format"] == "email"
        assert schema["x-field-type"] == "email"
        assert schema["x-input-type"] == "email"
        assert schema["x-validation"]["required"] is True

    def test_email_field_with_max_length(self):
        """Test EmailField with max_length."""
        field = EmailField(max_length=100)
        schema = field.to_json_schema("email")
        assert schema["maxLength"] == 100
        assert schema["x-validation"]["maxLength"] == 100


class TestURLField:
    """Tests for URLField."""

    def test_url_field_to_json_schema(self):
        """Test URLField JSON Schema conversion."""
        field = URLField(required=True)
        schema = field.to_json_schema("url")
        assert schema["type"] == "string"
        assert schema["format"] == "uri"
        assert schema["x-field-type"] == "url"
        assert schema["x-input-type"] == "url"
        assert schema["x-validation"]["required"] is True


class TestIntegerField:
    """Tests for IntegerField."""

    def test_integer_field_initialization(self):
        """Test IntegerField initialization."""
        field = IntegerField(min_value=0, max_value=100)
        assert field.min_value == 0
        assert field.max_value == 100

    def test_integer_field_to_json_schema(self):
        """Test IntegerField JSON Schema conversion."""
        field = IntegerField(min_value=0, max_value=100, required=True)
        schema = field.to_json_schema("age")
        assert schema["type"] == "integer"
        assert schema["x-field-type"] == "integer"
        assert schema["x-input-type"] == "number"
        assert schema["minimum"] == 0
        assert schema["maximum"] == 100
        assert schema["x-validation"]["minValue"] == 0
        assert schema["x-validation"]["maxValue"] == 100


class TestFloatField:
    """Tests for FloatField."""

    def test_float_field_to_json_schema(self):
        """Test FloatField JSON Schema conversion."""
        field = FloatField(min_value=0.0, max_value=100.0, required=True)
        schema = field.to_json_schema("price")
        assert schema["type"] == "number"
        assert schema["x-field-type"] == "float"
        assert schema["x-input-type"] == "number"
        assert schema["minimum"] == 0.0
        assert schema["maximum"] == 100.0


class TestBooleanField:
    """Tests for BooleanField."""

    def test_boolean_field_to_json_schema(self):
        """Test BooleanField JSON Schema conversion."""
        field = BooleanField(required=True)
        schema = field.to_json_schema("is_active")
        assert schema["type"] == "boolean"
        assert schema["x-field-type"] == "boolean"
        assert schema["x-input-type"] == "checkbox"
        assert schema["x-validation"]["required"] is True

    def test_boolean_field_with_default(self):
        """Test BooleanField with default value."""
        field = BooleanField(default=False)
        schema = field.to_json_schema("is_active")
        assert schema["default"] is False


class TestDateField:
    """Tests for DateField."""

    def test_date_field_to_json_schema(self):
        """Test DateField JSON Schema conversion."""
        field = DateField(required=True)
        schema = field.to_json_schema("birth_date")
        assert schema["type"] == "string"
        assert schema["format"] == "date"
        assert schema["x-field-type"] == "date"
        assert schema["x-input-type"] == "date"


class TestDateTimeField:
    """Tests for DateTimeField."""

    def test_datetime_field_to_json_schema(self):
        """Test DateTimeField JSON Schema conversion."""
        field = DateTimeField(required=True)
        schema = field.to_json_schema("created_at")
        assert schema["type"] == "string"
        assert schema["format"] == "date-time"
        assert schema["x-field-type"] == "datetime"
        assert schema["x-input-type"] == "datetime-local"


class TestImageField:
    """Tests for ImageField."""

    def test_image_field_initialization(self):
        """Test ImageField initialization."""
        field = ImageField(max_size_mb=5.0, allowed_formats=["jpg", "png"])
        assert field.max_size_mb == 5.0
        assert field.allowed_formats == ["jpg", "png"]

    def test_image_field_to_json_schema(self):
        """Test ImageField JSON Schema conversion."""
        field = ImageField(max_size_mb=5.0, allowed_formats=["jpg", "png"], required=True)
        schema = field.to_json_schema("avatar")
        assert schema["type"] == "string"
        assert schema["format"] == "binary"
        assert schema["x-field-type"] == "image"
        assert schema["x-input-type"] == "file"
        assert schema["x-file-type"] == "image"
        assert schema["x-validation"]["maxSizeMB"] == 5.0
        assert schema["x-validation"]["allowedFormats"] == ["jpg", "png"]

    def test_image_field_default_formats(self):
        """Test ImageField with default allowed formats."""
        field = ImageField()
        assert "jpg" in field.allowed_formats
        assert "png" in field.allowed_formats


class TestFileField:
    """Tests for FileField."""

    def test_file_field_to_json_schema(self):
        """Test FileField JSON Schema conversion."""
        field = FileField(max_size_mb=10.0, allowed_formats=["pdf", "doc"], required=True)
        schema = field.to_json_schema("document")
        assert schema["type"] == "string"
        assert schema["format"] == "binary"
        assert schema["x-field-type"] == "file"
        assert schema["x-input-type"] == "file"
        assert schema["x-file-type"] == "file"
        assert schema["x-validation"]["maxSizeMB"] == 10.0
        assert schema["x-validation"]["allowedFormats"] == ["pdf", "doc"]


class TestSelectField:
    """Tests for SelectField."""

    def test_select_field_initialization(self):
        """Test SelectField initialization."""
        choices = [("option1", "Option 1"), ("option2", "Option 2")]
        field = SelectField(choices=choices)
        assert field.choices == choices

    def test_select_field_to_json_schema(self):
        """Test SelectField JSON Schema conversion."""
        choices = [("option1", "Option 1"), ("option2", "Option 2")]
        field = SelectField(choices=choices, required=True)
        schema = field.to_json_schema("status")
        assert schema["type"] == "string"
        assert schema["x-field-type"] == "select"
        assert schema["x-input-type"] == "select"
        assert schema["enum"] == ["option1", "option2"]
        assert schema["x-choices"] == {"option1": "Option 1", "option2": "Option 2"}
