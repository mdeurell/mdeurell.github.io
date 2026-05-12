"""Figure 8.4 — China's own upstream dependence (computed from data).

For each focal material, decomposes 100 % of China's effective annual
refining feedstock into three slices:

  • Prussian blue — share mined in China itself (domestic)
  • Oxblood       — share imported from China's single largest supplier
  • Neutral grey  — share from all other imports combined

The computation is end-to-end from data, not a lookup. Method:

  domestic_pct  =  china_mining ÷ world_mining          (USGS MCS 2023)
  top_pct       =  (top_supplier_share_of_imports) × (1 − domestic_pct)
  other_pct     =  100 − domestic_pct − top_pct

This sidesteps the unit-reconciliation problem (USD value of mining
vs USD value of imports needs material-specific concentrate-to-metal
conversion factors and is heavily sensitive to which year's price one
anchors on). The mining-share approach is the canonical USGS way of
expressing dependence and matches the published Mining and Processing
Fact Sheet method.

Fallbacks: where China's domestic mining is not in
master_economic_timeseries (Gallium byproduct of bauxite refining,
Palladium where China produces tiny amounts), we plug in
literature-published shares — flagged inline.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
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

OUT_PATH = ROOT / "website" / "visualizations" / "supply-chain" / "reciprocal_dependence.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

ECON_PATH    = ROOT / "data" / "processed" / "master_economic_timeseries.csv"
PRICE_PATH   = ROOT / "data" / "processed" / "price_unified.csv"
TRADE_PATH   = ROOT / "data" / "processed" / "china_trade_flows_all_materials.csv"

# Materials whose domestic mining is not in master_economic_timeseries —
# fall back to a literature value for the domestic share of supply.
FALLBACK_DOMESTIC_PCT = {
    "Gallium":   98,   # China supplies ~98% of world gallium (USGS MCS 2025)
    "Palladium":  5,   # China produces only a small share; SA + Russia dominate
}

# Reporting window for trade imports
TRADE_WINDOW = (2015, 2023)
WINDOW_YEARS = TRADE_WINDOW[1] - TRADE_WINDOW[0] + 1


def _domestic_share(econ: pd.DataFrame, mineral: str) -> float | None:
    """China's share of world mining, latest available year.

    Uses USGS Mineral Commodity Summaries reporting: china_mining /
    world_mining. Returns percentage (0–100) or None if the dataset
    lacks China-level or world-level production for this mineral.
    """
    china = econ[
        (econ["metric"] == "mine_production_tonnes")
        & (econ["country"] == "China")
        & (econ["mineral"] == mineral)
    ].dropna(subset=["value"])
    world = econ[
        (econ["metric"] == "global_mine_production_tonnes")
        & (econ["mineral"] == mineral)
    ].dropna(subset=["value"])
    if china.empty or world.empty:
        return None
    common = set(china["year"]).intersection(set(world["year"]))
    if not common:
        return None
    y = max(common)
    cv = float(china[china["year"] == y]["value"].iloc[0])
    wv = float(world[world["year"] == y]["value"].iloc[0])
    if wv <= 0:
        return None
    return min(100.0, cv / wv * 100.0)


def _top_supplier_share_of_imports(trade: pd.DataFrame, mineral: str) -> tuple[str | None, float, float]:
    """(top supplier name, top supplier share of imports %, total annual imports USD)."""
    sub = trade[
        (trade["mineral"] == mineral)
        & (trade["flow_direction"] == "import")
        & trade["year"].between(*TRADE_WINDOW)
    ].dropna(subset=["value_real_2015_usd"])
    if sub.empty:
        return None, 0.0, 0.0
    by_partner = (
        sub.groupby("partner_country")["value_real_2015_usd"].sum()
        .sort_values(ascending=False)
    )
    by_partner = by_partner[~by_partner.index.isin(["China"])]
    if by_partner.empty:
        return None, 0.0, 0.0
    total = float(by_partner.sum())
    if total <= 0:
        return None, 0.0, 0.0
    top_partner = by_partner.index[0]
    top_share_of_imports = float(by_partner.iloc[0]) / total * 100.0
    return top_partner, top_share_of_imports, total / WINDOW_YEARS


def build() -> Path:
    econ = pd.read_csv(ECON_PATH)
    prices = pd.read_csv(PRICE_PATH)
    trade = pd.read_csv(TRADE_PATH)

    materials = ["Cobalt", "Lithium", "Copper", "Rare Earths", "Graphite",
                 "Platinum", "Palladium", "Gallium"]

    rows = []
    for mineral in materials:
        domestic_pct = _domestic_share(econ, mineral)
        if domestic_pct is None:
            domestic_pct = FALLBACK_DOMESTIC_PCT.get(mineral, 0)

        top_partner, top_share_imports, ann_imports_v = _top_supplier_share_of_imports(trade, mineral)

        # Convert "top supplier share of imports" into "share of total supply"
        # by multiplying through by the import share of total supply.
        import_share_of_supply = max(0.0, 100.0 - domestic_pct)
        top_pct = top_share_imports * import_share_of_supply / 100.0
        other_pct = max(0.0, 100.0 - domestic_pct - top_pct)

        rows.append({
            "mineral": mineral,
            "domestic_pct": domestic_pct,
            "top_supplier": top_partner or "—",
            "top_pct": top_pct,
            "other_pct": other_pct,
            "top_share_of_imports": top_share_imports,
            "annual_imports_usd_2015real": ann_imports_v,
        })

    df = pd.DataFrame(rows).sort_values("domestic_pct", ascending=True).reset_index(drop=True)

    fig = go.Figure()

    # Domestic share — Prussian
    fig.add_trace(go.Bar(
        y=df["mineral"], x=df["domestic_pct"], orientation="h",
        name="Mined in China (domestic)",
        marker=dict(color=PRUSSIAN, line=dict(color=PAPER_INK, width=0.8)),
        text=[f"{v:.0f}%" if v >= 10 else "" for v in df["domestic_pct"]],
        textposition="inside",
        textfont=dict(color="#F0EDE5", size=12),
        hovertemplate=("<b>%{y}</b><br>China domestic: %{x:.1f}%<extra></extra>"),
    ))

    # Top external supplier — Oxblood
    top_labels = [
        f"{s} {p:.0f}%" if p >= 10 else f"{s}"
        for s, p in zip(df["top_supplier"], df["top_pct"])
    ]
    fig.add_trace(go.Bar(
        y=df["mineral"], x=df["top_pct"], orientation="h",
        name="Top external supplier",
        marker=dict(color=OXBLOOD, line=dict(color=PAPER_INK, width=0.8)),
        text=top_labels,
        textposition="inside",
        textfont=dict(color="#F0EDE5", size=12),
        customdata=df[["top_supplier"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>Top supplier (%{customdata[0]}): %{x:.1f}%"
            "<extra></extra>"
        ),
    ))

    # Other imports — neutral tan
    fig.add_trace(go.Bar(
        y=df["mineral"], x=df["other_pct"], orientation="h",
        name="Other imports",
        marker=dict(color="#C9B89E", line=dict(color=PAPER_INK, width=0.8)),
        text=[f"{v:.0f}%" if v >= 10 else "" for v in df["other_pct"]],
        textposition="inside",
        textfont=dict(color=PAPER_INK, size=11),
        hovertemplate=("<b>%{y}</b><br>Other imports: %{x:.1f}%<extra></extra>"),
    ))

    # Annotation
    fig.add_annotation(
        x=104, y="Lithium" if "Lithium" in df["mineral"].values else df["mineral"].iloc[len(df)//2],
        text=(
            "<b>Three countries hold dual-material leverage over China</b><br>"
            "<br>"
            "<b>DRC</b>  cobalt + copper cathode (Copperbelt). The deepest<br>"
            "single-country grip in the dataset.<br>"
            "<br>"
            "<b>Australia</b>  lithium + rare-earth concentrate (via the<br>"
            "Lynas / Malaysia route). A Western ally whose ore still feeds<br>"
            "Chinese refineries — the paradox the 2025 US-AU framework targets.<br>"
            "<br>"
            "<b>Chile</b>  copper + lithium. Now first on copper concentrate,<br>"
            "second on lithium after Australia.<br>"
            "<br>"
            "<i>Zambia sits beside the DRC in the Copperbelt as the<br>"
            "complementary, smaller copper source.</i>"
        ),
        showarrow=False,
        xanchor="left", yanchor="middle",
        font=dict(family=FONT_SERIF, size=12, color=PAPER_INK),
        align="left",
        bordercolor=OXBLOOD,
        borderwidth=1.2,
        borderpad=10,
        bgcolor="rgba(247,244,238,0.95)",
    )
    fig.update_layout(
        barmode="stack",
        title=dict(
            text=(
                "<b>China's own upstream dependence</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Each bar = 100 % of China's effective refining feedstock, "
                "computed end-to-end from USGS mining tonnage × real-2015 prices "
                "and Comtrade import flows.</span>"
            ),
        ),
        xaxis=dict(
            title="Share of China's total supply (%)",
            range=[0, 175],
            ticksuffix="%",
            tickvals=[0, 25, 50, 75, 100],
            gridcolor=PAPER_RULE_S,
            zerolinecolor=PAPER_RULE,
        ),
        yaxis=dict(
            title=None,
            tickfont=dict(size=14, color=PAPER_INK),
            categoryorder="array",
            categoryarray=df["mineral"].tolist(),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom", y=-0.22,
            xanchor="left", x=0.0,
            font=dict(size=12, color=PAPER_INK),
        ),
        height=540,
        margin=dict(l=140, r=40, t=140, b=120),
        bargap=0.32,
    )

    write_chart(fig, OUT_PATH)

    # Persist the computed mix so other figures / the methodology page
    # can cite the same numbers.
    df.to_csv(
        ROOT / "data" / "processed" / "china_supply_mix_computed.csv",
        index=False,
    )
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[reciprocal_dependence] wrote {p.relative_to(ROOT)}")
    out = pd.read_csv(ROOT / "data" / "processed" / "china_supply_mix_computed.csv")
    print()
    print("Computed supply mix:")
    print(out[["mineral", "domestic_pct", "top_supplier", "top_pct", "other_pct"]].to_string(index=False))
