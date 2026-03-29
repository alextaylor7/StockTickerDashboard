import dash
from dash import Input, Output, State, callback, no_update
import random
import plotly.graph_objects as go
from constants import commodities, COMMODITY_BAR_COLORS, CHART_BG, CHART_TEXT

from session_persistence import save_session
from callbacks.user_callbacks import ANONYMOUS_USER_KEY, _net_value, count_named_players

# Initialize stock prices with default values
stock_prices = {commodity: 1.00 for commodity in commodities}


def build_stock_graph_figure(stock_prices_dict):
    x = list(commodities)
    y = [stock_prices_dict[c] for c in commodities]
    colors = [COMMODITY_BAR_COLORS[c] for c in commodities]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=x,
            y=y,
            marker_color=colors,
            marker_line=dict(color="rgba(0,0,0,0.35)", width=1),
        )
    )
    fig.update_layout(
        title=dict(text="Stock Prices", font=dict(color=CHART_TEXT, size=22)),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color=CHART_TEXT, size=16),
        margin=dict(l=56, r=28, t=64, b=52),
        yaxis=dict(
            range=[0, 2],
            gridcolor="rgba(255,255,255,0.15)",
            zerolinecolor="rgba(255,255,255,0.25)",
            tickfont=dict(size=16),
            title=dict(text="Price", font=dict(size=16)),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=15),
        ),
    )
    return fig


def _timeline_base_layout(title: str, y_title: str):
    return dict(
        title=dict(text=title, font=dict(color=CHART_TEXT, size=22)),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color=CHART_TEXT, size=16),
        margin=dict(l=56, r=28, t=64, b=52),
        legend=dict(font=dict(color=CHART_TEXT, size=14)),
        xaxis=dict(
            title=dict(text="Completed turn", font=dict(size=14)),
            gridcolor="rgba(255,255,255,0.15)",
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=14)),
            gridcolor="rgba(255,255,255,0.15)",
            zerolinecolor="rgba(255,255,255,0.25)",
            tickfont=dict(size=14),
        ),
    )


def build_player_net_timeline_figure(timeline: list) -> go.Figure:
    fig = go.Figure()
    if not isinstance(timeline, list) or len(timeline) == 0:
        fig.update_layout(**_timeline_base_layout("Player net value", "Net value ($)"))
        return fig

    turns = [p["turn"] for p in timeline if isinstance(p, dict)]
    names: set[str] = set()
    for p in timeline:
        if isinstance(p, dict) and isinstance(p.get("player_net"), dict):
            names.update(p["player_net"].keys())
    for name in sorted(names):
        ys = []
        for p in timeline:
            if not isinstance(p, dict):
                ys.append(None)
                continue
            pn = p.get("player_net") if isinstance(p.get("player_net"), dict) else {}
            v = pn.get(name)
            ys.append(v if v is not None else None)
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=ys,
                mode="lines+markers",
                name=name,
                connectgaps=False,
            )
        )
    fig.update_layout(**_timeline_base_layout("Player net value", "Net value ($)"))
    return fig


def build_commodity_timeline_figure(timeline: list) -> go.Figure:
    fig = go.Figure()
    if not isinstance(timeline, list) or len(timeline) == 0:
        fig.update_layout(**_timeline_base_layout("Commodity prices (end of turn)", "Price ($)"))
        return fig

    turns = [p["turn"] for p in timeline if isinstance(p, dict)]
    for c in commodities:
        ys = []
        for p in timeline:
            if not isinstance(p, dict):
                ys.append(None)
                continue
            sp = p.get("stock_prices") if isinstance(p.get("stock_prices"), dict) else {}
            ys.append(sp.get(c))
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=ys,
                mode="lines+markers",
                name=c,
                line=dict(color=COMMODITY_BAR_COLORS.get(c, "#cccccc")),
                connectgaps=False,
            )
        )
    fig.update_layout(**_timeline_base_layout("Commodity prices (end of turn)", "Price ($)"))
    return fig


def roll_dice():
    stock = random.choice(commodities)
    action = random.choice(["Up", "Down", "Dividend"])
    value = random.choice([0.05, 0.10, 0.20])
    return stock, action, value


