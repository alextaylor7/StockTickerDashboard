"""Root-level callbacks: navigation, shared polls, Plotly resize clientside hook."""

from dash import ClientsideFunction, Input, Output, dash as dash_ns


def register_root_callbacks(app):
    from domain.user_state import count_named_players

    @app.callback(
        Output("url", "pathname"),
        Input("nav-store", "data"),
        prevent_initial_call=True,
    )
    def navigate(page):
        if page:
            return page
        return dash_ns.no_update

    @app.callback(
        Output("stock-prices-store", "data"),
        Input("stock-prices-poll", "n_intervals"),
    )
    def poll_stock_prices(_n):
        return app.server.config.get("STOCK_PRICES", {})

    @app.callback(
        Output("game-meta-store", "data"),
        Input("stock-prices-poll", "n_intervals"),
    )
    def poll_game_meta(_n):
        users = app.server.config.get("USER_STATE")
        n_players = count_named_players(users)
        turn = int(app.server.config.get("TURN_COUNT", 1))
        return {"turn": turn, "players": n_players}

    # Plotly keeps stale dimensions after DPI / monitor changes until Plots.resize runs.
    app.clientside_callback(
        ClientsideFunction("stock_ticker", "plotlyResizeHook"),
        Output("plotly-resize-hook", "data"),
        Input("url", "pathname"),
    )
