"""Figure 7.1 — Where China gets its rock.

Static Scattergeo map. For each of the seven focal materials, draws arcs
from China's top upstream supplier countries (China-as-importer,
cumulative 2015-2023) into a single origin point in China. Arc colour
encodes the material (per MINERAL_COLORS); arc width encodes total trade
value.

Inputs:
  data/processed/upstream_top10_by_material.csv (built by
  pipeline.transform.build_upstream_view)
  data/raw/G Natural Earth/ne_110m_admin_0_sovereignty.shp
    (via the existing build_china_flow_animation.country_centroids helper)
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

from pipeline.build.build_china_flow_animation import (
    CHINA_LAT, CHINA_LON, country_centroids,
)
from website.theme import (
    FONT_FAMILY,
    MINERAL_COLORS,
    PAPER_INK,
    PAPER_WARM,
    write_chart,
)

TOP_PATH = ROOT / "data" / "processed" / "upstream_top10_by_material.csv"
OUT_PATH = ROOT / "website" / "visualizations" / "trade-flows" / "upstream_supplier_map.html"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


MIN_SHARE_PCT = 2.0   # arcs below this trip the visual noise threshold
TOP_PARTNERS_PER_MINERAL = 5

# Materials in the order they appear in the dataset's actual top suppliers.
# Maps a few naming differences between the upstream CSV and ISO3 helper.
PARTNER_ISO_PATCHES = {
    "Dem. Rep. of the Congo": "COD",
    "Korea, Rep.": "KOR",
    "Russian Federation": "RUS",
    "Saudi Arabia": "SAU",
    "United States of America": "USA",
    "Viet Nam": "VNM",
    "Iran, Islamic Rep.": "IRN",
    "Türkiye": "TUR",
    "Czechia": "CZE",
    "Slovakia": "SVK",
    "Bolivia (Plurinational State of)": "BOL",
    "Tanzania, United Rep. of": "TZA",
    "China, Hong Kong SAR": "HKG",
    "China, Taiwan Province of": "TWN",
}


def _arc_lat_lon(rows: pd.DataFrame):
    """NaN-separated arc segments China → each partner."""
    lats, lons = [], []
    for _, r in rows.iterrows():
        lats += [CHINA_LAT, r["lat"], np.nan]
        lons += [CHINA_LON, r["lon"], np.nan]
    return lats, lons


FOCUS_MATERIALS = {
    "Cobalt", "Lithium", "Copper", "Graphite", "Gallium",
    "Platinum", "Rare Earths",
}


def build() -> Path:
    top = pd.read_csv(TOP_PATH)
    top = top[top["share_pct"] >= MIN_SHARE_PCT].copy()
    # Filter to the seven focus materials. Palladium was pulled in via the
    # extended Comtrade fetch but is not part of the project's portfolio.
    top = top[top["mineral"].isin(FOCUS_MATERIALS)]

    # Resolve partner lat/lon
    centroids = country_centroids()
    iso = top["partner_iso3"].copy()
    # backfill missing iso via name patches
    missing = iso.isna() | (iso == "")
    if missing.any():
        iso.loc[missing] = top.loc[missing, "partner_country"].map(PARTNER_ISO_PATCHES)
    top["partner_iso3"] = iso
    top = top.dropna(subset=["partner_iso3"])
    top = top[top["partner_iso3"].isin(centroids)]
    top[["lat", "lon"]] = top["partner_iso3"].apply(lambda c: pd.Series(centroids[c]))

    # Cap to top-N per material
    top = (
        top.sort_values(["mineral", "value_usd"], ascending=[True, False])
        .groupby("mineral", group_keys=False)
        .head(TOP_PARTNERS_PER_MINERAL)
        .reset_index(drop=True)
    )

    fig = go.Figure()

    # China origin marker (drawn first, same style as 7.3 animated map)
    fig.add_trace(go.Scattergeo(
        lon=[CHINA_LON], lat=[CHINA_LAT],
        mode="markers",
        marker=dict(size=13, color="#DE2910",
                    line=dict(color=PAPER_INK, width=1.4)),
        hovertemplate="<b>China</b><br>Reporter (importer)<extra></extra>",
        name="China",
        showlegend=False,
    ))

    # Arc + marker trace per material — geometry and sizing match 7.3
    for mineral in sorted(top["mineral"].unique()):
        sub = top[top["mineral"] == mineral]
        color = MINERAL_COLORS.get(mineral, "#888888")
        lats, lons = _arc_lat_lon(sub)

        # Arc
        fig.add_trace(go.Scattergeo(
            lat=lats, lon=lons,
            mode="lines",
            line=dict(color=color, width=2.2),
            opacity=0.6,
            name=f"{mineral} (arcs)",
            legendgroup=mineral,
            hoverinfo="skip",
            showlegend=False,
        ))

        # Markers — sqrt-scaled, same formula as 7.3
        if len(sub):
            max_v = sub["value_usd"].max() or 1
            sizes = (np.sqrt(sub["value_usd"].fillna(0)) / np.sqrt(max_v) * 36 + 8)
        else:
            sizes = []
        fig.add_trace(go.Scattergeo(
            lat=sub["lat"], lon=sub["lon"],
            mode="markers",
            marker=dict(
                size=sizes,
                color=color,
                line=dict(color=PAPER_INK, width=0.8),
                opacity=0.85,
            ),
            customdata=np.stack(
                [sub["partner_country"], sub["value_usd"], sub["share_pct"]],
                axis=-1,
            ) if len(sub) else None,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                f"{mineral} · import<br>"
                "USD %{customdata[1]:,.0f}<br>"
                "%{customdata[2]:.1f}% of China's "
                f"{mineral.lower()} imports<extra></extra>"
            ),
            name=mineral,
            legendgroup=mineral,
            showlegend=True,
        ))

    fig.update_layout(
        title=dict(
            text=(
                "<b>Where China gets its rock</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Top upstream suppliers per material — cumulative 2015–2023 imports.</span>"
            ),
        ),
        margin=dict(l=8, r=8, t=140, b=40),
        font=dict(family=FONT_FAMILY, size=12, color=PAPER_INK),
        geo=dict(
            projection=dict(type="natural earth", scale=1.0),
            bgcolor=PAPER_WARM,
            showland=True,
            landcolor="#EFEAE0",
            showcountries=True,
            countrycolor="rgba(20,17,13,0.18)",
            countrywidth=0.4,
            showcoastlines=True,
            coastlinecolor=PAPER_INK,
            coastlinewidth=0.4,
            showocean=True,
            oceancolor=PAPER_WARM,
            showframe=False,
            lonaxis=dict(range=[-170, 190]),
            lataxis=dict(range=[-58, 78]),
            domain=dict(x=[0, 1], y=[0, 1]),
        ),
        paper_bgcolor=PAPER_WARM,
        plot_bgcolor=PAPER_WARM,
    )

    write_chart(fig, OUT_PATH)
    return OUT_PATH


if __name__ == "__main__":
    p = build()
    print(f"[upstream_map] wrote {p.relative_to(ROOT)}")
