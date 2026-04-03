from dash import dcc, html, register_page, dash_table
from dash.dash_table.Format import Format, Scheme
from constants import COMMODITIES, DEFAULT_GAME_MAX_TURNS
from dashboard_charts import (
    dashboard_table_rows,
    build_commodity_timeline_figure,
    build_player_net_timeline_figure,
    build_stock_graph_figure,
)

register_page(__name__, path="/dashboard")

stock_prices = {commodity: 1.00 for commodity in COMMODITIES}
fig = build_stock_graph_figure(stock_prices)
player_net_timeline_fig = build_player_net_timeline_figure([])
commodity_timeline_fig = build_commodity_timeline_figure([])

_GRAPH_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "responsive": True,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

_TABLE_FONT = "clamp(1rem, 1.35vw, 1.35rem)"
_TITLE_SIZE = "clamp(1.75rem, 4vw, 3rem)"
_HEADER_COUNTER = {
    "fontSize": "clamp(1rem, 2.2vw, 1.35rem)",
    "fontWeight": "600",
    "color": "#1a1a1a",
    "flex": "0 0 auto",
    "minWidth": "0",
}

layout = html.Div(
    [
        dcc.Store(id="_initial_load", data=True),
        dcc.Store(id="turn-sequence-store", data=None),
        dcc.Interval(id="turn-roll-interval", interval=1000, n_intervals=0, disabled=True),
        html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            id="player-counter-display",
                            children="Players: 0",
                            n_clicks=0,
                            title="View players",
                            style={
                                **_HEADER_COUNTER,
                                "textAlign": "left",
                                "flex": "1 1 0",
                                "minWidth": "0",
                                "border": "none",
                                "background": "transparent",
                                "cursor": "pointer",
                                "padding": "0",
                                "fontFamily": "inherit",
                            },
                        ),
                        html.H1(
                            "Stock Ticker",
                            style={
                                "text-align": "center",
                                "margin": "0",
                                "flex": "1 1 0",
                                "minWidth": "0",
                                "font-size": _TITLE_SIZE,
                                "font-weight": "700",
                                "letter-spacing": "0.02em",
                                "color": "#1a1a1a",
                            },
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "\u2699",
                                    id="settings-gear-btn",
                                    n_clicks=0,
                                    title="Game settings",
                                    className="dashboard-settings-gear",
                                    style={
                                        "margin": "0",
                                        "marginLeft": "auto",
                                        "padding": "0",
                                        "width": "44px",
                                        "height": "44px",
                                        "border": "none",
                                        "borderRadius": "10px",
                                        "backgroundColor": "#ffffff",
                                        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                                        "cursor": "pointer",
                                        "fontSize": "clamp(1.35rem, 3vw, 1.65rem)",
                                        "lineHeight": "1",
                                        "color": "#333",
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "center",
                                    },
                                ),
                            ],
                            style={
                                "flex": "1 1 0",
                                "minWidth": "0",
                                "display": "flex",
                                "justifyContent": "flex-end",
                                "alignItems": "center",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "alignItems": "center",
                        "gap": "12px",
                        "width": "100%",
                        "marginBottom": "12px",
                    },
                ),
                html.Div(
                    id="settings-modal",
                    style={
                        "display": "none",
                        "position": "fixed",
                        "inset": "0",
                        "zIndex": "1000",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "padding": "24px",
                        "boxSizing": "border-box",
                    },
                    children=[
                        html.Button(
                            id="settings-modal-backdrop-btn",
                            n_clicks=0,
                            style={
                                "position": "absolute",
                                "inset": "0",
                                "border": "none",
                                "margin": "0",
                                "padding": "0",
                                "background": "rgba(0,0,0,0.45)",
                                "cursor": "pointer",
                            },
                            title="Close",
                        ),
                        html.Div(
                            style={
                                "position": "relative",
                                "zIndex": "1",
                                "background": "#ffffff",
                                "borderRadius": "12px",
                                "padding": "22px 26px",
                                "minWidth": "min(100%, 380px)",
                                "maxWidth": "100%",
                                "boxShadow": "0 16px 48px rgba(0,0,0,0.22)",
                                "boxSizing": "border-box",
                                "fontFamily": "system-ui, Segoe UI, sans-serif",
                            },
                            children=[
                                html.Div(
                                    [
                                        html.H2(
                                            "Game settings",
                                            style={
                                                "margin": "0",
                                                "fontSize": "clamp(1.15rem, 2.5vw, 1.35rem)",
                                                "fontWeight": "700",
                                                "color": "#1a1a1a",
                                            },
                                        ),
                                        html.Button(
                                            "\u00d7",
                                            id="settings-modal-close-btn",
                                            n_clicks=0,
                                            title="Close",
                                            style={
                                                "border": "none",
                                                "background": "transparent",
                                                "cursor": "pointer",
                                                "fontSize": "1.75rem",
                                                "lineHeight": "1",
                                                "padding": "4px 8px",
                                                "color": "#555",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "space-between",
                                        "marginBottom": "20px",
                                        "gap": "12px",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            "Turn Rolls:",
                                            style={
                                                "fontWeight": "600",
                                                "fontSize": "clamp(0.95rem, 2vw, 1.05rem)",
                                                "color": "#1a1a1a",
                                                "marginRight": "10px",
                                            },
                                        ),
                                        dcc.Input(
                                            id="turn-roll-sec-input",
                                            className="settings-number-input",
                                            type="number",
                                            min=1,
                                            max=600,
                                            step=1,
                                            value=1,
                                            debounce=True,
                                            style={
                                                "width": "72px",
                                                "padding": "8px 10px",
                                                "fontSize": "1rem",
                                                "borderRadius": "8px",
                                                "border": "1px solid #ccc",
                                                "boxSizing": "border-box",
                                            },
                                        ),
                                        html.Span(
                                            "second intervals",
                                            style={
                                                "marginLeft": "10px",
                                                "fontSize": "clamp(0.95rem, 2vw, 1.05rem)",
                                                "color": "#333",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexWrap": "wrap",
                                        "alignItems": "center",
                                        "marginBottom": "18px",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Span(
                                            "End game after:",
                                            style={
                                                "fontWeight": "600",
                                                "fontSize": "clamp(0.95rem, 2vw, 1.05rem)",
                                                "color": "#1a1a1a",
                                                "marginRight": "10px",
                                            },
                                        ),
                                        dcc.Input(
                                            id="game-max-turns-input",
                                            className="settings-number-input",
                                            type="number",
                                            min=1,
                                            max=999,
                                            step=1,
                                            value=DEFAULT_GAME_MAX_TURNS,
                                            debounce=True,
                                            style={
                                                "width": "72px",
                                                "padding": "8px 10px",
                                                "fontSize": "1rem",
                                                "borderRadius": "8px",
                                                "border": "1px solid #ccc",
                                                "boxSizing": "border-box",
                                            },
                                        ),
                                        html.Span(
                                            "turns",
                                            style={
                                                "marginLeft": "10px",
                                                "fontSize": "clamp(0.95rem, 2vw, 1.05rem)",
                                                "color": "#333",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "flexWrap": "wrap",
                                        "alignItems": "center",
                                        "marginBottom": "22px",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.Button(
                                            "Apply",
                                            id="settings-apply-btn",
                                            n_clicks=0,
                                            style={
                                                "padding": "10px 22px",
                                                "fontSize": "1rem",
                                                "fontWeight": "600",
                                                "border": "none",
                                                "borderRadius": "8px",
                                                "backgroundColor": "#2563eb",
                                                "color": "#ffffff",
                                                "cursor": "pointer",
                                                "boxShadow": "0 2px 10px rgba(37, 99, 235, 0.35)",
                                            },
                                        ),
                                    ],
                                    style={"display": "flex", "justifyContent": "flex-end"},
                                ),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    id="players-modal",
                    style={
                        "display": "none",
                        "position": "fixed",
                        "inset": "0",
                        "zIndex": "1000",
                        "alignItems": "center",
                        "justifyContent": "center",
                        "padding": "24px",
                        "boxSizing": "border-box",
                    },
                    children=[
                        html.Button(
                            id="players-modal-backdrop-btn",
                            n_clicks=0,
                            style={
                                "position": "absolute",
                                "inset": "0",
                                "border": "none",
                                "margin": "0",
                                "padding": "0",
                                "background": "rgba(0,0,0,0.45)",
                                "cursor": "pointer",
                            },
                            title="Close",
                        ),
                        html.Div(
                            style={
                                "position": "relative",
                                "zIndex": "1",
                                "background": "#ffffff",
                                "borderRadius": "12px",
                                "padding": "22px 26px",
                                "minWidth": "min(100%, 420px)",
                                "maxWidth": "100%",
                                "maxHeight": "min(80vh, 520px)",
                                "overflowY": "auto",
                                "boxShadow": "0 16px 48px rgba(0,0,0,0.22)",
                                "boxSizing": "border-box",
                                "fontFamily": "system-ui, Segoe UI, sans-serif",
                            },
                            children=[
                                html.Div(
                                    [
                                        html.H2(
                                            "Players",
                                            style={
                                                "margin": "0",
                                                "fontSize": "clamp(1.15rem, 2.5vw, 1.35rem)",
                                                "fontWeight": "700",
                                                "color": "#1a1a1a",
                                            },
                                        ),
                                        html.Button(
                                            "\u00d7",
                                            id="players-modal-close-btn",
                                            n_clicks=0,
                                            title="Close",
                                            style={
                                                "border": "none",
                                                "background": "transparent",
                                                "cursor": "pointer",
                                                "fontSize": "1.75rem",
                                                "lineHeight": "1",
                                                "padding": "4px 8px",
                                                "color": "#555",
                                            },
                                        ),
                                    ],
                                    style={
                                        "display": "flex",
                                        "alignItems": "center",
                                        "justifyContent": "space-between",
                                        "marginBottom": "16px",
                                        "gap": "12px",
                                    },
                                ),
                                html.Div(id="players-modal-list", children=[]),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                dash_table.DataTable(
                                    id="stock-table",
                                    columns=[
                                        {"name": "Commodity", "id": "Commodity"},
                                        {
                                            "name": "Price",
                                            "id": "Price",
                                            "type": "numeric",
                                            "format": Format(precision=0, scheme=Scheme.fixed),
                                        },
                                        {
                                            "name": "Change",
                                            "id": "ChangeThisTurn",
                                            "type": "numeric",
                                            "format": Format(precision=0, scheme=Scheme.fixed),
                                        },
                                    ],
                                    data=dashboard_table_rows(stock_prices),
                                    style_data_conditional=[
                                        {
                                            "if": {
                                                "filter_query": "{ChangeThisTurn} > 0",
                                                "column_id": "ChangeThisTurn",
                                            },
                                            "color": "#0d7d0d",
                                        },
                                        {
                                            "if": {
                                                "filter_query": "{ChangeThisTurn} < 0",
                                                "column_id": "ChangeThisTurn",
                                            },
                                            "color": "#c62828",
                                        },
                                        {
                                            "if": {
                                                "filter_query": "{ChangeThisTurn} = 0",
                                                "column_id": "ChangeThisTurn",
                                            },
                                            "color": "#1a1a1a",
                                        },
                                    ],
                                    style_table={
                                        "width": "100%",
                                        "height": "100%",
                                        "minHeight": "280px",
                                        "backgroundColor": "#ffffff",
                                        "borderRadius": "8px",
                                        "overflow": "hidden",
                                        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                                    },
                                    style_cell={
                                        "textAlign": "center",
                                        "fontSize": _TABLE_FONT,
                                        "padding": "14px 16px",
                                        "fontFamily": "system-ui, Segoe UI, sans-serif",
                                    },
                                    style_header={
                                        "fontWeight": "700",
                                        "fontSize": _TABLE_FONT,
                                        "backgroundColor": "#e8e8e8",
                                        "color": "#111",
                                    },
                                ),
                            ],
                            style={
                                "flex": "1 1 32%",
                                "minWidth": "220px",
                                "minHeight": "0",
                                "display": "flex",
                                "flexDirection": "column",
                            },
                        ),
                        html.Div(
                            [
                                html.Div(
                                    id="turn-rolls-feed",
                                    style={
                                        "width": "100%",
                                        "maxHeight": "min(480px, 52vh)",
                                        "overflowY": "auto",
                                        "flex": "1 1 auto",
                                        "minHeight": "min(200px, 28vh)",
                                        "padding": "4px 4px 8px",
                                        "boxSizing": "border-box",
                                    },
                                ),
                            ],
                            style={
                                "flex": "0 0 28%",
                                "minWidth": "240px",
                                "maxWidth": "420px",
                                "minHeight": "0",
                                "display": "flex",
                                "flexDirection": "column",
                                "justifyContent": "center",
                                "alignItems": "stretch",
                                "padding": "14px 18px",
                                "backgroundColor": "#ffffff",
                                "borderRadius": "8px",
                                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                            },
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                                    id="stock-graph",
                                    figure=fig,
                                    config=_GRAPH_CONFIG,
                                    style={
                                        "width": "100%",
                                        "height": "100%",
                                        "minHeight": "200px",
                                        "flex": "1 1 auto",
                                    },
                                ),
                            ],
                            style={
                                "flex": "1 1 40%",
                                "minWidth": "260px",
                                "minHeight": "0",
                                "display": "flex",
                                "flexDirection": "column",
                            },
                        ),
                    ],
                    style={
                        "display": "flex",
                        "flex-wrap": "nowrap",
                        "justify-content": "space-between",
                        "align-items": "stretch",
                        "gap": "16px",
                        "width": "100%",
                        "minWidth": 0,
                        "flex": "1 1 auto",
                        "minHeight": "0",
                        "overflow-x": "auto",
                        "overflow-y": "visible",
                    },
                    className="dashboard-main-row",
                ),
                html.Div(
                    [
                        html.Button(
                            "Turn 1",
                            id="roll-btn",
                            n_clicks=0,
                            disabled=True,
                            style={
                                "margin-top": "16px",
                                "width": "100%",
                                "maxWidth": "720px",
                                "margin-left": "auto",
                                "margin-right": "auto",
                                "display": "block",
                                "padding": "18px 28px",
                                "font-size": "clamp(1.25rem, 2.5vw, 1.85rem)",
                                "font-weight": "700",
                                "cursor": "pointer",
                                "border": "none",
                                "border-radius": "8px",
                                "backgroundColor": "#2563eb",
                                "color": "#ffffff",
                                "boxShadow": "0 4px 14px rgba(37, 99, 235, 0.45)",
                            },
                        ),
                    ],
                    style={"width": "100%", "padding": "0 8px"},
                ),
                html.Div(
                    [
                        html.Div(
                            dcc.Graph(
                                id="player-net-timeline-graph",
                                figure=player_net_timeline_fig,
                                config=_GRAPH_CONFIG,
                                style={
                                    "width": "100%",
                                    "height": "100%",
                                    "minHeight": "280px",
                                },
                            ),
                            style={
                                "flex": "0 0 calc(50% - 8px)",
                                "minWidth": 0,
                                "maxWidth": "calc(50% - 8px)",
                                "boxSizing": "border-box",
                            },
                            className="dashboard-timeline-cell",
                        ),
                        html.Div(
                            dcc.Graph(
                                id="commodity-timeline-graph",
                                figure=commodity_timeline_fig,
                                config=_GRAPH_CONFIG,
                                style={
                                    "width": "100%",
                                    "height": "100%",
                                    "minHeight": "280px",
                                },
                            ),
                            style={
                                "flex": "0 0 calc(50% - 8px)",
                                "minWidth": 0,
                                "maxWidth": "calc(50% - 8px)",
                                "boxSizing": "border-box",
                            },
                            className="dashboard-timeline-cell",
                        ),
                    ],
                    style={
                        "width": "100%",
                        "maxWidth": "1600px",
                        "marginLeft": "auto",
                        "marginRight": "auto",
                        "padding": "16px 8px 24px",
                        "display": "flex",
                        "flexDirection": "row",
                        "flexWrap": "nowrap",
                        "justifyContent": "space-between",
                        "alignItems": "stretch",
                        "gap": "16px",
                        "boxSizing": "border-box",
                    },
                    className="dashboard-timeline-row",
                ),
                html.Div(id="roll-result", style={"margin-top": "12px"}),
            ],
            style={
                "maxWidth": "1600px",
                "margin": "0 auto",
                "padding": "16px clamp(12px, 2vw, 28px) 24px",
                "box-sizing": "border-box",
                "flex": "1 1 auto",
                "minHeight": "min-content",
                "overflow": "visible",
                "display": "flex",
                "flexDirection": "column",
                "width": "100%",
            },
        ),
    ],
    className="dashboard-page",
    style={
        "width": "100%",
        "margin": "0",
        "padding": "0",
        "boxSizing": "border-box",
        "overflowX": "hidden",
        "backgroundColor": "#e9e9e9",
    },
)
