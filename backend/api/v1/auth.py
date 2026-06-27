from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status

from api.deps import get_auth_service, get_security_service
from core.logging import get_logger
from core.security import SecurityService
from schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = get_logger(__name__)


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    body: RegisterRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    access_token, refresh_token = await auth.register(
        email=body.email,
        password=body.password,
        display_name=body.display_name,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    access_token, refresh_token = await auth.login(
        email=body.email,
        password=body.password,
        user_agent=request.headers.get("user-agent"),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    body: RefreshRequest,
    auth: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    access_token, refresh_token = await auth.refresh_tokens(body.refresh_token)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/logout", status_code=204)
async def logout(
    body: RefreshRequest,
    auth: AuthService = Depends(get_auth_service),
) -> None:
    await auth.logout(body.refresh_token)
