"""Figure 8.4 — Did the lever actually move prices?

Plots the 2000–2024 real-price index (2015 = 100) for the four
materials China has actually weaponised in trade — Tb, Dy, Gallium,
the rare-earth basket — and overlays the verified export-control
events from the Section 8 factbox. Read it as: when MOFCOM pulls
the lever, does the spot market notice?

Data: data/processed/price_unified.csv (column price_index_2015_eq_100).
Events: Senkaku 2010, REE quotas 2010–2014, Aug 2023 Ga/Ge licensing,
Dec 2024 US ban, Apr 2025 REE additions.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from website.theme import (
    MINERAL_COLORS,
    OXBLOOD,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PRUSSIAN,
    apply_theme,
    write_chart,
)

PRICE_PATH = ROOT / "data" / "processed" / "price_unified.csv"
OUT_PATH = ROOT / "website" / "visualizations" / "supply-chain" / "event_overlay.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

# Materials China has actually used policy levers on
TARGET_MINERALS = ["Rare Earths", "Terbium", "Dysprosium", "Gallium"]

# Verified export-control events (sourced in Section 8 factbox).
# (year_fractional, label, color)
EVENTS = [
    (2010.7, "Sep 2010<br>Senkaku halt",                       OXBLOOD),
    (2014.2, "Mar 2014<br>WTO ruling",                         "#5a544c"),
    (2023.6, "Aug 2023<br>Ga/Ge licensing",                    OXBLOOD),
    (2024.9, "Dec 2024<br>US-only ban",                        OXBLOOD),
    (2025.3, "Apr 2025<br>7 REEs added",                       OXBLOOD),
]


def build() -> Path:
    df = pd.read_csv(PRICE_PATH)
    df = df[df["mineral"].isin(TARGET_MINERALS)]
    df = df[(df["year"] >= 2000) & (df["year"] <= 2025)]
    df = df.dropna(subset=["price_index_2015_eq_100"])

    fig = go.Figure()
    for mineral in TARGET_MINERALS:
        sub = df[df["mineral"] == mineral].sort_values("year")
        if sub.empty:
            continue
        color = MINERAL_COLORS.get(mineral, PRUSSIAN)
        fig.add_trace(go.Scatter(
            x=sub["year"], y=sub["price_index_2015_eq_100"],
            mode="lines+markers",
            name=mineral,
            line=dict(color=color, width=2.6),
            marker=dict(size=5, color=color),
            hovertemplate=(
                f"<b>{mineral}</b><br>%{{x}} · index %{{y:.0f}} (2015 = 100)"
                "<extra></extra>"
            ),
        ))

    # Event verticals
    for x_pos, label, color in EVENTS:
        fig.add_vline(
            x=x_pos, line_dash="dot",
            line_color=color, line_width=1.6,
            opacity=0.7,
        )
        fig.add_annotation(
            x=x_pos, y=1.06, xref="x", yref="paper",
            text=f"<b style='color:{color}'>{label}</b>",
            showarrow=False, xanchor="center", yanchor="bottom",
            font=dict(size=10, color=PAPER_INK),
            align="center",
        )

    # 2015 baseline
    fig.add_hline(y=100, line_dash="dot", line_color="rgba(20,17,13,0.30)")
    fig.update_layout(
        title=dict(
            text=(
                "<b>Did the lever actually move prices?</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Real-price index, 2000–2024, with verified Chinese export-control "
                "events overlaid. The Senkaku halt, the 2010–11 quota regime, the "
                "August 2023 Ga/Ge licensing — all visible as breaks.</span>"
            ),
        ),
        xaxis=dict(
            title="Year",
            range=[2000, 2025.5],
            gridcolor=PAPER_RULE_S,
            zerolinecolor=PAPER_RULE,
        ),
        yaxis=dict(
            title="Real-price index (2015 = 100)",
            type="log",
            gridcolor=PAPER_RULE_S,
            zerolinecolor=PAPER_RULE,
        ),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.16,
            xanchor="left", x=0,
            font=dict(size=12, color=PAPER_INK),
        ),
        margin=dict(l=80, r=40, t=190, b=120),
        height=560,
    )

    write_chart(fig, OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[event_overlay] wrote {p.relative_to(ROOT)}")
