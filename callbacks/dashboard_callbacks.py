import dash
from dash import Input, Output, callback
import random
import plotly.graph_objects as go

# Stock data setup
commodities = ["Gold", "Silver", "Bonds", "Oil", "Industrials", "Grain"]
stock_prices = {commodity: 1.00 for commodity in commodities}


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
    Input("roll-btn", "n_clicks")
)
def update_stock(n):
    if n > 0:
        stock, action, value = roll_dice()
        global stock_prices

        if action == "Up":
            stock_prices[stock] += value
        elif action == "Down":
            stock_prices[stock] = max(0, stock_prices[stock] - value)

        if stock_prices[stock] >= 2.00:
            stock_prices[stock] = 1.00
        elif stock_prices[stock] == 0:
            stock_prices[stock] = 1.00

        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(stock_prices.keys()), y=list(stock_prices.values()), marker_color='blue'))
        fig.update_layout(yaxis=dict(range=[0, 2]), title="Stock Prices")

        return ([{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                f"Stock: {stock}",
                f"Action: {action}",
                f"Value: {value}",
                fig)

    return dash.no_update