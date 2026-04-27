"""JWT authentication utilities.

Provides:
- create_access_token(user_id) -> str
- decode_access_token(token) -> str | None
- get_current_user_id_from_token(token) -> str | None
- hash_password(password) -> str
- verify_password(plain, hashed) -> bool

Single-user mode: when KALEIDOSCOPE_JWT_SECRET is not set, falls back to
DEFAULT_USER_ID sentinel so existing behaviour is preserved.
"""

import os
from datetime import UTC, datetime, timedelta

from app.models.collection import DEFAULT_USER_ID

try:
    from jose import JWTError, jwt

    _JWT_AVAILABLE = True
except ImportError:
    JWTError = Exception
    jwt = None
    _JWT_AVAILABLE = False

JWT_SECRET = os.getenv("KALEIDOSCOPE_JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = int(os.getenv("KALEIDOSCOPE_JWT_EXPIRE_MINUTES", "1440"))


def create_access_token(user_id: str) -> str:
    """Create a signed JWT for ``user_id`` or return an empty string."""
    if not _JWT_AVAILABLE or not JWT_SECRET:
        return ""
    expire = datetime.now(UTC) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire},
        JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> str | None:
    """Decode a JWT and return the embedded user ID."""
    if not _JWT_AVAILABLE or not JWT_SECRET or not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        subject = payload.get("sub")
        return subject if isinstance(subject, str) else None
    except JWTError:
        return None


def get_current_user_id_from_token(token: str) -> str | None:
    """Resolve a user ID from token, falling back in single-user mode."""
    user_id = decode_access_token(token)
    if user_id:
        return user_id
    if not JWT_SECRET:
        return DEFAULT_USER_ID
    return None


def hash_password(password: str) -> str:
    """Hash a password for storage."""
    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.hash(password)
    except ImportError:
        import hashlib

        return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    try:
        from passlib.context import CryptContext

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(plain, hashed)
    except ImportError:
        import hashlib

        return hashlib.sha256(plain.encode()).hexdigest() == hashed
