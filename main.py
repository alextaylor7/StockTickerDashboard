from dash import Dash, dcc, html, page_container, callback, clientside_callback, Output, Input, dash
import callbacks.dashboard_callbacks
import callbacks.user_callbacks  # noqa: F401 — register portfolio callbacks at startup
from callbacks.user_callbacks import count_named_players
from session_persistence import load_session, register_shutdown_handlers

app = Dash(
    __name__,
    use_pages=True,
    suppress_callback_exceptions=True,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1, viewport-fit=cover",
        },
    ],
)

load_session(app)
register_shutdown_handlers(app)

# Define layout — #dash-shell / #content flex chain works with assets/viewport_desktop.css
app.layout = html.Div(
    [
        dcc.Location(id="url", refresh="callback-nav"),
        dcc.Store(id="nav-store", storage_type="memory"),
        dcc.Store(id="stock-prices-store", storage_type="memory"),
        dcc.Store(id="game-meta-store", storage_type="memory"),
        dcc.Store(id="session-reload", storage_type="memory"),
        dcc.Store(id="session-load-dummy", data=None),
        dcc.Download(id="session-download"),
        dcc.Upload(
            id="session-upload",
            children=[],
            accept=".json,application/json",
            style={"display": "none"},
            multiple=False,
        ),
        dcc.Interval(id="stock-prices-poll", interval=1000, n_intervals=0),
        dcc.Store(id="plotly-resize-hook", data=0),
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


@callback(
    Output("game-meta-store", "data"),
    Input("stock-prices-poll", "n_intervals"),
)
def poll_game_meta(_n):
    users = app.server.config.get("USER_STATE")
    n_players = count_named_players(users)
    turn = int(app.server.config.get("TURN_COUNT", 1))
    return {"turn": turn, "players": n_players}


# Plotly keeps stale dimensions after DPI / monitor changes until Plots.resize runs.
clientside_callback(
    """
    function(_pathname) {
        if (window.__stockTickerPlotlyResizeHook) {
            return window.dash_clientside.no_update;
        }
        function resizeAllPlotly() {
            if (!window.Plotly || !window.Plotly.Plots) return;
            document.querySelectorAll(".js-plotly-plot").forEach(function (gd) {
                try {
                    window.Plotly.Plots.resize(gd);
                } catch (e) {
                }
            });
        }
        function scheduleResize() {
            window.requestAnimationFrame(resizeAllPlotly);
        }
        window.addEventListener("resize", scheduleResize);
        window.addEventListener("load", function () {
            setTimeout(scheduleResize, 150);
        });
        document.addEventListener("visibilitychange", function () {
            if (!document.hidden) setTimeout(scheduleResize, 150);
        });
        if (window.ResizeObserver) {
            var shell = document.getElementById("dash-shell");
            if (shell) {
                new ResizeObserver(function () {
                    scheduleResize();
                }).observe(shell);
            }
        }
        setTimeout(scheduleResize, 400);
        setTimeout(scheduleResize, 1200);
        window.__stockTickerPlotlyResizeHook = true;
        return 1;
    }
    """,
    Output("plotly-resize-hook", "data"),
    Input("url", "pathname"),
)


import callbacks.session_callbacks  # noqa: F401 — Save/Load session on landing page

if __name__ == "__main__":
    # use_reloader=False: Werkzeug's stat-reloader parent process never serves requests, so
    # server.config stays empty; its atexit would overwrite session_state.json with defaults.
    app.run(host="0.0.0.0", port=8050, debug=True, use_reloader=False)