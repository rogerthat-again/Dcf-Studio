"""dcf_charts.py - Plotly figures."""
from __future__ import annotations
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

TEXT, MUTED, PANEL, BORDER = "#E8ECF4", "#9AA7C0", "#1A2238", "#2A3350"
BLUE, TEAL, RED, AMBER, VIOLET, SLATE = "#4C8DFF", "#26A69A", "#EF5350", "#F5B544", "#8B7CF6", "#5B6B8C"
GRID = "rgba(154,167,192,0.14)"
FONT = "IBM Plex Sans, sans-serif"


def _style(fig: go.Figure, height: int = 380) -> go.Figure:
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(family=FONT, color=TEXT, size=13), height=height, dragmode=False,
                      margin=dict(l=16, r=16, t=36, b=36),
                      hoverlabel=dict(bgcolor=PANEL, bordercolor=BORDER, font=dict(family=FONT, color=TEXT, size=13)))
    fig.update_xaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, automargin=True, fixedrange=True,
                     tickfont=dict(color=MUTED, size=12), title_font=dict(color=MUTED, size=12))
    fig.update_yaxes(gridcolor=GRID, zeroline=False, linecolor=GRID, automargin=True, fixedrange=True,
                     tickfont=dict(color=MUTED, size=12), title_font=dict(color=MUTED, size=12))
    return fig


def heatmap(grid, price: float) -> go.Figure:
    z = grid.values / price - 1 if price > 0 else np.zeros(grid.shape)
    text = [["" if np.isnan(v) else f"{v:,.0f}" for v in row] for row in grid.values]
    xs = [f"{c * 100:.2f}%" for c in grid.columns]
    ys = [f"{r * 100:.1f}%" for r in grid.index]
    fig = go.Figure(go.Heatmap(
        z=z, x=xs, y=ys, text=text, texttemplate="₹%{text}", textfont=dict(color="#0D1220", size=12),
        zmin=-0.5, zmax=0.5, xgap=3, ygap=3,
        colorscale=[[0, "#F08A8A"], [0.5, "#F3D27A"], [1, "#6FD8B0"]],
        colorbar=dict(title=dict(text="vs CMP", font=dict(color=MUTED, size=12)), tickformat=".0%", outlinewidth=0,
                      thickness=10, len=0.9, tickfont=dict(color=MUTED, size=11)),
        hovertemplate="Required return %{y} | long-run growth %{x}<br>Value ₹%{text}<br>%{z:.0%} vs CMP<extra></extra>"))
    fig.add_trace(go.Scatter(x=[xs[len(xs) // 2]], y=[ys[len(ys) // 2]], mode="markers", hoverinfo="skip",
                             showlegend=False, marker=dict(symbol="square-open", size=40, line=dict(width=3, color="#FFFFFF"))))
    _style(fig, 460).update_layout(xaxis_title="Long-run (terminal) growth", yaxis_title="Required return (WACC)")
    return fig


def football_field(bars: list[tuple], price: float) -> go.Figure:
    fig = go.Figure()
    for b in bars:
        label, lo, hi = b[:3]
        if not (np.isfinite(lo) and np.isfinite(hi)):
            continue
        lo, hi = min(lo, hi), max(lo, hi)
        fig.add_trace(go.Bar(y=[label], x=[hi - lo], base=[lo], orientation="h", showlegend=False, width=0.5,
                             marker_color=b[3] if len(b) > 3 else TEAL,
                             hovertemplate=f"{label}<br>₹{lo:,.0f} to ₹{hi:,.0f}<extra></extra>"))
    if price and price > 0:
        fig.add_vline(x=price, line_dash="dash", line_color=AMBER, annotation_text=f"CMP ₹{price:,.0f}",
                      annotation_position="top", annotation_font=dict(color=AMBER, size=12))
    _style(fig, 340).update_layout(xaxis_title="Value per share (₹)", margin=dict(l=16, r=16, t=48, b=40))
    fig.update_yaxes(autorange="reversed", showgrid=False)
    return fig


def waterfall(pv_fcff: float, pv_tv: float, net_debt: float, minority: float, years: int) -> go.Figure:
    ev = pv_fcff + pv_tv
    ys = [pv_fcff, pv_tv, ev, -net_debt, -minority, ev - net_debt - minority]
    labels = [f"Cash flows<br>({years} yrs)", "Value after<br>that", "Whole<br>business",
              "Net debt" if net_debt >= 0 else "Net cash", "Minorities", "Share-<br>holders"]
    fig = go.Figure(go.Waterfall(
        x=labels, measure=["relative", "relative", "total", "relative", "relative", "total"], y=ys,
        text=[f"{v:,.0f}" for v in ys], textposition="outside", cliponaxis=False,
        increasing=dict(marker_color=TEAL), decreasing=dict(marker_color=RED), totals=dict(marker_color=BLUE),
        connector=dict(line=dict(color=GRID)), textfont=dict(color=TEXT, size=11)))
    _style(fig, 360).update_layout(yaxis_title="₹ crore", showlegend=False, margin=dict(l=16, r=16, t=48, b=36))
    return fig


def tv_donut(pv_fcff: float, pv_tv: float, years: int) -> go.Figure:
    fig = go.Figure(go.Pie(labels=[f"Next {years} years", "Value after that"], values=[pv_fcff, pv_tv], hole=0.62,
                           marker=dict(colors=[SLATE, BLUE], line=dict(color="#0D1220", width=3)), sort=False,
                           textinfo="percent", textfont=dict(color="#FFFFFF", size=14),
                           hovertemplate="%{label}: ₹%{value:,.0f} cr (%{percent})<extra></extra>"))
    _style(fig, 360).update_layout(showlegend=True, legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.05,
                                                                font=dict(color=MUTED, size=12)))
    return fig


def history_vs_forecast(hist, table, margin: float) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    hx = [f"FY{y}" for y in hist.index]
    last = int(hist.index[-1])
    fx = [f"FY{last + int(t)}E" for t in table.index]
    fig.add_trace(go.Bar(x=hx, y=hist["revenue"], name="Reported revenue", marker_color=SLATE), secondary_y=False)
    fig.add_trace(go.Bar(x=fx, y=table["Revenue"], name="Forecast revenue", marker_color=BLUE), secondary_y=False)
    if "ebit" in hist.columns:
        m = (hist["ebit"] / hist["revenue"]) * 100
        fig.add_trace(go.Scatter(x=hx, y=m, name="Margin (reported)", mode="lines+markers",
                                 line=dict(color=AMBER, width=2)), secondary_y=True)
        fig.add_trace(go.Scatter(x=[hx[-1]] + fx, y=[m.iloc[-1]] + [margin * 100] * len(fx), name="Margin (assumed)",
                                 mode="lines", line=dict(color=AMBER, width=2, dash="dash")), secondary_y=True)
    _style(fig, 400).update_layout(legend=dict(orientation="h", x=0, y=-0.22, font=dict(color=MUTED, size=12)),
                                   barmode="group", hovermode="x unified", margin=dict(l=16, r=16, t=30, b=70))
    fig.update_yaxes(title_text="Revenue (₹ crore)", secondary_y=False)
    fig.update_yaxes(title_text="Profit margin (%)", secondary_y=True, showgrid=False)
    return fig
