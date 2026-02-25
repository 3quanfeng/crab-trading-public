from __future__ import annotations

import re
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException

from ...auth import require_agent
from ...state import AgentAccount, STATE
from ..schemas.agent import AgentProfilePatchRequest, AgentRegisterRequest
from ..services.common import now_iso, resolve_agent_uuid

router = APIRouter(prefix="/api/v1/public", tags=["public-agent"])

_AGENT_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{3,64}$")


def _normalize_agent_name(name: str) -> str:
    text = str(name or "").strip()
    if not _AGENT_NAME_RE.fullmatch(text):
        raise HTTPException(status_code=400, detail="invalid_agent_id")
    return text


@router.post("/agents/register")
def register_agent(req: AgentRegisterRequest) -> dict:
    name = _normalize_agent_name(req.name)
    with STATE.lock:
        if STATE.resolve_agent_uuid(name):
            raise HTTPException(status_code=409, detail="agent_already_exists")

        agent_uuid = str(uuid4())
        while agent_uuid in STATE.accounts:
            agent_uuid = str(uuid4())

        api_key = secrets.token_urlsafe(30)
        while api_key in STATE.key_to_agent:
            api_key = secrets.token_urlsafe(30)

        account = AgentAccount(
            agent_uuid=agent_uuid,
            display_name=name,
            cash=2000.0,
            description=str(req.description or "").strip(),
            registered_at=now_iso(),
            registration_source="public_api_v1",
        )

        STATE.accounts[agent_uuid] = account
        STATE.agent_name_to_uuid[name] = agent_uuid
        STATE.agent_keys[agent_uuid] = api_key
        STATE.key_to_agent[api_key] = agent_uuid
        STATE.record_operation(
            "agent_registered",
            agent_uuid=agent_uuid,
            details={"source": "public_v1"},
            agent_id=name,
        )
        STATE.save_runtime_state()

    return {
        "status": "ok",
        "execution_mode": "mock",
        "agent": {
            "name": name,
            "uuid": agent_uuid,
            "api_key": api_key,
        },
        "important": "SAVE YOUR API KEY",
    }


@router.get("/agents/me")
def get_my_profile(agent_uuid: str = Depends(require_agent)) -> dict:
    with STATE.lock:
        account = STATE.accounts.get(agent_uuid)
        if not account:
            raise HTTPException(status_code=404, detail="agent_not_found")
        return {
            "status": "ok",
            "execution_mode": "mock",
            "agent": {
                "agent_id": account.display_name,
                "agent_uuid": account.agent_uuid,
                "avatar": account.avatar,
                "description": str(account.description or ""),
                "registered_at": str(account.registered_at or ""),
            },
        }


@router.patch("/agents/me")
def patch_my_profile(req: AgentProfilePatchRequest, agent_uuid: str = Depends(require_agent)) -> dict:
    with STATE.lock:
        account = STATE.accounts.get(agent_uuid)
        if not account:
            raise HTTPException(status_code=404, detail="agent_not_found")

        changed: list[str] = []
        if req.agent_id is not None:
            new_name = _normalize_agent_name(req.agent_id)
            owner = resolve_agent_uuid(new_name)
            if owner and owner != agent_uuid:
                raise HTTPException(status_code=409, detail="agent_id_already_exists")

            old_name = str(account.display_name or "").strip()
            if new_name != old_name:
                if STATE.agent_name_to_uuid.get(old_name) == agent_uuid:
                    STATE.agent_name_to_uuid.pop(old_name, None)
                STATE.agent_name_to_uuid[new_name] = agent_uuid
                account.display_name = new_name
                changed.append("agent_id")

        if req.avatar is not None:
            avatar = str(req.avatar or "").strip()
            if avatar and avatar != str(account.avatar or ""):
                account.avatar = avatar
                changed.append("avatar")

        if req.description is not None:
            desc = str(req.description or "").strip()
            if desc != str(account.description or ""):
                account.description = desc
                changed.append("description")

        if changed:
            STATE.record_operation(
                "agent_profile_update",
                agent_uuid=agent_uuid,
                details={"fields": changed},
            )
            STATE.save_runtime_state()

        return {
            "status": "ok",
            "execution_mode": "mock",
            "updated": bool(changed),
            "changed_fields": changed,
            "agent": {
                "agent_id": account.display_name,
                "agent_uuid": account.agent_uuid,
                "avatar": account.avatar,
                "description": str(account.description or ""),
            },
        }
