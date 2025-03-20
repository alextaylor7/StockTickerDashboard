import dash
from dash import Input, Output, callback


@callback(
    Output("nav-store", "data"),
    Input("nav-dashboard", "n_clicks"),
    Input("nav-user", "n_clicks"),
    Input('username-input', 'value'),
    prevent_initial_call=True
)
def update_nav(dashboard, user, input):
    ctx = dash.callback_context  # Get the triggered input
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if button_id == "nav-dashboard":
        return "/dashboard"
    elif button_id == "nav-user":
        if input:
            return f"/user?name={input}"

    return dash.no_update