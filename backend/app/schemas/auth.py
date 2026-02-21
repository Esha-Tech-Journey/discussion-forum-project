from pydantic import BaseModel, EmailStr


# ==============================
# Login Request
# ==============================

class LoginRequest(BaseModel):
    """
    User login payload.
    """

    email: EmailStr
    password: str


# ==============================
# Token Response
# ==============================

class TokenResponse(BaseModel):
    """
    JWT token response.
    """

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ==============================
# Refresh Token Request
# ==============================

class RefreshTokenRequest(BaseModel):
    """
    Refresh token payload.
    """

    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str


class ChangePasswordRequest(BaseModel):
    email: EmailStr
    old_password: str
    new_password: str
