import time

import dash
from dash import Input, Output, State, no_update, set_props, ALL, html

from callbacks.app_ref import callback
from constants import COMMODITIES

from dashboard_charts import (
    dashboard_table_rows,
    build_commodity_timeline_figure,
    build_player_net_timeline_figure,
    build_stock_graph_figure,
)
from domain.dice import roll_dice
from domain.market_surge import (
    ensure_market_surge_config,
    maybe_bias_roll,
    normalize_market_surge_enabled,
    rotate_turn_state,
)
from domain.roll_effects import apply_roll_to_state
from domain.timeline import timeline_for_figures, turn_baseline_stock_prices
from domain.user_state import (
    ANONYMOUS_USER_KEY,
    count_named_players,
    named_player_names,
    net_value,
)
from callbacks.user_callbacks import remove_named_player_everywhere
from runtime.live_stock_prices import live_prices, normalize_live_prices_round_trip, replace_live_prices
from session_persistence import (
    save_session,
    _normalize_game_max_turns,
    _normalize_turn_roll_interval_sec,
)


def _turn_baseline_stock_prices(server) -> dict:
    """Dollar prices at end of last completed turn; par $1.00 when timeline is empty."""
    return turn_baseline_stock_prices(server.config.get("TURN_TIMELINE"))


def _timeline_for_figures(server):
    return timeline_for_figures(
        server.config.get("TURN_TIMELINE"),
        server.config.get("USER_STATE") or {},
    )


def _apply_one_roll(stock, action, value):
    """Apply one dice outcome to live_prices, USER_STATE, and server.config; persist."""
    server = dash.get_app().server
    action, value = maybe_bias_roll(server, stock, action, value)
    user_state = server.config.setdefault("USER_STATE", {})
    apply_roll_to_state(live_prices, user_state, stock, action, value)
    server.config["STOCK_PRICES"] = {
        c: round(float(live_prices.get(c, 1.00)), 2) for c in COMMODITIES
    }
    save_session(dash.get_app())
    return action, value


def _roll_once_outputs():
    stock, action, value = roll_dice()
    action, value = _apply_one_roll(stock, action, value)
    value_str = str(int(round(value * 100)))
    server = dash.get_app().server
    rolls = server.config.setdefault("CURRENT_TURN_ROLLS", [])
    if not isinstance(rolls, list):
        rolls = []
        server.config["CURRENT_TURN_ROLLS"] = rolls
    rolls.append({"commodity": stock, "action": action, "value": value_str})
    fig = build_stock_graph_figure(live_prices)
    return dashboard_table_rows(live_prices, _turn_baseline_stock_prices(server)), fig


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


def _game_has_ended(server) -> bool:
    turn_num = int(server.config.get("TURN_COUNT", 1))
    max_t = _normalize_game_max_turns(server.config.get("GAME_MAX_TURNS"))
    return turn_num > max_t


def _sequence_remaining(seq_data):
    if not isinstance(seq_data, dict):
        return 0
    try:
        return max(0, int(seq_data.get("remaining", 0)))
    except (TypeError, ValueError):
        return 0


def _append_turn_timeline_snapshot():
    """Record completed-turn prices and player net values (before TURN_COUNT increments)."""
    server = dash.get_app().server
    completed_turn = int(server.config.get("TURN_COUNT", 1))
    stored = server.config.get("STOCK_PRICES")
    if isinstance(stored, dict):
        prices = {c: round(float(stored.get(c, 1.00)), 2) for c in COMMODITIES}
    else:
        prices = {c: round(float(live_prices.get(c, 1.00)), 2) for c in COMMODITIES}

    user_state = server.config.get("USER_STATE") or {}
    player_net: dict[str, float] = {}
    for username, state in user_state.items():
        if username == ANONYMOUS_USER_KEY or not isinstance(state, dict):
            continue
        stocks = state.get("stocks")
        if not isinstance(stocks, dict):
            stocks = {}
        player_net[username] = net_value(
            float(state.get("balance", 0)),
            stocks,
            prices,
        )

    entry = {"turn": completed_turn, "stock_prices": prices, "player_net": player_net}
    tl = server.config.setdefault("TURN_TIMELINE", [])
    tl.append(entry)


