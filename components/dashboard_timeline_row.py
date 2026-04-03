from dash import dcc, html

from components.dashboard_styles import GRAPH_CONFIG


def build_timeline_row(player_net_timeline_fig, commodity_timeline_fig):
    return html.Div(
        [
            html.Div(
                dcc.Graph(
                    id="player-net-timeline-graph",
                    figure=player_net_timeline_fig,
                    config=GRAPH_CONFIG,
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
                    config=GRAPH_CONFIG,
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
    )
