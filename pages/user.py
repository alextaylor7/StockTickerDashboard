from dash import dcc, html, register_page, dash_table
import callbacks.user_callbacks

# User stock data setup
commodities = ["Gold", "Silver", "Bonds", "Oil", "Industrials", "Grain"]
user_stocks = {commodity: 0 for commodity in commodities}
user_balance = 5000
stock_prices = {commodity: 1.00 for commodity in commodities}  # Default stock prices

register_page(__name__, path="/user")

layout = html.Div([
        html.H2("User Portfolio", id="profile-name", style={'text-align': 'center'}),

        html.Div(f"Balance: ${user_balance}", id='user-balance',
                 style={'text-align': 'center', 'font-size': '18px', 'margin-bottom': '10px'}),
        html.Div(f"Net Value: ${user_balance}", id='user-net-value',
                 style={'text-align': 'center', 'font-size': '18px', 'margin-bottom': '10px'}),

        html.Div([
            dash_table.DataTable(
                id='user-stock-table',
                columns=[{"name": "Commodity", "id": "Commodity"},
                         {"name": "Shares", "id": "Shares"}],
                data=[{"Commodity": k, "Shares": v} for k, v in user_stocks.items()],
                style_table={'width': '100%', 'margin': 'auto'},
                style_cell={'textAlign': 'center', 'fontSize': '14px', 'padding': '10px'},
                style_header={'fontWeight': 'bold'}
            )
        ], style={'display': 'flex', 'justify-content': 'center', 'margin-bottom': '20px', 'width': '100%'}),

        html.Div([
            dcc.Dropdown(id='stock-select', options=[{'label': c, 'value': c} for c in commodities],
                         placeholder='Select a stock', style={'width': '100%', 'margin-bottom': '10px'},
                         clearable=False, searchable=False),

            html.Div([
                html.Div("Buy", style={'text-align': 'center', 'font-weight': 'bold'}),
                html.Div("Sell", style={'text-align': 'center', 'font-weight': 'bold'})
            ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%', 'margin-bottom': '5px'}),

            html.Div([
                html.Div([
                    html.Button("500", id='buy-500-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'green', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px', 'margin-bottom': '5px'}),
                    html.Button("1000", id='buy-1000-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'green', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px', 'margin-bottom': '5px'}),
                    html.Button("2000", id='buy-2000-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'green', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px', 'margin-bottom': '5px'}),
                    html.Button("5000", id='buy-5000-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'green', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px'})
                ], style={'width': '48%'}),

                html.Div([
                    html.Button("500", id='sell-500-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'red', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px', 'margin-bottom': '5px'}),
                    html.Button("1000", id='sell-1000-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'red', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px', 'margin-bottom': '5px'}),
                    html.Button("2000", id='sell-2000-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'red', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px', 'margin-bottom': '5px'}),
                    html.Button("5000", id='sell-5000-btn', n_clicks=0,
                                style={'width': '100%', 'background-color': 'red', 'color': 'white',
                                       'font-size': '18px', 'padding': '10px'})
                ], style={'width': '48%'})
            ], style={'display': 'flex', 'justify-content': 'space-between', 'width': '100%', 'gap': '4%',
                      'margin': 'auto'}),
        ], style={'text-align': 'center', 'margin-top': '20px', 'width': '90%', 'margin': 'auto'}),

        html.Div(id='transaction-message', style={'text-align': 'center', 'margin-top': '10px', 'font-size': '16px'}),
        dcc.Store(id="user-data", storage_type="session"),
    ], style={'width': '90%', 'margin': 'auto', 'padding': '10px', 'display': 'flex', 'flex-direction': 'column',
              'align-items': 'center'})
