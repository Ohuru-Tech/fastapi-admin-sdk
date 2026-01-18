from typing import Optional

from fastapi import APIRouter, Depends, Query, Request

from fastapi_admin_sdk.dependencies import get_admin_service
from fastapi_admin_sdk.services.admin_service import AdminService

router = APIRouter(tags=["admin"])


@router.get("/manifest")
async def get_manifest(
    request: Request,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Get admin manifest with resources filtered by user permissions."""
    return await admin_service.get_manifest(request)


@router.post("/{resource_name}/create")
async def create_resource(
    resource_name: str,
    data: dict,
    request: Request,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Create a new resource instance."""
    return await admin_service.create_resource(resource_name, data, request)


@router.patch("/{resource_name}/{lookup}/update")
async def update_resource(
    resource_name: str,
    lookup: str,
    data: dict,
    request: Request,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Update an existing resource instance."""
    return await admin_service.update_resource(resource_name, lookup, data, request)


@router.get("/{resource_name}/list")
async def list_resource(
    resource_name: str,
    request: Request,
    limit: Optional[int] = Query(10, ge=1),
    offset: int = Query(0, ge=0),
    filters: Optional[str] = Query(None, description="JSON-encoded filters dict"),
    ordering: Optional[str] = Query(
        None, description="Comma-separated field names (prefix with '-' for descending)"
    ),
    admin_service: AdminService = Depends(get_admin_service),
):
    """List resource instances with filtering and pagination."""
    return await admin_service.list_resource(
        resource_name, request, limit, offset, filters, ordering
    )


@router.get("/{resource_name}/{lookup}/retrieve")
async def retrieve_resource(
    resource_name: str,
    lookup: str,
    request: Request,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Retrieve a specific resource instance."""
    return await admin_service.retrieve_resource(resource_name, lookup, request)


@router.delete("/{resource_name}/{lookup}/delete")
async def delete_resource(
    resource_name: str,
    lookup: str,
    request: Request,
    admin_service: AdminService = Depends(get_admin_service),
):
    """Delete a resource instance."""
    return await admin_service.delete_resource(resource_name, lookup, request)
