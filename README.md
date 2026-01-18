# FastAPI Admin SDK

[![PyPI version](https://img.shields.io/pypi/v/fastapi-admin-sdk.svg)](https://pypi.org/project/fastapi-admin-sdk/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/Ohuru-Tech/fastapi-admin-sdk/actions/workflows/publish.yml/badge.svg)](https://github.com/Ohuru-Tech/fastapi-admin-sdk/actions/workflows/publish.yml)
[![codecov](https://codecov.io/gh/Ohuru-Tech/fastapi-admin-sdk/branch/main/graph/badge.svg?token=96PIBKDSFR)](https://codecov.io/gh/Ohuru-Tech/fastapi-admin-sdk)

A FastAPI admin SDK for building admin interfaces with resource management, permissions, and CRUD operations.

## Installation

Install the package using pip:

```bash
pip install fastapi-admin-sdk
```

Or using uv:

```bash
uv add fastapi-admin-sdk
```

## Quick Start

### 1. Configure Settings

Set up your environment variables:

```bash
export ADMIN_DB_URL="postgresql+asyncpg://user:password@localhost/dbname"
export ORM_TYPE="sqlalchemy"
```

Or create a `.env` file:

```env
ADMIN_DB_URL=postgresql+asyncpg://user:password@localhost/dbname
ORM_TYPE=sqlalchemy
```

### 2. Define Your Model

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
```

### 3. Create a Resource

```python
from fastapi_admin_sdk import Resource, SQLAlchemyResource
from fastapi_admin_sdk.db import get_session_factory

session_factory = get_session_factory()
user_resource = SQLAlchemyResource(
    model=User,
    session_factory=session_factory,
    lookup_field="id"
)
```

### 4. Create an Admin Class

```python
from fastapi import Request
from pydantic import BaseModel
from fastapi_admin_sdk import BaseAdmin, register

class UserCreateSchema(BaseModel):
    name: str
    email: str

class UserUpdateSchema(BaseModel):
    name: str | None = None
    email: str | None = None

@register(user_resource)
class UserAdmin(BaseAdmin):
    list_display = ["id", "name", "email"]
    list_filter = ["name"]
    search_fields = ["name", "email"]
    ordering = ["id"]
    
    create_form_schema = UserCreateSchema
    update_form_schema = UserUpdateSchema
    lookup_field = "id"
    
    async def has_create_permission(self, request: Request):
        # Add your permission logic here
        return True
```

### 5. Add Routes to Your FastAPI App

```python
from fastapi import FastAPI
from fastapi_admin_sdk import router

app = FastAPI()
app.include_router(router, prefix="/admin")
```

## Features

- **Resource Management**: Define resources with CRUD operations
- **Permission System**: Customizable permission checks for create, read, update, delete, and list operations
- **Filtering & Pagination**: Built-in support for filtering and pagination
- **SQLAlchemy Support**: First-class support for SQLAlchemy async models
- **Type Safety**: Built with Pydantic for data validation
- **Manifest API**: Dynamic resource discovery for building admin UIs

## API Endpoints

Once you've registered your admin classes and included the router, the following endpoints will be available:

### Manifest API

- `GET /admin/manifest` - Get admin manifest with all registered resources and their configurations

The manifest endpoint returns a JSON object containing metadata about all registered admin resources, filtered by user permissions. This is particularly useful for building dynamic admin UIs that can discover available resources and their capabilities at runtime.

**Response Structure:**

```json
{
  "resources": [
    {
      "name": "users",
      "verbose_name": "users",
      "actions": ["list", "create", "update", "delete", "retrieve"],
      "list_config": {
        "display_fields": ["id", "name", "email"],
        "filter_fields": ["name"],
        "search_fields": ["name", "email"],
        "ordering": ["id"]
      },
      "create_schema": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "x-field-type": "char",
            "maxLength": 100
          },
          "email": {
            "type": "string",
            "format": "email",
            "x-field-type": "email"
          }
        },
        "required": ["name", "email"]
      },
      "update_schema": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string",
            "x-field-type": "char",
            "maxLength": 100
          },
          "email": {
            "type": "string",
            "format": "email",
            "x-field-type": "email"
          }
        }
      }
    }
  ]
}
```

**Key Features:**

- **Permission-aware**: Only returns resources and actions the user has permission to access
- **Schema information**: Includes JSON Schema for create and update forms with form field type metadata
- **List configuration**: Provides display fields, filter fields, search fields, and ordering preferences
- **Action-based**: Lists available actions (list, create, update, delete, retrieve) per resource

### CRUD Endpoints

- `POST /admin/{resource_name}/create` - Create a new resource instance
- `GET /admin/{resource_name}/list` - List resource instances with filtering and pagination
  - Query parameters:
    - `limit` (int): Number of items per page (default: 10)
    - `offset` (int): Number of items to skip (default: 0)
    - `filters` (str): JSON-encoded filters dictionary
    - `ordering` (str): Comma-separated field names (prefix with '-' for descending)
- `GET /admin/{resource_name}/{lookup}/retrieve` - Retrieve a specific resource instance
- `PATCH /admin/{resource_name}/{lookup}/update` - Update an existing resource instance
- `DELETE /admin/{resource_name}/{lookup}/delete` - Delete a resource instance

## Frontend Integration

The manifest API makes it easy to build dynamic admin UIs. See [Building Admin UIs with shadcn/ui + Next.js](docs/shadcn-nextjs-integration.md) for a complete guide on integrating this SDK with modern frontend frameworks.

## Development

### Running Tests

```bash
# Install dev dependencies
uv sync --all-groups --all-extras

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=fastapi_admin_sdk --cov-report=term
```

### Building the Package

```bash
python -m build
```

### Publishing to PyPI

The package is automatically published to PyPI when a git tag is pushed. Make sure to set up the `PYPI_API_TOKEN` secret in your GitHub repository.

## License

MIT License - see [LICENSE](LICENSE) file for details.
