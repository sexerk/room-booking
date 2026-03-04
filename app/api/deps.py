from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.models.user import User
from app.services.auth import AuthService

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False
)


async def get_current_user(
        token: str | None = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User | None:
    if not token:
        return None
    auth_service = AuthService(db)
    return await auth_service.get_user_from_token(token)


async def get_current_active_user(
        current_user: User | None = Depends(get_current_user)
) -> User:
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return current_user


async def get_current_admin_user(
        current_user: User = Depends(get_current_active_user)
) -> User:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions. Admin access required."
        )

    return current_user


async def get_optional_user(
        token: str | None = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
) -> User | None:
    if not token:
        return None
    auth_service = AuthService(db)
    return await auth_service.get_user_from_token(token)