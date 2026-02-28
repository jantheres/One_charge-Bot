from __future__ import annotations

from typing import Optional

from fastapi import Header, HTTPException
from pydantic import BaseModel, field_validator


class UserContext(BaseModel):
    user_id: str
    name: Optional[str] = None
    phone: Optional[str] = None
    vehicle_model: Optional[str] = None

    @field_validator("user_id")
    @classmethod
    def _user_id_not_blank(cls, v: str) -> str:
        v = (v or "").strip()
        if not v:
            raise ValueError("user_id is required")
        return v

def get_user_context(
    x_user_id: str = Header(..., alias="X-User-Id"),
    x_user_name: Optional[str] = Header(None, alias="X-User-Name"),
    x_user_phone: Optional[str] = Header(None, alias="X-User-Phone"),
    x_vehicle_model: Optional[str] = Header(None, alias="X-Vehicle-Model"),
) -> UserContext:
    """
    Trusted header-based identity/context. This endpoint must be behind a gateway
    that injects these headers after authenticating the user.
    """
    try:
        return UserContext(
            user_id=x_user_id,
            name=x_user_name,
            phone=x_user_phone,
            vehicle_model=x_vehicle_model,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid auth context headers: {e}")

