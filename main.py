from dash import Dash, dcc, html, page_container, callback, Output, Input, dash
import callbacks.dashboard_callbacks
import callbacks.user_callbacks  # noqa: F401 — register portfolio callbacks at startup

app = Dash(
    __name__,
    use_pages=True,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, viewport-fit=cover",
        },
    ],
)

# Define layout — #dash-shell / #content flex chain works with assets/viewport_desktop.css
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh="callback-nav"),
        dcc.Store(id="nav-store", storage_type="memory"),
        dcc.Store(id="stock-prices-store", storage_type="memory"),
        dcc.Interval(id="stock-prices-poll", interval=1000, n_intervals=0),
        html.Div(
            id="content",
            className="dash-page-slot",
            children=page_container,
            style={
                "flex": "1 1 auto",
                "minHeight": "0",
                "display": "flex",
                "flexDirection": "column",
                "boxSizing": "border-box",
            },
        ),
    ],
    id="dash-shell",
    style={
        "display": "flex",
        "flexDirection": "column",
        "minHeight": "100dvh",
        "boxSizing": "border-box",
    },
)

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