from dash import dcc, html, register_page

from components.dashboard_header import build_dashboard_header
from components.dashboard_main_row import build_dashboard_main_row
from components.dashboard_modals import build_players_modal, build_settings_modal
from components.dashboard_play_section import build_play_turn_section
from components.dashboard_timeline_row import build_timeline_row
from dashboard_charts import (
    build_commodity_timeline_figure,
    build_player_net_timeline_figure,
    build_stock_graph_figure,
)
from runtime.live_stock_prices import par_prices_copy

register_page(__name__, path="/dashboard")

stock_prices = par_prices_copy()
fig = build_stock_graph_figure(stock_prices)
player_net_timeline_fig = build_player_net_timeline_figure([])
commodity_timeline_fig = build_commodity_timeline_figure([])

layout = html.Div(
    [
        dcc.Store(id="_initial_load", data=True),
        dcc.Store(id="turn-sequence-store", data=None),
        dcc.Interval(id="turn-roll-interval", interval=1000, n_intervals=0, disabled=True),
        html.Div(
            [
                build_dashboard_header(),
                build_settings_modal(),
                build_players_modal(),
                build_dashboard_main_row(stock_prices, fig),
                build_play_turn_section(),
                build_timeline_row(player_net_timeline_fig, commodity_timeline_fig),
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
