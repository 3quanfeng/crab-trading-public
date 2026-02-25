from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DiscoveryQuery(BaseModel):
    window: str = Field(default="7d", min_length=2, max_length=8)
    limit: int = Field(default=20, ge=1, le=500)
    page: int = Field(default=1, ge=1, le=1000)
    symbol: Optional[str] = Field(default="", max_length=24)
    risk: Optional[str] = Field(default="", max_length=32)
    tag: Optional[str] = Field(default="", max_length=64)
