from dash import Dash, dcc, html, page_container, callback, Output, Input, dash
import callbacks.dashboard_callbacks

app = Dash(__name__, use_pages=True)

# Define layout
app.layout = html.Div([
    dcc.Location(id='url', refresh="callback-nav"),  # Tracks URL changes
    dcc.Store(id="nav-store", storage_type="memory"),  # Stores navigation state

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

# Import callbacks



if __name__ == '__main__':
    app.run(debug=True)