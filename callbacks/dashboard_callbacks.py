import time

import dash
from dash import Input, Output, State, callback, no_update, set_props, ALL, html
import random
import plotly.graph_objects as go
from constants import (
    CHART_BG,
    CHART_TEXT,
    COMMODITY_BAR_COLORS,
    COMMODITY_TIMELINE_LINE_COLORS,
    commodities,
    user_starting_balance,
)

from session_persistence import save_session, _normalize_turn_roll_interval_sec
from callbacks.user_callbacks import (
    ANONYMOUS_USER_KEY,
    _net_value,
    count_named_players,
    named_player_names,
    remove_named_player_everywhere,
)

# Initialize stock prices with default values
stock_prices = {commodity: 1.00 for commodity in commodities}


def _turn_baseline_stock_prices(server) -> dict:
    """Dollar prices at end of last completed turn; par $1.00 when timeline is empty."""
    tl = server.config.get("TURN_TIMELINE")
    if not isinstance(tl, list) or len(tl) == 0:
        return {c: round(1.00, 2) for c in commodities}
    last = tl[-1]
    if not isinstance(last, dict):
        return {c: round(1.00, 2) for c in commodities}
    sp = last.get("stock_prices")
    if not isinstance(sp, dict):
        return {c: round(1.00, 2) for c in commodities}
    return {c: round(float(sp.get(c, 1.00)), 2) for c in commodities}


def _dashboard_table_rows(stock_prices_dict: dict, baseline_prices: dict | None = None) -> list[dict]:
    """Table shows Price as value×100 and ChangeThisTurn vs baseline (×100); storage stays in dollars."""
    if baseline_prices is None:
        baseline_prices = {c: round(1.00, 2) for c in commodities}
    rows: list[dict] = []
    for k, v in stock_prices_dict.items():
        cur = int(round(float(v) * 100))
        base = int(round(float(baseline_prices.get(k, 1.00)) * 100))
        rows.append(
            {
                "Commodity": k,
                "Price": cur,
                "ChangeThisTurn": cur - base,
            }
        )
    return rows


def build_stock_graph_figure(stock_prices_dict):
    x = list(commodities)
    y = [stock_prices_dict[c] * 100 for c in commodities]
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
            range=[0, 200],
            gridcolor="rgba(255,255,255,0.15)",
            zerolinecolor="rgba(255,255,255,0.25)",
            tickfont=dict(size=16),
            title=dict(text="Price (×100)", font=dict(size=16)),
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
            title=dict(text="Turn", font=dict(size=14)),
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
        fig.update_layout(**_timeline_base_layout("Player Net Value", "Net Value ($)"))
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
    fig.update_layout(**_timeline_base_layout("Player Net Value", "Net Value ($)"))
    return fig


def build_commodity_timeline_figure(timeline: list) -> go.Figure:
    fig = go.Figure()
    if not isinstance(timeline, list) or len(timeline) == 0:
        fig.update_layout(**_timeline_base_layout("Commodity Prices", "Price (×100)"))
        return fig

    turns = [p["turn"] for p in timeline if isinstance(p, dict)]
    for c in commodities:
        ys = []
        for p in timeline:
            if not isinstance(p, dict):
                ys.append(None)
                continue
            sp = p.get("stock_prices") if isinstance(p.get("stock_prices"), dict) else {}
            raw = sp.get(c)
            ys.append(raw * 100 if raw is not None else None)
        line_color = COMMODITY_TIMELINE_LINE_COLORS.get(c, "#cccccc")
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=ys,
                mode="lines+markers",
                name=c,
                line=dict(color=line_color, width=2),
                marker=dict(
                    size=8,
                    color=line_color,
                    line=dict(width=1, color="rgba(0,0,0,0.45)"),
                ),
                connectgaps=False,
            )
        )
    fig.update_layout(**_timeline_base_layout("Commodity Prices", "Price (×100)"))
    return fig


def _turn_zero_timeline_entry(server):
    """Starting snapshot: par prices, each named player at starting balance and zero shares."""
    par_prices = {c: round(1.00, 2) for c in commodities}
    zero_stocks = {c: 0 for c in commodities}
    user_state = server.config.get("USER_STATE") or {}
    player_net: dict[str, float] = {}
    for name in named_player_names(user_state):
        player_net[name] = _net_value(
            float(user_starting_balance),
            zero_stocks,
            par_prices,
        )
    return {"turn": 0, "stock_prices": par_prices, "player_net": player_net}


