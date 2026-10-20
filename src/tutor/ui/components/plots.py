"""Plotly helpers following the plot rules of spec 16.9.

* every axis: quantity + unit
* direct labels instead of legends
* exact = solid, approximation = dashed (distinguishable without colour)
* operating-point marker for the current slider value
* fixed axis ranges (no auto-rescale), zoom disabled → no "reset view" needed
"""

from __future__ import annotations

import math
import textwrap

import plotly.graph_objects as go
import streamlit as st

from tutor.ui.svg.core import CURRENT, INK, MINUS, MUTED, PLUS, VOLT

FONT = "Segoe UI, system-ui, -apple-system, Helvetica Neue, Arial, sans-serif"
COLORS = {"ink": INK, "volt": VOLT, "cur": CURRENT, "plus": PLUS, "minus": MINUS, "muted": MUTED}


def figure(x_title: str, y_title: str, x_range: tuple[float, float], y_range: tuple[float, float],
           height: int = 300) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        height=height,
        margin=dict(l=64, r=110, t=16, b=52),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#ffffff",
        font=dict(family=FONT, size=13, color=INK),
        showlegend=False,
        hovermode=False,
        dragmode=False,
    )
    axis = dict(showgrid=True, gridcolor="#ece7dc", zeroline=True, zerolinecolor="#b9b2a2", zerolinewidth=1.2,
                linecolor="#b9b2a2", showline=True, mirror=True, ticks="outside", fixedrange=True,
                automargin=True)
    fig.update_xaxes(title_text=x_title, range=list(x_range), **axis)
    fig.update_yaxes(title_text=y_title, range=list(y_range), **axis)
    return fig


def line(fig: go.Figure, x, y, label: str, color: str = INK, dash: str = "solid", width: float = 2.6,
         label_at: float | None = None, label_y_shift: int = 0, x_log: bool = False) -> None:
    fig.add_trace(go.Scatter(x=list(x), y=list(y), mode="lines", line=dict(color=color, width=width, dash=dash),
                             name=label, hoverinfo="skip"))
    # direct label at the right end (or at a given x)
    xs, ys = list(x), list(y)
    if not xs:
        return
    if label_at is None:
        lx, ly = xs[-1], ys[-1]
    else:
        idx = min(range(len(xs)), key=lambda i: abs(xs[i] - label_at))
        lx, ly = xs[idx], ys[idx]
    if x_log:  # Plotly positions annotations on log axes in log10 units
        lx = math.log10(lx)
    # Keep direct labels inside the reserved margin at tablet widths. Preserve
    # words and notation; stack a long explanation instead of shrinking it.
    label_lines = textwrap.wrap(label, width=14, break_long_words=False, break_on_hyphens=False)
    display_label = "<br>".join(label_lines)
    if label_y_shift:
        label_y_shift += math.copysign(9 * (len(label_lines) - 1), label_y_shift)
    fig.add_annotation(x=lx, y=ly, text=f"<b>{display_label}</b>", showarrow=False, xanchor="left", xshift=6,
                       yshift=label_y_shift, font=dict(color=color, size=12))


def point(fig: go.Figure, x: float, y: float, label: str, color: str = VOLT, show_guides: bool = True) -> None:
    if show_guides:
        fig.add_vline(x=x, line=dict(color=color, width=1.2, dash="dot"))
    fig.add_trace(go.Scatter(x=[x], y=[y], mode="markers", marker=dict(size=13, color=color, symbol="circle",
                                                                        line=dict(color="#ffffff", width=2)),
                             hoverinfo="skip"))
    # Point callouts face into the plotting area near its top/right edges.
    # Plotly annotations (unlike traces) require log10 coordinates on log axes.
    label_x = math.log10(x) if fig.layout.xaxis.type == "log" else x
    x_lo, x_hi = fig.layout.xaxis.range
    y_lo, y_hi = fig.layout.yaxis.range
    ax = -34 if label_x > x_lo + 0.8 * (x_hi - x_lo) else 34
    ay = 28 if y > y_lo + 0.85 * (y_hi - y_lo) else -28
    fig.add_annotation(x=label_x, y=y, text=label, showarrow=True, arrowhead=0, ax=ax, ay=ay,
                       font=dict(color=color, size=12), bgcolor="rgba(255,255,255,.85)")


def band(fig: go.Figure, x0: float, x1: float, label: str, color: str = "#b91c1c") -> None:
    """Hatched region (unstable / invalid) — pattern + text, never colour alone."""
    fig.add_vrect(x0=x0, x1=x1, fillcolor=color, opacity=0.07, line_width=0, layer="below")
    fig.add_vrect(x0=x0, x1=x1, fillcolor="rgba(0,0,0,0)", line=dict(color=color, width=1, dash="dot"))
    fig.add_annotation(x=(x0 + x1) / 2, y=1, yref="paper", text=label, showarrow=False, yanchor="top",
                       font=dict(color=color, size=11))


def show(fig: go.Figure, key: str) -> None:
    st.plotly_chart(fig, key=key, config={"displayModeBar": False, "staticPlot": False, "responsive": True})
