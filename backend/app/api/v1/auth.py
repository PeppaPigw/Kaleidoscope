"""Auth API — login and identity helpers."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.auth import JWT_SECRET, create_access_token
from app.config import settings
from app.models.collection import DEFAULT_USER_ID

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    mode: str


def _token_response() -> TokenResponse:
    if JWT_SECRET:
        return TokenResponse(
            access_token=create_access_token(DEFAULT_USER_ID),
            user_id=DEFAULT_USER_ID,
            mode="jwt",
        )
    return TokenResponse(
        access_token="single-user-mode",
        user_id=DEFAULT_USER_ID,
        mode="single_user",
    )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """Validate admin credentials and return an access token."""
    if req.username != settings.admin_username or req.password != settings.admin_password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _token_response()


@router.get("/me")
async def me():
    """Return current user identity in the active auth mode."""
    return {
        "user_id": DEFAULT_USER_ID,
        "username": settings.admin_username,
        "mode": "single_user" if not JWT_SECRET else "jwt",
    }


@router.post("/logout")
async def logout():
    """Client-side token invalidation — the API remains stateless."""
    return {"ok": True}
