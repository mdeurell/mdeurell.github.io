"""Figure 9.3 — Swing states: who do they actually sell to?

Five-panel small-multiples chart. For each "playing both sides"
upstream country (Australia, Chile, Indonesia, India) and the
non-swing contrast case (DRC), plots the share of critical-mineral
exports going to:

  • China
  • the Western alliance (US, Japan, Korea, Canada, UK, NZ, Norway,
    Switzerland)
  • everywhere else

Reading: where the China line sits well above the Western line and
shows no convergence, the country is locked into the Chinese supply
chain (DRC). Where the two lines weave or rebalance, the country is
actively diversifying its customer mix (Australia, India). Chile and
Indonesia sit in between.

Inputs:
  data/raw/comtrade/swing_*_exports_*.csv (one file per country-year)
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
    OXBLOOD,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PAPER_WARM,
    PRUSSIAN,
    apply_theme,
    write_chart,
)

RAW_DIR = ROOT / "data" / "raw" / "comtrade"
OUT_PATH = ROOT / "website" / "visualizations" / "bifurcation" / "swing_states.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


COUNTRIES = [
    ("Australia", "australia"),
    ("Chile",     "chile"),
    ("Indonesia", "indonesia"),
    ("India",     "india"),
    ("DRC",       "drc"),
]

# Bloc definitions
CHINA_NAMES = {"China", "China, Hong Kong SAR"}
WESTERN_NAMES = {
    "USA", "United States of America", "Japan", "Rep. of Korea",
    "Canada", "United Kingdom", "Australia", "New Zealand",
    "Norway", "Switzerland", "Netherlands", "Germany", "France",
    "Italy", "Spain", "Belgium", "Sweden", "Finland", "Denmark",
    "Austria", "Ireland", "Portugal",
    "Greece", "Czechia", "Poland", "Hungary", "Slovakia",
    "Slovenia", "Romania", "Bulgaria", "Croatia", "Lithuania",
    "Latvia", "Estonia", "Luxembourg", "Malta", "Cyprus",
}


def _load_country(slug: str) -> pd.DataFrame:
    rows = []
    for path in sorted(RAW_DIR.glob(f"swing_{slug}_exports*_*.csv")):
        # Filter file names: swing_<slug>_exports_<year>.csv and any split-suffix variants
        stem = path.stem
        if not stem.startswith(f"swing_{slug}_exports"):
            continue
        year_part = stem.split("_")[-1]
        if not year_part.isdigit():
            continue
        year = int(year_part)
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if df.empty:
            continue
        df = df[df["partnerCode"] != 0]
        if df.empty:
            continue
        rows.append(pd.DataFrame({
            "year": year,
            "partner": df["partnerDesc"],
            "value_usd": pd.to_numeric(df["primaryValue"], errors="coerce"),
        }))
    if not rows:
        return pd.DataFrame(columns=["year", "partner", "value_usd"])
    return pd.concat(rows, ignore_index=True)


def _bloc(partner: str) -> str:
    if partner in CHINA_NAMES:
        return "China"
    if partner in WESTERN_NAMES:
        return "Western"
    return "Other"


def build() -> Path:
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=[c[0] for c in COUNTRIES] + [""],
        horizontal_spacing=0.07, vertical_spacing=0.18,
    )

    for idx, (label, slug) in enumerate(COUNTRIES):
        df = _load_country(slug)
        if df.empty:
            continue
        df = df.dropna(subset=["value_usd"])
        df = df[df["value_usd"] > 0]
        df["bloc"] = df["partner"].apply(_bloc)
        agg = (
            df.groupby(["year", "bloc"], as_index=False)["value_usd"]
            .sum()
        )
        totals = agg.groupby("year")["value_usd"].sum().rename("total")
        agg = agg.merge(totals, on="year")
        agg["share"] = agg["value_usd"] / agg["total"] * 100

        row = idx // 3 + 1
        col = idx % 3 + 1

        for bloc, colour, dash in [
            ("China",   OXBLOOD,  "solid"),
            ("Western", PRUSSIAN, "solid"),
            ("Other",   "#888888","dot"),
        ]:
            sub = agg[agg["bloc"] == bloc].sort_values("year")
            if sub.empty:
                continue
            fig.add_trace(
                go.Scatter(
                    x=sub["year"], y=sub["share"],
                    mode="lines+markers",
                    name=bloc,
                    line=dict(color=colour, width=2.4, dash=dash),
                    marker=dict(size=4, color=colour),
                    legendgroup=bloc,
                    showlegend=(idx == 0),
                    hovertemplate=(
                        f"<b>{label} → {bloc}</b><br>"
                        "%{x} · %{y:.1f}% of exports"
                        "<extra></extra>"
                    ),
                ),
                row=row, col=col,
            )

        fig.update_xaxes(
            row=row, col=col,
            range=[2000, 2024],
            gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE,
            tickfont=dict(size=10, color=PAPER_INK),
        )
        fig.update_yaxes(
            row=row, col=col,
            range=[0, 100], ticksuffix="%",
            gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE,
            tickfont=dict(size=10, color=PAPER_INK),
        )
    fig.update_layout(
        title=dict(
            text=(
                "<b>Playing both sides?</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Each panel: one upstream country's exports of the eight focal "
                "HS codes, split between China, the Western alliance and the "
                "rest, 2000–2024.</span>"
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="top", y=-0.08,
            xanchor="left", x=0,
            font=dict(size=12, color=PAPER_INK),
        ),
        height=620,
        margin=dict(l=60, r=40, t=140, b=80),
    )
    fig.update_annotations(font=dict(size=14, color=PAPER_INK))

    write_chart(fig, OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[swing_states] wrote {p.relative_to(ROOT)}")
