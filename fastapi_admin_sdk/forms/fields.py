"""Concrete form field type implementations."""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi_admin_sdk.forms.base import BaseFormField


class TextField(BaseFormField):
    """Multi-line text input field."""

    def __init__(
        self,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        pattern: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a text field.

        Args:
            min_length: Minimum length of the text
            max_length: Maximum length of the text
            pattern: Regex pattern for validation
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="text", **kwargs)
        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["x-input-type"] = "textarea"

        validation = schema.get("x-validation", {})
        if self.min_length is not None:
            schema["minLength"] = self.min_length
            validation["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
            validation["maxLength"] = self.max_length
        if self.pattern:
            schema["pattern"] = self.pattern
            validation["pattern"] = self.pattern

        schema["x-validation"] = validation
        return schema


class CharField(BaseFormField):
    """Single-line text input field."""

    def __init__(
        self,
        max_length: Optional[int] = None,
        min_length: Optional[int] = None,
        pattern: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize a character field.

        Args:
            max_length: Maximum length of the text
            min_length: Minimum length of the text
            pattern: Regex pattern for validation
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="char", **kwargs)
        self.max_length = max_length
        self.min_length = min_length
        self.pattern = pattern

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["x-input-type"] = "text"

        validation = schema.get("x-validation", {})
        if self.min_length is not None:
            schema["minLength"] = self.min_length
            validation["minLength"] = self.min_length
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
            validation["maxLength"] = self.max_length
        if self.pattern:
            schema["pattern"] = self.pattern
            validation["pattern"] = self.pattern

        schema["x-validation"] = validation
        return schema


class EmailField(BaseFormField):
    """Email input field with email validation."""

    def __init__(self, max_length: Optional[int] = 255, **kwargs):
        """
        Initialize an email field.

        Args:
            max_length: Maximum length of the email
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="email", **kwargs)
        self.max_length = max_length

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["format"] = "email"
        schema["x-input-type"] = "email"

        validation = schema.get("x-validation", {})
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
            validation["maxLength"] = self.max_length

        schema["x-validation"] = validation
        return schema


class URLField(BaseFormField):
    """URL input field with URL validation."""

    def __init__(self, max_length: Optional[int] = None, **kwargs):
        """
        Initialize a URL field.

        Args:
            max_length: Maximum length of the URL
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="url", **kwargs)
        self.max_length = max_length

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["format"] = "uri"
        schema["x-input-type"] = "url"

        validation = schema.get("x-validation", {})
        if self.max_length is not None:
            schema["maxLength"] = self.max_length
            validation["maxLength"] = self.max_length

        schema["x-validation"] = validation
        return schema


class IntegerField(BaseFormField):
    """Integer input field."""

    def __init__(
        self,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
        **kwargs,
    ):
        """
        Initialize an integer field.

        Args:
            min_value: Minimum value allowed
            max_value: Maximum value allowed
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="integer", **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "integer")
        schema["x-input-type"] = "number"

        validation = schema.get("x-validation", {})
        if self.min_value is not None:
            schema["minimum"] = self.min_value
            validation["minValue"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
            validation["maxValue"] = self.max_value

        schema["x-validation"] = validation
        return schema


class FloatField(BaseFormField):
    """Float input field."""

    def __init__(
        self,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        **kwargs,
    ):
        """
        Initialize a float field.

        Args:
            min_value: Minimum value allowed
            max_value: Maximum value allowed
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="float", **kwargs)
        self.min_value = min_value
        self.max_value = max_value

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "number")
        schema["x-input-type"] = "number"

        validation = schema.get("x-validation", {})
        if self.min_value is not None:
            schema["minimum"] = self.min_value
            validation["minValue"] = self.min_value
        if self.max_value is not None:
            schema["maximum"] = self.max_value
            validation["maxValue"] = self.max_value

        schema["x-validation"] = validation
        return schema


class BooleanField(BaseFormField):
    """Boolean checkbox field."""

    def __init__(self, **kwargs):
        """
        Initialize a boolean field.

        Args:
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="boolean", **kwargs)

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "boolean")
        schema["x-input-type"] = "checkbox"
        return schema


class DateField(BaseFormField):
    """Date input field."""

    def __init__(self, format: str = "date", **kwargs):
        """
        Initialize a date field.

        Args:
            format: Date format (default: "date")
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="date", **kwargs)
        self.format = format

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["format"] = "date"
        schema["x-input-type"] = "date"
        return schema


class DateTimeField(BaseFormField):
    """Date-time input field."""

    def __init__(self, format: str = "date-time", **kwargs):
        """
        Initialize a datetime field.

        Args:
            format: DateTime format (default: "date-time")
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="datetime", **kwargs)
        self.format = format

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["format"] = "date-time"
        schema["x-input-type"] = "datetime-local"
        return schema


class ImageField(BaseFormField):
    """Image upload field."""

    def __init__(
        self,
        max_size_mb: Optional[float] = None,
        allowed_formats: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Initialize an image field.

        Args:
            max_size_mb: Maximum file size in MB
            allowed_formats: List of allowed image formats (e.g., ["jpg", "png", "gif"])
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="image", **kwargs)
        self.max_size_mb = max_size_mb
        self.allowed_formats = allowed_formats or ["jpg", "jpeg", "png", "gif", "webp"]

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["format"] = "binary"
        schema["x-input-type"] = "file"
        schema["x-file-type"] = "image"

        validation = schema.get("x-validation", {})
        if self.max_size_mb is not None:
            validation["maxSizeMB"] = self.max_size_mb
        if self.allowed_formats:
            validation["allowedFormats"] = self.allowed_formats

        schema["x-validation"] = validation
        return schema


class FileField(BaseFormField):
    """File upload field."""

    def __init__(
        self,
        max_size_mb: Optional[float] = None,
        allowed_formats: Optional[List[str]] = None,
        **kwargs,
    ):
        """
        Initialize a file field.

        Args:
            max_size_mb: Maximum file size in MB
            allowed_formats: List of allowed file extensions (e.g., ["pdf", "doc", "docx"])
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="file", **kwargs)
        self.max_size_mb = max_size_mb
        self.allowed_formats = allowed_formats

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["format"] = "binary"
        schema["x-input-type"] = "file"
        schema["x-file-type"] = "file"

        validation = schema.get("x-validation", {})
        if self.max_size_mb is not None:
            validation["maxSizeMB"] = self.max_size_mb
        if self.allowed_formats:
            validation["allowedFormats"] = self.allowed_formats

        schema["x-validation"] = validation
        return schema


class SelectField(BaseFormField):
    """Dropdown select field with choices."""

    def __init__(self, choices: List[tuple], **kwargs):
        """
        Initialize a select field.

        Args:
            choices: List of tuples (value, label) for options
            **kwargs: Additional options passed to BaseFormField
        """
        super().__init__(field_type="select", **kwargs)
        self.choices = choices

    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """Convert to JSON Schema format."""
        schema = self._base_json_schema(field_name, "string")
        schema["x-input-type"] = "select"

        # Add enum values
        enum_values = [choice[0] for choice in self.choices]
        schema["enum"] = enum_values

        # Add choice labels for frontend
        choices_dict = {str(choice[0]): choice[1] for choice in self.choices}
        schema["x-choices"] = choices_dict

        return schema
