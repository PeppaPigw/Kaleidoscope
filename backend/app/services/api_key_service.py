"""API key management service."""

from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import APIKey

VALID_API_SCOPES = {
    "search:read",
    "papers:read",
    "papers:write",
    "analysis:run",
    "rag:ask",
    "workspace:read",
    "admin:run",
}


class APIKeyService:
    """Create, list, and revoke hashed external API keys."""

    def __init__(self, db: AsyncSession, user_id: str):
        self.db = db
        self.user_id = user_id

    async def create_key(
        self,
        name: str,
        scopes: list[str],
        expires_at: datetime | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        """Create an API key and return the raw secret exactly once."""
        normalized_scopes = self._normalize_scopes(scopes)
        raw_key = self._generate_key()
        key = APIKey(
            user_id=self.user_id,
            name=name.strip(),
            key_hash=self.hash_key(raw_key),
            key_prefix=raw_key[:16],
            scopes=normalized_scopes,
            expires_at=expires_at,
            description=description,
        )
        self.db.add(key)
        await self.db.flush()
        return {**self._serialize_key(key), "key": raw_key}

    async def list_keys(self, include_revoked: bool = False) -> list[dict[str, Any]]:
        """List keys for the current user without exposing raw secrets."""
        query = select(APIKey).where(APIKey.user_id == self.user_id)
        if not include_revoked:
            query = query.where(APIKey.revoked_at.is_(None))
        query = query.order_by(APIKey.created_at.desc())
        result = await self.db.execute(query)
        return [self._serialize_key(key) for key in result.scalars().all()]

    async def revoke_key(self, key_id: str) -> dict[str, Any] | None:
        """Soft-revoke a key owned by the current user."""
        result = await self.db.execute(
            select(APIKey).where(APIKey.id == key_id, APIKey.user_id == self.user_id)
        )
        key = result.scalar_one_or_none()
        if key is None:
            return None
        if key.revoked_at is None:
            key.revoked_at = datetime.now(UTC)
            await self.db.flush()
        return self._serialize_key(key)

    @staticmethod
    def hash_key(raw_key: str) -> str:
        """Hash an API key for storage or lookup."""
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _generate_key() -> str:
        return f"ks_live_{secrets.token_urlsafe(32)}"

    @staticmethod
    def _normalize_scopes(scopes: list[str]) -> list[str]:
        normalized = list(dict.fromkeys(scope.strip() for scope in scopes if scope.strip()))
        invalid = sorted(set(normalized) - VALID_API_SCOPES)
        if invalid:
            raise ValueError(f"Invalid API key scopes: {', '.join(invalid)}")
        return normalized

    @staticmethod
    def _serialize_key(key: APIKey) -> dict[str, Any]:
        return {
            "id": str(key.id),
            "name": key.name,
            "key_prefix": key.key_prefix,
            "scopes": key.scopes,
            "description": key.description,
            "created_at": key.created_at.isoformat() if key.created_at else None,
            "updated_at": key.updated_at.isoformat() if key.updated_at else None,
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "last_used_at": key.last_used_at.isoformat() if key.last_used_at else None,
            "revoked_at": key.revoked_at.isoformat() if key.revoked_at else None,
        }
