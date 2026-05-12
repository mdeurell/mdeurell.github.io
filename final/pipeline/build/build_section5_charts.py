"""Section-5 price visualisations built from price_unified.csv.

Outputs (under website/visualizations/prices/):
  - price_small_multiples.html   (new Figure 5.1) — 10 per-material panels,
    real-2015 USD/kg, 1900–2024, independent y-axes per panel.
  - price_index_modern.html      (new Figure 5.2) — 2000–2024 zoom, all ten
    materials on one chart, 2015 = 100.
  - price_correlation.html       (new Figure 5.3) — pairwise YoY correlation
    matrix across the ten materials, 2000–2024, clustered.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.cluster.hierarchy import linkage, leaves_list

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from website.theme import (
    FONT_FAMILY,
    MINERAL_COLORS,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PAPER_WARM,
    PRUSSIAN,
    OXBLOOD,
    apply_theme,
    write_chart,
)

PRICE_PATH = ROOT / "data" / "processed" / "price_unified.csv"
OUT_DIR = ROOT / "website" / "visualizations" / "prices"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MINERALS_ORDER = [
    "Copper", "Lithium", "Graphite",
    "Cobalt", "Gallium", "Platinum",
    "Rare Earths", "Neodymium", "Dysprosium", "Terbium",
]

# Per-mineral display unit. $/kg for high-value or low-tonnage materials so
# tooltips read naturally; $/tonne for industrial bulk.
DISPLAY_UNIT_KG = {"Cobalt", "Gallium", "Platinum", "Rare Earths",
                   "Neodymium", "Dysprosium", "Terbium"}


def _load_prices() -> pd.DataFrame:
    df = pd.read_csv(PRICE_PATH)
    return df


# ── Figure 5.1: small multiples (full-history per-material price panels) ───
def build_small_multiples() -> Path:
    df = _load_prices()
    df = df[df["mineral"].isin(MINERALS_ORDER)].copy()

    # 5 columns × 2 rows
    n_cols = 5
    n_rows = 2
    fig = make_subplots(
        rows=n_rows, cols=n_cols,
        subplot_titles=MINERALS_ORDER,
        horizontal_spacing=0.045, vertical_spacing=0.18,
    )

    for idx, mineral in enumerate(MINERALS_ORDER):
        row = idx // n_cols + 1
        col = idx % n_cols + 1
        sub = df[df["mineral"] == mineral].dropna(subset=["price_real_2015_usd_per_tonne"])
        if sub.empty:
            continue
        # Convert $/tonne to display unit
        unit = "kg" if mineral in DISPLAY_UNIT_KG else "tonne"
        divisor = 1000.0 if unit == "kg" else 1.0
        y = sub["price_real_2015_usd_per_tonne"] / divisor

        color = MINERAL_COLORS.get(mineral, PRUSSIAN)
        fig.add_trace(
            go.Scatter(
                x=sub["year"], y=y,
                mode="lines",
                line=dict(color=color, width=2.2),
                name=mineral, showlegend=False,
                hovertemplate=(
                    f"<b>{mineral}</b><br>"
                    "%{x} · $%{y:,.1f}/" + unit
                    + " (real 2015 USD)<extra></extra>"
                ),
            ),
            row=row, col=col,
        )
        # 2015 baseline marker on each panel
        if 2015 in sub["year"].values:
            base_v = (sub.loc[sub["year"] == 2015, "price_real_2015_usd_per_tonne"].iloc[0]) / divisor
            fig.add_trace(
                go.Scatter(
                    x=[2015], y=[base_v], mode="markers",
                    marker=dict(size=6, color=PAPER_INK, line=dict(width=0)),
                    showlegend=False, hoverinfo="skip",
                ),
                row=row, col=col,
            )
        # axis unit label
        fig.update_yaxes(
            title_text=f"$/{unit}",
            title_font=dict(size=11, color=PAPER_INK),
            tickfont=dict(size=10, color=PAPER_INK),
            gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE,
            row=row, col=col,
        )
        fig.update_xaxes(
            range=[1900, 2025],
            tickfont=dict(size=10, color=PAPER_INK),
            gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE,
            row=row, col=col,
        )
    fig.update_layout(
        title=dict(
            text=(
                "<b>Real prices, 1900–2024, by material</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Each panel is rebased to real 2015 USD. Y-axis independent — "
                "compare shapes, not levels.</span>"
            ),
        ),
        height=700,
        margin=dict(l=70, r=40, t=140, b=80),
        showlegend=False,
    )
    # Bigger subplot titles
    fig.update_annotations(font=dict(size=14, color=PAPER_INK))

    out = OUT_DIR / "price_small_multiples.html"
    write_chart(fig, out)
    return out


# ── Figure 5.2: modern-era zoom (2000–2024, 2015 = 100) ────────────────────
def build_index_modern() -> Path:
    df = _load_prices()
    df = df[df["mineral"].isin(MINERALS_ORDER)].copy()
    df = df[(df["year"] >= 2000) & (df["year"] <= 2024)]

    fig = go.Figure()
    for mineral in MINERALS_ORDER:
        sub = df[df["mineral"] == mineral].dropna(subset=["price_index_2015_eq_100"])
        if sub.empty:
            continue
        color = MINERAL_COLORS.get(mineral, PRUSSIAN)
        fig.add_trace(
            go.Scatter(
                x=sub["year"], y=sub["price_index_2015_eq_100"],
                mode="lines",
                name=mineral,
                line=dict(color=color, width=2.6),
                hovertemplate=(
                    f"<b>{mineral}</b><br>"
                    "%{x} · index %{y:.0f} (2015 = 100)<extra></extra>"
                ),
            )
        )

    fig.add_hline(y=100, line_dash="dot", line_color="rgba(20,17,13,0.35)")
    fig.update_layout(
        title=dict(
            text=(
                "<b>Modern-era price moves, 2000–2024</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Each line indexed to its own 2015 average = 100. Real terms.</span>"
            ),
        ),
        xaxis=dict(title="Year", range=[2000, 2024]),
        yaxis=dict(title="Index (2015 = 100)"),
        margin=dict(l=80, r=80, t=140, b=130),
    )

    out = OUT_DIR / "price_index_modern.html"
    write_chart(fig, out, legend_pos="top-center")
    return out


# Materials used in the correlation matrix. Nd / Dy / Tb derive from the
# same Rare Earths basket series in price_unified.csv, so a per-element
# matrix shows them as perfectly correlated (r ≈ 1) and inflates the REE
# cluster. We group them into the single "Rare Earths" row/column.
CORR_MINERALS = [
    "Copper", "Lithium", "Graphite",
    "Cobalt", "Gallium", "Platinum",
    "Rare Earths",
]


# ── Figure 5.3: correlation matrix (YoY % change, 2000-2024, clustered) ────
def build_correlation() -> Path:
    df = _load_prices()
    df = df[df["mineral"].isin(CORR_MINERALS)].copy()
    df = df[(df["year"] >= 2000) & (df["year"] <= 2024)]

    # Pivot to wide, then YoY % change
    wide = df.pivot(index="year", columns="mineral", values="price_index_2015_eq_100")
    yoy = wide.pct_change().dropna(how="all")

    corr = yoy.corr(method="pearson", min_periods=8)

    # Hierarchical clustering on 1-corr distance
    dist = (1 - corr.fillna(0)).values
    # condensed form for linkage
    tri = dist[np.triu_indices_from(dist, k=1)]
    Z = linkage(tri, method="average")
    order_idx = leaves_list(Z)
    ordered_mins = corr.columns[order_idx].tolist()
    corr_ord = corr.loc[ordered_mins, ordered_mins]

    z = corr_ord.values
    n = len(ordered_mins)

    # Diverging colorscale: oxblood (neg) ↔ paper-warm (0) ↔ prussian (pos)
    colorscale = [
        [0.00, OXBLOOD],
        [0.25, "#C9A38C"],
        [0.50, PAPER_WARM],
        [0.75, "#7B9DB1"],
        [1.00, PRUSSIAN],
    ]

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=ordered_mins,
        y=ordered_mins,
        zmid=0, zmin=-1, zmax=1,
        colorscale=colorscale,
        colorbar=dict(
            title=dict(text="Pearson r", font=dict(color=PAPER_INK, size=14)),
            tickfont=dict(color=PAPER_INK, size=12),
            outlinewidth=0,
        ),
        hovertemplate=(
            "<b>%{y}</b> ↔ <b>%{x}</b><br>r = %{z:.3f}<extra></extra>"
        ),
    ))
    # Per-cell value labels via annotations — lets us flip text colour to
    # white on the darkest cells where ink would disappear.
    for i in range(n):
        for j in range(n):
            val = z[i, j]
            cell_color = PAPER_WARM if abs(val) > 0.55 else PAPER_INK
            fig.add_annotation(
                x=ordered_mins[j], y=ordered_mins[i],
                text=f"{val:.2f}",
                showarrow=False,
                font=dict(family=FONT_FAMILY, size=12, color=cell_color),
                xref="x", yref="y",
            )
    fig.update_layout(
        title=dict(
            text=(
                "<b>Do prices move together?</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Pearson correlation of year-on-year % change, 2000–2024. "
                "Materials ordered by hierarchical clustering.</span>"
            ),
        ),
        xaxis=dict(side="bottom", tickfont=dict(size=12, color=PAPER_INK)),
        yaxis=dict(tickfont=dict(size=12, color=PAPER_INK), autorange="reversed"),
        height=620,
        margin=dict(l=140, r=40, t=140, b=140),
    )

    out = OUT_DIR / "price_correlation.html"
    write_chart(fig, out)
    return out


def main() -> None:
    p1 = build_small_multiples()
    p2 = build_index_modern()
    p3 = build_correlation()
    print(f"[section5] wrote {p1.relative_to(ROOT)}")
    print(f"[section5] wrote {p2.relative_to(ROOT)}")
    print(f"[section5] wrote {p3.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
