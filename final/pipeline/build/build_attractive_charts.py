"""
Generate the three Section 3 + Section 4 visualisations:

    visualizations/attractive/slope_mining_vs_processing.html  (Fig 3.1)
    visualizations/attractive/concentration_type2.html         (Fig 3.2)
    visualizations/processing/ree_value_cliff.html             (Fig 4.1)

Data is baked in from the notebook
`notebooks/exploration/02_attractive_but_hard_to_get.ipynb` so this script
runs without external data files. Theme is the locked
LAYOUT_NEWSPAPER from website.theme — same chrome as Figures 5.1–5.4.

Run: python -m pipeline.build.build_attractive_charts
"""
from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from website.theme import (
    COUNTRY_COLORS,
    FONT_FAMILY,
    MINERAL_COLORS,
    MOLTEN_ORANGE,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PAPER_WARM,
    PRUSSIAN,
    apply_theme,
    write_chart,
)

VIS_ROOT = ROOT / "website" / "visualizations"

# Same Google-Fonts inject as build_visualizations.py — Lato + Playfair.
_FONT_INJECT = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap" rel="stylesheet">
<style>
html, body { font-family: 'Lato', -apple-system, BlinkMacSystemFont, sans-serif; background: #F7F4EE; }
.plotly, .plotly text, .js-plotly-plot text { font-family: 'Lato', sans-serif !important; }
</style>
"""


def write_plotly(fig: go.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        path,
        full_html=True,
        include_plotlyjs=True,
        config={"displayModeBar": False, "responsive": True},
    )
    html = path.read_text(encoding="utf-8")
    if "<head>" in html and _FONT_INJECT not in html:
        html = html.replace("<head>", "<head>\n" + _FONT_INJECT, 1)
        path.write_text(html, encoding="utf-8")


# ── Figure 3.1 — Slope chart: mining vs processing share ───────────────────
SLOPE_DATA = {
    "Copper":      [("China", 8, 44), ("Chile", 23, 7), ("DRC", 14, 9), ("Peru", 12, 1), ("Japan", 0, 6), ("Korea", 0, 2), ("Other", 43, 31)],
    "Lithium":     [("China", 17, 60), ("Australia", 37, 5), ("Chile", 20, 8), ("Argentina", 8, 1), ("Other", 18, 26)],
    "Graphite":    [("China", 78, 90), ("Mozambique", 8, 1), ("Madagascar", 4, 0), ("Other", 10, 9)],
    "Rare Earths": [("China", 69, 88), ("USA", 12, 1), ("Australia", 7, 3), ("Other", 12, 8)],
}

# Map country names to a colour pulled from existing tokens, with sensible fallbacks.
def _country_colour(name: str) -> str:
    table = {
        "China": COUNTRY_COLORS["China"],
        "Chile": COUNTRY_COLORS["Chile"],
        "DRC": COUNTRY_COLORS["Democratic Republic of the Congo"],
        "Peru": "#9aa3a8",
        "Japan": COUNTRY_COLORS["Japan"],
        "Korea": "#FF8C00",
        "Australia": COUNTRY_COLORS["Australia"],
        "Argentina": "#7aa3c4",
        "Mozambique": "#9aa3a8",
        "Madagascar": "#9aa3a8",
        "USA": COUNTRY_COLORS["United States"],
        "Other": "#a8a39c",
    }
    return table.get(name, "#888888")


def build_slope_mining_vs_processing() -> Path:
    minerals = list(SLOPE_DATA.keys())
    n = len(minerals)
    fig = go.Figure()

    # Layout: 4 panels side-by-side using xaxis domains. Each panel uses two
    # x positions (mining=0, processing=1) inside a domain slot.
    panel_width = 0.95 / n
    panel_gap = 0.05 / max(1, (n - 1))

    for i, mineral in enumerate(minerals):
        x_left = 0 + i * (panel_width + panel_gap)
        x_right = x_left + panel_width
        x_axis_id = "x" if i == 0 else f"x{i+1}"

        # Each country becomes a 2-point line trace.
        for country, mining, processing in SLOPE_DATA[mineral]:
            colour = _country_colour(country)
            featured = country in {"China", "Japan", "Korea", "Australia", "DRC", "USA"}
            width = 4 if country == "China" else (3 if featured else 1.5)
            opacity = 0.95 if featured else 0.45
            fig.add_trace(
                go.Scatter(
                    x=[0, 1], y=[mining, processing],
                    mode="lines+markers",
                    line=dict(color=colour, width=width),
                    marker=dict(size=8, color=colour, line=dict(color=PAPER_WARM, width=1)),
                    opacity=opacity,
                    name=country,
                    legendgroup=country,
                    showlegend=(i == 0),  # only show legend entries on first panel
                    xaxis=x_axis_id,
                    yaxis="y",
                    hovertemplate=f"<b>{country}</b><br>{mineral}<br>Mining %{{x:.0f}} → Processing %{{y:.0f}}<extra></extra>",
                )
            )

        # Per-panel x-axis: only "Mining" / "Processing" tick labels.
        fig.update_layout(**{
            f"xaxis{i+1 if i else ''}": dict(
                domain=[x_left, x_right],
                tickvals=[0, 1],
                ticktext=["Mining %", "Processing %"],
                showgrid=False,
                zeroline=False,
                tickfont=dict(family=FONT_FAMILY, size=14, color=PAPER_INK),
                anchor="y",
                range=[-0.18, 1.18],
            ),
        })

        # Per-panel title (mineral name) — placed via annotation above each panel.
        fig.add_annotation(
            text=f"<b>{mineral}</b>",
            xref="paper", yref="paper",
            x=(x_left + x_right) / 2, y=1.02,
            xanchor="center", yanchor="bottom",
            showarrow=False,
            font=dict(family=FONT_FAMILY, size=18, color=PAPER_INK),
        )

    fig.update_layout(
        yaxis=dict(
            range=[-3, 100],
            ticksuffix="%",
            showgrid=True,
            zeroline=False,
        ),
        title=dict(
            text=(
                "<b>Mining share is not the same as processing share</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Where ore is extracted vs. where it is refined — Type 1 minerals, 2023–2024</span>"
            ),
        ),
        margin=dict(l=80, r=40, t=160, b=100),
    )

    out = VIS_ROOT / "attractive" / "slope_mining_vs_processing.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_chart(fig, out, legend_pos="bottom")
    return out


# ── Figure 3.2 — Stacked horizontal bars: ore concentration for Type 2 ─────
TYPE2_DATA = {
    "Cobalt":     [("DRC", 76), ("Indonesia", 10), ("Australia", 4), ("Other", 10)],
    "Dysprosium": [("China", 70), ("Myanmar", 15), ("Australia", 5), ("Other", 10)],
    "Gallium":    [("China", 99), ("Other", 1)],
    "Platinum":   [("South Africa", 70), ("Russia", 13), ("Zimbabwe", 8), ("Other", 9)],
    "Terbium":    [("China", 80), ("Myanmar", 12), ("Other", 8)],
}

def _type2_colour(name: str) -> str:
    overrides = {
        "Indonesia": "#3aa37f",
        "Myanmar": "#c75e5e",
        "Russia": COUNTRY_COLORS["Russia"],
        "Zimbabwe": "#a47148",
    }
    if name in overrides:
        return overrides[name]
    return _country_colour(name)


def build_concentration_type2() -> Path:
    minerals = list(TYPE2_DATA.keys())
    fig = go.Figure()

    # Build one bar trace per (mineral, country) combo, stacking horizontally.
    # We build one trace per UNIQUE country across all minerals so the legend stays clean.
    countries_seen: list[str] = []
    for mineral in minerals:
        for country, _ in TYPE2_DATA[mineral]:
            if country not in countries_seen:
                countries_seen.append(country)

    for country in countries_seen:
        xs, ys, hovers = [], [], []
        for mineral in minerals:
            share = next((s for c, s in TYPE2_DATA[mineral] if c == country), 0)
            xs.append(share)
            ys.append(mineral)
            hovers.append(f"<b>{country}</b><br>{mineral}: {share}%")
        fig.add_trace(
            go.Bar(
                y=ys, x=xs,
                name=country,
                orientation="h",
                marker=dict(color=_type2_colour(country), line=dict(color=PAPER_WARM, width=1)),
                hovertemplate="%{customdata}<extra></extra>",
                customdata=hovers,
                text=[(f"{country} {s}%" if s >= 9 else "") for s in xs],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(family=FONT_FAMILY, size=14, color="white"),
            )
        )

    fig.update_layout(
        barmode="stack",
        title=dict(
            text=(
                "<b>Who holds the ore?</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Share of global mine production, Type 2 minerals, 2023–2024</span>"
            ),
        ),
        xaxis=dict(
            title=dict(text="Share of global mine production (%)"),
            range=[0, 102], ticksuffix="%",
            gridcolor=PAPER_RULE_S, zerolinecolor=PAPER_RULE,
        ),
        yaxis=dict(title=dict(text="")),
        margin=dict(l=140, r=40, t=140, b=90),
    )

    out = VIS_ROOT / "attractive" / "concentration_type2.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    write_chart(fig, out)
    return out


# ── Figure 4.1 — REE separation value cliff ────────────────────────────────
# 2024 USGS MCS estimates baked in from the source CSV (mcs2025_all_prices.csv).
# The notebook reads these from disk; we hardcode them so this generator runs
# without the raw data tree. Order: ascending — easy separations on the left,
# magnet-grade in the middle, terbium at the cliff edge.
REE_VALUE_CLIFF = [
    ("Cerium oxide (Ce₂O₃ 99.5%)",     1.5),
    ("Lanthanum oxide (La₂O₃ 99.5%)",  1.7),
    ("Mischmetal (65Ce/35La)",         8.0),
    ("Neodymium oxide (Nd₂O₃ 99.5%)",  72.0),
    ("Dysprosium oxide (Dy₂O₃ 99.5%)", 320.0),
    ("Terbium oxide (Tb₂O₃ 99.99%)",   810.0),
]
REE_COLOURS = ["#666666", "#777777", "#9c9c9c", "#C49A02", "#FF8C00", COUNTRY_COLORS["China"]]


def build_ree_value_cliff() -> Path:
    labels = [e[0] for e in REE_VALUE_CLIFF]
    values = [e[1] for e in REE_VALUE_CLIFF]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels, x=values,
            orientation="h",
            marker=dict(color=REE_COLOURS, line=dict(color=PAPER_WARM, width=1)),
            text=[f"${v:,.0f}/kg" for v in values],
            textposition="outside",
            textfont=dict(family=FONT_FAMILY, size=15, color=PAPER_INK),
            hovertemplate="<b>%{y}</b><br>$%{x:,.1f} per kg<extra></extra>",
            showlegend=False,
        )
    )

    apply_theme(fig)

    fig.update_layout(
        title=dict(
            text=(
                "<b>The rare-earth separation value cliff</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Same ore body — eight-hundred-fold price spread driven by separation complexity</span>"
            ),
        ),
        xaxis=dict(
            title=dict(text="<b>Price ($ per kg, 2024 estimate)</b>"),
            type="log",
            tickprefix="$",
            tickvals=[1, 3, 10, 30, 100, 300, 1000],
            range=[0, 3.05],
        ),
        yaxis=dict(title=dict(text=""), automargin=True),
        margin=dict(l=80, r=120, t=170, b=110),
        height=520,
        showlegend=False,
    )

    out = VIS_ROOT / "processing" / "ree_value_cliff.html"
    write_plotly(fig, out)
    return out


def main() -> None:
    print("Building Section 3 + 4 charts...")
    p1 = build_slope_mining_vs_processing()
    print(f"  ok{p1.relative_to(ROOT)}")
    p2 = build_concentration_type2()
    print(f"  ok{p2.relative_to(ROOT)}")
    p3 = build_ree_value_cliff()
    print(f"  ok{p3.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
