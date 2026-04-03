import logging
import socket

from dash import Dash, dcc, html, page_container, Output, Input, dash
from waitress import serve

import constants
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

from callbacks.app_ref import bind_app

bind_app(app)

load_session(app)
register_shutdown_handlers(app)

server = app.server

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
        dcc.Interval(
            id="stock-prices-poll",
            interval=constants.PRICE_POLL_INTERVAL_MS,
            n_intervals=0,
        ),
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

# Register callbacks only after the Dash app exists (Dash 3 requires a bound app instance).
# Page modules must not import these at load time — Dash imports pages during __init__ before the app is registered.
import callbacks.dashboard_callbacks  # noqa: F401
import callbacks.user_callbacks  # noqa: F401
import callbacks.session_callbacks  # noqa: F401
import callbacks.sign_in_callbacks  # noqa: F401
from callbacks.user_callbacks import count_named_players


# Callback to update the URL based on `dcc.Store`
@app.callback(
    Output("url", "pathname"),
    Input("nav-store", "data"),
    prevent_initial_call=True,
)
def navigate(page):
    if page:
        return page
    return dash.no_update


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

LISTEN_HOST = "0.0.0.0"
LISTEN_PORT = 8050


def _guess_lan_ipv4() -> str | None:
    """Best-effort primary IPv4 for URLs other devices can use (same as outbound route)."""
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            probe.connect(("8.8.8.8", 80))
            return probe.getsockname()[0]
        finally:
            probe.close()
    except OSError:
        pass
    try:
        host = socket.gethostname()
        ip = socket.gethostbyname(host)
        if ip and ip != "127.0.0.1":
            return ip
    except OSError:
        pass
    return None


def _print_startup_banner() -> None:
    local_url = f"http://127.0.0.1:{LISTEN_PORT}/"
    print(f"\n  This PC:     {local_url}", flush=True)
    lan = _guess_lan_ipv4()
    if lan and lan != "127.0.0.1":
        print(f"  Other devices: http://{lan}:{LISTEN_PORT}/", flush=True)
    else:
        print(
            f"  Other devices: use this machine's IPv4 in Network settings, port {LISTEN_PORT} "
            "(e.g. http://192.168.x.x:8050/)",
            flush=True,
        )
    print("  Logs and errors (INFO and above) follow. Ctrl+C to stop.\n", flush=True)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
        force=True,
    )
    # Threaded Waitress WSGI: handles many concurrent Dash clients (LAN parties). Single process
    # only — game state lives in server.config (see README). PyInstaller exe uses this block too.
    _print_startup_banner()
    serve(
        server,
        host=LISTEN_HOST,
        port=LISTEN_PORT,
        threads=constants.WAITRESS_THREADS,
    )