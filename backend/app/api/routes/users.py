from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import create_invite_token, hash_password, decode_token
from app.core.config import settings
from app.models.user import User, ROLES
from app.models.organization import Organization
from app.schemas.user import UserOut, UserUpdate, UserRoleUpdate, InviteRequest, InviteResponse
from app.schemas.auth import InviteAcceptRequest
from app.schemas.common import PaginatedResponse
from app.api.deps import get_current_user, require_admin, require_super_admin
from app.services.email import send_invite_email

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=PaginatedResponse[UserOut])
async def list_users(
    page: int = 1,
    per_page: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    offset = (page - 1) * per_page

    if current_user.role == "super_admin":
        count_q = select(func.count()).select_from(User)
        q = select(User).offset(offset).limit(per_page).order_by(User.created_at.desc())
    else:
        count_q = select(func.count()).select_from(User).where(User.org_id == current_user.org_id)
        q = select(User).where(User.org_id == current_user.org_id).offset(offset).limit(per_page).order_by(User.created_at.desc())

    total = (await db.execute(count_q)).scalar()
    users = (await db.execute(q)).scalars().all()

    return PaginatedResponse(
        data=[UserOut.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        pages=-(-total // per_page),
    )


@router.patch("/me", response_model=UserOut)
async def update_me(
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if body.name is not None:
        current_user.name = body.name
    if body.email is not None:
        # Check uniqueness
        existing = (await db.execute(select(User).where(User.email == body.email.lower(), User.id != current_user.id))).scalar_one_or_none()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        current_user.email = body.email.lower()
    await db.commit()
    return UserOut.model_validate(current_user)


@router.patch("/{user_id}/role", response_model=UserOut)
async def update_user_role(
    user_id: str,
    body: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if body.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be one of: {', '.join(ROLES)}")

    # Non-super-admins can't set super_admin role
    if body.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Only super admins can assign super_admin role")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Org admins can only manage their own org
    if current_user.role == "admin" and user.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Cannot manage users outside your organization")

    user.role = body.role
    await db.commit()
    return UserOut.model_validate(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.role == "admin" and user.org_id != current_user.org_id:
        raise HTTPException(status_code=403, detail="Cannot manage users outside your organization")

    user.is_active = False
    await db.commit()
    return {"message": "User deactivated"}


@router.post("/invite", response_model=InviteResponse)
async def invite_user(
    body: InviteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if body.role not in ROLES:
        raise HTTPException(status_code=400, detail=f"Invalid role")
    if body.role == "super_admin" and current_user.role != "super_admin":
        raise HTTPException(status_code=403, detail="Cannot invite super admins")

    # Check if already a user
    existing = (await db.execute(select(User).where(User.email == body.email.lower()))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="A user with that email already exists")

    org_id = current_user.org_id or ""
    token = create_invite_token(body.email.lower(), body.role, org_id)
    invite_link = f"{settings.frontend_url}/invite?token={token}"

    await send_invite_email(
        to=body.email,
        invited_by=current_user.name or current_user.email,
        role=body.role,
        invite_link=invite_link,
    )

    return InviteResponse(
        message=f"Invite sent to {body.email}",
        email=body.email,
        invite_link=invite_link if settings.environment == "development" else None,
    )


@router.post("/accept-invite", response_model=UserOut)
async def accept_invite(body: InviteAcceptRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(body.token)
    if not payload or payload.get("type") != "invite":
        raise HTTPException(status_code=400, detail="Invalid or expired invite token")

    email = payload.get("sub")
    role = payload.get("role", "viewer")
    org_id = payload.get("org_id")

    existing = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Account already exists. Please log in.")

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    import uuid
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        name=body.name,
        password_hash=hash_password(body.password),
        role=role,
        org_id=org_id if org_id else None,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserOut.model_validate(user)
