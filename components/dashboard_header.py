from dash import html

from components.dashboard_styles import HEADER_COUNTER, TITLE_SIZE


def build_dashboard_header():
    return html.Div(
        [
            html.Button(
                id="player-counter-display",
                children="Players: 0",
                n_clicks=0,
                title="View players",
                style={
                    **HEADER_COUNTER,
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
                    "font-size": TITLE_SIZE,
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
    )
