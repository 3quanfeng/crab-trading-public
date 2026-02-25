from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/public", tags=["public-health"])


@router.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "service": "crab-trading-public",
        "execution_mode": "mock",
        "api_prefix": "/api/v1/public",
    }
