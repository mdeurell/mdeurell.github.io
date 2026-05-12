"""Build lightweight story context for the website and explainer notebook.

The output is derived from processed data only and keeps narrative-facing facts
in one place so the static website and notebook stay aligned.
"""

from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
WEBSITE_DATA = ROOT / "website" / "data"
MANIFEST_PATH = ROOT / "website" / "visualizations" / "manifest.json"

ECONOMIC_PATH = PROCESSED / "master_economic_timeseries.csv"
TRADE_PATH = PROCESSED / "master_supply_chain_trade.csv"
DEPOSITS_PATH = PROCESSED / "master_geo_deposits.geojson"

TARGET_MINERALS = [
    "Copper",
    "Lithium",
    "Graphite",
    "Neodymium",
    "Dysprosium",
    "Cobalt",
    "Gallium",
    "Platinum",
]
TRADE_DEDUP_COLS = [
    "year",
    "country",
    "partner_country",
    "flow_direction",
    "hs_code",
    "value_usd",
    "quantity_tonnes",
]


def read_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def read_economic() -> pd.DataFrame:
    df = pd.read_csv(ECONOMIC_PATH)
    return df[df["mineral"].isin(TARGET_MINERALS)].copy()


def read_trade() -> pd.DataFrame:
    df = pd.read_csv(TRADE_PATH)
    return df[df["mineral"].isin(TARGET_MINERALS)].copy()


def read_deposits() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DEPOSITS_PATH)
    return gdf[gdf["mineral"].isin(TARGET_MINERALS)].copy()


def unique_trade_flows(df: pd.DataFrame) -> pd.DataFrame:
    trade = df[df["record_type"] == "trade_flow"].copy()
    trade["partner_group"] = trade["partner_group"].fillna("Other countries")
    trade["partner_country"] = trade["partner_country"].fillna("Unknown")
    trade["country"] = trade["country"].fillna("Unknown")
    return trade.drop_duplicates(subset=TRADE_DEDUP_COLS)


def latest_price_snapshot(economic: pd.DataFrame) -> dict:
    prices = economic[economic["metric"] == "historical_price_usd_per_tonne"].copy()
    latest_year = int(prices["year"].max())
    latest = prices[prices["year"] == latest_year][["mineral", "value"]].rename(
        columns={"value": "latest_value"}
    )
    base = prices[prices["year"] == 2015][["mineral", "value"]].rename(
        columns={"value": "base_value"}
    )
    indexed = latest.merge(base, on="mineral", how="inner")
    indexed = indexed[indexed["base_value"] > 0].copy()
    indexed["index_vs_2015"] = indexed["latest_value"] / indexed["base_value"] * 100
    top = indexed.sort_values("index_vs_2015", ascending=False).iloc[0]
    return {
        "latest_year": latest_year,
        "top_mineral": top["mineral"],
        "top_index_vs_2015": round(float(top["index_vs_2015"]), 1),
    }


def top_end_uses(economic: pd.DataFrame) -> list[dict]:
    end_use = economic[economic["metric"] == "end_use_share_pct"].copy()
    latest_year = int(end_use["year"].max())
    top = (
        end_use[end_use["year"] == latest_year]
        .sort_values(["mineral", "value"], ascending=[True, False])
        .groupby("mineral", as_index=False)
        .head(1)[["mineral", "category", "value"]]
    )
    records = top.to_dict(orient="records")
    for record in records:
        record["year"] = latest_year
        record["value"] = round(float(record["value"]), 1)
    return records


def leader_snapshot(trade: pd.DataFrame) -> dict:
    stage = trade[trade["record_type"] == "stage_share"].copy()
    stage = stage[(stage["year"] == 2023) & (stage["country"] != "Other")].copy()
    stage = stage[stage["stage"].isin(["mining", "processing"])]

    mining = (
        stage[stage["stage"] == "mining"]
        .sort_values(["mineral", "share_pct"], ascending=[True, False])
        .groupby("mineral", as_index=False)
        .head(1)[["mineral", "country", "share_pct"]]
        .rename(columns={"country": "mining_country", "share_pct": "mining_share"})
    )
    processing = (
        stage[stage["stage"] == "processing"]
        .sort_values(["mineral", "share_pct"], ascending=[True, False])
        .groupby("mineral", as_index=False)
        .head(1)[["mineral", "country", "share_pct"]]
        .rename(
            columns={
                "country": "processing_country",
                "share_pct": "processing_share",
            }
        )
    )
    leaders = mining.merge(processing, on="mineral", how="inner").to_dict(orient="records")
    return {row["mineral"]: row for row in leaders}


