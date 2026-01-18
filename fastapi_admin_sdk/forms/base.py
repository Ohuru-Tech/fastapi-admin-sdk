"""Base form field class for form field types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseFormField(ABC):
    """Base class for all form field types."""

    def __init__(
        self,
        field_type: str,
        required: bool = True,
        label: Optional[str] = None,
        help_text: Optional[str] = None,
        default: Any = None,
        **kwargs,
    ):
        """
        Initialize a form field.

        Args:
            field_type: Type identifier for the field (e.g., "text", "date")
            required: Whether the field is required
            label: Human-readable label for the field
            help_text: Help text to display with the field
            default: Default value for the field
            **kwargs: Additional field-specific options
        """
        self.field_type = field_type
        self.required = required
        self.label = label
        self.help_text = help_text
        self.default = default
        self.extra_options = kwargs

    @abstractmethod
    def to_json_schema(self, field_name: str) -> Dict[str, Any]:
        """
        Convert the field to JSON Schema format.

        Args:
            field_name: Name of the field in the schema

        Returns:
            Dictionary representing the field in JSON Schema format
        """
        pass

    def _base_json_schema(self, field_name: str, json_type: str) -> Dict[str, Any]:
        """
        Create base JSON Schema structure.

        Args:
            field_name: Name of the field
            json_type: JSON Schema type (string, integer, number, boolean, etc.)

        Returns:
            Base JSON Schema dictionary
        """
        schema = {
            "type": json_type,
            "x-field-type": self.field_type,
        }

        if self.label:
            schema["title"] = self.label
        elif field_name:
            # Generate title from field name (convert snake_case to Title Case)
            schema["title"] = field_name.replace("_", " ").title()

        if self.help_text:
            schema["description"] = self.help_text

        if self.default is not None:
            schema["default"] = self.default

        # Add validation metadata
        validation = {}
        if not self.required:
            validation["required"] = False
        else:
            validation["required"] = True

        # Add any extra options as x- prefixed extensions
        for key, value in self.extra_options.items():
            if not key.startswith("x-"):
                schema[f"x-{key}"] = value
            else:
                schema[key] = value

        if validation:
            schema["x-validation"] = validation

        return schema
