# FastAPI Admin SDK

[![Coverage](https://codecov.io/gh/yourusername/fastapi-admin-sdk/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/fastapi-admin-sdk)
[![PyPI version](https://badge.fury.io/py/fastapi-admin-sdk.svg)](https://badge.fury.io/py/fastapi-admin-sdk)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)](https://github.com/yourusername/fastapi-admin-sdk)

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

## API Endpoints

Once you've registered your admin classes and included the router, the following endpoints will be available:

- `POST /admin/{resource_name}/create` - Create a new resource instance
- `GET /admin/{resource_name}/list` - List resource instances with filtering and pagination
- `GET /admin/{resource_name}/{lookup}/retrieve` - Retrieve a specific resource instance
- `PATCH /admin/{resource_name}/{lookup}/update` - Update an existing resource instance
- `DELETE /admin/{resource_name}/{lookup}/delete` - Delete a resource instance

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
