"""Root Dash layout: shell, shared stores, and page slot (no callbacks)."""

from dash import dcc, html, page_container

import constants


def build_root_layout():
    # #dash-shell / #content flex chain works with assets/viewport_desktop.css
    return html.Div(
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
