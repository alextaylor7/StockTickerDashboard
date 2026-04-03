"""Single in-process mirror of commodity prices for the dashboard dice loop (synced with server.config)."""

from constants import COMMODITIES

# Canonical mutable dict — importers must not rebind this name; use replace_live_prices.
live_prices: dict[str, float] = {c: round(1.00, 2) for c in COMMODITIES}


def replace_live_prices(prices: dict[str, float]) -> None:
    """Replace all COMMODITIES entries in live_prices in place (normalized to 2 decimals)."""
    normalized = {c: round(float(prices.get(c, 1.00)), 2) for c in COMMODITIES}
    live_prices.clear()
    live_prices.update(normalized)


def par_prices_copy() -> dict[str, float]:
    """Fresh par ($1) price dict for initial page layout (not the live mutable dict)."""
    return {c: round(1.00, 2) for c in COMMODITIES}


def normalize_live_prices_round_trip() -> None:
    """Re-round every commodity in live_prices (e.g. after hydrate when server had no STOCK_PRICES)."""
    for c in COMMODITIES:
        live_prices[c] = round(float(live_prices.get(c, 1.00)), 2)
