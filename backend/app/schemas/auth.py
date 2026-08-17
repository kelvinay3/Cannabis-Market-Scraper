from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class InviteAcceptRequest(BaseModel):
    token: str
    name: str
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


from app.schemas.user import UserOut  # noqa: E402
TokenResponse.model_rebuild()
