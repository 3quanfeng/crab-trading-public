from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class FollowCreateRequest(BaseModel):
    agent_id: str = Field(..., min_length=3, max_length=128)
    symbols: Optional[list[str]] = None
    min_notional: Optional[float] = Field(default=None, ge=0)
    include_stock: bool = True
    include_poly: bool = True
    muted: bool = False


class FollowEventRequest(BaseModel):
    event_name: str = Field(..., min_length=1, max_length=96)
    details: dict = Field(default_factory=dict)
