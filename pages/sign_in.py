from dash import dcc, html, register_page
import callbacks.sign_in_callbacks

register_page(__name__, path="/")

layout = html.Div([
        html.H2("Welcome to Stock Ticker", style={'text-align': 'center'}),

        html.Div([
            dcc.Input(id='username-input', type='text', placeholder='Enter your name',
                      style={'width': '100%', 'padding': '10px', 'font-size': '16px'}),
            html.Button("Enter User Mode", id='nav-user', n_clicks=0,
                        style={'width': '100%', 'margin-top': '10px', 'padding': '10px', 'font-size': '16px'}),
            html.Button("Go to Dashboard", id='nav-dashboard', n_clicks=0,
                        style={'width': '100%', 'margin-top': '10px', 'padding': '10px', 'font-size': '16px'}),
            dcc.Store(id="nav-store", storage_type="memory"),
        ], style={'max-width': '300px', 'margin': 'auto', 'text-align': 'center'})
    ], style={'display': 'flex', 'flex-direction': 'column', 'align-items': 'center', 'justify-content': 'center',
              'height': '100vh'})
