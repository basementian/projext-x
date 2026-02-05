"""Generic repository pattern for CRUD operations."""

from typing import TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from flipflow.core.models.base import Base

T = TypeVar("T", bound=Base)


class Repository:
    """Generic async repository for SQLAlchemy models."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, model: type[T], id: int) -> T | None:
        """Get a single record by primary key."""
        return await self.session.get(model, id)

    async def get_all(self, model: type[T], **filters) -> list[T]:
        """Get all records, optionally filtered by column values."""
        stmt = select(model)
        for key, value in filters.items():
            stmt = stmt.where(getattr(model, key) == value)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, instance: T) -> T:
        """Add and flush a new record. Returns the instance with ID populated."""
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def update(self, instance: T, **kwargs) -> T:
        """Update fields on an existing record."""
        for key, value in kwargs.items():
            setattr(instance, key, value)
        await self.session.flush()
        return instance

    async def delete(self, instance: T) -> None:
        """Hard delete a record."""
        await self.session.delete(instance)
        await self.session.flush()
