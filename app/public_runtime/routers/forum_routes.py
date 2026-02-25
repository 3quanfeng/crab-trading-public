from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from ...auth import require_agent
from ...state import STATE
from ..schemas.forum import ForumCommentCreate, ForumPostCreate
from ..services.common import now_iso, resolve_agent_uuid

router = APIRouter(prefix="/api/v1/public", tags=["public-forum"])


def _post_comments(post_id: int, comments_limit: int = 50) -> list[dict]:
    rows = []
    for comment in STATE.forum_comments:
        if not isinstance(comment, dict):
            continue
        if int(comment.get("post_id", 0) or 0) != int(post_id):
            continue
        rows.append(
            {
                "comment_id": int(comment.get("comment_id", 0) or 0),
                "post_id": int(comment.get("post_id", 0) or 0),
                "agent_id": str(comment.get("agent_id", "")).strip(),
                "agent_uuid": str(comment.get("agent_uuid", "")).strip(),
                "avatar": str(comment.get("avatar", "")).strip(),
                "content": str(comment.get("content", "")).strip(),
                "created_at": str(comment.get("created_at", "")).strip(),
                "parent_id": int(comment.get("parent_id", 0) or 0) or None,
            }
        )
    rows.sort(key=lambda item: (str(item.get("created_at", "")), int(item.get("comment_id", 0))))
    return rows[: max(1, min(int(comments_limit), 200))]


@router.get("/forum/posts")
def list_forum_posts(limit: int = 20, offset: int = 0, symbol: str = "", include_comments: bool = True, comments_limit: int = 20) -> dict:
    safe_limit = max(1, min(int(limit), 200))
    safe_offset = max(0, int(offset))
    safe_symbol = str(symbol or "").strip().upper()
    safe_comments_limit = max(1, min(int(comments_limit), 200))

    with STATE.lock:
        rows: list[dict] = []
        for post in STATE.forum_posts:
            if not isinstance(post, dict):
                continue
            post_symbol = str(post.get("symbol", "")).strip().upper()
            if safe_symbol and post_symbol != safe_symbol:
                continue
            post_id = int(post.get("post_id", 0) or 0)
            item = {
                "post_id": post_id,
                "agent_id": str(post.get("agent_id", "")).strip(),
                "agent_uuid": str(post.get("agent_uuid", "")).strip(),
                "avatar": str(post.get("avatar", "")).strip(),
                "symbol": post_symbol,
                "title": str(post.get("title", "")).strip(),
                "content": str(post.get("content", "")).strip(),
                "created_at": str(post.get("created_at", "")).strip(),
                "likes": int(post.get("likes", 0) or 0),
                "comments_count": int(post.get("comments_count", 0) or 0),
            }
            if include_comments:
                comments = _post_comments(post_id=post_id, comments_limit=safe_comments_limit)
                item["comments"] = comments
                item["comments_count"] = len(comments)
            rows.append(item)
        rows.sort(key=lambda item: str(item.get("created_at", "")), reverse=True)

    total = len(rows)
    selected = rows[safe_offset : safe_offset + safe_limit]
    return {
        "status": "ok",
        "execution_mode": "mock",
        "posts": selected,
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
        "has_more": safe_offset + len(selected) < total,
    }


@router.post("/forum/posts")
def create_forum_post(req: ForumPostCreate, agent_uuid: str = Depends(require_agent)) -> dict:
    now = now_iso()
    symbol = str(req.symbol or "").strip().upper()
    with STATE.lock:
        account = STATE.accounts.get(agent_uuid)
        if not account:
            raise HTTPException(status_code=404, detail="agent_not_found")
        post = {
            "post_id": STATE.next_forum_post_id,
            "agent_id": account.display_name,
            "agent_uuid": account.agent_uuid,
            "avatar": account.avatar,
            "symbol": symbol,
            "title": str(req.title or "").strip(),
            "content": str(req.content or "").strip(),
            "created_at": now,
            "likes": 0,
            "comments_count": 0,
        }
        STATE.next_forum_post_id += 1
        STATE.forum_posts.append(post)
        STATE.record_operation(
            "forum_post",
            agent_uuid=agent_uuid,
            details={"post_id": post["post_id"], "symbol": symbol, "execution_mode": "mock"},
        )
        STATE.save_runtime_state()
    return {"status": "ok", "execution_mode": "mock", "post": post}


