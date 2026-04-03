"""User portfolio shape, naming, and net value (no Dash / persistence)."""

from constants import COMMODITIES, USER_STARTING_BALANCE

ANONYMOUS_USER_KEY = "__anonymous__"


def count_named_players(user_state) -> int:
    """Count USER_STATE keys except the shared anonymous portfolio."""
    if not isinstance(user_state, dict):
        return 0
    return sum(1 for k in user_state if k != ANONYMOUS_USER_KEY)


def named_player_names(user_state) -> list[str]:
    """Sorted USER_STATE keys excluding the shared anonymous portfolio (modal list source)."""
    if not isinstance(user_state, dict):
        return []
    return sorted(k for k in user_state if k != ANONYMOUS_USER_KEY)


def default_user_state() -> dict:
    return {
        "balance": float(USER_STARTING_BALANCE),
        "stocks": {commodity: 0 for commodity in COMMODITIES},
    }


def normalize_user_state(user_state: dict) -> dict:
    normalized_stocks = {commodity: 0 for commodity in COMMODITIES}
    for commodity in COMMODITIES:
        normalized_stocks[commodity] = int(user_state.get("stocks", {}).get(commodity, 0))

    return {
        "balance": round(float(user_state.get("balance", USER_STARTING_BALANCE)), 2),
        "stocks": normalized_stocks,
    }


def net_value(balance, stocks, stock_prices) -> float:
    holdings_value = sum(
        stocks.get(commodity, 0) * stock_prices.get(commodity, 1.00) for commodity in COMMODITIES
    )
    return round(balance + holdings_value, 2)
