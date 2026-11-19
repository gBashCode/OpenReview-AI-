"""Generic Base Repository implementing async CRUD patterns."""

from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository providing asynchronous database abstraction."""

    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
    ) -> Sequence[ModelType]:
        """List records with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        """Count total records in the model table."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one() or 0

    async def create(self, instance: ModelType) -> ModelType:
        """Add and commit an instance to database."""
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance

    async def delete(self, instance: ModelType) -> None:
        """Remove an instance from database."""
        await self.session.delete(instance)
        await self.session.commit()
