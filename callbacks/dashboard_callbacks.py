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
        title=dict(text="Stock Prices", font=dict(color=CHART_TEXT)),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color=CHART_TEXT),
        yaxis=dict(
            range=[0, 2],
            gridcolor="rgba(255,255,255,0.15)",
            zerolinecolor="rgba(255,255,255,0.25)",
        ),
        xaxis=dict(gridcolor="rgba(255,255,255,0.1)"),
    )
    return fig


def roll_dice():
    stock = random.choice(commodities)
    action = random.choice(["Up", "Down", "Dividend"])
    value = random.choice([0.05, 0.10, 0.20])
    return stock, action, value

@callback(
    [Output("stock-table", "data"),
     Output("rolled-stock", "children"),
     Output("rolled-action", "children"),
     Output("rolled-value", "children"),
     Output("stock-graph", "figure")],
    [Input("roll-btn", "n_clicks"),
    Input("_initial_load", "data")],
    prevent_initial_call=False
)
def update_stock(n, initial_load):
    global stock_prices  # Move global declaration to the beginning of the function
    
    if n > 0:
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

        fig = build_stock_graph_figure(stock_prices)

        return ([{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                f"Stock: {stock}",
                f"Action: {action}",
                f"Value: {value:.2f}",
                fig)
    elif initial_load:
        # Get stored prices if they exist, otherwise use defaults
        stored_prices = dash.get_app().server.config.get('STOCK_PRICES')
        if stored_prices:
            stock_prices = {commodity: round(float(stored_prices.get(commodity, 1.00)), 2) for commodity in commodities}
        else:
            stock_prices = {commodity: round(price, 2) for commodity, price in stock_prices.items()}

        fig = build_stock_graph_figure(stock_prices)

        return ([{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                "Stock: ",
                "Action: ",
                "Value: ",
                fig)

    return dash.no_update