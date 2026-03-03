from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):

    def __init__(self, db: AsyncSession):
        super().__init__(User, db)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create_user(
            self,
            email: str,
            username: str,
            hashed_password: str,
            full_name: Optional[str] = None,
            is_admin: bool = False
    ) -> User:
        return await self.create(
            email=email,
            username=username,
            hashed_password=hashed_password,
            full_name=full_name,
            is_admin=is_admin
        )