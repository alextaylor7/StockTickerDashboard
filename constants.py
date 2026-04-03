# --- Game rules ---
COMMODITIES = ["Gold", "Silver", "Bonds", "Oil", "Industrials", "Grain"]
USER_STARTING_BALANCE = 5000

# --- Server / polling ---
# Default length of a game in turns (current turn label 1..N; ends when TURN_COUNT > N).
DEFAULT_GAME_MAX_TURNS = 52

# Client poll interval for shared stock prices / game meta (ms). Higher values reduce
# Dash HTTP load per phone on LAN parties (see main.py dcc.Interval).
PRICE_POLL_INTERVAL_MS = 2500

# Waitress WSGI thread pool size (single process; do not use multiple Waitress workers).
WAITRESS_THREADS = 16

# Delay before writing session after a trade burst (debounced disk save).
SESSION_SAVE_DEBOUNCE_SEC = 0.75

# --- Chart theme ---
# Dashboard bar chart: one RGB color per commodity (Plotly rgb strings)
COMMODITY_BAR_COLORS = {
    "Gold": "rgb(233,184,81)",
    "Silver": "rgb(236,233,226)",
    "Bonds": "rgb(201,213,193)",
    "Oil": "rgb(228,183,150)",
    "Industrials": "rgb(231,189,209)",
    "Grain": "rgb(233,218,151)",
}

# Timeline line chart: higher saturation for legibility on dark chart background
COMMODITY_TIMELINE_LINE_COLORS = {
    "Gold": "rgb(255, 193, 7)",
    "Silver": "rgb(187, 222, 251)",
    "Bonds": "rgb(102, 187, 106)",
    "Oil": "rgb(255, 152, 0)",
    "Industrials": "rgb(236, 64, 122)",
    "Grain": "rgb(205, 220, 57)",
}

CHART_BG = "#2e2e2e"
CHART_TEXT = "#ececec"
