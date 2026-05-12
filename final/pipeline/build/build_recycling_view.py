"""Figure 9.3 — Recycling and urban mining.

Two-panel chart that pairs each focal material's
end-of-life recycling input rate (EOL-RIR) with its 10-year demand
growth multiple. The point: where the recycling bar is short and the
demand bar is tall, the gap between waste-stream supply and growth
is widening, not closing. Urban mining is a slogan only when the
recovery infrastructure exists; today it largely doesn't for the
materials that matter most.

EOL-RIR values are widely-cited industry estimates (UNEP 2011 base
+ IEA / EC Joint Research Centre 2023 updates). Demand-growth
multiples are computed from `master_economic_timeseries.csv` —
global_mine_production_tonnes from 2014 to 2024 ratio.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    PRUSSIAN,
    apply_theme,
    write_chart,
)

ECON_PATH = ROOT / "data" / "processed" / "master_economic_timeseries.csv"
OUT_PATH = ROOT / "website" / "visualizations" / "bifurcation" / "recycling_view.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# End-of-life recycling input rate (%, share of secondary material in
# total annual supply). Sources: UNEP 2011 metals stocks-and-flows
# report; EU Joint Research Centre Critical Raw Materials 2023; IEA
# Critical Minerals Outlook 2024.
EOL_RIR = {
    "Copper":      32,   # well-established secondary market
    "Platinum":    35,   # autocatalyst recovery
    "Gallium":     0,    # no commercial recovery stream
    "Cobalt":      22,   # rising with Li-ion recycling
    "Lithium":      1,   # almost none; technology pre-commercial
    "Graphite":     1,   # battery-anode graphite essentially unrecovered
    "Rare Earths":  1,   # 1–6% basket, 1% typical
}

# Index by mineral so we can plot in two-panel ordering


def _demand_multiplier_2014_2024(df: pd.DataFrame, mineral: str) -> float | None:
    """Production tonnage in 2024 ÷ 2014 — a 10-year demand multiple."""
    sub = df[(df["mineral"] == mineral) & (df["metric"] == "global_mine_production_tonnes")]
    if sub.empty:
        return None
    sub = sub.dropna(subset=["value"])
    v_2014 = sub[sub["year"] == 2014]["value"]
    v_2024 = sub[sub["year"] == 2024]["value"]
    if v_2014.empty or v_2024.empty:
        return None
    if float(v_2014.iloc[0]) <= 0:
        return None
    return float(v_2024.iloc[0]) / float(v_2014.iloc[0])


def build() -> Path:
    df = pd.read_csv(ECON_PATH)

    rows = []
    for mineral, rir in EOL_RIR.items():
        mult = _demand_multiplier_2014_2024(df, mineral)
        if mult is None:
            mult = float("nan")
        rows.append((mineral, rir, mult))

    rows.sort(key=lambda r: r[1])  # by recycling rate ascending
    minerals = [r[0] for r in rows]
    rir_vals = [r[1] for r in rows]
    mults = [r[2] for r in rows]

    colors = [MINERAL_COLORS.get(m, PRUSSIAN) for m in minerals]

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=(
            "End-of-life recycling rate, %",
            "Demand multiple, 2014 → 2024",
        ),
        horizontal_spacing=0.18,
        shared_yaxes=True,
    )

    # Left panel — recycling rates
    fig.add_trace(
        go.Bar(
            x=rir_vals, y=minerals, orientation="h",
            marker=dict(color=PRUSSIAN, line=dict(color=PAPER_INK, width=1)),
            text=[f"{v} %" for v in rir_vals],
            textposition="outside",
            textfont=dict(family=FONT_SERIF, size=12, color=PAPER_INK),
            hovertemplate=(
                "<b>%{y}</b><br>Recycling input rate: %{x}%<extra></extra>"
            ),
            showlegend=False,
        ),
        row=1, col=1,
    )

    # Right panel — demand growth
    fig.add_trace(
        go.Bar(
            x=mults, y=minerals, orientation="h",
            marker=dict(color=OXBLOOD, line=dict(color=PAPER_INK, width=1)),
            text=[f"× {v:.1f}" if v == v else "—" for v in mults],   # NaN-safe
            textposition="outside",
            textfont=dict(family=FONT_SERIF, size=12, color=PAPER_INK),
            hovertemplate=(
                "<b>%{y}</b><br>Demand 2024 vs 2014: ×%{x:.2f}<extra></extra>"
            ),
            showlegend=False,
        ),
        row=1, col=2,
    )

    # Reference lines
    fig.add_vline(x=10, line_dash="dot", line_color=PAPER_RULE_S, opacity=0.6, row=1, col=1)
    fig.add_vline(x=1,  line_dash="dot", line_color=PAPER_RULE,    opacity=0.6, row=1, col=2)
    fig.update_layout(
        title=dict(
            text=(
                "<b>The urban-mining gap</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Where recycling is low and demand is climbing, "
                "the second-supply story is a slogan rather than a reality.</span>"
            ),
        ),
        height=470,
        margin=dict(l=140, r=80, t=140, b=80),
        bargap=0.32,
        showlegend=False,
    )
    fig.update_xaxes(row=1, col=1,
                     range=[0, max(rir_vals) * 1.30 if max(rir_vals) > 0 else 50],
                     gridcolor=PAPER_RULE_S, ticksuffix="%")
    fig.update_xaxes(row=1, col=2,
                     range=[0, max([m for m in mults if m == m], default=2) * 1.25],
                     gridcolor=PAPER_RULE_S)
    fig.update_yaxes(tickfont=dict(size=13, color=PAPER_INK))

    fig.update_annotations(font=dict(size=14, color=PAPER_INK))

    write_chart(fig, OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[recycling_view] wrote {p.relative_to(ROOT)}")
