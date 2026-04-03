from dash import html


def build_play_turn_section():
    return html.Div(
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
    )
