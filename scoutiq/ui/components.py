"""Plotly visualization components and charts for ScoutIQ."""

from __future__ import annotations
from typing import Dict, List, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

PALETTE = {
    "emerald": "#10b981",
    "blue": "#38bdf8",
    "gold": "#f59e0b",
    "rose": "#f43f5e",
    "purple": "#a855f7",
    "slate": "#64748b",
    "dark_bg": "#0f172a",
    "card_bg": "#131d31"
}


def render_player_radar(player1: pd.Series, player2: pd.Series | None = None) -> go.Figure:
    """Render a FIFA-style hexagonal attribute radar chart."""
    categories = ["Pace", "Shooting", "Passing", "Dribbling", "Defending", "Physical"]
    p1_vals = [
        player1.get("pace", 60),
        player1.get("shooting", 60),
        player1.get("passing", 60),
        player1.get("dribbling", 60),
        player1.get("defending", 60),
        player1.get("physical", 60)
    ]
    # Close polygon
    p1_vals.append(p1_vals[0])
    cat_closed = categories + [categories[0]]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=p1_vals,
        theta=cat_closed,
        fill='toself',
        name=player1.get("name", "Player 1"),
        line=dict(color=PALETTE["emerald"], width=2.5),
        fillcolor="rgba(16, 185, 129, 0.28)"
    ))

    if player2 is not None:
        p2_vals = [
            player2.get("pace", 60),
            player2.get("shooting", 60),
            player2.get("passing", 60),
            player2.get("dribbling", 60),
            player2.get("defending", 60),
            player2.get("physical", 60)
        ]
        p2_vals.append(p2_vals[0])
        fig.add_trace(go.Scatterpolar(
            r=p2_vals,
            theta=cat_closed,
            fill='toself',
            name=player2.get("name", "Player 2"),
            line=dict(color=PALETTE["blue"], width=2.5),
            fillcolor="rgba(56, 189, 248, 0.25)"
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[20, 100],
                tickfont=dict(color="#64748b", size=9),
                linecolor="rgba(255, 255, 255, 0.1)",
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            angularaxis=dict(
                tickfont=dict(color="#e2e8f0", size=11, family="Inter"),
                linecolor="rgba(255, 255, 255, 0.15)",
                gridcolor="rgba(255, 255, 255, 0.1)"
            ),
            bgcolor="rgba(0,0,0,0)"
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=30, b=30),
        legend=dict(
            font=dict(color="#cbd5e1"),
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=340
    )
    return fig


def render_valuation_drivers_bar(explanations: List[Dict[str, Any]]) -> go.Figure:
    """Render horizontal bar chart explaining driver deltas (+/- €M)."""
    if not explanations:
        return go.Figure()

    cats = [e["category"] for e in explanations]
    deltas = [e["delta_eur_m"] for e in explanations]
    colors = [PALETTE["emerald"] if d >= 0 else PALETTE["rose"] for d in deltas]

    fig = go.Figure(go.Bar(
        y=cats,
        x=deltas,
        orientation='h',
        marker=dict(color=colors, line=dict(width=0)),
        text=[f"{'+' if d >= 0 else ''}{d:.1f}M €" for d in deltas],
        textposition='outside',
        textfont=dict(color="#f8fafc", size=11)
    ))

    fig.update_layout(
        title=dict(
            text="Key Valuation Drivers vs. Market Baseline",
            font=dict(color="#f1f5f9", size=13)
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            title="Impact on Valuation (€ Millions)",
            color="#94a3b8",
            gridcolor="rgba(255, 255, 255, 0.08)",
            zerolinecolor="rgba(255, 255, 255, 0.3)"
        ),
        yaxis=dict(
            color="#cbd5e1",
            autorange="reversed"
        ),
        margin=dict(l=10, r=40, t=40, b=20),
        height=260
    )
    return fig


def render_feature_importance_chart(fi_df: pd.DataFrame, top_n: int = 12) -> go.Figure:
    """Render top feature importances from the regression tree ensemble."""
    top_df = fi_df.head(top_n).iloc[::-1]  # reverse for horizontal bar

    fig = go.Figure(go.Bar(
        x=top_df["importance"],
        y=top_df["display_name"],
        orientation='h',
        marker=dict(
            color=top_df["importance"],
            colorscale=[[0, "#064e3b"], [0.5, "#10b981"], [1.0, "#38bdf8"]],
            line=dict(width=0)
        )
    ))

    fig.update_layout(
        title=dict(text="Top Machine Learning Feature Importances (Tree Ensemble)", font=dict(color="#f1f5f9", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Relative Gini Importance", color="#94a3b8", gridcolor="rgba(255, 255, 255, 0.08)"),
        yaxis=dict(color="#cbd5e1"),
        margin=dict(l=10, r=20, t=40, b=20),
        height=380
    )
    return fig


def render_residuals_plot(y_true: np.ndarray, y_pred: np.ndarray) -> go.Figure:
    """Render Actual vs. Predicted scatter plot with perfect prediction diagonal."""
    max_val = max(np.max(y_true), np.max(y_pred)) * 1.05

    fig = go.Figure()

    # Scatter points
    fig.add_trace(go.Scatter(
        x=y_true,
        y=y_pred,
        mode='markers',
        marker=dict(
            color=PALETTE["blue"],
            size=6,
            opacity=0.6,
            line=dict(width=1, color="rgba(255,255,255,0.2)")
        ),
        name="Players (Test Set)"
    ))

    # 45-degree reference line
    fig.add_trace(go.Scatter(
        x=[0, max_val],
        y=[0, max_val],
        mode='lines',
        line=dict(color=PALETTE["gold"], dash='dash', width=2),
        name="Ideal 1:1 Parity"
    ))

    fig.update_layout(
        title=dict(text="Model Validation: Actual vs. Predicted Market Value (€M)", font=dict(color="#f1f5f9", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(title="Actual Market Value (€M)", color="#94a3b8", gridcolor="rgba(255, 255, 255, 0.08)"),
        yaxis=dict(title="Model Predicted Value (€M)", color="#94a3b8", gridcolor="rgba(255, 255, 255, 0.08)"),
        legend=dict(font=dict(color="#cbd5e1")),
        margin=dict(l=20, r=20, t=40, b=20),
        height=380
    )
    return fig


def render_correlation_heatmap(df: pd.DataFrame, cols: List[str]) -> go.Figure:
    """Render correlation heatmap for key football performance features."""
    valid_cols = [c for c in cols if c in df.columns]
    corr = df[valid_cols].corr()

    labels = [c.replace("_p90", "/90").replace("_", " ").title() for c in valid_cols]

    fig = px.imshow(
        corr,
        x=labels,
        y=labels,
        color_continuous_scale="Viridis",
        aspect="auto"
    )

    fig.update_layout(
        title=dict(text="Feature Correlation Matrix", font=dict(color="#f1f5f9", size=14)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", size=10),
        margin=dict(l=20, r=20, t=40, b=20),
        height=400
    )
    return fig
