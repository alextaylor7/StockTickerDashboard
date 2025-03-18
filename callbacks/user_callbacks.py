import dash
from dash import Input, Output, State, callback
import urllib

# User stock data setup
commodities = ["Gold", "Silver", "Bonds", "Oil", "Industrials", "Grain"]
user_stocks = {commodity: 0 for commodity in commodities}
user_balance = 5000
stock_prices = {commodity: 1.00 for commodity in commodities}  # Default stock prices

@callback(
    [Output("user-stock-table", "data"),
     Output("user-balance", "children"),
     Output("transaction-message", "children")],
    [Input("buy-500-btn", "n_clicks"), Input("buy-1000-btn", "n_clicks"), Input("buy-2000-btn", "n_clicks"),
     Input("buy-5000-btn", "n_clicks"),
     Input("sell-500-btn", "n_clicks"), Input("sell-1000-btn", "n_clicks"), Input("sell-2000-btn", "n_clicks"),
     Input("sell-5000-btn", "n_clicks")],
    [State("stock-select", "value")]
)
def handle_transaction(buy500, buy1000, buy2000, buy5000, sell500, sell1000, sell2000, sell5000, stock):
    global user_balance, user_stocks
    ctx = dash.callback_context

    if not ctx.triggered or stock is None:
        return dash.no_update

    action = ctx.triggered[0]['prop_id'].split('.')[0]
    amount = int(action.split('-')[1])
    transaction_type = action.split('-')[0]
    price = stock_prices.get(stock, 1.00)
    cost = (amount / 500) * price * 500

    if transaction_type == "buy" and user_balance >= cost:
        user_stocks[stock] += amount
        user_balance -= cost
        message = f"Bought {amount} shares of {stock} for ${cost:.2f}"
    elif transaction_type == "sell" and user_stocks[stock] >= amount:
        user_stocks[stock] -= amount
        user_balance += cost
        message = f"Sold {amount} shares of {stock} for ${cost:.2f}"
    else:
        message = "Invalid transaction"

    return ([{"Commodity": k, "Shares": v} for k, v in user_stocks.items()],
            f"Balance: ${user_balance}",
            message)


@callback(
    Output("profile-name", "children"),
    Input("url", "search")  # Extracts query parameters
)
def display_user_info(search):
    if not search:
        return "User Profile"
    else:
        query_params = urllib.parse.parse_qs(search.lstrip("?"))
        name = query_params.get("name", [""])[0]
        return f"{name}'s Profile"