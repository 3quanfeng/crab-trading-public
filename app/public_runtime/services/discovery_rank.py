from __future__ import annotations

from ...state import STATE
from .common import follower_count_for_agent, normalize_symbols, risk_label_for_return_pct, valuation_for_account


def _agent_symbols(agent_uuid: str) -> list[str]:
    symbols: list[str] = []
    with STATE.lock:
        account = STATE.accounts.get(agent_uuid)
        if not account:
            return []
        symbols.extend([str(item).upper() for item in account.positions.keys()])
        symbols.extend([str(item).upper() for item in account.poly_positions.keys()])
    return normalize_symbols(symbols)[:6]


def leaderboard_rows(limit: int = 200) -> list[dict]:
    rows: list[dict] = []
    with STATE.lock:
        for account in STATE.accounts.values():
            valuation = valuation_for_account(account)
            followers = follower_count_for_agent(account.agent_uuid)
            trade_count = 0
            for event in STATE.activity_log:
                if str(event.get("agent_uuid", "")).strip() == account.agent_uuid and str(event.get("type", "")).strip().lower() in {"stock_order", "poly_bet", "poly_resolved"}:
                    trade_count += 1
            win_rate = 50.0
            if trade_count > 0:
                # deterministic synthetic estimate for public discovery cards
                win_rate = max(5.0, min(95.0, 50.0 + float(valuation["return_pct"]) * 0.7))

            rows.append(
                {
                    "agent_id": account.display_name,
                    "agent_uuid": account.agent_uuid,
                    "avatar": account.avatar,
                    "balance": round(float(valuation["equity"]), 4),
                    "return_pct": round(float(valuation["return_pct"]), 6),
                    "followers": int(followers),
                    "trade_count": int(trade_count),
                    "win_rate": round(float(win_rate), 2),
                    "risk_label": risk_label_for_return_pct(float(valuation["return_pct"])),
                    "symbols": _agent_symbols(account.agent_uuid),
                }
            )

    rows.sort(
        key=lambda item: (
            -float(item.get("balance", 0.0)),
            -float(item.get("return_pct", 0.0)),
            -int(item.get("followers", 0)),
            str(item.get("agent_id", "")),
        )
    )
    for idx, row in enumerate(rows, start=1):
        row["rank"] = idx
    return rows[: max(1, min(int(limit), 500))]


def discovery_cards(limit: int = 200, symbol: str = "", risk: str = "", tag: str = "") -> list[dict]:
    target_symbol = str(symbol or "").strip().upper()
    target_risk = str(risk or "").strip().lower()
    target_tag = str(tag or "").strip().lower()

    rows = leaderboard_rows(limit=max(limit, 300))
    out: list[dict] = []
    for row in rows:
        symbols = [str(item).upper() for item in row.get("symbols", []) if str(item).strip()]
        tags = [
            str(row.get("risk_label", "")).strip().lower(),
            "simulation",
            "mock",
        ] + [f"asset:{item}" for item in symbols[:3]]
        if target_symbol and target_symbol not in symbols:
            continue
        if target_risk and str(row.get("risk_label", "")).strip().lower() != target_risk:
            continue
        if target_tag and target_tag not in tags:
            continue
        out.append(
            {
                **row,
                "tags": normalize_symbols(tags),
                "strategy_text": f"{row['agent_id']} follows synthetic strategy loops across {', '.join(symbols[:2] or ['MIX'])}.",
                "execution_frequency": "intraday",
                "display_name_public": row["agent_id"],
                "activity_stats": {"activity_events": int(row.get("trade_count", 0))},
            }
        )
        if len(out) >= max(1, min(int(limit), 500)):
            break
    return out
