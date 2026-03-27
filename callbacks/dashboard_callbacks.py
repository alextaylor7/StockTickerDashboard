import dash
from dash import Input, Output, callback, State
import random
import plotly.graph_objects as go
from constants import commodities, COMMODITY_BAR_COLORS, CHART_BG, CHART_TEXT

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


def roll_dice():
    stock = random.choice(commodities)
    action = random.choice(["Up", "Down", "Dividend"])
    value = random.choice([0.05, 0.10, 0.20])
    return stock, action, value

def _hydrate_dashboard_from_server():
    """Rebuild module stock_prices and figure from server.config (after load or navigation)."""
    global stock_prices
    stored_prices = dash.get_app().server.config.get("STOCK_PRICES")
    # Use isinstance — empty dict {} is falsy but is still valid server state
    if isinstance(stored_prices, dict):
        stock_prices = {
            commodity: round(float(stored_prices.get(commodity, 1.00)), 2) for commodity in commodities
        }
    else:
        stock_prices = {commodity: round(price, 2) for commodity, price in stock_prices.items()}

    fig = build_stock_graph_figure(stock_prices)
    return (
        [{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
        "",
        "",
        "",
        fig,
    )


def _pathname_is_dashboard(pathname) -> bool:
    if not pathname:
        return False
    return pathname.rstrip("/") == "/dashboard"


@callback(
    [Output("stock-table", "data"),
     Output("rolled-stock-value", "children"),
     Output("rolled-action-value", "children"),
     Output("rolled-value-value", "children"),
     Output("stock-graph", "figure")],
    [Input("roll-btn", "n_clicks"),
     Input("_initial_load", "data"),
     Input("session-reload", "data"),
     Input("url", "pathname")],
    prevent_initial_call=False
)
def update_stock(n, initial_load, session_reload, pathname):
    global stock_prices  # Move global declaration to the beginning of the function

    ctx = dash.callback_context
    # Initial callback often has no ctx.triggered; must hydrate from server (same idea as user_callbacks).
    if not ctx.triggered:
        return _hydrate_dashboard_from_server()

    prop_id = ctx.triggered[0]["prop_id"]
    tid = prop_id.split(".")[0] if prop_id else ""

    roll_fired = any("roll-btn" in t.get("prop_id", "") for t in ctx.triggered)
    if roll_fired and n and n > 0:
        stock, action, value = roll_dice()

        if action == "Up":
            stock_prices[stock] = round(stock_prices[stock] + value, 2)
        elif action == "Down":
            stock_prices[stock] = round(max(0, stock_prices[stock] - value), 2)

        server = dash.get_app().server
        user_state = server.config.setdefault("USER_STATE", {})

        # Dividend: pay cash = shares * value when stock is at/above par ($1.00); no price change
        if action == "Dividend" and stock_prices[stock] >= 1.00:
            for _username, state in user_state.items():
                if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                    shares = int(state["stocks"].get(stock, 0))
                    cash = round(shares * value, 2)
                    state["balance"] = round(float(state.get("balance", 0)) + cash, 2)

        if stock_prices[stock] >= 2.00:
            # Split: price resets to 1; everyone's shares of this stock double
            for _username, state in user_state.items():
                if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                    state["stocks"][stock] = int(state["stocks"].get(stock, 0)) * 2
            stock_prices[stock] = 1.00
        elif stock_prices[stock] <= 0:
            # Wipe: price resets to 1; everyone loses shares of this stock
            for _username, state in user_state.items():
                if isinstance(state, dict) and isinstance(state.get("stocks"), dict):
                    state["stocks"][stock] = 0
            stock_prices[stock] = 1.00

        stock_prices = {commodity: round(price, 2) for commodity, price in stock_prices.items()}

        # Store updated stock prices in session
        dash.get_app().server.config['STOCK_PRICES'] = stock_prices

        from session_persistence import save_session

        save_session(dash.get_app())

        fig = build_stock_graph_figure(stock_prices)

        return ([{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                stock,
                action,
                f"{value:.2f}",
                fig)

    # Navigating to /dashboard after loading session on / — session-reload may have fired with no outputs mounted.
    # Prefer scanning all triggers: order is not guaranteed when several inputs update at once.
    triggered_ids = [t["prop_id"].split(".")[0] for t in ctx.triggered if t.get("prop_id")]
    if "url" in triggered_ids and _pathname_is_dashboard(pathname):
        return _hydrate_dashboard_from_server()

    if (
        any(x in triggered_ids for x in ("_initial_load", "session-reload"))
        or initial_load
        or session_reload is not None
    ):
        return _hydrate_dashboard_from_server()

    return dash.no_update