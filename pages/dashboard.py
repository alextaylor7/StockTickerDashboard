from dash import dcc, html, register_page, dash_table
from dash.dash_table.Format import Format, Scheme
from constants import commodities
from callbacks.dashboard_callbacks import (
    build_commodity_timeline_figure,
    build_player_net_timeline_figure,
    build_stock_graph_figure,
)

register_page(__name__, path="/dashboard")

stock_prices = {commodity: 1.00 for commodity in commodities}
fig = build_stock_graph_figure(stock_prices)
player_net_timeline_fig = build_player_net_timeline_figure([])
commodity_timeline_fig = build_commodity_timeline_figure([])

_GRAPH_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}

_TABLE_FONT = "clamp(1rem, 1.35vw, 1.35rem)"
_DICE_FONT = "clamp(1.25rem, 2.2vw, 2rem)"
_TITLE_SIZE = "clamp(1.75rem, 4vw, 3rem)"
_HEADER_COUNTER = {
    "fontSize": "clamp(1rem, 2.2vw, 1.35rem)",
    "fontWeight": "600",
    "color": "#1a1a1a",
    "flex": "0 0 auto",
    "minWidth": "0",
}

_DICE_LABEL_STYLE = {
    "fontSize": _DICE_FONT,
    "fontWeight": "600",
    "lineHeight": "1.35",
    "color": "#111",
    "padding": "10px 12px 10px 0",
    "verticalAlign": "middle",
    "textAlign": "right",
    "width": "42%",
    "whiteSpace": "nowrap",
    "border": "none",
}
_DICE_VALUE_STYLE = {
    "fontSize": _DICE_FONT,
    "fontWeight": "600",
    "lineHeight": "1.35",
    "color": "#111",
    "padding": "10px 0 10px 8px",
    "verticalAlign": "middle",
    "textAlign": "left",
    "width": "58%",
    "border": "none",
}

layout = html.Div(
    [
        dcc.Store(id="_initial_load", data=True),
        dcc.Store(id="turn-sequence-store", data=None),
        dcc.Interval(id="turn-roll-interval", interval=1500, n_intervals=0, disabled=True),
        html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            id="player-counter-display",
                            children="Players: 0",
                            style={**_HEADER_COUNTER, "textAlign": "left"},
                        ),
                        html.H1(
                            "Stock Ticker Game",
                            style={
                                "text-align": "center",
                                "margin": "0",
                                "flex": "1 1 auto",
                                "minWidth": "0",
                                "font-size": _TITLE_SIZE,
                                "font-weight": "700",
                                "letter-spacing": "0.02em",
                                "color": "#1a1a1a",
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
                                            "format": Format(precision=2, scheme=Scheme.fixed),
                                        },
                                    ],
                                    data=[{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
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
                                html.Table(
                                    html.Tbody(
                                        [
                                            html.Tr(
                                                [
                                                    html.Td("Stock:", style=_DICE_LABEL_STYLE),
                                                    html.Td(
                                                        id="rolled-stock-value",
                                                        children="",
                                                        style=_DICE_VALUE_STYLE,
                                                    ),
                                                ]
                                            ),
                                            html.Tr(
                                                [
                                                    html.Td("Action:", style=_DICE_LABEL_STYLE),
                                                    html.Td(
                                                        id="rolled-action-value",
                                                        children="",
                                                        style=_DICE_VALUE_STYLE,
                                                    ),
                                                ]
                                            ),
                                            html.Tr(
                                                [
                                                    html.Td("Value:", style=_DICE_LABEL_STYLE),
                                                    html.Td(
                                                        id="rolled-value-value",
                                                        children="",
                                                        style=_DICE_VALUE_STYLE,
                                                    ),
                                                ]
                                            ),
                                        ]
                                    ),
                                    style={
                                        "width": "100%",
                                        "borderCollapse": "collapse",
                                        "tableLayout": "fixed",
                                        "border": "none",
                                    },
                                ),
                            ],
                            style={
                                "flex": "0 0 24%",
                                "minWidth": "200px",
                                "maxWidth": "320px",
                                "display": "flex",
                                "flex-direction": "column",
                                "justify-content": "center",
                                "padding": "12px 16px",
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
                        "flex": "1 1 auto",
                        "minHeight": "0",
                        "overflow": "visible",
                    },
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
                        dcc.Graph(
                            id="player-net-timeline-graph",
                            figure=player_net_timeline_fig,
                            config=_GRAPH_CONFIG,
                            style={
                                "width": "100%",
                                "minWidth": "280px",
                                "minHeight": "280px",
                                "flex": "1 1 400px",
                                "maxWidth": "100%",
                            },
                        ),
                        dcc.Graph(
                            id="commodity-timeline-graph",
                            figure=commodity_timeline_fig,
                            config=_GRAPH_CONFIG,
                            style={
                                "width": "100%",
                                "minWidth": "280px",
                                "minHeight": "280px",
                                "flex": "1 1 400px",
                                "maxWidth": "100%",
                            },
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
                        "flexWrap": "wrap",
                        "justifyContent": "center",
                        "alignItems": "stretch",
                        "gap": "16px",
                        "boxSizing": "border-box",
                    },
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
