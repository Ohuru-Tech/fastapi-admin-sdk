from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fastapi_admin_sdk.config.settings import settings
from fastapi_admin_sdk.db.session_factory import SessionFactory


class SQLAlchemySessionFactory(SessionFactory):
    """SQLAlchemy implementation of SessionFactory."""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self._current_session: AsyncSession | None = None

    async def create_session(self) -> AsyncSession:
        """Create and return a new SQLAlchemy async session."""
        return self.async_session_maker()

    async def close_session(self, session: AsyncSession) -> None:
        """Close a SQLAlchemy session."""
        await session.close()

    async def __aenter__(self) -> AsyncSession:
        """Async context manager entry."""
        self._current_session = await self.create_session()
        return self._current_session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._current_session:
            await self.close_session(self._current_session)
            self._current_session = None

    async def close(self):
        """Close the engine and all connections."""
        await self.engine.dispose()


# Singleton instance
_sqlalchemy_factory: SQLAlchemySessionFactory | None = None


def get_sqlalchemy_factory() -> SQLAlchemySessionFactory:
    """Get or create the singleton SQLAlchemy session factory."""
    global _sqlalchemy_factory
    if _sqlalchemy_factory is None:
        _sqlalchemy_factory = SQLAlchemySessionFactory(settings.admin_db_url)
    return _sqlalchemy_factory
