"""Figure 7.3 — A material is not a single shipment.

Stacked area panels per material, showing how the *mix of HS-coded
forms* in which the material trades into China has shifted over time.
For lithium: ore (spodumene) → carbonate → hydroxide. For copper:
concentrate / cathode / blister / scrap. For cobalt: mattes / oxide /
sulfate. Reinforces the HS-codes factbox.

Data: china_trade_flows_all_materials.csv, filtered to imports only,
grouped by (mineral, year, hs_form), summed by value_usd.
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
    MINERAL_COLORS,
    OXBLOOD,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PRUSSIAN,
    apply_theme,
    write_chart,
)

TRADE_PATH = ROOT / "data" / "processed" / "china_trade_flows_all_materials.csv"
OUT_PATH = ROOT / "website" / "visualizations" / "trade-flows" / "multi_form_view.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


# Panel layout: materials with multi-form coverage. Lithium, Cobalt,
# Copper, Rare Earths have the richest HS-form mix; the others are
# single-form imports.
PANELS = [
    ("Lithium",     ["ore", "carbonate", "hydroxide"]),
    ("Cobalt",      ["mattes", "sulfate", "oxide"]),
    ("Copper",      ["concentrate", "cathode", "blister", "scrap"]),
    ("Rare Earths", ["ore", "metal", "cerium_compounds", "ree_compounds", "magnets"]),
]

# Per-form palette — gradient from primary (raw upstream) through
# Prussian-and-oxblood mid-stream to muted (finished downstream).
FORM_COLOURS = {
    # Lithium
    "ore":               "#A07850",
    "carbonate":         PRUSSIAN,
    "hydroxide":         OXBLOOD,
    # Cobalt
    "mattes":            "#A07850",
    "sulfate":           PRUSSIAN,
    "oxide":             OXBLOOD,
    # Copper
    "concentrate":       "#A07850",
    "cathode":           PRUSSIAN,
    "blister":           "#5C8AA6",
    "scrap":             "#C9B89E",
    # Rare Earths
    "metal":             "#5C8AA6",
    "cerium_compounds":  "#C9B89E",
    "ree_compounds":     PRUSSIAN,
    "magnets":           OXBLOOD,
}

FORM_LABELS = {
    "ore": "Ore / concentrate (raw)",
    "concentrate": "Concentrate (raw)",
    "blister": "Blister (mid-stream)",
    "cathode": "Cathode (refined)",
    "scrap": "Scrap (recycled)",
    "mattes": "Mattes / intermediates",
    "carbonate": "Carbonate (battery feedstock)",
    "hydroxide": "Hydroxide (high-energy battery)",
    "oxide": "Oxide (battery precursor)",
    "sulfate": "Sulfate (cathode chemistry)",
    "metal": "Metal / alloy",
    "cerium_compounds": "Cerium compounds",
    "ree_compounds": "Other REE compounds",
    "magnets": "Permanent magnets",
}


def build() -> Path:
    df = pd.read_csv(TRADE_PATH)
    df = df[df["flow_direction"] == "import"]
    df = df[df["year"].between(2000, 2024)]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[m for m, _ in PANELS],
        horizontal_spacing=0.10, vertical_spacing=0.18,
    )

    for idx, (mineral, forms) in enumerate(PANELS):
        row = idx // 2 + 1
        col = idx % 2 + 1
        sub = df[df["mineral"] == mineral]
        if sub.empty:
            continue
        # Per-form annual totals in $B (real 2015 USD where available)
        value_col = "value_real_2015_usd" if "value_real_2015_usd" in sub.columns else "value_usd"
        agg = (
            sub.groupby(["year", "hs_form"], as_index=False)[value_col]
            .sum()
        )
        agg["value_b"] = agg[value_col] / 1e9

        for form in forms:
            line = agg[agg["hs_form"] == form]
            if line.empty:
                continue
            line = line.sort_values("year")
            colour = FORM_COLOURS.get(form, "#888888")
            label = FORM_LABELS.get(form, form)
            fig.add_trace(
                go.Scatter(
                    x=line["year"], y=line["value_b"],
                    mode="lines",
                    stackgroup=f"stack-{mineral}",
                    name=label,
                    line=dict(width=0.5, color=colour),
                    fillcolor=colour,
                    hovertemplate=(
                        f"<b>{mineral} — {label}</b><br>"
                        "%{x} · $%{y:.2f} B<extra></extra>"
                    ),
                    showlegend=False,
                ),
                row=row, col=col,
            )
            # Annotation: last-year share inside the panel for the dominant form
        # Form-name micro-legend in the corner of each panel
        legend_lines = []
        for form in forms:
            line = agg[agg["hs_form"] == form]
            if line.empty:
                continue
            colour = FORM_COLOURS.get(form, "#888888")
            legend_lines.append(
                f"<span style='color:{colour}'>■</span> {FORM_LABELS.get(form, form)}"
            )
        axis_idx = idx + 1
        x_ref = f"x{axis_idx if axis_idx > 1 else ''} domain"
        y_ref = f"y{axis_idx if axis_idx > 1 else ''} domain"
        fig.add_annotation(
            text="<br>".join(legend_lines),
            xref=x_ref, yref=y_ref,
            x=0.02, y=0.96, xanchor="left", yanchor="top",
            showarrow=False,
            font=dict(size=10, color=PAPER_INK),
            align="left",
            bgcolor="rgba(247,244,238,0.85)",
            borderwidth=0.5, bordercolor=PAPER_RULE,
            borderpad=4,
        )

        fig.update_xaxes(row=row, col=col,
                         range=[2000, 2024],
                         gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE,
                         tickfont=dict(size=10, color=PAPER_INK))
        fig.update_yaxes(row=row, col=col,
                         title="USD B / yr",
                         gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE,
                         tickfont=dict(size=10, color=PAPER_INK),
                         title_font=dict(size=11, color=PAPER_INK))
    fig.update_layout(
        title=dict(
            text=(
                "<b>Same material, different shipments</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "China's annual imports decomposed by HS-coded form — each panel "
                "is one material, each band one trade code. Reading one code alone "
                "understates the real flow.</span>"
            ),
        ),
        height=680,
        margin=dict(l=70, r=40, t=140, b=70),
        showlegend=False,
    )
    fig.update_annotations(font=dict(size=14, color=PAPER_INK))

    write_chart(fig, OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[multi_form_view] wrote {p.relative_to(ROOT)}")
