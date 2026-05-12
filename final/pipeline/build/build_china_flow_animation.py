"""
Build animated bilateral trade-flow maps for China, 2000–2024.

Outputs two standalone Plotly HTML files:
    website/visualizations/bifurcation/china_flow_exports.html
    website/visualizations/bifurcation/china_flow_imports.html

Each file: scattergeo with great-circle-ish arcs, year slider with play
button, mineral dropdown. Newspaper theme inherits from website/theme.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from website.theme import (  # noqa: E402
    FONT_FAMILY, MOLTEN_ORANGE, PAPER_INK, PAPER_WARM, PAPER_RULE_S,
    MINERAL_COLORS, write_chart,
)

VIS_OUT = ROOT / "website" / "visualizations" / "bifurcation"
NE_PATH = ROOT / "data" / "raw" / "G Natural Earth" / "ne_110m_admin_0_sovereignty.shp"
# Unified China trade flows: original 4 minerals (master_supply_chain_trade)
# plus the 3 Cu/Graphite/Pt extensions fetched May 2026.
TRADE_PATH = ROOT / "data" / "processed" / "china_trade_flows_all_materials.csv"

CHINA_LAT, CHINA_LON = 35.0, 104.0  # geographic centroid, roughly
TOP_N_PARTNERS = 10
YEARS = list(range(2000, 2025))

# Category → label, colour, direction, [HS codes].
# Multiple HS codes per category collapse the REE-tagging duplication into
# one map per supply-chain story (rather than four maps showing the same data).
CATEGORIES = [
    # name,           colour,    direction, hs_codes
    # All seven focus materials carried on both maps so the dropdown
    # is identical regardless of direction. Materials with limited
    # flow in one direction simply read sparse — but the option exists.
    ("Rare Earths",   "#A07850", "both", [253090.0, 280530.0, 284610.0, 284690.0, 850511.0]),
    ("Gallium",       "#6E8898", "both", [811292.0]),
    ("Lithium",       "#45B7D1", "both", [283691.0]),
    ("Cobalt",        "#3A5EA5", "both", [810520.0]),
    ("Copper",        "#8B5A2B", "both", [260300.0, 740311.0]),
    ("Graphite",      "#5C5C5C", "both", [250410.0, 380110.0]),
    ("Platinum",      "#A8A8A8", "both", [711011.0, 711019.0]),
]

# Manual ISO3 → (lat, lon) fallback for codes that disagree between
# Comtrade (standard ISO3) and Natural Earth's 110m sovereignty file
# (which uses suffixed codes like US1 / FR1). Without these, partner
# rows are silently dropped from the map.
ISO3_FALLBACK = {
    "USA": (39.8, -98.6),
    "FRA": (46.2,   2.2),
    "AUS": (-25.3, 133.8),
    "CHN": (35.0,  104.0),
    "DNK": (56.0,   10.0),
    "ESH": (24.2,  -12.9),
    "FIN": (64.5,   26.0),
    "GBR": (54.0,   -2.0),
    "GEO": (42.0,   43.5),
    "ISR": (31.0,   34.8),
    "NLD": (52.1,    5.3),
    "NZL": (-41.0, 174.0),
    "SSD": (7.0,    30.0),
}


def country_centroids() -> dict[str, tuple[float, float]]:
    """ISO3 -> (lat, lon) representative point."""
    gdf = gpd.read_file(NE_PATH)
    # representative_point() guarantees the centroid lies inside the polygon
    pts = gdf.geometry.representative_point()
    out: dict[str, tuple[float, float]] = {}
    for iso3, pt in zip(gdf["ADM0_A3"], pts):
        if isinstance(iso3, str) and len(iso3) == 3:
            out[iso3] = (float(pt.y), float(pt.x))
    # A few small / disputed countries that show up in Comtrade but not in the
    # 110m sovereignty file — fall back to obvious points.
    out.setdefault("HKG", (22.3, 114.2))
    out.setdefault("SGP", (1.35, 103.82))
    out.setdefault("BHR", (26.07, 50.55))
    out.setdefault("MLT", (35.9, 14.5))
    out.setdefault("MUS", (-20.3, 57.55))
    # Patch standard ISO3 codes that Natural Earth's sovereignty file
    # encodes with suffixes (USA→US1, FRA→FR1, etc.).
    for iso3, latlon in ISO3_FALLBACK.items():
        out.setdefault(iso3, latlon)
    return out


def filter_china_flows(direction: str) -> pd.DataFrame:
    """Load China-as-reporter trade flows, deduplicated to one row per
    (year, partner, hs_code) by max value (the same row is duplicated by
    the master pipeline once per REE label — we collapse that here).

    Uses `value_real_2015_usd` (CPI-deflated) where available so the
    animated comparisons across 2000-2024 are honest — a 2010 dollar of
    trade volume is shown on the same scale as a 2024 dollar.
    """
    df = pd.read_csv(TRADE_PATH, low_memory=False)
    # Prefer the inflation-adjusted column when present; fall back to
    # nominal value_usd for any rows that lack the deflation.
    if "value_real_2015_usd" in df.columns:
        df["value_usd"] = df["value_real_2015_usd"].fillna(df["value_usd"])
    # Patch missing partner_iso3 codes from partner_country names. The
    # Comtrade extract has DRC rows (~$29 B cumulative cobalt) with no iso3,
    # so without this they get filtered out below and Zambia ends up
    # looking like the biggest supplier — wrong by two orders of magnitude.
    _ISO_PATCH = {
        "Dem. Rep. of the Congo":          "COD",
        "Democratic Republic of the Congo": "COD",
        "Congo (Kinshasa)":                 "COD",
        "Korea, Rep.":                      "KOR",
        "Russian Federation":               "RUS",
        "Viet Nam":                         "VNM",
        "United States of America":        "USA",
        "Bolivia (Plurinational State of)": "BOL",
        "Tanzania, United Rep. of":        "TZA",
        "Iran, Islamic Rep.":              "IRN",
        "Türkiye":                          "TUR",
    }
    missing_iso = df["partner_iso3"].isna() | (df["partner_iso3"] == "")
    df.loc[missing_iso, "partner_iso3"] = df.loc[missing_iso, "partner_country"].map(_ISO_PATCH)
    # The new combined source is already China-as-reporter, trade_flow rows
    # only, so the record_type / country filters drop away.
    df = df[
        (df["flow_direction"] == direction)
        & df["partner_iso3"].notna()
        & df["value_usd"].notna()
        & df["hs_code"].notna()
    ].copy()
    df["year"] = df["year"].astype(int)
    df = df[df["year"].between(YEARS[0], YEARS[-1])]
    # Dedupe on the HS-code level (one underlying customs row per HS code)
    df = (
        df.sort_values("value_usd", ascending=False)
        .drop_duplicates(subset=["year", "partner_iso3", "hs_code"], keep="first")
    )
    # Map HS code → category, restricting to categories valid for this direction
    code_to_cat: dict[float, str] = {}
    for name, _color, dir_, codes in CATEGORIES:
        if dir_ == direction or dir_ == "both":
            for c in codes:
                code_to_cat[c] = name
    df = df[df["hs_code"].isin(code_to_cat)].copy()
    df["category"] = df["hs_code"].map(code_to_cat)
    return df


def aggregate_top_partners(
    df: pd.DataFrame,
    categories: list[str],
    centroids: dict[str, tuple[float, float]],
) -> pd.DataFrame:
    """Returns rows: category, year, partner_iso3, partner, value_usd, lat, lon."""
    df = df[df["category"].isin(categories)].copy()
    grp = (
        df.groupby(["category", "year", "partner_iso3", "partner_country"], as_index=False)
        ["value_usd"].sum()
    )
    grp = grp[grp["partner_iso3"].isin(centroids)]
    grp[["lat", "lon"]] = grp["partner_iso3"].apply(
        lambda c: pd.Series(centroids[c])
    )
    grp = (
        grp.sort_values(["category", "year", "value_usd"], ascending=[True, True, False])
        .groupby(["category", "year"], as_index=False)
        .head(TOP_N_PARTNERS)
    )
    return grp


def arc_lat_lon(top: pd.DataFrame, origin_lat: float, origin_lon: float):
    """Build NaN-separated lat/lon arrays for one trace's arc segments."""
    lats: list[float] = []
    lons: list[float] = []
    for _, r in top.iterrows():
        lats += [origin_lat, r.lat, np.nan]
        lons += [origin_lon, r.lon, np.nan]
    return lats, lons


