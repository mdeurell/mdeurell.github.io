"""New Figure 6.1 — Supply-chain schematic.

Hand-drawn editorial graphic showing the five stages between mine and
end-product, with per-stage annotations on what happens, who typically does
it, and where strategic value gets captured. Not a data viz — a conceptual
frame for Section 6.
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
OXBLOOD,
    PAPER_INK,
    PAPER_RULE,
    PAPER_RULE_S,
    PAPER_WARM,
    PRUSSIAN,
    apply_theme,
    write_chart,
)


OUT_PATH = ROOT / "website" / "visualizations" / "supply-chain" / "supply_chain_schematic.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


STAGES = [
    {
        "title": "Ore",
        "verb": "Extraction",
        "who": "Mining companies",
        "where": "DRC, Chile,<br>Australia, China",
        "what": "Rock and brine pulled<br>from the ground.<br>Tonnage measured here.",
        "lock": "Geology decides<br>location.",
    },
    {
        "title": "Concentrate",
        "verb": "Beneficiation",
        "who": "On-site mill,<br>often same operator",
        "where": "At or near the mine",
        "what": "Crushing, flotation,<br>gravity sorting. Strips<br>waste rock.",
        "lock": "Cheap. Easy.<br>First filter.",
    },
    {
        "title": "Refined<br>intermediate",
        "verb": "Refining",
        "who": "Specialised<br>processors",
        "where": "China for 60–100%<br>of focal materials",
        "what": "Smelting, leaching,<br>solvent extraction.<br>Hundreds of stages<br>for REEs.",
        "lock": "The chemistry<br>chokepoint.",
    },
    {
        "title": "Functional<br>material",
        "verb": "Conversion",
        "who": "Industrial chemical /<br>metal makers",
        "where": "China, Japan, Korea,<br>EU specialists",
        "what": "Battery-grade salts,<br>magnet-grade oxides,<br>semiconductor purity.",
        "lock": "Patents, IP,<br>decades of process<br>knowledge.",
    },
    {
        "title": "End<br>product",
        "verb": "Manufacture",
        "who": "OEMs and tier-one<br>suppliers",
        "where": "Global — China, Japan,<br>Korea, EU, US",
        "what": "Magnets, batteries,<br>chips, alloys built into<br>cars, turbines, weapons.",
        "lock": "Where consumer<br>demand is felt.",
    },
]


def build() -> Path:
    n = len(STAGES)
    fig = go.Figure()

    # Geometry — boxes laid out left-to-right with gaps for arrows
    box_w = 1.55
    box_h = 1.5
    gap = 0.50
    x_start = 0.30
    box_y_top = 4.0
    box_y_bot = box_y_top - box_h

    centers = []
    for i in range(n):
        x0 = x_start + i * (box_w + gap)
        x1 = x0 + box_w
        cx = (x0 + x1) / 2
        centers.append((x0, x1, cx))

    # Colour deepens upstream → midstream → downstream as a visual gradient
    box_fills = [PAPER_WARM, "#EDE6D8", "#D8CBB6", "#C9A38C", "#A07850"]
    box_lines = [PRUSSIAN, PRUSSIAN, OXBLOOD, OXBLOOD, "#5A3D2A"]

    # Upstream / midstream / downstream grouping bands above the boxes
    band_y_top = box_y_top + 1.10
    band_y_bot = box_y_top + 0.55
    band_groups = [
        ("Upstream",   centers[0][0], centers[1][1], "rgba(15, 61, 92, 0.10)", PRUSSIAN),
        ("Midstream",  centers[2][0], centers[2][1], "rgba(123, 45, 38, 0.18)", OXBLOOD),
        ("Downstream", centers[3][0], centers[4][1], "rgba(160, 120, 80, 0.18)", "#5A3D2A"),
    ]
    for label, gx0, gx1, fill, edge in band_groups:
        fig.add_shape(
            type="rect",
            x0=gx0, x1=gx1, y0=band_y_bot, y1=band_y_top,
            line=dict(color=edge, width=1.2),
            fillcolor=fill,
            layer="below",
        )
        fig.add_annotation(
            x=(gx0 + gx1) / 2, y=(band_y_top + band_y_bot) / 2,
            text=f"<b>{label}</b>",
            showarrow=False,
            font=dict(family=FONT_SERIF, size=18, color=edge),
            xanchor="center", yanchor="middle",
        )

    for i, stage in enumerate(STAGES):
        x0, x1, cx = centers[i]

        # Stage number ABOVE the box
        fig.add_annotation(
            x=cx, y=box_y_top + 0.22,
            text=f"<span style='letter-spacing:.18em;font-size:11px;color:#5a544c'>STAGE {i+1}</span>",
            showarrow=False, xanchor="center", yanchor="bottom",
        )

        # Box
        fig.add_shape(
            type="rect",
            x0=x0, x1=x1, y0=box_y_bot, y1=box_y_top,
            line=dict(color=box_lines[i], width=2.2),
            fillcolor=box_fills[i],
            layer="below",
        )

        # Stage title (centered inside box)
        fig.add_annotation(
            x=cx, y=(box_y_top + box_y_bot) / 2,
            text=f"<b>{stage['title']}</b>",
            showarrow=False,
            font=dict(family=FONT_SERIF, size=22, color=PAPER_INK),
            xanchor="center", yanchor="middle",
        )

        # Arrow connector to next box
        if i < n - 1:
            ax0 = x1
            ax1 = centers[i + 1][0]
            ay = (box_y_top + box_y_bot) / 2
            # arrow line
            fig.add_annotation(
                x=ax1, y=ay, ax=ax0, ay=ay,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.4, arrowwidth=2.4,
                arrowcolor=PRUSSIAN if i < 2 else OXBLOOD,
            )
            # verb above arrow
            fig.add_annotation(
                x=(ax0 + ax1) / 2, y=ay + 0.25,
                text=f"<i>{stage['verb'] if i == 0 else STAGES[i+1]['verb']}</i>",
                showarrow=False,
                font=dict(family=FONT_SERIF, size=13, color=PAPER_INK),
                xanchor="center", yanchor="bottom",
            )

        # Annotation block below each box
        below_y_start = box_y_bot - 0.30
        line_gap = 0.70

        fig.add_annotation(
            x=cx, y=below_y_start,
            text=f"<b style='color:{PRUSSIAN}'>Who</b>  {stage['who']}",
            showarrow=False, xanchor="center", yanchor="top",
            font=dict(size=12, color=PAPER_INK),
            align="center",
        )
        fig.add_annotation(
            x=cx, y=below_y_start - line_gap,
            text=f"<b style='color:{PRUSSIAN}'>Where</b>  {stage['where']}",
            showarrow=False, xanchor="center", yanchor="top",
            font=dict(size=12, color=PAPER_INK),
            align="center",
        )
        fig.add_annotation(
            x=cx, y=below_y_start - 2 * line_gap,
            text=f"<span style='color:#4a443c'>{stage['what']}</span>",
            showarrow=False, xanchor="center", yanchor="top",
            font=dict(size=12, color=PAPER_INK),
            align="center",
        )
        fig.add_annotation(
            x=cx, y=below_y_start - 3 * line_gap - 0.05,
            text=f"<b style='color:{OXBLOOD};font-style:italic'>{stage['lock']}</b>",
            showarrow=False, xanchor="center", yanchor="top",
            font=dict(size=12, color=PAPER_INK),
            align="center",
        )

    # Bottom narrative summary band — pushed below the wrapped 4-line text
    summary_y = box_y_bot - 4.50
    fig.add_shape(
        type="rect",
        x0=x_start - 0.05, x1=centers[-1][1] + 0.05,
        y0=summary_y - 0.55, y1=summary_y + 0.20,
        line=dict(color=PAPER_RULE, width=1),
        fillcolor="rgba(15, 61, 92, 0.06)",
        layer="below",
    )
    fig.add_annotation(
        x=(x_start + centers[-1][1]) / 2, y=summary_y - 0.18,
        text=(
            "<b>The strategic question is not who pulls the rock — it is who runs Stage 3.</b><br>"
            "<span style='color:#4a443c;font-size:13px'>"
            "Mining is geographically diversified; refining is not. Whoever controls the "
            "refined-intermediate stage sets the price and decides whether the chain runs at all.</span>"
        ),
        showarrow=False, xanchor="center", yanchor="middle",
        font=dict(family=FONT_SERIF, size=15, color=PAPER_INK),
        align="center",
    )

    # Layout
    fig.update_layout(
        title=dict(
            text=(
                "<b>From rock to product — five stages</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Where each stage sits, what happens, and where the leverage lives.</span>"
            ),
        ),
        xaxis=dict(
            range=[x_start - 0.20, centers[-1][1] + 0.20],
            visible=False,
        ),
        yaxis=dict(
            range=[summary_y - 1.20, band_y_top + 0.30],
            visible=False,
        ),
        height=820,
        margin=dict(l=20, r=20, t=120, b=40),
        showlegend=False,
        plot_bgcolor=PAPER_WARM,
    )

    write_chart(fig, OUT_PATH, static=True)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[supply_chain_schematic] wrote {p.relative_to(ROOT)}")
