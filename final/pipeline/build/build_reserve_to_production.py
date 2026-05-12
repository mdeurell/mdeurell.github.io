"""Figure 2.2 — How long does the rock last?

Reserve-to-production ratio per focal material, computed from
USGS-published reserve tonnage divided by world annual production.
Plotted as horizontal bars, sorted ascending so the tightest
materials sit at the top — i.e. the ones that would actually exhaust
their currently economically extractable reserves first.

The point: across the focal basket, no material is on the edge of
running out. Cobalt and copper are tightest at ~40 years; everything
else exceeds a century. The deposit map shows "deposits are
everywhere"; the R/P ratio confirms "and there is enough for the
foreseeable future." That sets up Section 3+, where the constraint
moves from the rock to what happens after.

Source: USGS Mineral Commodity Summaries 2025 (reserves in metric
tonnes contained-element basis; production same units, 2024).
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from website.theme import (
    FONT_SERIF,
    MINERAL_COLORS,
    OXBLOOD,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PAPER_WARM,
    PRUSSIAN,
    apply_theme,
    write_chart,
)

OUT_PATH = ROOT / "website" / "visualizations" / "deposits" / "reserve_to_production.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# (mineral, reserves_tonnes, production_tonnes_per_year, footnote)
# Numbers drawn from USGS MCS 2025 published reserves and 2024 mine
# production, both on contained-element basis where applicable.
# REE values are for the basket; Nd / Dy / Tb individuals share the
# same reserve pool (no separate HREE breakdown in MCS).
# Platinum corrected from the master_economic_timeseries unit issue —
# USGS publishes PGM reserves as ~70,000 t metal content.
# Gallium has no formal reserve estimate (recovered as byproduct of
# bauxite refining); omitted from the chart and noted in caption.
SUPPLY_DATA = [
    # mineral,        reserves_t,    production_t,   note
    ("Cobalt",         11_000_000,        290_000,  ""),
    ("Copper",        980_000_000,     23_000_000,  ""),
    ("Lithium",        30_000_000,        240_000,  ""),
    ("Graphite",      290_000_000,      1_600_000,  ""),
    ("Platinum",          70_000,             360,  "PGM reserves combined"),
    ("Rare Earths",   110_000_000,        390_000,  "Same reserves apply to Nd / Dy / Tb"),
]


def build() -> Path:
    # Compute years-of-supply and sort tightest-first
    rows = []
    for mineral, reserves, prod, note in SUPPLY_DATA:
        years = reserves / prod
        rows.append((mineral, reserves, prod, years, note))
    rows.sort(key=lambda r: r[3])  # ascending years

    minerals = [r[0] for r in rows]
    years = [r[3] for r in rows]
    reserves = [r[1] for r in rows]
    prods = [r[2] for r in rows]
    notes = [r[4] for r in rows]

    colors = [MINERAL_COLORS.get(m, PRUSSIAN) for m in minerals]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years, y=minerals, orientation="h",
        marker=dict(color=colors, line=dict(color=PAPER_INK, width=1)),
        text=[f"<b>{y:.0f}</b> yr" for y in years],
        textposition="outside",
        textfont=dict(family=FONT_SERIF, size=14, color=PAPER_INK),
        customdata=list(zip(
            [r / 1e6 for r in reserves],
            [p / 1e3 for p in prods],
            notes,
        )),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Reserves: %{customdata[0]:.1f} Mt<br>"
            "Annual production: %{customdata[1]:.1f} kt<br>"
            "Years of supply: %{x:.0f}<br>"
            "%{customdata[2]}<extra></extra>"
        ),
    ))

    # Reference verticals — common policy horizons
    fig.add_vline(x=30, line_dash="dot", line_color=OXBLOOD, opacity=0.7)
    fig.add_annotation(
        x=30, y=-0.45,
        text="<i>30 yr — typical mine planning horizon</i>",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(size=11, color=OXBLOOD),
    )
    fig.add_vline(x=100, line_dash="dot", line_color=PAPER_RULE, opacity=0.6)
    fig.add_annotation(
        x=100, y=-0.45,
        text="<i>100 yr — long-horizon planning</i>",
        showarrow=False, xanchor="left", yanchor="top",
        font=dict(size=11, color=PAPER_INK),
    )
    fig.update_layout(
        title=dict(
            text=(
                "<b>How much rock is left?</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Years of supply at current production rates — reserves "
                "divided by annual world output, USGS MCS 2025.</span>"
            ),
        ),
        xaxis=dict(
            title="Years of supply",
            range=[0, max(years) * 1.20],
            gridcolor=PAPER_RULE_S,
            zerolinecolor=PAPER_RULE,
            tickfont=dict(size=13, color=PAPER_INK),
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=14, color=PAPER_INK),
            categoryorder="array",
            categoryarray=minerals,
        ),
        showlegend=False,
        height=440,
        margin=dict(l=140, r=80, t=140, b=110),
        bargap=0.32,
    )

    write_chart(fig, OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[reserve_to_production] wrote {p.relative_to(ROOT)}")