def _timeline_for_figures(server):
    tl = server.config.get("TURN_TIMELINE")
    if not isinstance(tl, list):
        tl = []
    if tl and isinstance(tl[0], dict):
        try:
            if int(tl[0].get("turn")) == 0:
                return tl
        except (TypeError, ValueError):
            pass
    return [_turn_zero_timeline_entry(server), *tl]


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
    server = dash.get_app().server
    return (
        _dashboard_table_rows(stock_prices, _turn_baseline_stock_prices(server)),
        stock,
        action,
        str(int(round(value * 100))),
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
    tl = _timeline_for_figures(server)
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
    ms = (
        _normalize_turn_roll_interval_sec(
            dash.get_app().server.config.get("TURN_ROLL_INTERVAL_SEC")
        )
        * 1000
    )
    set_props("turn-roll-interval", {"interval": ms})
    server = dash.get_app().server
    return (
        _dashboard_table_rows(stock_prices, _turn_baseline_stock_prices(server)),
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


_HIDDEN_SETTINGS_MODAL_STYLE = {
    "display": "none",
    "position": "fixed",
    "inset": "0",
    "zIndex": "1000",
    "alignItems": "center",
    "justifyContent": "center",
    "padding": "24px",
    "boxSizing": "border-box",
}
_VISIBLE_SETTINGS_MODAL_STYLE = {**_HIDDEN_SETTINGS_MODAL_STYLE, "display": "flex"}


def _remove_button_click_value(ctx) -> int:
    """Best n_clicks from triggered props for remove-player-btn (0 if none / not a real click)."""
    for t in ctx.triggered or []:
        pid = str(t.get("prop_id", ""))
        if "remove-player-btn" not in pid or ".n_clicks" not in pid:
            continue
        v = t.get("value")
        try:
            return int(v) if v is not None else 0
        except (TypeError, ValueError):
            return 0
    return 0


def _max_remove_n_clicks(n_clicks_list) -> int:
    """Highest n_clicks across ALL remove buttons (0 when list mounts with all zeros)."""
    if not n_clicks_list:
        return 0
    try:
        return max(int(x or 0) for x in n_clicks_list)
    except (TypeError, ValueError):
        return 0


def _build_players_modal_list_children():
    users = dash.get_app().server.config.get("USER_STATE")
    names = named_player_names(users)
    if not names:
        return html.Div(
            "No named players.",
            style={"fontSize": "clamp(0.95rem, 2vw, 1.05rem)", "color": "#666"},
        )
    row_wrap = {
        "display": "flex",
        "alignItems": "center",
        "justifyContent": "space-between",
        "gap": "12px",
        "padding": "10px 0",
        "borderBottom": "1px solid #eee",
    }
    remove_btn_style = {
        "flex": "0 0 auto",
        "marginLeft": "12px",
        "padding": "8px 14px",
        "fontSize": "0.95rem",
        "fontWeight": "600",
        "border": "none",
        "borderRadius": "8px",
        "backgroundColor": "#dc2626",
        "color": "#ffffff",
        "cursor": "pointer",
    }
    rows = []
    for name in names:
        rows.append(
            html.Div(
                [
                    html.Span(
                        name,
                        style={
                            "fontSize": "clamp(0.95rem, 2vw, 1.05rem)",
                            "color": "#1a1a1a",
                            "flex": "1 1 auto",
                            "minWidth": "0",
                            "wordBreak": "break-word",
                        },
                    ),
                    html.Button(
                        "Remove",
                        id={"type": "remove-player-btn", "name": name},
                        n_clicks=0,
                        style=remove_btn_style,
                    ),
                ],
                style=row_wrap,
            )
        )
    return html.Div(rows)


@callback(
    Output("settings-modal", "style"),
    Output("turn-roll-sec-input", "value"),
    [
        Input("settings-gear-btn", "n_clicks"),
        Input("settings-modal-backdrop-btn", "n_clicks"),
        Input("settings-modal-close-btn", "n_clicks"),
        Input("settings-apply-btn", "n_clicks"),
        Input("url", "pathname"),
        Input("session-reload", "data"),
        Input("_initial_load", "data"),
    ],
    State("turn-roll-sec-input", "value"),
    prevent_initial_call=False,
)
def settings_modal_and_interval(
    _n_gear,
    _n_backdrop,
    _n_close,
    _n_apply,
    pathname,
    _session_reload,
    _initial_load,
    sec_input,
):
    """Modal only. Do not Output turn-roll-interval.interval here — that resets the timer in Dash 3 and drops ticks."""
    ctx = dash.callback_context
    server = dash.get_app().server
    # Dashboard-only layout: never patch these outputs or set_props from other routes (breaks Dash 3 renderer).
    if not _pathname_is_dashboard(pathname):
        return no_update, no_update

    hid, vis = _HIDDEN_SETTINGS_MODAL_STYLE, _VISIBLE_SETTINGS_MODAL_STYLE

    def sec_from_server() -> int:
        return _normalize_turn_roll_interval_sec(server.config.get("TURN_ROLL_INTERVAL_SEC"))

    trig = ctx.triggered_id
    if trig is None:
        return hid, no_update

    if trig == "url":
        return no_update, no_update

    if trig in ("session-reload", "_initial_load"):
        return no_update, no_update

    if trig == "settings-gear-btn":
        s = sec_from_server()
        return vis, s

    if trig in ("settings-modal-backdrop-btn", "settings-modal-close-btn"):
        return hid, no_update

    if trig == "settings-apply-btn":
        sec = _normalize_turn_roll_interval_sec(sec_input)
        server.config["TURN_ROLL_INTERVAL_SEC"] = sec
        save_session(dash.get_app())
        set_props("turn-roll-interval", {"interval": sec * 1000})
        return hid, sec

    return no_update, no_update


@callback(
    Output("players-modal", "style"),
    Output("players-modal-list", "children"),
    [
        Input("player-counter-display", "n_clicks"),
        Input("players-modal-backdrop-btn", "n_clicks"),
        Input("players-modal-close-btn", "n_clicks"),
        Input("url", "pathname"),
        Input("session-reload", "data"),
        Input("_initial_load", "data"),
    ],
    prevent_initial_call=False,
)
def players_modal_open_close(
    _n_counter,
    _n_backdrop,
    _n_close,
    pathname,
    _session_reload,
    _initial_load,
):
    ctx = dash.callback_context
    if not _pathname_is_dashboard(pathname):
        return no_update, no_update

    hid, vis = _HIDDEN_SETTINGS_MODAL_STYLE, _VISIBLE_SETTINGS_MODAL_STYLE

    trig = ctx.triggered_id
    if trig is None:
        return hid, no_update

    if trig == "url":
        return no_update, no_update

    if trig in ("session-reload", "_initial_load"):
        return no_update, no_update

    if trig == "player-counter-display":
        if not _n_counter:
            return no_update, no_update
        return vis, _build_players_modal_list_children()

    if trig in ("players-modal-backdrop-btn", "players-modal-close-btn"):
        return hid, no_update

    return no_update, no_update


@callback(
    Output("players-modal-list", "children", allow_duplicate=True),
    Output("session-reload", "data", allow_duplicate=True),
    Input({"type": "remove-player-btn", "name": ALL}, "n_clicks"),
    Input("url", "pathname"),
    prevent_initial_call=True,
)
def remove_named_player_from_modal(_n_remove_clicks, pathname):
    ctx = dash.callback_context
    if not _pathname_is_dashboard(pathname):
        return no_update, no_update

    trig = ctx.triggered_id
    if trig == "url":
        return no_update, no_update

    # Opening the modal mounts new ALL targets; Dash may fire this callback with n_clicks=0 on every button.
    # Only treat as a user action when some Remove button's n_clicks is >= 1 (avoids removing on open).
    if _max_remove_n_clicks(_n_remove_clicks) < 1 and _remove_button_click_value(ctx) < 1:
        return no_update, no_update

    if not isinstance(trig, dict) or trig.get("type") != "remove-player-btn":
        return no_update, no_update

    username = trig.get("name")
    if not username or username == ANONYMOUS_USER_KEY:
        return no_update, no_update

    remove_named_player_everywhere(username)
    return _build_players_modal_list_children(), time.time()


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
    tp = ctx.triggered_prop_ids

    # Dashboard-only layout: avoid outputs + set_props for missing components (e.g. sign-in /).
    if not _pathname_is_dashboard(pathname):
        return (no_update,) * 9

    if not ctx.triggered:
        return _hydrate_dashboard_from_server()

    interval_fired = "turn-roll-interval.n_intervals" in tp
    roll_fired = "roll-btn.n_clicks" in tp

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

    if "url.pathname" in tp and _pathname_is_dashboard(pathname):
        return _hydrate_dashboard_from_server()

    if ("_initial_load.data" in tp or "session-reload.data" in tp) and _pathname_is_dashboard(
        pathname
    ):
        return _hydrate_dashboard_from_server()

    return (no_update,) * 9


@callback(
    Output("player-counter-display", "children"),
    Input("stock-prices-poll", "n_intervals"),
    Input("turn-sequence-store", "data"),
    Input("session-reload", "data"),
    Input("url", "pathname"),
)
def update_player_counter_display(_poll_n, _seq_data, _session_reload, pathname):
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
