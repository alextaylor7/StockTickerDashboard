import urllib
import dash
from dash import Input, Output, State, callback, no_update
from constants import commodities, user_starting_balance

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


def remove_named_player_everywhere(username: str) -> None:
    """Remove a named user from USER_STATE and scrub TURN_TIMELINE player_net; persist."""
    if not username or username == ANONYMOUS_USER_KEY:
        return
    server = dash.get_app().server
    user_state = server.config.setdefault("USER_STATE", {})
    user_state.pop(username, None)
    tl = server.config.get("TURN_TIMELINE")
    if isinstance(tl, list):
        for entry in tl:
            if isinstance(entry, dict):
                pn = entry.get("player_net")
                if isinstance(pn, dict) and username in pn:
                    pn.pop(username, None)

    from session_persistence import save_session

    save_session(dash.get_app())


def _parse_username(search):
    if not search:
        return ""
    query_params = urllib.parse.parse_qs(search.lstrip("?"))
    return query_params.get("name", [""])[0].strip()


def _default_user_state():
    return {
        "balance": float(user_starting_balance),
        "stocks": {commodity: 0 for commodity in commodities}
    }


def _normalize_user_state(user_state):
    normalized_stocks = {commodity: 0 for commodity in commodities}
    for commodity in commodities:
        normalized_stocks[commodity] = int(user_state.get("stocks", {}).get(commodity, 0))

    return {
        "balance": round(float(user_state.get("balance", user_starting_balance)), 2),
        "stocks": normalized_stocks
    }


def _get_stock_prices():
    stored_prices = dash.get_app().server.config.get("STOCK_PRICES", {})
    return {commodity: round(float(stored_prices.get(commodity, 1.00)), 2) for commodity in commodities}


def _to_table_data(stocks):
    return [{"Commodity": commodity, "Shares": stocks.get(commodity, 0)} for commodity in commodities]


def _net_value(balance, stocks, stock_prices):
    holdings_value = sum(stocks.get(commodity, 0) * stock_prices.get(commodity, 1.00) for commodity in commodities)
    return round(balance + holdings_value, 2)


def _get_user_state_store():
    """In-memory portfolios keyed by username; resets when the server process restarts."""
    server = dash.get_app().server
    if "USER_STATE" not in server.config:
        server.config["USER_STATE"] = {}
    return server.config["USER_STATE"]


