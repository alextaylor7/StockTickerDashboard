commodities = ["Gold", "Silver", "Bonds", "Oil", "Industrials", "Grain"]
user_starting_balance = 5000

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
