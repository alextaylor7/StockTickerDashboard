from dash import dcc, html, register_page, dash_table
import callbacks.user_callbacks
from constants import commodities, user_starting_balance

user_stocks = {commodity: 0 for commodity in commodities}
user_balance = user_starting_balance
stock_prices = {commodity: 1.00 for commodity in commodities}

register_page(__name__, path="/user")

_TITLE = "clamp(1.35rem, 5vw, 1.85rem)"
_BALANCE = "clamp(1.05rem, 4vw, 1.35rem)"
_TABLE = "clamp(0.88rem, 3.4vw, 1.05rem)"
_LABEL = "clamp(0.85rem, 3.2vw, 1rem)"

# Inline styles so colours always apply (Dash/React); 2x2 grid uses gap (no per-button margin).
_TRADE_BTN_BASE = {
    "width": "100%",
    "minHeight": "50px",
    "padding": "12px 8px",
    "fontSize": "clamp(1rem, 4.2vw, 1.2rem)",
    "fontWeight": "600",
    "border": "none",
    "borderRadius": "8px",
    "cursor": "pointer",
    "touchAction": "manipulation",
    "marginBottom": "0",
    "color": "#ffffff",
    "boxSizing": "border-box",
}

_TRADE_GRID = {
    "display": "grid",
    "gridTemplateColumns": "repeat(2, minmax(0, 1fr))",
    "gap": "8px",
    "width": "100%",
    "minWidth": "0",
}

_SELL_STYLE = {**_TRADE_BTN_BASE, "backgroundColor": "#dc2626"}
_BUY_STYLE = {**_TRADE_BTN_BASE, "backgroundColor": "#16a34a"}

# Same palette and proportions as sell/buy; fixed 20% width in the cash row.
_CASH_BTN_BASE = {
    "flex": "0 0 20%",
    "width": "20%",
    "minWidth": "0",
    "minHeight": "56px",
    "padding": "14px 10px",
    "fontSize": "clamp(1.1rem, 4.8vw, 1.3rem)",
    "fontWeight": "600",
    "border": "none",
    "borderRadius": "8px",
    "cursor": "pointer",
    "touchAction": "manipulation",
    "color": "#ffffff",
    "boxSizing": "border-box",
}
_CASH_MINUS_STYLE = {**_CASH_BTN_BASE, "backgroundColor": "#dc2626"}
_CASH_PLUS_STYLE = {**_CASH_BTN_BASE, "backgroundColor": "#16a34a"}


def _sell_btn(qty, btn_id):
    return html.Button(str(qty), id=btn_id, n_clicks=0, className="user-trade-btn", style=_SELL_STYLE)


def _buy_btn(qty, btn_id):
    return html.Button(str(qty), id=btn_id, n_clicks=0, className="user-trade-btn", style=_BUY_STYLE)


layout = html.Div(
    [
        html.H2(
            "User Portfolio",
            id="profile-name",
            style={
                "textAlign": "center",
                "margin": "0 0 10px 0",
                "fontSize": _TITLE,
                "fontWeight": "700",
                "color": "#111",
                "lineHeight": "1.25",
            },
        ),
        html.Div(
            f"Balance: ${user_balance:.2f}",
            id="user-balance",
            style={
                "textAlign": "center",
                "fontSize": _BALANCE,
                "fontWeight": "600",
                "marginBottom": "6px",
                "color": "#111",
            },
        ),
        html.Div(
            f"Net Value: ${user_balance:.2f}",
            id="user-net-value",
            style={
                "textAlign": "center",
                "fontSize": _BALANCE,
                "fontWeight": "600",
                "marginBottom": "12px",
                "color": "#111",
            },
        ),
        html.Div(
            [
                dash_table.DataTable(
                    id="user-stock-table",
                    columns=[
                        {"name": "Commodity", "id": "Commodity"},
                        {"name": "Shares", "id": "Shares"},
                    ],
                    data=[{"Commodity": k, "Shares": v} for k, v in user_stocks.items()],
                    style_table={
                        "width": "100%",
                        "minWidth": "100%",
                    },
                    style_cell={
                        "textAlign": "center",
                        "fontSize": _TABLE,
                        "padding": "12px 10px",
                        "fontFamily": "system-ui, Segoe UI, sans-serif",
                        "minWidth": "72px",
                    },
                    style_header={
                        "fontWeight": "700",
                        "fontSize": _TABLE,
                        "padding": "12px 10px",
                        "backgroundColor": "#e8e8e8",
                        "color": "#111",
                    },
                )
            ],
            className="user-table-wrap",
        ),
        html.Div(
            [
                dcc.Dropdown(
                    id="stock-select",
                    options=[{"label": c, "value": c} for c in commodities],
                    placeholder="Select a stock",
                    clearable=False,
                    searchable=False,
                    style={
                        "width": "100%",
                        "marginBottom": "10px",
                        "fontSize": "max(16px, 1rem)",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            "Sell",
                            style={
                                "textAlign": "center",
                                "fontWeight": "700",
                                "fontSize": _LABEL,
                                "marginBottom": "6px",
                                "color": "#111",
                                "flex": "1 1 48%",
                                "minWidth": "0",
                            },
                        ),
                        html.Div(
                            "Buy",
                            style={
                                "textAlign": "center",
                                "fontWeight": "700",
                                "fontSize": _LABEL,
                                "marginBottom": "6px",
                                "color": "#111",
                                "flex": "1 1 48%",
                                "minWidth": "0",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "width": "100%",
                        "gap": "8px",
                    },
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                _sell_btn(500, "sell-500-btn"),
                                _sell_btn(1000, "sell-1000-btn"),
                                _sell_btn(2000, "sell-2000-btn"),
                                _sell_btn(5000, "sell-5000-btn"),
                            ],
                            className="user-trade-grid",
                            style={**_TRADE_GRID, "flex": "1 1 48%"},
                        ),
                        html.Div(
                            [
                                _buy_btn(500, "buy-500-btn"),
                                _buy_btn(1000, "buy-1000-btn"),
                                _buy_btn(2000, "buy-2000-btn"),
                                _buy_btn(5000, "buy-5000-btn"),
                            ],
                            className="user-trade-grid",
                            style={**_TRADE_GRID, "flex": "1 1 48%"},
                        ),
                    ],
                    style={
                        "display": "flex",
                        "justifyContent": "space-between",
                        "width": "100%",
                        "gap": "8px",
                    },
                ),
            ],
            className="user-trading-block",
            style={"marginBottom": "8px"},
        ),
        html.Div(
            [
                html.Button(
                    "-",
                    id="remove-cash-btn",
                    n_clicks=0,
                    title="Remove cash",
                    className="user-cash-btn",
                    style=_CASH_MINUS_STYLE,
                ),
                dcc.Input(
                    id="cash-input",
                    type="number",
                    inputMode="numeric",
                    placeholder="Cash",
                    min=0,
                    step=1,
                    className="user-cash-input",
                ),
                html.Button(
                    "+",
                    id="add-cash-btn",
                    n_clicks=0,
                    title="Add cash",
                    className="user-cash-btn",
                    style=_CASH_PLUS_STYLE,
                ),
            ],
            className="user-cash-row",
            style={"marginTop": "12px"},
        ),
        html.Div(
            id="transaction-message",
            className="user-msg",
            style={
                "textAlign": "center",
                "marginTop": "12px",
                "fontSize": "clamp(0.9rem, 3.5vw, 1.05rem)",
                "color": "#333",
            },
        ),
    ],
    className="user-page",
)