def build_figure(direction: str, df: pd.DataFrame, centroids: dict[str, tuple[float, float]]) -> go.Figure:
    # Use the full CATEGORIES list (in declared order) so all seven focus
    # materials appear in the dropdown regardless of direction. Categories
    # with no rows for this direction will render an empty map for the
    # selected year — visible as "no significant flow" rather than missing
    # from the picker entirely.
    categories = [name for name, _c, _d, _h in CATEGORIES]
    default_category = (
        "Rare Earths" if direction == "export" and "Rare Earths" in categories
        else ("Cobalt" if "Cobalt" in categories else categories[0])
    )

    top = aggregate_top_partners(df, categories, centroids)

    # Origin = China for exports (arrows leave China) and for imports too
    # (we still anchor at China and draw lines to the source partner — the
    # geometry is the same; the verb in the figure caption changes).
    origin_lat, origin_lon = CHINA_LAT, CHINA_LON

    fig = go.Figure()

    # Color lookup, available before traces are added so the China origin
    # marker can be tinted with the default category's colour.
    color_map = {name: col for name, col, _, _ in CATEGORIES}
    default_color = color_map.get(default_category, PAPER_INK)

    # Reference: China origin marker — fill AND outline take the selected
    # element's colour, so the map keys to whichever element the dropdown is
    # showing.
    fig.add_trace(
        go.Scattergeo(
            lon=[origin_lon],
            lat=[origin_lat],
            mode="markers",
            marker=dict(size=13, color=default_color, line=dict(color=PAPER_INK, width=1.4)),
            hovertemplate=(f"<b>China</b><br>{'Reporter (exporter)' if direction == 'export' else 'Reporter (importer)'}<extra></extra>"),
            name="China",
            showlegend=False,
        )
    )

    # Initial frame: cumulative 2000–2024 view so the chart opens with the
    # full historical picture, not just one slice. The slider sits on Σ
    # by default; the user can scrub left to walk through individual years.
    cumulative_initial = (
        top.groupby(["category", "partner_iso3", "partner_country", "lat", "lon"],
                    as_index=False)["value_usd"].sum()
    )
    cumulative_initial = (
        cumulative_initial.sort_values(["category", "value_usd"], ascending=[True, False])
        .groupby("category", as_index=False)
        .head(TOP_N_PARTNERS)
        .reset_index(drop=True)
    )

    trace_index_by_cat: dict[str, dict[str, int]] = {}
    for c in categories:
        color = color_map.get(c, MOLTEN_ORANGE)
        sub = cumulative_initial[cumulative_initial["category"] == c]
        lats, lons = arc_lat_lon(sub, origin_lat, origin_lon)
        visible = (c == default_category)

        arc_idx = len(fig.data)
        fig.add_trace(
            go.Scattergeo(
                lat=lats,
                lon=lons,
                mode="lines",
                line=dict(color=color, width=2.2),
                opacity=0.6,
                name=f"{c} (arcs)",
                hoverinfo="skip",
                visible=visible,
                showlegend=False,
            )
        )

        marker_idx = len(fig.data)
        fig.add_trace(
            go.Scattergeo(
                lat=sub["lat"],
                lon=sub["lon"],
                mode="markers",
                marker=dict(
                    size=(np.sqrt(sub["value_usd"].fillna(0)) / np.sqrt(sub["value_usd"].max() or 1) * 36 + 8)
                    if len(sub) else [],
                    color=color,
                    line=dict(color=PAPER_INK, width=0.8),
                    opacity=0.85,
                ),
                customdata=np.stack([sub["partner_country"], sub["value_usd"]], axis=-1) if len(sub) else None,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    f"{c} · {'export' if direction == 'export' else 'import'}<br>"
                    "USD %{customdata[1]:,.0f}<extra></extra>"
                ),
                name=c,
                visible=visible,
                showlegend=False,
            )
        )
        trace_index_by_cat[c] = {"arc": arc_idx, "marker": marker_idx}

    # ── Build animation frames (one per year) ───────────────────────────
    frames = []
    yearly = sorted(top["year"].unique())
    # Re-use the cumulative aggregate built for the initial state so the
    # Σ frame and the chart's opening view show identical data.
    cumulative = cumulative_initial

    def _frame_traces(scope_df: pd.DataFrame) -> list:
        traces = []
        for c in categories:
            sub = scope_df[scope_df["category"] == c]
            lats, lons = arc_lat_lon(sub, origin_lat, origin_lon)
            color = color_map.get(c, MOLTEN_ORANGE)
            traces.append(
                go.Scattergeo(lat=lats, lon=lons, mode="lines",
                              line=dict(color=color, width=2.2), opacity=0.6)
            )
            sizes = (
                (np.sqrt(sub["value_usd"].fillna(0)) / np.sqrt(sub["value_usd"].max() or 1) * 36 + 8).tolist()
                if len(sub) else []
            )
            traces.append(
                go.Scattergeo(
                    lat=sub["lat"],
                    lon=sub["lon"],
                    mode="markers",
                    marker=dict(size=sizes, color=color,
                                line=dict(color=PAPER_INK, width=0.8), opacity=0.85),
                    customdata=np.stack([sub["partner_country"], sub["value_usd"]], axis=-1)
                    if len(sub) else None,
                )
            )
        return traces

    traces_to_update: list[int] = []
    for c in categories:
        traces_to_update.append(trace_index_by_cat[c]["arc"])
        traces_to_update.append(trace_index_by_cat[c]["marker"])

    for yr in yearly:
        scope = top[top["year"] == yr]
        frames.append(go.Frame(
            name=str(yr),
            data=_frame_traces(scope),
            traces=traces_to_update,
        ))

    # Final cumulative frame — 2000–2024 total flow per partner.
    frames.append(go.Frame(
        name="Cumulative",
        data=_frame_traces(cumulative),
        traces=traces_to_update,
    ))

    fig.frames = frames

    # ── Updatemenus: category dropdown + play/pause buttons ────────────
    # Pre-compute the static marker.color value for each trace once, so
    # each dropdown button can ship a full per-trace array. Trace 0 is the
    # China origin (retinted per-button); arc traces are line-only (the
    # marker.color value is harmless there); per-category marker traces keep
    # their existing per-element colour.
    base_marker_colors: list[str] = [PAPER_INK] * len(fig.data)
    for cc in categories:
        cc_color = color_map.get(cc, PAPER_INK)
        cidx = trace_index_by_cat[cc]
        base_marker_colors[cidx["arc"]] = cc_color
        base_marker_colors[cidx["marker"]] = cc_color

    category_buttons = []
    for c in categories:
        vis = [True] + [False] * (len(fig.data) - 1)
        idx = trace_index_by_cat[c]
        vis[idx["arc"]] = True
        vis[idx["marker"]] = True
        cat_color = color_map.get(c, PAPER_INK)
        # Override trace 0 (China origin) with the selected element's colour.
        marker_colors = base_marker_colors.copy()
        marker_colors[0] = cat_color
        category_buttons.append(dict(
            method="update",
            label=c,
            args=[{
                "visible": vis,
                "marker.color": marker_colors,
            }],
        ))

    play_pause = dict(
        type="buttons",
        direction="left",
        showactive=False,
        x=0.0, xanchor="left", y=-0.08, yanchor="top",
        pad=dict(t=4, b=4, l=4, r=4),
        bgcolor=PAPER_WARM, bordercolor=PAPER_INK, borderwidth=1,
        font=dict(family=FONT_FAMILY, size=10, color=PAPER_INK),
        buttons=[
            dict(label="▶ Play",  method="animate",
                 args=[None, {"frame": {"duration": 700, "redraw": True},
                              "fromcurrent": True,
                              "transition": {"duration": 200}}]),
            dict(label="❚❚ Pause", method="animate",
                 args=[[None], {"frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0}}]),
        ],
    )

    category_dd = dict(
        type="dropdown",
        direction="down",
        showactive=True,
        x=1.0, xanchor="right", y=1.12, yanchor="top",
        pad=dict(t=2, b=2, l=6, r=6),
        bgcolor=PAPER_WARM, bordercolor=PAPER_INK, borderwidth=1,
        font=dict(family=FONT_FAMILY, size=11, color=PAPER_INK),
        active=categories.index(default_category),
        buttons=category_buttons,
    )

    slider_steps = [
        dict(method="animate", label=str(yr),
             args=[[str(yr)], {"frame": {"duration": 0, "redraw": True},
                               "mode": "immediate"}])
        for yr in yearly
    ]
    slider_steps.append(dict(
        method="animate", label="Σ",
        args=[["Cumulative"], {"frame": {"duration": 0, "redraw": True},
                               "mode": "immediate"}],
    ))
    sliders = [dict(
        active=len(slider_steps) - 1,   # land on the cumulative frame
        x=0.12, xanchor="left", y=-0.05, yanchor="top",
        len=0.86,
        pad=dict(t=4, b=4),
        currentvalue=dict(
            prefix="Year ",
            font=dict(family=FONT_FAMILY, size=12, color=PAPER_INK),
        ),
        bgcolor=PAPER_RULE_S,
        bordercolor=PAPER_INK,
        activebgcolor=PAPER_INK,
        tickcolor=PAPER_INK,
        font=dict(family=FONT_FAMILY, size=10, color=PAPER_INK),
        steps=slider_steps,
    )]

    title_main = ("China critical-mineral exports, 2000–2024"
                  if direction == "export"
                  else "China critical-mineral imports, 2000–2024")
    title_sub = ("Refined value-added flowing out of China — animated by year."
                 if direction == "export"
                 else "Raw upstream material flowing into China — animated by year.")
    fig.update_layout(
        paper_bgcolor=PAPER_WARM,
        plot_bgcolor=PAPER_WARM,
        margin=dict(l=80, r=80, t=140, b=110),
        font=dict(family=FONT_FAMILY, size=12, color=PAPER_INK),
        title=dict(
            text=(
                f"<b>{title_main}</b>"
                f"<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                f"{title_sub}</span>"
            ),
        ),
        geo=dict(
            projection=dict(type="natural earth"),
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
        ),
        updatemenus=[play_pause, category_dd],
        sliders=sliders,
        hoverlabel=dict(
            bgcolor=PAPER_INK,
            font=dict(family=FONT_FAMILY, size=12, color=PAPER_WARM),
            bordercolor=PAPER_INK,
        ),
    )
    return fig


def write_html(fig: go.Figure, path: Path) -> None:
    write_chart(fig, path, legend_pos="none")


def main() -> None:
    VIS_OUT.mkdir(parents=True, exist_ok=True)
    centroids = country_centroids()

    for direction, fname in [("export", "china_flow_exports.html"),
                             ("import", "china_flow_imports.html")]:
        df = filter_china_flows(direction)
        if df.empty:
            print(f"  skipping {direction} — no data")
            continue
        fig = build_figure(direction, df, centroids)
        out = VIS_OUT / fname
        write_html(fig, out)
        print(f"  wrote {out.relative_to(ROOT)}  ({df['category'].nunique()} HS categories, {df['year'].nunique()} years)")


if __name__ == "__main__":
    main()