def _increment_turn_and_save():
    """After a full turn's rolls finish, advance the 1-based turn label for the button."""
    server = dash.get_app().server
    cur = server.config.get("CURRENT_TURN_ROLLS")
    if not isinstance(cur, list):
        cur = []
    server.config["LAST_TURN_ROLLS"] = [
        {
            "commodity": str(r.get("commodity", "")),
            "action": str(r.get("action", "")),
            "value": str(r.get("value", "")),
        }
        for r in cur
        if isinstance(r, dict)
    ]
    server.config["CURRENT_TURN_ROLLS"] = []
    rotate_turn_state(server)
    _append_turn_timeline_snapshot()
    server.config["TURN_COUNT"] = int(server.config.get("TURN_COUNT", 1)) + 1
    save_session(dash.get_app())


def _timeline_figures_from_server():
    server = dash.get_app().server
    tl = _timeline_for_figures(server)
    return build_player_net_timeline_figure(tl), build_commodity_timeline_figure(tl)


def _turn_rolls_feed_children(server=None):
    if server is None:
        server = dash.get_app().server
    cur = server.config.get("CURRENT_TURN_ROLLS")
    last = server.config.get("LAST_TURN_ROLLS")
    if isinstance(cur, list) and len(cur) > 0:
        rows = cur
    elif isinstance(last, list):
        rows = last
    else:
        rows = []
    # Storage order is oldest→newest; show newest on top.
    feed_font = "system-ui, Segoe UI, sans-serif"
    item_style = {
        "fontSize": "clamp(1.25rem, 2.2vw, 2rem)",
        "fontWeight": "600",
        "lineHeight": "1.35",
        "color": "#111",
        "padding": "10px 0",
        "borderBottom": "1px solid #e8e8e8",
        "fontFamily": feed_font,
    }
    out = []
    for r in reversed(rows):
        if not isinstance(r, dict):
            continue
        c = r.get("commodity", "")
        a = r.get("action", "")
        v = r.get("value", "")
        out.append(html.Div(f"{c}, {a}, {v}", style=item_style))
    return out


