from dash import dcc, html, dash_table
from dash.dash_table.Format import Format, Scheme

from components.dashboard_styles import GRAPH_CONFIG, TABLE_FONT
from dashboard_charts import dashboard_table_rows


def build_dashboard_main_row(stock_prices, fig):
    return html.Div(
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
                            "fontSize": TABLE_FONT,
                            "padding": "14px 16px",
                            "fontFamily": "system-ui, Segoe UI, sans-serif",
                        },
                        style_header={
                            "fontWeight": "700",
                            "fontSize": TABLE_FONT,
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
                        config=GRAPH_CONFIG,
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
    )
