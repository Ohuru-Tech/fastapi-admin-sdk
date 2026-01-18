from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy import and_, asc, desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase

from fastapi_admin_sdk.db.session_factory import SessionFactory
from fastapi_admin_sdk.resource.base import Resource


class SQLAlchemyResource(Resource):
    def __init__(
        self,
        model: DeclarativeBase,
        session_factory: SessionFactory,
        lookup_field: str = "id",
        name: str | None = None,
        verbose_name_plural: str | None = None,
    ):
        # Derive name from model if not provided
        if name is None:
            name = getattr(model, "__tablename__", model.__name__.lower())
        if verbose_name_plural is None:
            verbose_name_plural = name + "s" if not name.endswith("s") else name

        super().__init__(name=name, verbose_name_plural=verbose_name_plural)
        self.model = model
        self.session_factory = session_factory
        self.lookup_field = lookup_field

    async def create(self, data: dict):
        async with self.session_factory as session:
            try:
                instance = self.model(**data)
                session.add(instance)
                await session.commit()
                await session.refresh(instance)
                return instance
            except IntegrityError as e:
                await session.rollback()
                raise HTTPException(
                    status_code=400,
                    detail=f"Database constraint violation: {str(e.orig)}",
                )

    async def update(self, lookup: Any, data: dict):
        async with self.session_factory as session:
            stmt = select(self.model).where(
                getattr(self.model, self.lookup_field) == lookup
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            for key, value in data.items():
                setattr(instance, key, value)

            await session.commit()
            await session.refresh(instance)

            return instance

    async def list(
        self,
        limit: Optional[int] = None,
        offset: int = 0,
        filters: Optional[dict] = None,
        ordering: Optional[list] = None,
    ):
        async with self.session_factory as session:
            stmt = select(self.model)

            # Apply filters
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        filter_conditions.append(getattr(self.model, key) == value)
                if filter_conditions:
                    stmt = stmt.where(and_(*filter_conditions))

            # Apply ordering
            if ordering:
                order_by_clauses = []
                for field in ordering:
                    if field.startswith("-"):
                        # Descending order
                        field_name = field[1:]
                        if hasattr(self.model, field_name):
                            order_by_clauses.append(
                                desc(getattr(self.model, field_name))
                            )
                    else:
                        # Ascending order
                        if hasattr(self.model, field):
                            order_by_clauses.append(asc(getattr(self.model, field)))
                if order_by_clauses:
                    stmt = stmt.order_by(*order_by_clauses)

            # Apply offset
            if offset > 0:
                stmt = stmt.offset(offset)

            # Apply limit
            if limit is not None and limit > 0:
                stmt = stmt.limit(limit)

            result = await session.execute(stmt)
            return result.scalars().all()

    async def retrieve(self, lookup: Any):
        async with self.session_factory as session:
            stmt = select(self.model).where(
                getattr(self.model, self.lookup_field) == lookup
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()

            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            return instance

    async def delete(self, lookup: Any):
        async with self.session_factory as session:
            stmt = select(self.model).where(
                getattr(self.model, self.lookup_field) == lookup
            )
            result = await session.execute(stmt)
            instance = result.scalar_one_or_none()
            if not instance:
                raise HTTPException(status_code=404, detail="Instance not found")

            await session.delete(instance)
            await session.commit()
            return True
