from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_user(
        self, username: str, email: str, password_hash: str
    ) -> User:
        """Insert a new user row and return the persisted instance."""
        user = User(username=username, email=email, password_hash=password_hash)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        """Return the User with the given email, or None if not found."""
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """Return True if a user with the given email already exists."""
        result = await self.session.execute(
            select(User.id).where(User.email == email)
        )
        return result.scalar_one_or_none() is not None
