from abc import ABC, abstractmethod
from typing import Any


class SessionFactory(ABC):
    """Abstract base class for database session factories."""

    @abstractmethod
    async def create_session(self) -> Any:
        """Create and return a new database session."""
        pass

    @abstractmethod
    async def close_session(self, session: Any) -> None:
        """Close a database session."""
        pass

    @abstractmethod
    async def __aenter__(self):
        """Async context manager entry."""
        pass

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
