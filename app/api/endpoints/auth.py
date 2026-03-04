from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.auth import (
    Token,
    RegisterRequest,
    RefreshRequest,
    UserResponse
)
from app.services.auth import AuthService
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(
    # prefix="/auth",
    tags=["auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
        register_data: RegisterRequest,
        db: AsyncSession = Depends(get_db)
):

    auth_service = AuthService(db)
    user, access_token, refresh_token = await auth_service.register(register_data)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=Token)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_db)
):

    auth_service = AuthService(db)
    user, access_token, refresh_token = await auth_service.login(
        form_data.username,
        form_data.password
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh", response_model=Token)
async def refresh_token(
        refresh_data: RefreshRequest,
        db: AsyncSession = Depends(get_db)
):

    auth_service = AuthService(db)
    access_token, refresh_token = await auth_service.refresh_token(
        refresh_data.refresh_token
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
        current_user: User = Depends(get_current_active_user)
):

    return current_user