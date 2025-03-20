import dash
from dash import Input, Output, callback, State
import random
import plotly.graph_objects as go
from constants import commodities

# Initialize stock prices with default values
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
    [Input("roll-btn", "n_clicks"),
    Input("_initial_load", "data")],
    prevent_initial_call=False
)
def update_stock(n, initial_load):
    global stock_prices  # Move global declaration to the beginning of the function
    
    if n > 0:
        stock, action, value = roll_dice()

        if action == "Up":
            stock_prices[stock] += value
        elif action == "Down":
            stock_prices[stock] = max(0, stock_prices[stock] - value)

        if stock_prices[stock] >= 2.00:
            stock_prices[stock] = 1.00
        elif stock_prices[stock] == 0:
            stock_prices[stock] = 1.00

        # Store updated stock prices in session
        dash.get_app().server.config['STOCK_PRICES'] = stock_prices

        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(stock_prices.keys()), y=list(stock_prices.values()), marker_color='blue'))
        fig.update_layout(yaxis=dict(range=[0, 2]), title="Stock Prices")

        return ([{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                f"Stock: {stock}",
                f"Action: {action}",
                f"Value: {value}",
                fig)
    elif initial_load:
        # Get stored prices if they exist, otherwise use defaults
        stored_prices = dash.get_app().server.config.get('STOCK_PRICES')
        if stored_prices:
            stock_prices = stored_prices

        fig = go.Figure()
        fig.add_trace(go.Bar(x=list(stock_prices.keys()), y=list(stock_prices.values()), marker_color='blue'))
        fig.update_layout(yaxis=dict(range=[0, 2]), title="Stock Prices")

        return ([{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                "Stock: ",
                "Action: ",
                "Value: ",
                fig)

    return dash.no_update