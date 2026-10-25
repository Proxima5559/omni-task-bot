from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.telegram_id == telegram_id))

    async def get_or_create(self, telegram_id: int, username: str | None, first_name: str | None) -> User:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user
        try:
            async with self.session.begin_nested():
                user = User(telegram_id=telegram_id, username=username, first_name=first_name)
                self.session.add(user)
            return user
        except IntegrityError:
            return await self.get_by_telegram_id(telegram_id) 