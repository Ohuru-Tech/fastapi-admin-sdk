import json
from typing import Dict, Optional

from fastapi import HTTPException, Request
from pydantic import ValidationError

from fastapi_admin_sdk.admin import AdminRegistry
from fastapi_admin_sdk.db.session_factory import SessionFactory


class AdminService:
    """Service layer for admin operations."""

    def __init__(self, session_factory: SessionFactory):
        self.session_factory = session_factory

    async def create_resource(self, resource_name: str, data: dict, request: Request):
        """Create a new resource instance."""
        if resource_name not in AdminRegistry._registry:
            raise HTTPException(
                status_code=404, detail=f"Resource '{resource_name}' not found"
            )

        admin_config = AdminRegistry._registry[resource_name]
        admin_model = admin_config["admin"]
        resource = admin_config["resource"]

        # Check permissions
        if not await admin_model.has_create_permission(request):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to create this resource",
            )

        # Validate data
        create_schema = admin_model.create_form_schema
        try:
            create_schema(**data)
        except ValidationError as error:
            raise HTTPException(status_code=400, detail=error.errors())

        # Create instance
        instance = await resource.create(data)
        return instance

    async def update_resource(
        self, resource_name: str, lookup: str, data: dict, request: Request
    ):
        """Update an existing resource instance."""
        if resource_name not in AdminRegistry._registry:
            raise HTTPException(
                status_code=404, detail=f"Resource '{resource_name}' not found"
            )

        admin_config = AdminRegistry._registry[resource_name]
        admin_model = admin_config["admin"]
        resource = admin_config["resource"]

        # Check permissions
        if not await admin_model.has_update_permission(request):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to update this resource",
            )

        # Validate data
        update_schema = admin_model.update_form_schema
        try:
            update_schema(**data)
        except ValidationError as error:
            raise HTTPException(status_code=400, detail=error.errors())

        # Update instance
        instance = await resource.update(lookup, data)
        return instance

    async def list_resource(
        self,
        resource_name: str,
        request: Request,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[str] = None,
        ordering: Optional[str] = None,
    ):
        """List resource instances with filtering and pagination."""
        if resource_name not in AdminRegistry._registry:
            raise HTTPException(
                status_code=404, detail=f"Resource '{resource_name}' not found"
            )

        admin_config = AdminRegistry._registry[resource_name]
        admin_model = admin_config["admin"]
        resource = admin_config["resource"]

        # Check permissions
        if not await admin_model.has_list_permission(request):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to list this resource",
            )

        # Parse filters from JSON string if provided
        filters_dict = None
        if filters:
            try:
                filters_dict = json.loads(filters)
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON format for filters"
                )

        # Parse ordering from comma-separated string if provided
        ordering_list = None
        if ordering:
            ordering_list = [
                field.strip() for field in ordering.split(",") if field.strip()
            ]

        # List instances
        instances = await resource.list(limit, offset, filters_dict, ordering_list)
        return instances

    async def retrieve_resource(
        self, resource_name: str, lookup: str, request: Request
    ):
        """Retrieve a specific resource instance."""
        if resource_name not in AdminRegistry._registry:
            raise HTTPException(
                status_code=404, detail=f"Resource '{resource_name}' not found"
            )

        admin_config = AdminRegistry._registry[resource_name]
        admin_model = admin_config["admin"]
        resource = admin_config["resource"]

        # Check permissions
        if not await admin_model.has_retrieve_permission(request):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to retrieve this resource",
            )

        # Retrieve instance
        instance = await resource.retrieve(lookup)
        return instance

    async def delete_resource(self, resource_name: str, lookup: str, request: Request):
        """Delete a resource instance."""
        if resource_name not in AdminRegistry._registry:
            raise HTTPException(
                status_code=404, detail=f"Resource '{resource_name}' not found"
            )

        admin_config = AdminRegistry._registry[resource_name]
        admin_model = admin_config["admin"]
        resource = admin_config["resource"]

        # Check permissions
        if not await admin_model.has_delete_permission(request):
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to delete this resource",
            )

        # Delete instance
        result = await resource.delete(lookup)
        return result

    async def get_manifest(self, request: Request) -> Dict:
        """
        Get admin manifest with resources filtered by user permissions.

        Args:
            request: FastAPI Request object for permission checks

        Returns:
            Dictionary containing manifest with resources and their configurations
        """
        resources = []

        for resource_name, admin_config in AdminRegistry._registry.items():
            admin_model = admin_config["admin"]
            resource = admin_config["resource"]

            # Check permissions for each action
            actions = []
            if await admin_model.has_list_permission(request):
                actions.append("list")
            if await admin_model.has_create_permission(request):
                actions.append("create")
            if await admin_model.has_update_permission(request):
                actions.append("update")
            if await admin_model.has_delete_permission(request):
                actions.append("delete")
            if await admin_model.has_retrieve_permission(request):
                actions.append("retrieve")

            # Skip resources with no permissions
            if not actions:
                continue

            # Get form field types for create and update schemas
            create_field_types = admin_model.get_form_field_types(
                admin_model.create_form_schema
            )
            update_field_types = admin_model.get_form_field_types(
                admin_model.update_form_schema
            )

            # Convert Pydantic schemas to JSON Schema
            create_schema_json = admin_model.create_form_schema.model_json_schema()
            update_schema_json = admin_model.update_form_schema.model_json_schema()

            # Enhance JSON Schema with form field types
            create_schema_json = self._enhance_schema_with_field_types(
                create_schema_json, create_field_types
            )
            update_schema_json = self._enhance_schema_with_field_types(
                update_schema_json, update_field_types
            )

            resource_manifest = {
                "name": resource_name,
                "verbose_name": resource.verbose_name_plural,
                "actions": actions,
                "list_config": {
                    "display_fields": admin_model.list_display,
                    "filter_fields": admin_model.list_filter,
                    "search_fields": admin_model.search_fields,
                    "ordering": admin_model.ordering,
                },
                "create_schema": create_schema_json,
                "update_schema": update_schema_json,
            }

            resources.append(resource_manifest)

        return {"resources": resources}

    def _enhance_schema_with_field_types(
        self, schema_json: Dict, field_types: Dict[str, any]
    ) -> Dict:
        """
        Enhance JSON Schema with form field type metadata.

        Args:
            schema_json: JSON Schema from Pydantic model
            field_types: Dictionary mapping field names to FormField instances

        Returns:
            Enhanced JSON Schema dictionary
        """
        if "properties" not in schema_json:
            return schema_json

        enhanced_schema = schema_json.copy()
        enhanced_properties = {}

        for field_name, field_schema in schema_json.get("properties", {}).items():
            enhanced_field_schema = field_schema.copy()

            # If we have a form field type for this field, merge its JSON Schema
            if field_name in field_types:
                form_field_json = field_types[field_name].to_json_schema(field_name)
                # Merge form field JSON Schema into the field schema
                enhanced_field_schema.update(form_field_json)

            enhanced_properties[field_name] = enhanced_field_schema

        enhanced_schema["properties"] = enhanced_properties

        # Update required fields based on form field types
        # If we have form field types, use them to determine required fields
        # Otherwise, preserve the original required fields from the schema
        if field_types:
            required_fields = []
            for field_name, field_type in field_types.items():
                if field_type.required and field_name in enhanced_properties:
                    required_fields.append(field_name)
            enhanced_schema["required"] = required_fields
        # If no field_types provided, keep original required fields (already in schema_json)

        return enhanced_schema
