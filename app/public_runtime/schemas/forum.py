from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ForumPostCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=24)
    title: str = Field(..., min_length=3, max_length=120)
    content: str = Field(..., min_length=3, max_length=4000)


class ForumCommentCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    parent_id: Optional[int] = Field(default=None, ge=1)