def concentration_summary(trade: pd.DataFrame) -> dict:
    hhi = trade[
        (trade["record_type"] == "hhi")
        & (trade["year"] == 2023)
        & (trade["stage"].isin(["mining", "processing"]))
    ][["mineral", "stage", "hhi"]].dropna()
    hhi = hhi.drop_duplicates(subset=["mineral", "stage"])
    hhi["high_concentration"] = hhi["hhi"] >= 2500

    summary = {}
    for stage_name, group in hhi.groupby("stage"):
        summary[stage_name] = {
            "high_count": int(group["high_concentration"].sum()),
            "total": int(len(group)),
        }
    return summary


def china_bloc_shift(trade: pd.DataFrame) -> dict:
    china = unique_trade_flows(trade)
    china = china[
        (china["country"] == "China")
        & (china["flow_direction"] == "export")
        & (china["year"].isin([2015, 2023]))
    ].copy()
    china["bloc"] = china["partner_group"].where(
        china["partner_group"].isin(["EU-27", "United States"]),
        "Other countries",
    )

    grouped = china.groupby(["year", "bloc"], as_index=False)["value_usd"].sum()
    totals = grouped.groupby("year")["value_usd"].transform("sum")
    grouped["share_pct"] = grouped["value_usd"] / totals * 100

    summary: dict[str, dict[str, float]] = {}
    for year, group in grouped.groupby("year"):
        shares = {row["bloc"]: round(float(row["share_pct"]), 1) for _, row in group.iterrows()}
        shares["western_bloc"] = round(
            shares.get("EU-27", 0.0) + shares.get("United States", 0.0),
            1,
        )
        summary[str(int(year))] = shares
    return summary


def build_context() -> dict:
    manifest = read_manifest()
    economic = read_economic()
    trade = read_trade()
    deposits = read_deposits()

    price = latest_price_snapshot(economic)
    leaders = leader_snapshot(trade)
    concentration = concentration_summary(trade)
    bloc_shift = china_bloc_shift(trade)

    return {
        "project": {
            "title": "Critical Earth",
            "subtitle": "How a handful of minerals became leverage in the post-oil economy",
            "question": "Is the global critical minerals supply chain splitting into two blocs?",
            "notebook_href": "explainer_notebook.ipynb",
            "notebook_source_href": "../notebooks/explainer_notebook.ipynb",
        },
        "hero_stats": [
            {
                "value": len(TARGET_MINERALS),
                "label": "target minerals",
                "detail": "The story follows the same eight minerals across every processed master.",
            },
            {
                "value": int(len(deposits)),
                "label": "mapped deposits",
                "detail": "Deposit points and country-level fallbacks come from the processed geology master.",
            },
            {
                "value": int(deposits["country"].nunique()),
                "label": "countries with deposits",
                "detail": "Geology is widespread even when processing power is not.",
            },
        ],
        "highlights": {
            "price": price,
            "end_uses": top_end_uses(economic),
            "leaders_2023": leaders,
            "concentration_2023": concentration,
            "china_bloc_share": bloc_shift,
            "trade_note": "Comtrade evidence in the narrative compares 2015 with 2023. 2025 remains a partial reporting year.",
        },
        "visualization_manifest": manifest,
    }


def main() -> None:
    WEBSITE_DATA.mkdir(parents=True, exist_ok=True)
    context = build_context()

    json_path = WEBSITE_DATA / "story_context.json"
    js_path = WEBSITE_DATA / "story_context.js"

    json_text = json.dumps(context, indent=2)
    json_path.write_text(json_text, encoding="utf-8")
    js_path.write_text(f"window.STORY_CONTEXT = {json_text};\n", encoding="utf-8")

    print("Built story context:")
    print(f"- json: {json_path.relative_to(ROOT)}")
    print(f"- js: {js_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
