"""Build analysis-ready master datasets for the Critical Earth project.

Outputs:
- data/processed/master_geo_deposits.geojson
- data/processed/master_economic_timeseries.csv
- data/processed/master_supply_chain_trade.csv
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import geopandas as gpd
import pandas as pd
from pandas.errors import EmptyDataError


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

TARGET_MINERALS = {
    "Copper": {"case_group": "Case 1", "mineral_group": "base metal"},
    "Lithium": {"case_group": "Case 1", "mineral_group": "battery mineral"},
    "Graphite": {"case_group": "Case 1", "mineral_group": "battery mineral"},
    "Neodymium": {"case_group": "Case 1", "mineral_group": "rare earth"},
    "Dysprosium": {"case_group": "Case 2", "mineral_group": "rare earth"},
    "Terbium": {"case_group": "Case 2", "mineral_group": "rare earth"},
    "Rare Earths": {"case_group": "Case 1+2", "mineral_group": "rare earth"},
    "Cobalt": {"case_group": "Case 2", "mineral_group": "battery mineral"},
    "Gallium": {"case_group": "Case 2", "mineral_group": "semiconductor mineral"},
    "Platinum": {"case_group": "Case 2", "mineral_group": "platinum-group metal"},
}

LB_PER_TONNE = 2204.62262185
KG_PER_TONNE = 1000
TROY_OZ_PER_TONNE = 32150.7465686

COMTRADE_HS_MINERALS = {
    "253090": ("Neodymium", "Dysprosium", "Terbium", "Rare Earths"),
    "280530": ("Neodymium", "Dysprosium", "Terbium", "Rare Earths"),
    "284610": ("Neodymium", "Dysprosium", "Terbium", "Rare Earths"),
    "284690": ("Neodymium", "Dysprosium", "Terbium", "Rare Earths"),
    "850511": ("Neodymium", "Dysprosium", "Terbium", "Rare Earths"),
    "283691": ("Lithium",),
    "810520": ("Cobalt",),
    "811292": ("Gallium",),
}

EU27_ISO3 = {
    "AUT", "BEL", "BGR", "HRV", "CYP", "CZE", "DNK", "EST", "FIN",
    "FRA", "DEU", "GRC", "HUN", "IRL", "ITA", "LVA", "LTU", "LUX",
    "MLT", "NLD", "POL", "PRT", "ROU", "SVK", "SVN", "ESP", "SWE",
}

NORDIC_ISO3 = {"DNK", "SWE", "NOR", "FIN", "ISL", "GRL", "FRO"}


@dataclass(frozen=True)
class CountryInfo:
    country: str | None
    iso3: str | None
    continent: str | None


def clean_text(value: object) -> str | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def key(value: object) -> str:
    text = clean_text(value) or ""
    return (
        text.lower()
        .replace("&", "and")
        .replace(".", "")
        .replace(",", "")
        .replace("(", "")
        .replace(")", "")
        .replace("-", " ")
        .replace("_", " ")
        .strip()
    )


def numeric(value: object) -> float | None:
    if value is None or pd.isna(value):
        return None
    text = str(value).strip().replace(",", "")
    if text in {"", "W", "w", "--", "—", "NA", "N/A"}:
        return None
    number = pd.to_numeric(text, errors="coerce")
    if pd.isna(number):
        return None
    return number


def load_country_lookup() -> dict[str, CountryInfo]:
    world_path = RAW / "G Natural Earth" / "ne_110m_admin_0_sovereignty.shp"
    world = gpd.read_file(world_path)
    lookup: dict[str, CountryInfo] = {}

    def register(alias: object, row: pd.Series) -> None:
        alias_key = key(alias)
        if not alias_key:
            return
        iso3 = clean_text(row.get("ISO_A3_EH")) or clean_text(row.get("ISO_A3"))
        if iso3 == "-99":
            iso3 = clean_text(row.get("ADM0_A3_US")) or clean_text(row.get("ADM0_A3"))
        info = CountryInfo(
            country=clean_text(row.get("ADMIN")) or clean_text(row.get("NAME")),
            iso3=iso3,
            continent=clean_text(row.get("CONTINENT")),
        )
        lookup.setdefault(alias_key, info)

    alias_columns = [
        "NAME",
        "NAME_LONG",
        "ADMIN",
        "SOVEREIGNT",
        "BRK_NAME",
        "NAME_SORT",
        "FORMAL_EN",
    ]
    for _, row in world.iterrows():
        for col in alias_columns:
            register(row.get(col), row)

    manual = {
        "united states": CountryInfo("United States of America", "USA", "North America"),
        "united states of america": CountryInfo(
            "United States of America", "USA", "North America"
        ),
        "usa": CountryInfo("United States of America", "USA", "North America"),
        "drc": CountryInfo("Democratic Republic of the Congo", "COD", "Africa"),
        "congo kinshasa": CountryInfo("Democratic Republic of the Congo", "COD", "Africa"),
        "congo democratic republic": CountryInfo(
            "Democratic Republic of the Congo", "COD", "Africa"
        ),
        "democratic republic of congo": CountryInfo(
            "Democratic Republic of the Congo", "COD", "Africa"
        ),
        "burma": CountryInfo("Myanmar", "MMR", "Asia"),
        "myanmar": CountryInfo("Myanmar", "MMR", "Asia"),
        "russia": CountryInfo("Russia", "RUS", "Europe"),
        "world total": CountryInfo("World", "OWID_WRL", None),
        "world total excl us": CountryInfo("World", "OWID_WRL", None),
        "world": CountryInfo("World", "OWID_WRL", None),
        "other": CountryInfo("Other", None, None),
    }
    lookup.update({key(alias): info for alias, info in manual.items()})
    return lookup


def load_country_points() -> dict[str, tuple[CountryInfo, object]]:
    world_path = RAW / "G Natural Earth" / "ne_110m_admin_0_sovereignty.shp"
    world = gpd.read_file(world_path).to_crs("EPSG:4326")
    points: dict[str, tuple[CountryInfo, object]] = {}

    def register(alias: object, row: pd.Series) -> None:
        alias_key = key(alias)
        if not alias_key:
            return
        iso3 = clean_text(row.get("ISO_A3_EH")) or clean_text(row.get("ISO_A3"))
        if iso3 == "-99":
            iso3 = clean_text(row.get("ADM0_A3_US")) or clean_text(row.get("ADM0_A3"))
        info = CountryInfo(
            country=clean_text(row.get("ADMIN")) or clean_text(row.get("NAME")),
            iso3=iso3,
            continent=clean_text(row.get("CONTINENT")),
        )
        points.setdefault(alias_key, (info, row.geometry.representative_point()))

    alias_columns = [
        "NAME",
        "NAME_LONG",
        "ADMIN",
        "SOVEREIGNT",
        "BRK_NAME",
        "NAME_SORT",
        "FORMAL_EN",
    ]
    for _, row in world.iterrows():
        for col in alias_columns:
            register(row.get(col), row)

    manual_aliases = {
        "united states": "united states of america",
        "usa": "united states of america",
        "drc": "democratic republic of the congo",
        "congo kinshasa": "democratic republic of the congo",
        "congo democratic republic": "democratic republic of the congo",
        "democratic republic of congo": "democratic republic of the congo",
        "burma": "myanmar",
    }
    for alias, canonical in manual_aliases.items():
        if key(canonical) in points:
            points[key(alias)] = points[key(canonical)]

    return points


def country_info(country: object, lookup: dict[str, CountryInfo]) -> CountryInfo:
    text = clean_text(country)
    if not text:
        return CountryInfo(None, None, None)
    return lookup.get(key(text), CountryInfo(text, None, None))


def country_group(info: CountryInfo) -> str | None:
    if info.iso3 == "CHN":
        return "China"
    if info.iso3 == "USA":
        return "United States"
    if info.iso3 in EU27_ISO3:
        return "EU-27"
    if info.country == "World":
        return "World"
    if info.country == "Other":
        return "Other"
    return "Other countries" if info.country else None


def regional_group(info: CountryInfo) -> str | None:
    if info.iso3 in NORDIC_ISO3:
        return "Nordics"
    if info.iso3 in EU27_ISO3:
        return "EU-27 non-Nordic"
    return None


def group_from_values(iso3: object, country: object) -> str | None:
    return country_group(CountryInfo(clean_text(country), clean_text(iso3), None))


def region_from_values(iso3: object, country: object) -> str | None:
    return regional_group(CountryInfo(clean_text(country), clean_text(iso3), None))


def map_source_mineral(source_mineral: object) -> list[str]:
    text = clean_text(source_mineral)
    if not text:
        return []
    lower = text.lower()

    direct = {
        "copper": ["Copper"],
        "lithium": ["Lithium"],
        "graphite": ["Graphite"],
        "cobalt": ["Cobalt"],
        "gallium": ["Gallium"],
        "platinum": ["Platinum"],
        "platinum group metals (platinum)": ["Platinum"],
        "platinum-group metals": ["Platinum"],
        "platinum-group elements": ["Platinum"],
        "rare earths": ["Neodymium", "Dysprosium", "Terbium", "Rare Earths"],
        "rare-earth elements": ["Neodymium", "Dysprosium", "Terbium", "Rare Earths"],
        "rare earth elements": ["Neodymium", "Dysprosium", "Terbium", "Rare Earths"],
        "neodymium oxide 99.5%": ["Neodymium"],
        "dysprosium oxide 99.5%": ["Dysprosium"],
        "terbium oxide 99.99%": ["Terbium"],
        "terbium": ["Terbium"],
    }
    if lower in direct:
        return direct[lower]

    targets: list[str] = []
    parts = [part.strip() for part in lower.replace("/", ";").split(";")]
    for part in parts:
        if "rare-earth" in part or "rare earth" in part or part == "ree":
            targets.extend(["Neodymium", "Dysprosium", "Terbium", "Rare Earths"])
        elif "terbium" in part:
            targets.append("Terbium")
        elif "platinum" in part:
            targets.append("Platinum")
        else:
            for target in TARGET_MINERALS:
                if target.lower() in part:
                    targets.append(target)
    return sorted(set(targets), key=list(TARGET_MINERALS).index)


def mineral_fields(mineral: str) -> dict[str, str]:
    meta = TARGET_MINERALS[mineral]
    return {
        "mineral": mineral,
        "mineral_group": meta["mineral_group"],
        "case_group": meta["case_group"],
    }


def output_path(name: str) -> Path:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    return PROCESSED / name


def build_geo_master(country_lookup: dict[str, CountryInfo]) -> gpd.GeoDataFrame:
    records = []

    shapefiles = [
        RAW / "A USGS Critical Minerals GDB" / "PP1802_CritMin_pts.shp",
        RAW / "A USGS Critical Minerals GDB" / "PP1802_CritMin_polys.shp",
    ]
    for path in shapefiles:
        gdf = gpd.read_file(path).to_crs("EPSG:4326")
        for _, row in gdf.iterrows():
            targets = map_source_mineral(row.get("CRITICAL_M"))
            if not targets:
                continue
            info = country_info(row.get("LOCATION"), country_lookup)
            for mineral in targets:
                records.append(
                    {
                        **mineral_fields(mineral),
                        "source_mineral": clean_text(row.get("CRITICAL_M")),
                        "deposit_name": clean_text(row.get("DEPOSIT_NA")),
                        "deposit_type": clean_text(row.get("DEPOSIT_TY")),
                        "country": info.country,
                        "iso3": info.iso3,
                        "continent": info.continent,
                        "latitude": numeric(row.get("LATITUDE")),
                        "longitude": numeric(row.get("LONGITUDE")),
                        "location_detail": clean_text(row.get("LOC_DETAIL")),
                        "ree_subgroup": None,
                        # GDB has no activity-status field; treat all entries as known deposits
                        "deposit_status": "Deposit",
                        "production_status": None,
                        "commodities": None,
                        "ore_minerals": None,
                        "significant_minerals": None,
                        "host_lithology": None,
                        "source": "USGS Critical Minerals GDB",
                        "notes": None,
                        "geometry": row.geometry,
                    }
                )

    ree_path = RAW / "B USGS REE Occurrences GDB" / "Global_REE_occurrence_database.xlsx"
    ree = pd.read_excel(ree_path, sheet_name=0)
    ree_gdf = gpd.GeoDataFrame(
        ree,
        geometry=gpd.points_from_xy(ree["Longitude"], ree["Latitude"], crs="EPSG:4326"),
    )
    for _, row in ree_gdf.iterrows():
        info = country_info(row.get("Country"), country_lookup)
        hree_note = clean_text(row.get("HREE_Note"))
        lree_note = clean_text(row.get("LREE_Note"))
        if hree_note and lree_note:
            ree_subgroup = "mixed"
        elif hree_note:
            ree_subgroup = "HREE"
        elif lree_note:
            ree_subgroup = "LREE"
        else:
            ree_subgroup = None
        deposit_status = clean_text(row.get("Status"))
        production_status = clean_text(row.get("P_Status"))
        commodities = clean_text(row.get("Commods"))
        ore_minerals = clean_text(row.get("REE_Mins"))
        significant_minerals = clean_text(row.get("Sig_Mins"))
        host_lithology = clean_text(row.get("Host_Lith"))
        for mineral in ("Neodymium", "Dysprosium", "Terbium", "Rare Earths"):
            records.append(
                {
                    **mineral_fields(mineral),
                    "source_mineral": "Rare earth elements",
                    "deposit_name": clean_text(row.get("Name")),
                    "deposit_type": clean_text(row.get("Dep_Type")),
                    "country": info.country,
                    "iso3": info.iso3,
                    "continent": info.continent or clean_text(row.get("Region")),
                    "latitude": numeric(row.get("Latitude")),
                    "longitude": numeric(row.get("Longitude")),
                    "location_detail": clean_text(row.get("State_Prov")),
                    "ree_subgroup": ree_subgroup,
                    "deposit_status": deposit_status,
                    "production_status": production_status,
                    "commodities": commodities,
                    "ore_minerals": ore_minerals,
                    "significant_minerals": significant_minerals,
                    "host_lithology": host_lithology,
                    "source": "USGS Global REE Occurrence Database",
                    "notes": "REE occurrence proxy; not element-specific unless source notes identify mineralogy",
                    "geometry": row.geometry,
                }
            )

    # ── MRDS copper deposits ──────────────────────────────────────
    mrds_path = RAW / "H MRDS Copper" / "mrds_copper.csv"
    if mrds_path.exists():
        mrds = pd.read_csv(mrds_path, low_memory=False)
        # Keep only active producers and plants — past producers/prospects add 26k rows
        # and are not needed for the supply-chain narrative (Chile/Peru/DRC geography)
        mrds = mrds[mrds["dev_stat"].isin(["Producer", "Plant"])]
        for _, row in mrds.iterrows():
            dev_stat = clean_text(row.get("dev_stat")) or "Unknown"
            commod_parts = [
                clean_text(row.get("commod2")),
                clean_text(row.get("commod3")),
            ]
            commodities = "; ".join(p for p in commod_parts if p) or None
            oper = clean_text(row.get("oper_type"))
            dep_type = clean_text(row.get("dep_type"))
            if dep_type and oper and oper.lower() not in ("unknown", ""):
                dep_type = f"{dep_type} ({oper})"
            elif oper and oper.lower() not in ("unknown", ""):
                dep_type = oper
            lat = pd.to_numeric(row.get("latitude"), errors="coerce")
            lon = pd.to_numeric(row.get("longitude"), errors="coerce")
            if pd.isna(lat) or pd.isna(lon):
                continue
            country_raw = clean_text(row.get("country")) or ""
            info = country_info(country_raw, country_lookup)
            from shapely.geometry import Point
            records.append(
                {
                    **mineral_fields("Copper"),
                    "source_mineral": "copper",
                    "deposit_name": clean_text(row.get("site_name")),
                    "deposit_type": dep_type,
                    "country": info.country or country_raw or None,
                    "iso3": info.iso3,
                    "continent": info.continent,
                    "latitude": lat,
                    "longitude": lon,
                    "location_detail": clean_text(row.get("state")),
                    "ree_subgroup": None,
                    "deposit_status": dev_stat,
                    "production_status": dev_stat,
                    "commodities": commodities,
                    "ore_minerals": None,
                    "significant_minerals": None,
                    "host_lithology": clean_text(row.get("hrock_type")),
                    "source": "USGS MRDS",
                    "notes": None,
                    "geometry": Point(lon, lat),
                }
            )
    else:
        print("  [warn] MRDS copper CSV not found — run pipeline/ingest/fetch_mrds_copper.py first")

    present_minerals = {record["mineral"] for record in records}
    missing_minerals = set(TARGET_MINERALS) - present_minerals
    if missing_minerals:
        country_points = load_country_points()
        mcs_production_path = RAW / "D+ USGS MCS 2025" / "mcs2025_all_production.csv"
        mcs_prod = pd.read_csv(
            mcs_production_path,
            comment="#",
            header=None,
            names=[
                "source_mineral",
                "country",
                "production_2023",
                "production_2024e",
                "reserves",
                "unit",
            ],
        )
        for _, row in mcs_prod.iterrows():
            targets = [m for m in map_source_mineral(row["source_mineral"]) if m in missing_minerals]
            if not targets:
                continue
            country = clean_text(row["country"])
            if not country or "world" in country.lower() or country.lower() == "other":
                continue
            point_entry = country_points.get(key(country))
            if not point_entry:
                continue
            info, geometry = point_entry
            for mineral in targets:
                records.append(
                    {
                        **mineral_fields(mineral),
                        "source_mineral": clean_text(row.get("source_mineral")),
                        "deposit_name": f"{info.country} {mineral} production",
                        "deposit_type": "country production centroid",
                        "country": info.country,
                        "iso3": info.iso3,
                        "continent": info.continent,
                        "latitude": geometry.y,
                        "longitude": geometry.x,
                        "location_detail": None,
                        "ree_subgroup": None,
                        "deposit_status": "centroid",
                        "production_status": None,
                        "commodities": None,
                        "ore_minerals": None,
                        "significant_minerals": None,
                        "host_lithology": None,
                        "source": "USGS MCS 2025 production extraction",
                        "notes": (
                            "Country-level centroid fallback because no deposit-level "
                            "geometry was available for this target mineral"
                        ),
                        "geometry": geometry,
                    }
                )

    master = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    columns = [
        "mineral",
        "source_mineral",
        "mineral_group",
        "case_group",
        "deposit_name",
        "deposit_type",
        "country",
        "iso3",
        "continent",
        "latitude",
        "longitude",
        "location_detail",
        "ree_subgroup",
        "deposit_status",
        "production_status",
        "commodities",
        "ore_minerals",
        "significant_minerals",
        "host_lithology",
        "source",
        "notes",
        "geometry",
    ]
    return master[columns]


def append_metric(
    rows: list[dict[str, object]],
    *,
    mineral: str,
    source_mineral: str,
    country: str | None,
    iso3: str | None,
    continent: str | None,
    year: int | None,
    metric: str,
    category: str | None,
    value: object,
    unit: str,
    source: str,
    notes: str | None = None,
) -> None:
    number = numeric(value)
    if number is None or pd.isna(number):
        return
    rows.append(
        {
            **mineral_fields(mineral),
            "source_mineral": source_mineral,
            "country": country,
            "iso3": iso3,
            "continent": continent,
            "year": year,
            "metric": metric,
            "category": category,
            "value": float(number),
            "unit": unit,
            "source": source,
            "notes": notes,
        }
    )


def to_usd_per_tonne(value: object, unit: object) -> float | None:
    number = numeric(value)
    unit_text = (clean_text(unit) or "").lower()
    if number is None or pd.isna(number):
        return None
    if unit_text == "$/t":
        return float(number)
    if unit_text == "$/kg":
        return float(number) * KG_PER_TONNE
    if unit_text == "$/lb":
        return float(number) * LB_PER_TONNE
    if unit_text == "cents/lb":
        return float(number) * 0.01 * LB_PER_TONNE
    if unit_text == "$/troy oz":
        return float(number) * TROY_OZ_PER_TONNE
    return None


def tonnes(value: object, unit: object) -> float | None:
    number = numeric(value)
    if number is None or pd.isna(number):
        return None
    unit_text = (clean_text(unit) or "").lower()
    if unit_text == "kt":
        return float(number) * 1000
    if unit_text in {"t", "t li", "t reo", "metric tons", "metric tonnes"}:
        return float(number)
    return float(number)


def build_economic_master(country_lookup: dict[str, CountryInfo]) -> pd.DataFrame:
    rows: list[dict[str, object]] = []

    owid_path = RAW / "C OWID Mine Production" / "global-mine-production-minerals.csv"
    owid = pd.read_csv(owid_path)
    owid_value_col = "Global mine production of different minerals"
    for _, row in owid.iterrows():
        for mineral in map_source_mineral(row["Entity"]):
            append_metric(
                rows,
                mineral=mineral,
                source_mineral=clean_text(row["Entity"]) or mineral,
                country="World",
                iso3="OWID_WRL",
                continent=None,
                year=int(row["Year"]),
                metric="global_mine_production_tonnes",
                category=None,
                value=row[owid_value_col],
                unit="metric tonnes",
                source="Our World in Data global mine production",
                notes=None,
            )

    mcs_production_path = RAW / "D+ USGS MCS 2025" / "mcs2025_all_production.csv"
    mcs_prod = pd.read_csv(
        mcs_production_path,
        comment="#",
        header=None,
        names=[
            "source_mineral",
            "country",
            "production_2023",
            "production_2024e",
            "reserves",
            "unit",
        ],
    )
    mcs_prod = mcs_prod.dropna(how="all")
    for _, row in mcs_prod.iterrows():
        info = country_info(row["country"], country_lookup)
        for mineral in map_source_mineral(row["source_mineral"]):
            production_2023 = tonnes(row["production_2023"], row["unit"])
            production_2024 = tonnes(row["production_2024e"], row["unit"])
            reserves = tonnes(row["reserves"], row["unit"])
            append_metric(
                rows,
                mineral=mineral,
                source_mineral=clean_text(row["source_mineral"]) or mineral,
                country=info.country,
                iso3=info.iso3,
                continent=info.continent,
                year=2023,
                metric="mine_production_tonnes",
                category=None,
                value=production_2023,
                unit="metric tonnes",
                source="USGS MCS 2025 production extraction",
                notes=f"Original unit: {row['unit']}",
            )
            append_metric(
                rows,
                mineral=mineral,
                source_mineral=clean_text(row["source_mineral"]) or mineral,
                country=info.country,
                iso3=info.iso3,
                continent=info.continent,
                year=2024,
                metric="mine_production_tonnes_estimate",
                category=None,
                value=production_2024,
                unit="metric tonnes",
                source="USGS MCS 2025 production extraction",
                notes=f"Original unit: {row['unit']}; estimated value",
            )
            append_metric(
                rows,
                mineral=mineral,
                source_mineral=clean_text(row["source_mineral"]) or mineral,
                country=info.country,
                iso3=info.iso3,
                continent=info.continent,
                year=2024,
                metric="reserves_tonnes",
                category=None,
                value=reserves,
                unit="metric tonnes",
                source="USGS MCS 2025 production extraction",
                notes=f"Original unit: {row['unit']}",
            )

    price_workbooks = {
        "Cobalt": "ds140-cobalt-2021.xlsx",
        "Copper": "ds140-copper-2020.xlsx",
        "Gallium": "ds140-gallium-2021.xlsx",
        "Graphite": "ds140-graphite-2022.xlsx",
        "Lithium": "ds140-lithium-2021.xlsx",
        "Platinum": "ds140-platinum-2022.xlsx",
        "Rare earths": "ds140-rare-earths-2020.xlsx",
    }
    for source_mineral, filename in price_workbooks.items():
        path = RAW / "D USGS Historical Prices" / filename
        df = pd.read_excel(path, sheet_name=0, header=4)
        df.columns = [clean_text(col) or "" for col in df.columns]
        for _, row in df.iterrows():
            year_value = numeric(row.get("Year"))
            if year_value is None:
                continue
            year = int(year_value)
            for mineral in map_source_mineral(source_mineral):
                append_metric(
                    rows,
                    mineral=mineral,
                    source_mineral=source_mineral,
                    country="World",
                    iso3="OWID_WRL",
                    continent=None,
                    year=year,
                    metric="historical_price_usd_per_tonne",
                    category="unit_value",
                    value=row.get("Unit value ($/t)"),
                    unit="USD per metric tonne",
                    source="USGS historical mineral statistics",
                    notes=None,
                )
                append_metric(
                    rows,
                    mineral=mineral,
                    source_mineral=source_mineral,
                    country="World",
                    iso3="OWID_WRL",
                    continent=None,
                    year=year,
                    metric="historical_real_price_1998_usd_per_tonne",
                    category="unit_value_real_1998",
                    value=row.get("Unit value (98$/t)"),
                    unit="1998 USD per metric tonne",
                    source="USGS historical mineral statistics",
                    notes=None,
                )
                for col in [c for c in df.columns if c.lower().startswith("world")]:
                    append_metric(
                        rows,
                        mineral=mineral,
                        source_mineral=source_mineral,
                        country="World",
                        iso3="OWID_WRL",
                        continent=None,
                        year=year,
                        metric="world_production_tonnes",
                        category=col,
                        value=row.get(col),
                        unit="metric tonnes",
                        source="USGS historical mineral statistics",
                        notes="Original workbook column retained in category",
                    )

    _US_COL_CANDIDATES = {
        "production": ["production", "primary production"],
        "imports": ["imports"],
        "exports": ["exports"],
        "consumption": [
            "apparent consumption",
            "estimated consumption",
            "consumption",
            "reported consumption",
        ],
    }

    def _find_us_col(cols: list[str], metric_key: str) -> str | None:
        stripped = {c.strip().lower(): c for c in cols}
        for candidate in _US_COL_CANDIDATES[metric_key]:
            if candidate in stripped:
                return stripped[candidate]
        return None

    for source_mineral, filename in price_workbooks.items():
        path = RAW / "D USGS Historical Prices" / filename
        df = pd.read_excel(path, sheet_name=0, header=4)
        df.columns = [clean_text(col) or "" for col in df.columns]
        prod_col = _find_us_col(df.columns.tolist(), "production")
        imp_col = _find_us_col(df.columns.tolist(), "imports")
        exp_col = _find_us_col(df.columns.tolist(), "exports")
        cons_col = _find_us_col(df.columns.tolist(), "consumption")
        for _, row in df.iterrows():
            year_value = numeric(row.get("Year"))
            if year_value is None:
                continue
            year = int(year_value)
            imp = numeric(row.get(imp_col)) if imp_col else None
            exp = numeric(row.get(exp_col)) if exp_col else None
            prod = numeric(row.get(prod_col)) if prod_col else None
            cons = numeric(row.get(cons_col)) if cons_col else None
            minerals = map_source_mineral(source_mineral)
            for mineral in minerals:
                for metric, val in [
                    ("us_imports_tonnes", imp),
                    ("us_exports_tonnes", exp),
                    ("us_production_tonnes", prod),
                    ("us_consumption_tonnes", cons),
                ]:
                    append_metric(
                        rows,
                        mineral=mineral,
                        source_mineral=source_mineral,
                        country="United States of America",
                        iso3="USA",
                        continent="North America",
                        year=year,
                        metric=metric,
                        category=None,
                        value=val,
                        unit="metric tonnes",
                        source="USGS historical mineral statistics",
                        notes="US data; values in metric tonnes of content",
                    )
            if imp is not None and exp is not None and cons is not None and cons > 0:
                nir = (imp - exp) / cons * 100
                for mineral in minerals:
                    append_metric(
                        rows,
                        mineral=mineral,
                        source_mineral=source_mineral,
                        country="United States of America",
                        iso3="USA",
                        continent="North America",
                        year=year,
                        metric="us_net_import_reliance_pct",
                        category=None,
                        value=nir,
                        unit="percent",
                        source="USGS historical mineral statistics",
                        notes="Derived: (imports - exports) / apparent consumption × 100",
                    )

    mcs_prices_path = RAW / "D+ USGS MCS 2025" / "mcs2025_all_prices.csv"
    mcs_prices = pd.read_csv(mcs_prices_path, comment="#")
    mcs_prices = mcs_prices.dropna(subset=["mineral", "unit"])
    year_cols = [col for col in mcs_prices.columns if col[:4].isdigit()]
    for _, row in mcs_prices.iterrows():
        for mineral in map_source_mineral(row["mineral"]):
            for col in year_cols:
                year = int(col[:4])
                converted = to_usd_per_tonne(row[col], row["unit"])
                append_metric(
                    rows,
                    mineral=mineral,
                    source_mineral=clean_text(row["mineral"]) or mineral,
                    country="World",
                    iso3="OWID_WRL",
                    continent=None,
                    year=year,
                    metric="mcs_price_usd_per_tonne",
                    category=clean_text(row["price_type"]),
                    value=converted,
                    unit="USD per metric tonne",
                    source="USGS MCS 2025 price extraction",
                    notes=f"Converted from {row['unit']}",
                )

    end_uses_path = RAW / "D+ USGS MCS 2025" / "mcs2025_all_end_uses.csv"
    end_uses = pd.read_csv(end_uses_path, comment="#")
    for _, row in end_uses.iterrows():
        for mineral in map_source_mineral(row["mineral"]):
            append_metric(
                rows,
                mineral=mineral,
                source_mineral=clean_text(row["mineral"]) or mineral,
                country="World",
                iso3="OWID_WRL",
                continent=None,
                year=2025,
                metric="end_use_share_pct",
                category=clean_text(row["end_use"]),
                value=row["share_pct"],
                unit="percent",
                source=clean_text(row["source"]) or "USGS MCS 2025",
                notes=None,
            )

    columns = [
        "mineral",
        "source_mineral",
        "mineral_group",
        "case_group",
        "country",
        "iso3",
        "continent",
        "year",
        "metric",
        "category",
        "value",
        "unit",
        "source",
        "notes",
    ]
    master = pd.DataFrame(rows, columns=columns)
    return master.sort_values(["mineral", "metric", "country", "year", "category"])


def stage_from_source_page(source_page: object) -> str:
    text = (clean_text(source_page) or "").lower()
    if "fig2" in text or "process" in text:
        return "processing"
    return "mining"


def supply_rows_from_extraction(
    country_lookup: dict[str, CountryInfo],
) -> pd.DataFrame:
    path = RAW / "E USGS Fact Sheet Mining vs Processing" / "mining_vs_processing_extracted.csv"
    raw = pd.read_csv(path, comment="#")
    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        stage = stage_from_source_page(row.get("source_page"))
        share = row.get("processing_share_pct")
        if numeric(share) is None:
            share = row.get("mining_share_pct")
        info = country_info(row.get("country"), country_lookup)
        for mineral in map_source_mineral(row.get("mineral")):
            value = numeric(share)
            if value is None:
                continue
            rows.append(
                {
                    **mineral_fields(mineral),
                    "source_mineral": clean_text(row.get("mineral")),
                    "year": 2023,
                    "record_type": "stage_share",
                    "stage": stage,
                    "country": info.country,
                    "iso3": info.iso3,
                    "partner_country": None,
                    "partner_iso3": None,
                    "flow_direction": None,
                    "hs_code": None,
                    "value_usd": None,
                    "quantity_tonnes": None,
                    "share_pct": float(value),
                    "hhi": None,
                    "source": "USGS FS 2025/3038 extraction",
                    "notes": f"Source page: {row.get('source_page')}",
                    "source_priority": 2,
                }
            )
    return pd.DataFrame(rows)


def supply_rows_from_summary(country_lookup: dict[str, CountryInfo]) -> pd.DataFrame:
    path = PROCESSED / "mining_vs_processing.csv"
    if not path.exists():
        return pd.DataFrame()
    raw = pd.read_csv(path)
    rows: list[dict[str, object]] = []
    for _, row in raw.iterrows():
        info = country_info(row.get("country"), country_lookup)
        for mineral in map_source_mineral(row.get("mineral")):
            for stage, col in [
                ("mining", "mining_share_pct"),
                ("processing", "processing_share_pct"),
            ]:
                value = numeric(row.get(col))
                if value is None:
                    continue
                rows.append(
                    {
                        **mineral_fields(mineral),
                        "source_mineral": clean_text(row.get("mineral")),
                        "year": 2023,
                        "record_type": "stage_share",
                        "stage": stage,
                        "country": info.country,
                        "iso3": info.iso3,
                        "partner_country": None,
                        "partner_iso3": None,
                        "flow_direction": None,
                        "hs_code": None,
                        "value_usd": None,
                        "quantity_tonnes": None,
                        "share_pct": float(value),
                        "hhi": None,
                        "source": clean_text(row.get("source")) or "USGS FS 2025/3038 summary",
                        "notes": "Existing curated summary file",
                        "source_priority": 1,
                    }
                )
    return pd.DataFrame(rows)


def first_present(row: pd.Series, names: Iterable[str]) -> object:
    for name in names:
        if name in row.index:
            value = row.get(name)
            if value is not None and not pd.isna(value):
                return value
    return None


def normalize_hs_code(value: object) -> str | None:
    text = clean_text(value)
    if not text:
        return None
    if "." in text:
        text = text.split(".", 1)[0]
    return text.strip().zfill(6)


def comtrade_quantity_tonnes(row: pd.Series) -> float | None:
    net_weight = numeric(first_present(row, ["netWgt", "netWeight", "NetWgt"]))
    if net_weight is not None:
        return float(net_weight) / 1000
    gross_weight = numeric(first_present(row, ["grossWgt", "grossWeight", "GrossWgt"]))
    if gross_weight is not None:
        return float(gross_weight) / 1000

    qty = numeric(first_present(row, ["qty", "Qty"]))
    unit = clean_text(first_present(row, ["qtyUnitAbbr", "qtyUnitCode", "Qty Unit"]))
    if qty is None or unit is None:
        return None
    unit_lower = unit.lower()
    if unit_lower in {"kg", "kilogram", "kilograms"}:
        return float(qty) / 1000
    if unit_lower in {"t", "ton", "tons", "tonne", "tonnes", "metric ton", "metric tons"}:
        return float(qty)
    return None


def supply_rows_from_comtrade(country_lookup: dict[str, CountryInfo]) -> pd.DataFrame:
    raw_dir = RAW / "comtrade"
    if not raw_dir.exists():
        return pd.DataFrame()

    rows: list[dict[str, object]] = []
    for path in sorted(raw_dir.glob("*.csv")):
        if path.name == "manifest.csv":
            continue
        try:
            data = pd.read_csv(path)
        except EmptyDataError:
            continue
        if data.empty:
            continue
        for _, row in data.iterrows():
            hs_code = normalize_hs_code(
                first_present(row, ["cmdCode", "cmd_code", "commodityCode"])
            )
            if hs_code not in COMTRADE_HS_MINERALS:
                continue

            partner_code = clean_text(
                first_present(row, ["partnerCode", "partner_code", "ptCode"])
            )
            partner_name = clean_text(
                first_present(row, ["partnerDesc", "partner_desc", "partnerISO"])
            )
            if partner_code in {"0", "0.0"} or key(partner_name) == "world":
                continue

            reporter_name = clean_text(
                first_present(row, ["reporterDesc", "reporter_desc", "reporterISO"])
            )
            reporter = country_info(reporter_name, country_lookup)
            partner = country_info(partner_name, country_lookup)
            period = numeric(first_present(row, ["period", "Period", "refYear"]))
            value_usd = numeric(
                first_present(row, ["primaryValue", "primary_value", "TradeValue"])
            )
            if period is None or value_usd is None:
                continue

            flow_code = clean_text(first_present(row, ["flowCode", "flow_code"]))
            flow_desc = clean_text(first_present(row, ["flowDesc", "flow_desc"]))
            if flow_code == "X":
                flow_direction = "export"
                stage = "trade_export"
            elif flow_code == "M":
                flow_direction = "import"
                stage = "trade_import"
            else:
                flow_direction = (flow_desc or flow_code or "trade").lower()
                stage = f"trade_{flow_direction}"

            cmd_desc = clean_text(first_present(row, ["cmdDesc", "cmd_desc"]))
            quantity_tonnes = comtrade_quantity_tonnes(row)
            for mineral in COMTRADE_HS_MINERALS[hs_code]:
                rows.append(
                    {
                        **mineral_fields(mineral),
                        "source_mineral": cmd_desc or hs_code,
                        "year": int(period),
                        "record_type": "trade_flow",
                        "stage": stage,
                        "country": reporter.country,
                        "iso3": reporter.iso3,
                        "partner_country": partner.country,
                        "partner_iso3": partner.iso3,
                        "flow_direction": flow_direction,
                        "hs_code": hs_code,
                        "value_usd": float(value_usd),
                        "quantity_tonnes": quantity_tonnes,
                        "share_pct": None,
                        "hhi": None,
                        "source": "UN Comtrade",
                        "notes": (
                            f"Raw file: {path.name}; Comtrade data may lag 1-2 years"
                        ),
                        "source_priority": 4,
                    }
                )

    if not rows:
        return pd.DataFrame()

    trade = pd.DataFrame(rows)
    group_cols = ["mineral", "year", "stage", "country", "hs_code"]
    totals = trade.groupby(group_cols)["value_usd"].transform("sum")
    trade["share_pct"] = (trade["value_usd"] / totals * 100).where(totals > 0)

    hhi_rows = []
    for (mineral, year, stage, country, hs_code), group in trade.groupby(group_cols):
        shares = group["share_pct"].dropna().astype(float)
        if shares.empty:
            continue
        reporter = country_info(country, country_lookup)
        hhi_rows.append(
            {
                **mineral_fields(mineral),
                "source_mineral": f"HS {hs_code}",
                "year": year,
                "record_type": "hhi",
                "stage": stage,
                "country": reporter.country,
                "iso3": reporter.iso3,
                "partner_country": None,
                "partner_iso3": None,
                "flow_direction": stage.replace("trade_", ""),
                "hs_code": hs_code,
                "value_usd": None,
                "quantity_tonnes": None,
                "share_pct": None,
                "hhi": float((shares**2).sum()),
                "source": "Derived from UN Comtrade",
                "notes": "HHI over partner shares by reporter, year, flow, and HS code",
                "source_priority": 4,
            }
        )
    return pd.concat([trade, pd.DataFrame(hhi_rows)], ignore_index=True)


def add_other_and_hhi(stage_rows: pd.DataFrame) -> pd.DataFrame:
    if stage_rows.empty:
        return stage_rows

    sort_cols = ["mineral", "source_mineral", "year", "stage", "country", "source_priority"]
    deduped = (
        stage_rows.sort_values(sort_cols)
        .drop_duplicates(["mineral", "year", "stage", "country"], keep="first")
        .copy()
    )

    supplemental_rows = []
    hhi_rows = []
    group_cols = ["mineral", "year", "stage"]
    for (mineral, year, stage), group in deduped.groupby(group_cols, dropna=False):
        listed_share = group["share_pct"].fillna(0).sum()
        residual = max(0.0, 100.0 - listed_share)
        if residual > 0.01:
            supplemental_rows.append(
                {
                    **mineral_fields(mineral),
                    "source_mineral": "Computed residual",
                    "year": year,
                    "record_type": "stage_share",
                    "stage": stage,
                    "country": "Other",
                    "iso3": None,
                    "partner_country": None,
                    "partner_iso3": None,
                    "flow_direction": None,
                    "hs_code": None,
                    "value_usd": None,
                    "quantity_tonnes": None,
                    "share_pct": residual,
                    "hhi": None,
                    "source": "Derived",
                    "notes": "Residual share computed as 100 minus listed country shares",
                    "source_priority": 3,
                }
            )
        shares = list(group["share_pct"].dropna().astype(float))
        if residual > 0.01:
            shares.append(residual)
        hhi = sum(share**2 for share in shares)
        hhi_rows.append(
            {
                **mineral_fields(mineral),
                "source_mineral": "Computed from stage shares",
                "year": year,
                "record_type": "hhi",
                "stage": stage,
                "country": None,
                "iso3": None,
                "partner_country": None,
                "partner_iso3": None,
                "flow_direction": None,
                "hs_code": None,
                "value_usd": None,
                "quantity_tonnes": None,
                "share_pct": None,
                "hhi": hhi,
                "source": "Derived from USGS FS 2025/3038",
                "notes": "HHI uses listed shares plus residual Other share where needed",
                "source_priority": 3,
            }
        )

    combined = pd.concat(
        [deduped, pd.DataFrame(supplemental_rows), pd.DataFrame(hhi_rows)],
        ignore_index=True,
    )
    return combined


def build_supply_chain_master(country_lookup: dict[str, CountryInfo]) -> pd.DataFrame:
    extracted = supply_rows_from_extraction(country_lookup)
    summary = supply_rows_from_summary(country_lookup)
    stage_rows = pd.concat([summary, extracted], ignore_index=True)
    trade_rows = supply_rows_from_comtrade(country_lookup)
    master = pd.concat([add_other_and_hhi(stage_rows), trade_rows], ignore_index=True)
    master["country_group"] = master.apply(
        lambda row: group_from_values(row.get("iso3"), row.get("country")), axis=1
    )
    master["country_region"] = master.apply(
        lambda row: region_from_values(row.get("iso3"), row.get("country")), axis=1
    )
    master["partner_group"] = master.apply(
        lambda row: group_from_values(row.get("partner_iso3"), row.get("partner_country")),
        axis=1,
    )
    master["partner_region"] = master.apply(
        lambda row: region_from_values(row.get("partner_iso3"), row.get("partner_country")),
        axis=1,
    )
    columns = [
        "mineral",
        "source_mineral",
        "mineral_group",
        "case_group",
        "year",
        "record_type",
        "stage",
        "country",
        "iso3",
        "country_group",
        "country_region",
        "partner_country",
        "partner_iso3",
        "partner_group",
        "partner_region",
        "flow_direction",
        "hs_code",
        "value_usd",
        "quantity_tonnes",
        "share_pct",
        "hhi",
        "source",
        "notes",
    ]
    return master[columns].sort_values(
        ["mineral", "record_type", "stage", "country"], na_position="last"
    )


def validate_outputs(
    geo: gpd.GeoDataFrame, economic: pd.DataFrame, supply: pd.DataFrame
) -> None:
    missing = {
        "geo": set(TARGET_MINERALS) - set(geo["mineral"].dropna()),
        "economic": set(TARGET_MINERALS) - set(economic["mineral"].dropna()),
        "supply": set(TARGET_MINERALS) - set(supply["mineral"].dropna()),
    }
    failures = [name for name, minerals in missing.items() if minerals]
    if failures:
        detail = "; ".join(f"{name}: {sorted(minerals)}" for name, minerals in missing.items())
        raise ValueError(f"Missing target minerals in master outputs: {detail}")

    if geo.empty or economic.empty or supply.empty:
        raise ValueError("One or more master outputs are empty.")
    if geo.geometry.isna().any():
        raise ValueError("Geo master contains missing geometries.")
    if economic["value"].isna().any():
        raise ValueError("Economic master contains missing numeric values.")
    if (
        supply.query("record_type == 'stage_share'")["share_pct"]
        .dropna()
        .between(0, 100)
        .all()
        is False
    ):
        raise ValueError("Supply-chain stage shares must be between 0 and 100.")


def write_outputs(
    geo: gpd.GeoDataFrame, economic: pd.DataFrame, supply: pd.DataFrame
) -> None:
    geo.to_file(output_path("master_geo_deposits.geojson"), driver="GeoJSON")
    economic.to_csv(output_path("master_economic_timeseries.csv"), index=False)
    supply.to_csv(output_path("master_supply_chain_trade.csv"), index=False)


def summarize(name: str, df: pd.DataFrame) -> str:
    return (
        f"{name}: {len(df):,} rows, "
        f"{df['mineral'].nunique()} minerals "
        f"({', '.join(sorted(df['mineral'].dropna().unique()))})"
    )


def build_all(write: bool = True) -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    country_lookup = load_country_lookup()
    geo = build_geo_master(country_lookup)
    economic = build_economic_master(country_lookup)
    supply = build_supply_chain_master(country_lookup)
    validate_outputs(geo, economic, supply)
    if write:
        write_outputs(geo, economic, supply)
    return geo, economic, supply


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build Critical Earth master datasets.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Build and validate in memory without writing output files.",
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    geo, economic, supply = build_all(write=not args.check)
    print(summarize("master_geo_deposits.geojson", geo))
    print(summarize("master_economic_timeseries.csv", economic))
    print(summarize("master_supply_chain_trade.csv", supply))
    if args.check:
        print("Validation passed without writing files.")
    else:
        print(f"Wrote master files to {PROCESSED.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