def _hydrate_dashboard_from_server():
    """Rebuild live_prices and figures from server.config (after load or navigation)."""
    stored_prices = dash.get_app().server.config.get("STOCK_PRICES")
    if isinstance(stored_prices, dict):
        replace_live_prices(stored_prices)
    else:
        normalize_live_prices_round_trip()

    fig = build_stock_graph_figure(live_prices)
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
        dashboard_table_rows(live_prices, _turn_baseline_stock_prices(server)),
        fig,
        None,
        True,
        pn_fig,
        co_fig,
        _turn_rolls_feed_children(server),
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
    Output("game-max-turns-input", "value"),
    Output("market-surge-checkbox", "value"),
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
    State("game-max-turns-input", "value"),
    State("market-surge-checkbox", "value"),
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
    max_turns_input,
    market_surge_value,
):
    """Modal only. Do not Output turn-roll-interval.interval here — that resets the timer in Dash 3 and drops ticks."""
    ctx = dash.callback_context
    server = dash.get_app().server
    # Dashboard-only layout: never patch these outputs or set_props from other routes (breaks Dash 3 renderer).
    if not _pathname_is_dashboard(pathname):
        return no_update, no_update, no_update, no_update

    hid, vis = _HIDDEN_SETTINGS_MODAL_STYLE, _VISIBLE_SETTINGS_MODAL_STYLE

    def sec_from_server() -> int:
        return _normalize_turn_roll_interval_sec(server.config.get("TURN_ROLL_INTERVAL_SEC"))

    def max_turns_from_server() -> int:
        return _normalize_game_max_turns(server.config.get("GAME_MAX_TURNS"))

    def market_surge_from_server() -> list[str]:
        enabled = normalize_market_surge_enabled(server.config.get("MARKET_SURGE_ENABLED"))
        return ["enabled"] if enabled else []

    trig = ctx.triggered_id
    if trig is None:
        return hid, no_update, no_update, no_update

    if trig == "url":
        return no_update, no_update, no_update, no_update

    if trig in ("session-reload", "_initial_load"):
        ensure_market_surge_config(server)
        return no_update, no_update, no_update, no_update

    if trig == "settings-gear-btn":
        s = sec_from_server()
        m = max_turns_from_server()
        surge = market_surge_from_server()
        return vis, s, m, surge

    if trig in ("settings-modal-backdrop-btn", "settings-modal-close-btn"):
        return hid, no_update, no_update, no_update

    if trig == "settings-apply-btn":
        sec = _normalize_turn_roll_interval_sec(sec_input)
        max_t = _normalize_game_max_turns(max_turns_input)
        surge_enabled = isinstance(market_surge_value, list) and "enabled" in market_surge_value
        server.config["TURN_ROLL_INTERVAL_SEC"] = sec
        server.config["GAME_MAX_TURNS"] = max_t
        server.config["MARKET_SURGE_ENABLED"] = surge_enabled
        save_session(dash.get_app())
        set_props("turn-roll-interval", {"interval": sec * 1000})
        return hid, sec, max_t, (["enabled"] if surge_enabled else [])

    return no_update, no_update, no_update, no_update


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
        Output("stock-graph", "figure"),
        Output("turn-sequence-store", "data"),
        Output("turn-roll-interval", "disabled"),
        Output("player-net-timeline-graph", "figure"),
        Output("commodity-timeline-graph", "figure"),
        Output("turn-rolls-feed", "children"),
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
    ctx = dash.callback_context
    tp = ctx.triggered_prop_ids

    # Dashboard-only layout: avoid outputs + set_props for missing components (e.g. sign-in /).
    if not _pathname_is_dashboard(pathname):
        return (no_update,) * 7

    if not ctx.triggered:
        return _hydrate_dashboard_from_server()

    interval_fired = "turn-roll-interval.n_intervals" in tp
    roll_fired = "roll-btn.n_clicks" in tp
    server = dash.get_app().server

    if interval_fired:
        if _game_has_ended(server):
            return (no_update,) * 7
        rem = _sequence_remaining(seq_data)
        if rem <= 0:
            return (no_update,) * 7
        table, fig = _roll_once_outputs()
        new_rem = rem - 1
        if new_rem <= 0:
            _increment_turn_and_save()
            pn_fig, co_fig = _timeline_figures_from_server()
            feed = _turn_rolls_feed_children()
            return (table, fig, None, True, pn_fig, co_fig, feed)
        feed = _turn_rolls_feed_children()
        return (table, fig, {"remaining": new_rem}, False, no_update, no_update, feed)

    if roll_fired and n_roll and n_roll > 0:
        if _game_has_ended(server):
            return (no_update,) * 7
        if _sequence_remaining(seq_data) > 0:
            return (no_update,) * 7
        p = _player_roll_count()
        if p <= 0:
            return (no_update,) * 7
        table, fig = _roll_once_outputs()
        rem_after = p - 1
        if rem_after <= 0:
            _increment_turn_and_save()
            pn_fig, co_fig = _timeline_figures_from_server()
            feed = _turn_rolls_feed_children()
            return (table, fig, None, True, pn_fig, co_fig, feed)
        feed = _turn_rolls_feed_children()
        return (table, fig, {"remaining": rem_after}, False, no_update, no_update, feed)

    if "url.pathname" in tp and _pathname_is_dashboard(pathname):
        return _hydrate_dashboard_from_server()

    if ("_initial_load.data" in tp or "session-reload.data" in tp) and _pathname_is_dashboard(
        pathname
    ):
        return _hydrate_dashboard_from_server()

    return (no_update,) * 7


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
    Input("settings-apply-btn", "n_clicks"),
    Input("url", "pathname"),
    prevent_initial_call=False,
)
def sync_roll_btn(_poll_n, seq_data, _settings_apply, pathname):
    """Button label is Turn N (1-based); updates when a turn completes and the sequence store clears."""
    if not _pathname_is_dashboard(pathname):
        return True, no_update
    server = dash.get_app().server
    turn_num = int(server.config.get("TURN_COUNT", 1))
    max_t = _normalize_game_max_turns(server.config.get("GAME_MAX_TURNS"))
    ended = turn_num > max_t
    label = "Game over" if ended else f"Turn {turn_num}"
    users = server.config.get("USER_STATE")
    players = count_named_players(users)
    disabled = _play_turn_button_disabled(players, seq_data) or ended
    return disabled, label