@callback(
    Output("user-stock-table", "data"),
    Output("user-balance", "children"),
    Output("user-net-value", "children"),
    Output("transaction-message", "children"),
    Input("url", "search"),
    Input("stock-prices-store", "data"),
    Input("buy-100-btn", "n_clicks"),
    Input("buy-500-btn", "n_clicks"),
    Input("buy-1000-btn", "n_clicks"),
    Input("buy-5000-btn", "n_clicks"),
    Input("sell-100-btn", "n_clicks"),
    Input("sell-500-btn", "n_clicks"),
    Input("sell-1000-btn", "n_clicks"),
    Input("sell-5000-btn", "n_clicks"),
    Input("add-cash-btn", "n_clicks"),
    Input("remove-cash-btn", "n_clicks"),
    State("selected-commodity-store", "data"),
    State("cash-input", "value"),
)
def handle_user_actions(
    search,
    _stock_prices_store_data,
    buy100, buy500, buy1000, buy5000,
    sell100, sell500, sell1000, sell5000,
    add_cash_clicks,
    remove_cash_clicks,
    stock, cash_amount,
):
    ctx = dash.callback_context
    triggered_props = [t["prop_id"] for t in ctx.triggered] if ctx.triggered else []
    if not triggered_props:
        url_hydrate = True
        poll_refresh = False
    else:
        url_hydrate = any(
            tp in ("", ".") or tp.startswith("url.") for tp in triggered_props
        )
        poll_refresh = any(tp.startswith("stock-prices-store") for tp in triggered_props)

    username = _parse_username(search)
    user_key = username or ANONYMOUS_USER_KEY
    all_users = _get_user_state_store()

    if user_key not in all_users:
        all_users[user_key] = _default_user_state()
    else:
        all_users[user_key] = _normalize_user_state(all_users[user_key])

    current_state = all_users[user_key]
    stock_prices = _get_stock_prices()

    # Hydration vs poll vs actions (URL takes precedence if both fire on initial load)
    message = ""
    if url_hydrate:
        net_value = _net_value(current_state["balance"], current_state["stocks"], stock_prices)
        return (
            _to_table_data(current_state["stocks"]),
            f"Balance: ${current_state['balance']:.2f}",
            f"Net Value: ${net_value:.2f}",
            message,
        )

    if poll_refresh:
        net_value = _net_value(current_state["balance"], current_state["stocks"], stock_prices)
        return (
            _to_table_data(current_state["stocks"]),
            f"Balance: ${current_state['balance']:.2f}",
            f"Net Value: ${net_value:.2f}",
            no_update,
        )

    # Action triggered: buy/sell/add cash
    action_id = ctx.triggered[0]["prop_id"].split(".")[0]  # component id
    if action_id == "add-cash-btn":
        if cash_amount is None:
            message = "Enter a valid cash amount greater than 0."
        else:
            # Truncate decimals to an integer amount.
            amount = int(float(cash_amount))
            if amount <= 0:
                message = "Enter a valid cash amount greater than 0."
            else:
                current_state["balance"] = round(current_state["balance"] + amount, 2)
                message = f"Added ${amount:.2f} to your balance."
    elif action_id == "remove-cash-btn":
        if cash_amount is None:
            message = "Enter a valid cash amount greater than 0."
        else:
            amount = int(float(cash_amount))
            if amount <= 0:
                message = "Enter a valid cash amount greater than 0."
            elif current_state["balance"] < amount:
                message = "Not enough balance to remove that amount."
            else:
                current_state["balance"] = round(current_state["balance"] - amount, 2)
                message = f"Removed ${amount:.2f} from your balance."
    else:
        if not stock:
            message = "Select a stock first."
        else:
            amount = int(action_id.split("-")[1])  # e.g. buy-500-btn -> 500
            transaction_type = action_id.split("-")[0]  # buy or sell
            price = stock_prices.get(stock, 1.00)
            cost = round(amount * price, 2)

            if transaction_type == "buy" and current_state["balance"] >= cost:
                current_state["stocks"][stock] += amount
                current_state["balance"] = round(current_state["balance"] - cost, 2)
                message = f"Bought {amount} shares of {stock} for ${cost:.2f}"
            elif transaction_type == "sell" and current_state["stocks"][stock] >= amount:
                current_state["stocks"][stock] -= amount
                current_state["balance"] = round(current_state["balance"] + cost, 2)
                message = f"Sold {amount} shares of {stock} for ${cost:.2f}"

    all_users[user_key] = current_state
    net_value = _net_value(current_state["balance"], current_state["stocks"], stock_prices)

    from session_persistence import schedule_debounced_save

    schedule_debounced_save(dash.get_app())

    return (
        _to_table_data(current_state["stocks"]),
        f"Balance: ${current_state['balance']:.2f}",
        f"Net Value: ${net_value:.2f}",
        message,
    )


@callback(
    Output("profile-name", "children"),
    Input("url", "search")
)
def display_user_info(search):
    name = _parse_username(search)
    if not name:
        return "User Profile"
    return f"{name}'s Profile"


@callback(
    Output("selected-commodity-store", "data"),
    Output("selected-commodity-display", "children"),
    Input("user-stock-table", "active_cell"),
    State("user-stock-table", "data"),
    prevent_initial_call=True,
)
def select_commodity_from_table(active_cell, data):
    if not active_cell or data is None:
        return no_update, no_update
    row = active_cell.get("row")
    if row is None or row < 0 or row >= len(data):
        return no_update, no_update
    commodity = data[row].get("Commodity")
    if not commodity:
        return no_update, no_update
    return commodity, commodity