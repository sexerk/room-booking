from datetime import timedelta
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user import UserRepository
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.core.exceptions import AuthenticationError, PermissionDeniedError
from app.schemas.auth import RegisterRequest
from app.models.user import User


class AuthService:

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register(self, register_data: RegisterRequest) -> Tuple[User, str, str]:
        existing_email = await self.user_repo.get_by_email(register_data.email)
        if existing_email:
            raise AuthenticationError("Email already registered")

        existing_username = await self.user_repo.get_by_username(register_data.username)
        if existing_username:
            raise AuthenticationError("Username already taken")

        hashed_password = get_password_hash(register_data.password)

        user = await self.user_repo.create_user(
            email=register_data.email,
            username=register_data.username,
            hashed_password=hashed_password,
            full_name=register_data.full_name
        )

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return user, access_token, refresh_token

    async def login(self, username: str, password: str) -> Tuple[User, str, str]:

        user = await self.user_repo.get_by_username(username)
        if not user:
            user = await self.user_repo.get_by_email(username)

        if not user:
            raise AuthenticationError("Incorrect username or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Incorrect username or password")

        if not user.is_active:
            raise PermissionDeniedError("User account is disabled")

        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})

        return user, access_token, refresh_token

    async def refresh_token(self, refresh_token: str) -> Tuple[str, str]:

        try:
            payload = decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")

            user_id = int(payload.get("sub"))

            user = await self.user_repo.get(user_id)
            if not user or not user.is_active:
                raise AuthenticationError("User not found or inactive")

            new_access_token = create_access_token({"sub": str(user.id)})
            new_refresh_token = create_refresh_token({"sub": str(user.id)})

            return new_access_token, new_refresh_token

        except Exception as e:
            raise AuthenticationError(f"Invalid refresh token: {str(e)}")

    async def get_current_user(self, user_id: int) -> Optional[User]:
        return await self.user_repo.get(user_id)


async def get_auth_service(db: AsyncSession = None) -> AuthService:
    return AuthService(db)