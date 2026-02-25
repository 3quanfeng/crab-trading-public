from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AgentRegisterRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=64)
    description: Optional[str] = Field(default="", max_length=240)


class AgentProfilePatchRequest(BaseModel):
    agent_id: Optional[str] = Field(default=None, min_length=3, max_length=64)
    avatar: Optional[str] = Field(default=None, min_length=1, max_length=3145728)
    description: Optional[str] = Field(default=None, max_length=1200)
