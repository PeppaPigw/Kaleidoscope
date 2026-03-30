"""Role-based permission utilities for Kaleidoscope."""

from fastapi import HTTPException

from app.models.collection import DEFAULT_USER_ID


def require_role(user_id: str, required_role: str = "member") -> None:
    """
    Check that user has sufficient role.

    In single-user mode (DEFAULT_USER_ID), all roles are granted.
    When multi-user is deployed, this will check the users table.
    """
    if user_id == DEFAULT_USER_ID:
        return
    return


def require_owner(user_id: str, resource_owner_id: str) -> None:
    """Require that user_id owns the resource, or is DEFAULT_USER_ID."""
    if user_id == DEFAULT_USER_ID:
        return
    if user_id != resource_owner_id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FORBIDDEN",
                "message": "You do not own this resource.",
            },
        )
