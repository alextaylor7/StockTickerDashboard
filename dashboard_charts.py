"""Plotly figures and table row helpers for the dashboard layout (no Dash callbacks).

Kept separate so `pages/dashboard.py` can import during `Dash(use_pages=True)` init without
registering callbacks before the app instance exists (Dash 3).
"""
from __future__ import annotations

import plotly.graph_objects as go

from constants import (
    CHART_BG,
    CHART_TEXT,
    COMMODITY_BAR_COLORS,
    COMMODITY_TIMELINE_LINE_COLORS,
    commodities,
)


def _dashboard_table_rows(stock_prices_dict: dict, baseline_prices: dict | None = None) -> list[dict]:
    """Table shows Price as value×100 and ChangeThisTurn vs baseline (×100); storage stays in dollars."""
    if baseline_prices is None:
        baseline_prices = {c: round(1.00, 2) for c in commodities}
    rows: list[dict] = []
    for k, v in stock_prices_dict.items():
        cur = int(round(float(v) * 100))
        base = int(round(float(baseline_prices.get(k, 1.00)) * 100))
        rows.append(
            {
                "Commodity": k,
                "Price": cur,
                "ChangeThisTurn": cur - base,
            }
        )
    return rows


def _timeline_base_layout(title: str, y_title: str):
    return dict(
        title=dict(text=title, font=dict(color=CHART_TEXT, size=22)),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color=CHART_TEXT, size=16),
        margin=dict(l=56, r=28, t=64, b=52),
        legend=dict(font=dict(color=CHART_TEXT, size=14)),
        xaxis=dict(
            title=dict(text="Turn", font=dict(size=14)),
            gridcolor="rgba(255,255,255,0.15)",
            tickfont=dict(size=14),
        ),
        yaxis=dict(
            title=dict(text=y_title, font=dict(size=14)),
            gridcolor="rgba(255,255,255,0.15)",
            zerolinecolor="rgba(255,255,255,0.25)",
            tickfont=dict(size=14),
        ),
    )


def build_stock_graph_figure(stock_prices_dict):
    x = list(commodities)
    y = [stock_prices_dict[c] * 100 for c in commodities]
    colors = [COMMODITY_BAR_COLORS[c] for c in commodities]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=x,
            y=y,
            marker_color=colors,
            marker_line=dict(color="rgba(0,0,0,0.35)", width=1),
        )
    )
    fig.update_layout(
        title=dict(text="Stock Prices", font=dict(color=CHART_TEXT, size=22)),
        plot_bgcolor=CHART_BG,
        paper_bgcolor=CHART_BG,
        font=dict(color=CHART_TEXT, size=16),
        margin=dict(l=56, r=28, t=64, b=52),
        yaxis=dict(
            range=[0, 200],
            gridcolor="rgba(255,255,255,0.15)",
            zerolinecolor="rgba(255,255,255,0.25)",
            tickfont=dict(size=16),
            title=dict(text="Price (×100)", font=dict(size=16)),
        ),
        xaxis=dict(
            gridcolor="rgba(255,255,255,0.1)",
            tickfont=dict(size=15),
        ),
    )
    return fig


def build_player_net_timeline_figure(timeline: list) -> go.Figure:
    fig = go.Figure()
    if not isinstance(timeline, list) or len(timeline) == 0:
        fig.update_layout(**_timeline_base_layout("Player Net Value", "Net Value ($)"))
        return fig

    turns = [p["turn"] for p in timeline if isinstance(p, dict)]
    names: set[str] = set()
    for p in timeline:
        if isinstance(p, dict) and isinstance(p.get("player_net"), dict):
            names.update(p["player_net"].keys())
    for name in sorted(names):
        ys = []
        for p in timeline:
            if not isinstance(p, dict):
                ys.append(None)
                continue
            pn = p.get("player_net") if isinstance(p.get("player_net"), dict) else {}
            v = pn.get(name)
            ys.append(v if v is not None else None)
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=ys,
                mode="lines+markers",
                name=name,
                connectgaps=False,
            )
        )
    fig.update_layout(**_timeline_base_layout("Player Net Value", "Net Value ($)"))
    return fig


def build_commodity_timeline_figure(timeline: list) -> go.Figure:
    fig = go.Figure()
    if not isinstance(timeline, list) or len(timeline) == 0:
        fig.update_layout(**_timeline_base_layout("Commodity Prices", "Price (×100)"))
        return fig

    turns = [p["turn"] for p in timeline if isinstance(p, dict)]
    for c in commodities:
        ys = []
        for p in timeline:
            if not isinstance(p, dict):
                ys.append(None)
                continue
            sp = p.get("stock_prices") if isinstance(p.get("stock_prices"), dict) else {}
            raw = sp.get(c)
            ys.append(raw * 100 if raw is not None else None)
        line_color = COMMODITY_TIMELINE_LINE_COLORS.get(c, "#cccccc")
        fig.add_trace(
            go.Scatter(
                x=turns,
                y=ys,
                mode="lines+markers",
                name=c,
                line=dict(color=line_color, width=2),
                marker=dict(
                    size=8,
                    color=line_color,
                    line=dict(width=1, color="rgba(0,0,0,0.45)"),
                ),
                connectgaps=False,
            )
        )
    fig.update_layout(**_timeline_base_layout("Commodity Prices", "Price (×100)"))
    return fig
