from dash import dcc, html

from constants import DEFAULT_GAME_MAX_TURNS


def build_settings_modal():
    return html.Div(
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
    )


def build_players_modal():
    return html.Div(
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
    )
