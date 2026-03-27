from dash import dcc, html, register_page, dash_table
from dash.dash_table.Format import Format, Scheme
from constants import commodities
from callbacks.dashboard_callbacks import build_stock_graph_figure

register_page(__name__, path="/dashboard")

# Stock data setup

stock_prices = {commodity: 1.00 for commodity in commodities}

fig = build_stock_graph_figure(stock_prices)

layout = html.Div([
        dcc.Store(id='_initial_load', data=True),
        html.H1("Stock Ticker Game", style={'text-align': 'center', 'margin': '10px 0'}),

        html.Div([
            dash_table.DataTable(
                id='stock-table',
                columns=[{"name": "Commodity", "id": "Commodity"},
                         {"name": "Price", "id": "Price", "type": "numeric",
                          "format": Format(precision=2, scheme=Scheme.fixed)}],
                data=[{"Commodity": k, "Price": v} for k, v in stock_prices.items()],
                style_table={'width': '40%', 'height': '100%', 'display': 'inline-block', 'vertical-align': 'top'},
                style_cell={'textAlign': 'center', 'fontSize': '16px', 'padding': '10px'},
                style_header={'fontWeight': 'bold'}
            ),

            html.Div([
                html.Div("Stock: ", id="rolled-stock", style={'font-size': '20px', 'margin': '5px'}),
                html.Div("Action: ", id="rolled-action", style={'font-size': '20px', 'margin': '5px'}),
                html.Div("Value: ", id="rolled-value", style={'font-size': '20px', 'margin': '5px'})
            ], style={'width': '20%', 'text-align': 'center', 'display': 'inline-block', 'vertical-align': 'top'}),

            dcc.Graph(
                id="stock-graph",
                figure=fig,
                style={'width': '40%', 'height': '100%', 'display': 'inline-block'}
            ),
        ], style={'display': 'flex', 'justify-content': 'space-between', 'align-items': 'stretch', 'width': '100%',
                  'height': '60vh'}),

        html.Button("Roll Dice", id="roll-btn", n_clicks=0, style={'margin-top': '20px','width': '100%', 'height': '100%'}),
        html.Div(id="roll-result", style={'margin-top': '10px'}),
    ], style={'width': '100%', 'height': '100%', 'margin': '0', 'padding': '20px', 'box-sizing': 'border-box',
              'overflow': 'hidden'})