def _apply_one_roll(stock, action, value):
    """Apply one dice outcome to module globals, USER_STATE, and server.config; persist."""
    global stock_prices

    if action == "Up":
        stock_prices[stock] = round(stock_prices[stock] + value, 2)
    elif action == "Down":
        stock_prices[stock] = round(max(0, stock_prices[stock] - value), 2)

    server = dash.get_app().server
    user_state = server.config.setdefault("USER_STATE", {})

    if action == "Dividend" and stock_prices[stock] >= 1.00:
        for _username, state in user_state.items():
            if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                shares = int(state["stocks"].get(stock, 0))
                cash = round(shares * value, 2)
                state["balance"] = round(float(state.get("balance", 0)) + cash, 2)

    if stock_prices[stock] >= 2.00:
        for _username, state in user_state.items():
            if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                state["stocks"][stock] = int(state["stocks"].get(stock, 0)) * 2
        stock_prices[stock] = 1.00
    elif stock_prices[stock] <= 0:
        for _username, state in user_state.items():
            if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                state["stocks"][stock] = 0
        stock_prices[stock] = 1.00

    stock_prices = {commodity: round(price, 2) for commodity, price in stock_prices.items()}
    server.config["STOCK_PRICES"] = stock_prices
    save_session(dash.get_app())


