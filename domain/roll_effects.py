"""Apply one dice outcome to price and user_state dicts (mutates in place)."""

from constants import COMMODITIES


def apply_roll_to_state(
    prices: dict[str, float],
    user_state: dict,
    stock: str,
    action: str,
    value: float,
) -> None:
    for c in COMMODITIES:
        prices.setdefault(c, round(1.00, 2))

    if action == "Up":
        prices[stock] = round(prices[stock] + value, 2)
    elif action == "Down":
        prices[stock] = round(max(0, prices[stock] - value), 2)

    if action == "Dividend" and prices[stock] >= 1.00:
        for _username, state in user_state.items():
            if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                shares = int(state["stocks"].get(stock, 0))
                cash = round(shares * value, 2)
                state["balance"] = round(float(state.get("balance", 0)) + cash, 2)

    if prices[stock] >= 2.00:
        for _username, state in user_state.items():
            if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                state["stocks"][stock] = int(state["stocks"].get(stock, 0)) * 2
        prices[stock] = 1.00
    elif prices[stock] <= 0:
        for _username, state in user_state.items():
            if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                state["stocks"][stock] = 0
        prices[stock] = 1.00

    for c in COMMODITIES:
        prices[c] = round(float(prices.get(c, 1.00)), 2)
