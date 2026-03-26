from dash import Dash, dcc, html, page_container, callback, Output, Input, dash
import callbacks.dashboard_callbacks
import callbacks.user_callbacks  # noqa: F401 — register portfolio callbacks at startup

app = Dash(__name__, use_pages=True)

# Define layout
app.layout = html.Div([
    dcc.Location(id='url', refresh="callback-nav"),  # Tracks URL changes
    dcc.Store(id="nav-store", storage_type="memory"),  # Stores navigation state
    dcc.Store(id="stock-prices-store", storage_type="memory"),
    dcc.Interval(id="stock-prices-poll", interval=1000, n_intervals=0),

    # Page content container
    html.Div(id="content", children=page_container)
])

# Callback to update the URL based on `dcc.Store`
@callback(
    Output("url", "pathname"),
    Input("nav-store", "data"),
    prevent_initial_call=True
)
def navigate(page):
    if page:
        return page
    return dash.no_update


@callback(
    Output("stock-prices-store", "data"),
    Input("stock-prices-poll", "n_intervals"),
)
def poll_stock_prices(_n):
    return app.server.config.get("STOCK_PRICES", {})


# Import callbacks



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8050, debug=True)