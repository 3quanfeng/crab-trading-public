from __future__ import annotations

from fastapi import APIRouter, Request

from ..schemas.protocol import ProtocolEvent

router = APIRouter(prefix="/api/v1/public", tags=["public-protocol"])


@router.get("/protocol/openapi.json")
def protocol_openapi(request: Request) -> dict:
    return request.app.openapi()


@router.get("/protocol/event-schema")
def protocol_event_schema() -> dict:
    return {
        "status": "ok",
        "execution_mode": "mock",
        "event_schema": ProtocolEvent.model_json_schema(),
    }
