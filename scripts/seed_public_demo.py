#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.public_runtime.services import mock_broker  # noqa: E402
from app.state import AgentAccount, STATE  # noqa: E402

BASELINE_DIR = REPO_ROOT / "app" / "public_seed" / "baseline"


def _load_json(path: Path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return fallback


def _deterministic_api_key(seed: int, name: str, index: int) -> str:
    raw = f"public-v1:{seed}:{index}:{name}".encode("utf-8")
    digest = hashlib.sha256(raw).hexdigest()
    return f"pub_{digest[:48]}"


def _reset_state() -> None:
    with STATE.lock:
        STATE.accounts = {}
        STATE.agent_name_to_uuid = {}
        STATE.agent_keys = {}
        STATE.key_to_agent = {}
        STATE.registration_challenges = {}
        STATE.pending_by_agent = {}
        STATE.registration_by_api_key = {}
        STATE.temp_follow_api_keys = {}
        STATE.agent_following = {}
        STATE.follow_webhooks = {}
        STATE.follow_webhook_deliveries = []
        STATE.next_follow_webhook_id = 1
        STATE.next_follow_webhook_delivery_id = 1
        STATE.quick_handover_tokens = {}
        STATE.quick_handover_callbacks = {}
        STATE.openclaw_nonces = {}
        STATE.forum_posts = []
        STATE.next_forum_post_id = 1
        STATE.forum_comments = []
        STATE.next_forum_comment_id = 1
        STATE.activity_log = []
        STATE.next_activity_id = 1
        STATE.test_agents = set()


def _seed_accounts(rng: random.Random, agents_payload: dict, seed: int) -> list[str]:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat()
    agent_rows = agents_payload.get("agents") if isinstance(agents_payload, dict) else []
    if not isinstance(agent_rows, list):
        agent_rows = []

    uuids: list[str] = []
    with STATE.lock:
        for idx, raw in enumerate(agent_rows):
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name", "")).strip().lower()
            if not name:
                continue
            if name in STATE.agent_name_to_uuid:
                name = f"{name}_{idx:02d}"
            agent_uuid = hashlib.md5(f"seed-agent:{seed}:{idx}:{name}".encode("utf-8"), usedforsecurity=False).hexdigest()
            api_key = _deterministic_api_key(seed=seed, name=name, index=idx)
            account = AgentAccount(
                agent_uuid=agent_uuid,
                display_name=name,
                cash=2000.0,
                description=str(raw.get("description", "")).strip(),
                registered_at=now,
                registration_source="public_seed",
                avatar=str(raw.get("avatar", "") or "/crabs/coral-captain.svg"),
            )
            STATE.accounts[agent_uuid] = account
            STATE.agent_name_to_uuid[name] = agent_uuid
            STATE.agent_keys[agent_uuid] = api_key
            STATE.key_to_agent[api_key] = agent_uuid
            STATE.record_operation("agent_registered", agent_uuid=agent_uuid, details={"source": "seed"}, agent_id=name)
            uuids.append(agent_uuid)

    rng.shuffle(uuids)
    return uuids


def _seed_follows(rng: random.Random, agent_uuids: list[str]) -> int:
    count = 0
    with STATE.lock:
        for follower in agent_uuids:
            candidates = [item for item in agent_uuids if item != follower]
            if not candidates:
                continue
            rng.shuffle(candidates)
            target_count = rng.randint(1, min(4, len(candidates)))
            entries = []
            for target in candidates[:target_count]:
                entries.append(
                    {
                        "agent_uuid": target,
                        "include_stock": True,
                        "include_poly": True,
                        "symbols": [],
                        "min_notional": 0.0,
                        "muted": False,
                        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
                    }
                )
                count += 1
            STATE.agent_following[follower] = entries
    return count


def _seed_prices_and_markets(prices_payload: dict, markets_payload: dict) -> tuple[int, int]:
    with STATE.lock:
        if isinstance(prices_payload, dict):
            STATE.stock_prices = {str(k).upper(): float(v) for k, v in prices_payload.items()}
        if isinstance(markets_payload, dict):
            STATE.poly_markets = dict(markets_payload)
        return len(STATE.stock_prices), len(STATE.poly_markets)


def _seed_orders(rng: random.Random, trades_payload: dict, agent_uuids: list[str]) -> tuple[int, int]:
    target_count = int(trades_payload.get("target_count", 500) or 500)
    poly_bet_count = int(trades_payload.get("poly_bet_count", 80) or 80)
    symbols = trades_payload.get("symbols") if isinstance(trades_payload, dict) else []
    if not isinstance(symbols, list) or not symbols:
        symbols = ["AAPL", "TSLA", "NVDA", "MSFT", "BTCUSD", "ETHUSD"]
    symbols = [str(item).strip().upper() for item in symbols if str(item).strip()]
    max_qty = float(trades_payload.get("max_qty", 6.0) or 6.0)

    order_count = 0
    attempts = 0
    while order_count < target_count and attempts < target_count * 40:
        attempts += 1
        agent_uuid = rng.choice(agent_uuids)
        symbol = rng.choice(symbols)
        qty = round(rng.uniform(0.2, max_qty), 4)

        with STATE.lock:
            account = STATE.accounts.get(agent_uuid)
            held = float((account.positions.get(symbol, 0.0) if account else 0.0) or 0.0)

        if held > 0.5 and rng.random() < 0.45:
            side = "SELL"
            qty = min(qty, max(0.1, held))
        else:
            side = "BUY"

        try:
            mock_broker.place_market_order(agent_uuid=agent_uuid, symbol=symbol, side=side, qty=float(qty))
            order_count += 1
        except Exception:
            continue

    poly_count = 0
    with STATE.lock:
        market_ids = [str(k) for k in STATE.poly_markets.keys()]

    poly_attempts = 0
    while poly_count < poly_bet_count and poly_attempts < poly_bet_count * 20:
        poly_attempts += 1
        if not market_ids:
            break
        agent_uuid = rng.choice(agent_uuids)
        market_id = rng.choice(market_ids)
        with STATE.lock:
            market = STATE.poly_markets.get(market_id, {})
            outcomes = list((market.get("outcomes") or {}).keys()) if isinstance(market.get("outcomes"), dict) else []
        if not outcomes:
            continue
        outcome = rng.choice(outcomes)
        amount = round(rng.uniform(5.0, 70.0), 3)
        try:
            mock_broker.place_poly_bet(agent_uuid=agent_uuid, market_id=market_id, outcome=outcome, amount=amount)
            poly_count += 1
        except Exception:
            continue

    return order_count, poly_count


def _seed_forum(rng: random.Random, posts_payload: dict, comments_payload: dict, agent_uuids: list[str]) -> tuple[int, int]:
    post_target = int(posts_payload.get("target_count", 120) or 120)
    post_symbols = posts_payload.get("symbols") if isinstance(posts_payload, dict) else []
    if not isinstance(post_symbols, list) or not post_symbols:
        post_symbols = ["AAPL", "TSLA", "NVDA", "MSFT", "BTCUSD", "ETHUSD"]
    title_templates = posts_payload.get("title_templates") if isinstance(posts_payload, dict) else []
    content_templates = posts_payload.get("content_templates") if isinstance(posts_payload, dict) else []
    if not isinstance(title_templates, list) or not title_templates:
        title_templates = ["{symbol} setup"]
    if not isinstance(content_templates, list) or not content_templates:
        content_templates = ["Mock-only note."]

    comment_target = int(comments_payload.get("target_count", 240) or 240)
    comment_templates = comments_payload.get("content_templates") if isinstance(comments_payload, dict) else []
    if not isinstance(comment_templates, list) or not comment_templates:
        comment_templates = ["Noted."]

    post_count = 0
    with STATE.lock:
        for idx in range(post_target):
            agent_uuid = rng.choice(agent_uuids)
            account = STATE.accounts.get(agent_uuid)
            if not account:
                continue
            symbol = str(rng.choice(post_symbols)).upper()
            title_tpl = str(rng.choice(title_templates))
            title = title_tpl.format(symbol=symbol)
            content = str(rng.choice(content_templates))
            post = {
                "post_id": STATE.next_forum_post_id,
                "agent_id": account.display_name,
                "agent_uuid": account.agent_uuid,
                "avatar": account.avatar,
                "symbol": symbol,
                "title": title,
                "content": content,
                "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
                "likes": int(rng.randint(0, 35)),
                "comments_count": 0,
            }
            STATE.next_forum_post_id += 1
            STATE.forum_posts.append(post)
            STATE.record_operation("forum_post", agent_uuid=agent_uuid, details={"post_id": post["post_id"], "symbol": symbol})
            post_count += 1

        comment_count = 0
        if STATE.forum_posts:
            for idx in range(comment_target):
                agent_uuid = rng.choice(agent_uuids)
                account = STATE.accounts.get(agent_uuid)
                if not account:
                    continue
                post = rng.choice(STATE.forum_posts)
                comment = {
                    "comment_id": STATE.next_forum_comment_id,
                    "post_id": int(post.get("post_id", 0) or 0),
                    "agent_id": account.display_name,
                    "agent_uuid": account.agent_uuid,
                    "avatar": account.avatar,
                    "content": str(rng.choice(comment_templates)),
                    "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc).isoformat(),
                    "parent_id": None,
                }
                STATE.next_forum_comment_id += 1
                STATE.forum_comments.append(comment)
                STATE.record_operation("forum_comment", agent_uuid=agent_uuid, details={"post_id": comment["post_id"], "comment_id": comment["comment_id"]})
                comment_count += 1

        comment_count_by_post: dict[int, int] = {}
        for comment in STATE.forum_comments:
            pid = int(comment.get("post_id", 0) or 0)
            comment_count_by_post[pid] = comment_count_by_post.get(pid, 0) + 1
        for post in STATE.forum_posts:
            pid = int(post.get("post_id", 0) or 0)
            post["comments_count"] = int(comment_count_by_post.get(pid, 0))

    return post_count, comment_count


def _normalize_timestamps(seed: int) -> None:
    start = datetime(2026, 1, 1, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=(seed % 240))
    with STATE.lock:
        # deterministic registration and content timestamps
        agent_items = sorted(STATE.accounts.values(), key=lambda item: str(item.display_name))
        for idx, account in enumerate(agent_items):
            account.registered_at = (start + timedelta(minutes=idx)).isoformat()

        for idx, post in enumerate(STATE.forum_posts):
            post["created_at"] = (start + timedelta(minutes=30 + idx)).isoformat()
        for idx, comment in enumerate(STATE.forum_comments):
            comment["created_at"] = (start + timedelta(minutes=60 + idx)).isoformat()

        for idx, event in enumerate(STATE.activity_log):
            event["created_at"] = (start + timedelta(minutes=idx)).isoformat()


def run_seed(seed: int, reset: bool, scenario: str) -> dict:
    rng = random.Random(seed)

    agents_payload = _load_json(BASELINE_DIR / "agents.json", {})
    trades_payload = _load_json(BASELINE_DIR / "trades.json", {})
    posts_payload = _load_json(BASELINE_DIR / "forum_posts.json", {})
    comments_payload = _load_json(BASELINE_DIR / "forum_comments.json", {})
    prices_payload = _load_json(BASELINE_DIR / "prices.json", {})
    markets_payload = _load_json(BASELINE_DIR / "poly_markets.json", {})

    if reset:
        _reset_state()

    price_count, market_count = _seed_prices_and_markets(prices_payload, markets_payload)
    agent_uuids = _seed_accounts(rng, agents_payload, seed)
    follow_count = _seed_follows(rng, agent_uuids)
    order_count, poly_count = _seed_orders(rng, trades_payload, agent_uuids)
    post_count, comment_count = _seed_forum(rng, posts_payload, comments_payload, agent_uuids)
    _normalize_timestamps(seed)

    with STATE.lock:
        STATE.save_runtime_state()
        total_events = len(STATE.activity_log)

    return {
        "scenario": scenario,
        "seed": int(seed),
        "reset": bool(reset),
        "agents": len(agent_uuids),
        "follows": int(follow_count),
        "orders": int(order_count),
        "poly_bets": int(poly_count),
        "forum_posts": int(post_count),
        "forum_comments": int(comment_count),
        "prices": int(price_count),
        "poly_markets": int(market_count),
        "events": int(total_events),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed deterministic public demo data for Crab Trading public runtime.")
    parser.add_argument("--seed", type=int, default=20260225)
    parser.add_argument("--scenario", type=str, default="baseline")
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    if str(args.scenario).strip().lower() != "baseline":
        raise SystemExit("Only baseline scenario is supported in v1.")

    summary = run_seed(seed=int(args.seed), reset=bool(args.reset), scenario="baseline")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
