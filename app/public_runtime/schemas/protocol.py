from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ProtocolEvent(BaseModel):
    id: int = Field(default=0)
    type: str = Field(default="")
    agent_uuid: str = Field(default="")
    agent_id: str = Field(default="")
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default="")
    execution_mode: str = Field(default="mock")
