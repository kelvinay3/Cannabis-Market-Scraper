from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    org_id: Optional[str]
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None


class UserRoleUpdate(BaseModel):
    role: str


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "viewer"
    name: Optional[str] = None


class InviteResponse(BaseModel):
    message: str
    email: str
    invite_link: Optional[str] = None