def _roll_once_outputs():
    stock, action, value = roll_dice()
    _apply_one_roll(stock, action, value)
    fig = build_stock_graph_figure(stock_prices)
    return (
        [{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
        stock,
        action,
        f"{value:.2f}",
        fig,
    )


def _player_roll_count() -> int:
    """Rolls per turn = number of named players (excludes __anonymous__)."""
    server = dash.get_app().server
    user_state = server.config.get("USER_STATE")
    return count_named_players(user_state)


def _play_turn_button_disabled(players: int, seq_data) -> bool:
    """Disabled when no named players or while a multi-roll turn is in progress."""
    if players <= 0:
        return True
    return _sequence_remaining(seq_data) > 0


def _sequence_remaining(seq_data):
    if not isinstance(seq_data, dict):
        return 0
    try:
        return max(0, int(seq_data.get("remaining", 0)))
    except (TypeError, ValueError):
        return 0


def _append_turn_timeline_snapshot():
    """Record completed-turn prices and player net values (before TURN_COUNT increments)."""
    global stock_prices
    server = dash.get_app().server
    completed_turn = int(server.config.get("TURN_COUNT", 1))
    stored = server.config.get("STOCK_PRICES")
    if isinstance(stored, dict):
        prices = {c: round(float(stored.get(c, 1.00)), 2) for c in commodities}
    else:
        prices = {c: round(float(stock_prices.get(c, 1.00)), 2) for c in commodities}

    user_state = server.config.get("USER_STATE") or {}
    player_net: dict[str, float] = {}
    for username, state in user_state.items():
        if username == ANONYMOUS_USER_KEY or not isinstance(state, dict):
            continue
        stocks = state.get("stocks")
        if not isinstance(stocks, dict):
            stocks = {}
        player_net[username] = _net_value(
            float(state.get("balance", 0)),
            stocks,
            prices,
        )

    entry = {"turn": completed_turn, "stock_prices": prices, "player_net": player_net}
    tl = server.config.setdefault("TURN_TIMELINE", [])
    tl.append(entry)


def _increment_turn_and_save():
    """After a full turn's rolls finish, advance the 1-based turn label for the button."""
    _append_turn_timeline_snapshot()
    server = dash.get_app().server
    server.config["TURN_COUNT"] = int(server.config.get("TURN_COUNT", 1)) + 1
    save_session(dash.get_app())


def _timeline_figures_from_server():
    server = dash.get_app().server
    tl = server.config.get("TURN_TIMELINE")
    if not isinstance(tl, list):
        tl = []
    return build_player_net_timeline_figure(tl), build_commodity_timeline_figure(tl)


def _hydrate_dashboard_from_server():
    """Rebuild module stock_prices and figure from server.config (after load or navigation)."""
    global stock_prices
    stored_prices = dash.get_app().server.config.get("STOCK_PRICES")
    if isinstance(stored_prices, dict):
        stock_prices = {
            commodity: round(float(stored_prices.get(commodity, 1.00)), 2) for commodity in commodities
        }
    else:
        stock_prices = {commodity: round(price, 2) for commodity, price in stock_prices.items()}

    fig = build_stock_graph_figure(stock_prices)
    pn_fig, co_fig = _timeline_figures_from_server()
    return (
        [{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
        "",
        "",
        "",
        fig,
        None,
        True,
        pn_fig,
        co_fig,
    )


def _pathname_is_dashboard(pathname) -> bool:
    if not pathname:
        return False
    return pathname.rstrip("/") == "/dashboard"


@callback(
    [
        Output("stock-table", "data"),
        Output("rolled-stock-value", "children"),
        Output("rolled-action-value", "children"),
        Output("rolled-value-value", "children"),
        Output("stock-graph", "figure"),
        Output("turn-sequence-store", "data"),
        Output("turn-roll-interval", "disabled"),
        Output("player-net-timeline-graph", "figure"),
        Output("commodity-timeline-graph", "figure"),
    ],
    [
        Input("roll-btn", "n_clicks"),
        Input("turn-roll-interval", "n_intervals"),
        Input("_initial_load", "data"),
        Input("session-reload", "data"),
        Input("url", "pathname"),
    ],
    State("turn-sequence-store", "data"),
    prevent_initial_call=False,
)
def update_dashboard(n_roll, _n_interval, _initial_load_data, _session_reload, pathname, seq_data):
    global stock_prices

    ctx = dash.callback_context
    triggered_ids = [t["prop_id"].split(".")[0] for t in ctx.triggered if t.get("prop_id")]

    if not ctx.triggered:
        return _hydrate_dashboard_from_server()

    interval_fired = "turn-roll-interval" in triggered_ids
    roll_fired = any("roll-btn" in t.get("prop_id", "") for t in ctx.triggered)

    if interval_fired:
        rem = _sequence_remaining(seq_data)
        if rem <= 0:
            return (no_update,) * 9
        table, rs, ra, rv, fig = _roll_once_outputs()
        new_rem = rem - 1
        if new_rem <= 0:
            _increment_turn_and_save()
            pn_fig, co_fig = _timeline_figures_from_server()
            return (table, rs, ra, rv, fig, None, True, pn_fig, co_fig)
        return (table, rs, ra, rv, fig, {"remaining": new_rem}, False, no_update, no_update)

    if roll_fired and n_roll and n_roll > 0:
        if _sequence_remaining(seq_data) > 0:
            return (no_update,) * 9
        p = _player_roll_count()
        if p <= 0:
            return (no_update,) * 9
        table, rs, ra, rv, fig = _roll_once_outputs()
        rem_after = p - 1
        if rem_after <= 0:
            _increment_turn_and_save()
            pn_fig, co_fig = _timeline_figures_from_server()
            return (table, rs, ra, rv, fig, None, True, pn_fig, co_fig)
        return (table, rs, ra, rv, fig, {"remaining": rem_after}, False, no_update, no_update)

    if "url" in triggered_ids and _pathname_is_dashboard(pathname):
        return _hydrate_dashboard_from_server()

    if any(x in triggered_ids for x in ("_initial_load", "session-reload")):
        return _hydrate_dashboard_from_server()

    return (no_update,) * 9


@callback(
    Output("player-counter-display", "children"),
    Input("stock-prices-poll", "n_intervals"),
    Input("turn-sequence-store", "data"),
    Input("url", "pathname"),
)
def update_player_counter_display(_poll_n, _seq_data, pathname):
    if not _pathname_is_dashboard(pathname):
        return no_update
    players = count_named_players(dash.get_app().server.config.get("USER_STATE"))
    return f"Players: {players}"


@callback(
    Output("roll-btn", "disabled"),
    Output("roll-btn", "children"),
    Input("stock-prices-poll", "n_intervals"),
    Input("turn-sequence-store", "data"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def sync_roll_btn(_poll_n, seq_data, pathname):
    """Button label is Turn N (1-based); updates when a turn completes and the sequence store clears."""
    if not _pathname_is_dashboard(pathname):
        return True, no_update
    server = dash.get_app().server
    turn_num = int(server.config.get("TURN_COUNT", 1))
    label = f"Turn {turn_num}"
    users = server.config.get("USER_STATE")
    players = count_named_players(users)
    disabled = _play_turn_button_disabled(players, seq_data)
    return disabled, label
