"""Turn timeline entries for dashboard charts (no Dash)."""

from constants import COMMODITIES, USER_STARTING_BALANCE
from domain.user_state import named_player_names, net_value


def turn_baseline_stock_prices(turn_timeline: list | None) -> dict[str, float]:
    """Dollar prices at end of last completed turn; par $1.00 when timeline is empty."""
    tl = turn_timeline if isinstance(turn_timeline, list) else []
    if len(tl) == 0:
        return {c: round(1.00, 2) for c in COMMODITIES}
    last = tl[-1]
    if not isinstance(last, dict):
        return {c: round(1.00, 2) for c in COMMODITIES}
    sp = last.get("stock_prices")
    if not isinstance(sp, dict):
        return {c: round(1.00, 2) for c in COMMODITIES}
    return {c: round(float(sp.get(c, 1.00)), 2) for c in COMMODITIES}


def turn_zero_timeline_entry(user_state: dict) -> dict:
    """Starting snapshot: par prices, each named player at starting balance and zero shares."""
    par_prices = {c: round(1.00, 2) for c in COMMODITIES}
    zero_stocks = {c: 0 for c in COMMODITIES}
    us = user_state if isinstance(user_state, dict) else {}
    player_net: dict[str, float] = {}
    for name in named_player_names(us):
        player_net[name] = net_value(
            float(USER_STARTING_BALANCE),
            zero_stocks,
            par_prices,
        )
    return {"turn": 0, "stock_prices": par_prices, "player_net": player_net}


def timeline_for_figures(turn_timeline: list | None, user_state: dict) -> list:
    tl = turn_timeline if isinstance(turn_timeline, list) else []
    if tl and isinstance(tl[0], dict):
        try:
            if int(tl[0].get("turn")) == 0:
                return tl
        except (TypeError, ValueError):
            pass
    return [turn_zero_timeline_entry(user_state), *tl]
