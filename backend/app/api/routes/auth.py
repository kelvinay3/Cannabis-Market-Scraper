from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.redis import get_redis
from app.core.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token,
    create_reset_token, create_invite_token, decode_token,
)
from app.core.config import settings
from app.models.user import User
from app.models.organization import Organization
from app.schemas.auth import (
    LoginRequest, TokenResponse, ForgotPasswordRequest,
    ResetPasswordRequest, InviteAcceptRequest, ChangePasswordRequest,
)
from app.schemas.user import UserOut
from app.services.email import send_password_reset_email
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated")

    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    access_token = create_access_token({"sub": user.id})
    refresh_token = create_refresh_token({"sub": user.id})

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        max_age=settings.refresh_token_expire_days * 86400,
        samesite="lax",
        secure=settings.environment == "production",
    )

    return TokenResponse(
        access_token=access_token,
        user=UserOut.model_validate(user),
    )


@router.post("/refresh")
async def refresh(request: Request, db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    blacklisted = await redis.get(f"blacklist:{refresh_token}")
    if blacklisted:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == payload["sub"]))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Blacklist old refresh token, issue new one
    exp = payload.get("exp", 0)
    ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
    if ttl > 0:
        await redis.setex(f"blacklist:{refresh_token}", ttl, "1")

    new_access = create_access_token({"sub": user.id})
    return {"access_token": new_access, "token_type": "bearer"}


@router.post("/logout")
async def logout(request: Request, response: Response, redis=Depends(get_redis), user: User = Depends(get_current_user)):
    # Blacklist the current access token
    from fastapi.security import HTTPBearer
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = decode_token(token)
        if payload:
            exp = payload.get("exp", 0)
            ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
            if ttl > 0:
                await redis.setex(f"blacklist:{token}", ttl, "1")

    # Clear refresh cookie
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        payload = decode_token(refresh_token)
        if payload:
            exp = payload.get("exp", 0)
            ttl = max(0, exp - int(datetime.now(timezone.utc).timestamp()))
            if ttl > 0:
                await redis.setex(f"blacklist:{refresh_token}", ttl, "1")

    response.delete_cookie("refresh_token")
    return {"message": "Logged out"}


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email.lower()))
    user = result.scalar_one_or_none()

    # Always return 200 to prevent email enumeration
    if user and user.is_active:
        token = create_reset_token(user.email)
        reset_link = f"{settings.frontend_url}/reset-password?token={token}"
        await send_password_reset_email(user.email, user.name or "", reset_link)

    return {"message": "If that email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.token)
    if not payload or payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    email = payload.get("sub")
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password reset successfully"}


@router.post("/change-password")
async def change_password(
    body: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    if len(body.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    user.password_hash = hash_password(body.new_password)
    await db.commit()
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserOut)
async def get_me(user: User = Depends(get_current_user)):
    return UserOut.model_validate(user)