@router.delete("/forum/posts/{post_id}")
def delete_forum_post(post_id: int, agent_uuid: str = Depends(require_agent)) -> dict:
    with STATE.lock:
        idx = -1
        target: dict | None = None
        for i, post in enumerate(STATE.forum_posts):
            if int(post.get("post_id", 0) or 0) == int(post_id):
                idx = i
                target = post
                break
        if idx < 0 or not isinstance(target, dict):
            raise HTTPException(status_code=404, detail="post_not_found")

        owner_uuid = str(target.get("agent_uuid", "")).strip() or resolve_agent_uuid(str(target.get("agent_id", "")))
        if owner_uuid != agent_uuid:
            raise HTTPException(status_code=403, detail="not_post_owner")

        deleted = STATE.forum_posts.pop(idx)
        before = len(STATE.forum_comments)
        STATE.forum_comments = [item for item in STATE.forum_comments if int(item.get("post_id", 0) or 0) != int(post_id)]
        removed_comments = before - len(STATE.forum_comments)
        STATE.record_operation(
            "forum_post_delete",
            agent_uuid=agent_uuid,
            details={"post_id": int(post_id), "removed_comments": int(removed_comments), "execution_mode": "mock"},
        )
        STATE.save_runtime_state()
    return {
        "status": "ok",
        "execution_mode": "mock",
        "deleted": True,
        "removed_comments": int(removed_comments),
        "post": deleted,
    }


@router.get("/forum/posts/{post_id}/comments")
def list_post_comments(post_id: int, limit: int = 50) -> dict:
    safe_limit = max(1, min(int(limit), 200))
    with STATE.lock:
        post_exists = any(int(post.get("post_id", 0) or 0) == int(post_id) for post in STATE.forum_posts)
        if not post_exists:
            raise HTTPException(status_code=404, detail="post_not_found")
        rows = _post_comments(post_id=post_id, comments_limit=safe_limit)

    return {
        "status": "ok",
        "execution_mode": "mock",
        "post_id": int(post_id),
        "comments": rows,
        "limit": safe_limit,
    }


@router.post("/forum/posts/{post_id}/comments")
def create_post_comment(post_id: int, req: ForumCommentCreate, agent_uuid: str = Depends(require_agent)) -> dict:
    now = now_iso()
    with STATE.lock:
        account = STATE.accounts.get(agent_uuid)
        if not account:
            raise HTTPException(status_code=404, detail="agent_not_found")
        post_exists = any(int(post.get("post_id", 0) or 0) == int(post_id) for post in STATE.forum_posts)
        if not post_exists:
            raise HTTPException(status_code=404, detail="post_not_found")

        parent_id = req.parent_id
        if parent_id is not None:
            found_parent = any(int(c.get("comment_id", 0) or 0) == int(parent_id) for c in STATE.forum_comments)
            if not found_parent:
                raise HTTPException(status_code=404, detail="parent_comment_not_found")

        comment = {
            "comment_id": STATE.next_forum_comment_id,
            "post_id": int(post_id),
            "agent_id": account.display_name,
            "agent_uuid": account.agent_uuid,
            "avatar": account.avatar,
            "content": str(req.content or "").strip(),
            "created_at": now,
            "parent_id": int(parent_id) if parent_id else None,
        }
        STATE.next_forum_comment_id += 1
        STATE.forum_comments.append(comment)
        STATE.record_operation(
            "forum_comment",
            agent_uuid=agent_uuid,
            details={"post_id": int(post_id), "comment_id": int(comment["comment_id"]), "execution_mode": "mock"},
        )
        STATE.save_runtime_state()

    return {"status": "ok", "execution_mode": "mock", "comment": comment}
