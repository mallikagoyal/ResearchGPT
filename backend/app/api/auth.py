"""Authentication endpoints: registration and login."""

import logging

from fastapi import APIRouter, Depends, status

from app.auth.dependencies import get_auth_service
from app.schemas.user import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Register a new user account and return an access token.

    Raises HTTP 409 (via the centralized exception handler) if the email
    is already registered.
    """
    user, token = await auth_service.register(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
    )
    return Token(access_token=token, user=UserResponse.model_validate(user))


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """Authenticate with email and password, returning an access token.

    Raises HTTP 401 (via the centralized exception handler) if credentials
    are invalid.
    """
    user, token = await auth_service.authenticate(
        email=payload.email,
        password=payload.password,
    )
    return Token(access_token=token, user=UserResponse.model_validate(user))
