from dash import dcc, html, register_page

import callbacks.sign_in_callbacks  # noqa: F401 — navigation callback

register_page(__name__, path="/")

layout = html.Div(
    [
        html.Div(
            [
                html.H1("Stock Ticker", className="landing-title"),
                html.P(
                    "Enter your name to open your portfolio, or jump to the dashboard to roll the market.",
                    className="landing-subtitle",
                ),
                html.Div(
                    [
                        dcc.Input(
                            id="username-input",
                            type="text",
                            placeholder="Your name",
                            autoComplete="name",
                            style={
                                "width": "100%",
                                "minHeight": "52px",
                                "padding": "12px 14px",
                                "fontSize": "max(16px, 1rem)",
                                "border": "1px solid #ccc",
                                "borderRadius": "8px",
                                "marginBottom": "4px",
                                "boxSizing": "border-box",
                                "fontFamily": "system-ui, Segoe UI, sans-serif",
                            },
                        ),
                        html.Button(
                            "Enter User Mode",
                            id="nav-user",
                            n_clicks=0,
                            className="landing-btn landing-btn-primary",
                        ),
                        html.Button(
                            "Go to Dashboard",
                            id="nav-dashboard",
                            n_clicks=0,
                            className="landing-btn landing-btn-secondary",
                        ),
                        html.Div(
                            [
                                html.Button(
                                    "Save session",
                                    id="session-save-btn",
                                    n_clicks=0,
                                    className="landing-btn landing-btn-session",
                                ),
                                html.Button(
                                    "Load session",
                                    id="session-load-btn",
                                    n_clicks=0,
                                    className="landing-btn landing-btn-session landing-btn-session-secondary",
                                ),
                            ],
                            className="session-actions",
                        ),
                        html.Div(id="session-feedback", className="session-feedback", children=""),
                    ],
                    className="landing-card",
                ),
            ],
            className="landing-inner",
        ),
    ],
    className="landing-page",
)
