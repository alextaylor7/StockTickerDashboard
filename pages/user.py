from dash import dcc, html, register_page, dash_table
import callbacks.user_callbacks
from constants import commodities, user_starting_balance

user_stocks = {commodity: 0 for commodity in commodities}
user_balance = user_starting_balance
stock_prices = {commodity: 1.00 for commodity in commodities}

register_page(__name__, path="/user")

_TITLE = "clamp(1.15rem, 4.2vw, 1.65rem)"
_BALANCE = "clamp(0.92rem, 3.4vw, 1.2rem)"
_TABLE = "clamp(0.8rem, 3vw, 1rem)"
_LABEL = "clamp(0.78rem, 2.9vw, 0.95rem)"

# Inline styles so colours always apply (Dash/React); 2x2 grid uses gap (no per-button margin).
_TRADE_BTN_BASE = {
    "width": "100%",
    "minHeight": "44px",
    "padding": "8px 6px",
    "fontSize": "clamp(0.9rem, 3.6vw, 1.08rem)",
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
    "gap": "6px",
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
    "minHeight": "48px",
    "padding": "10px 8px",
    "fontSize": "clamp(1rem, 4.2vw, 1.2rem)",
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
                "margin": "0 0 6px 0",
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
                "marginBottom": "4px",
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
                "marginBottom": "8px",
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
                        "minWidth": "0",
                        "tableLayout": "fixed",
                    },
                    style_cell={
                        "textAlign": "center",
                        "fontSize": _TABLE,
                        "padding": "8px 8px",
                        "fontFamily": "system-ui, Segoe UI, sans-serif",
                        "minWidth": "0",
                        "maxWidth": "50%",
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
                dcc.Store(id="selected-commodity-store"),
                html.Div(
                    id="selected-commodity-display",
                    children="",
                    style={
                        "width": "100%",
                        "marginBottom": "6px",
                        "fontSize": "max(16px, 0.95rem)",
                        "textAlign": "center",
                        "color": "#111",
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
                                "marginBottom": "4px",
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
                                "marginBottom": "4px",
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
                        "gap": "6px",
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
                        "gap": "6px",
                    },
                ),
            ],
            className="user-trading-block",
            style={"marginBottom": "6px"},
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
            style={"marginTop": "8px"},
        ),
        html.Div(
            id="transaction-message",
            className="user-msg",
            style={
                "textAlign": "center",
                "marginTop": "8px",
                "fontSize": "clamp(0.82rem, 3.1vw, 0.98rem)",
                "color": "#333",
            },
        ),
    ],
    className="user-page",
)
