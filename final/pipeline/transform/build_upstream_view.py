"""Unified China-trade-flow view across all ten focal materials.

Combines:
  - master_supply_chain_trade.csv (Cobalt, Lithium, Gallium, Rare Earths via
    pre-built HS bundle)
  - data/raw/comtrade/china_{copper,graphite,platinum}_{imports,exports}_*.csv
    (fetched May 2026 to extend coverage to Cu / Graphite / Pt)

Outputs:
  data/processed/china_trade_flows_all_materials.csv
    columns: mineral, year, flow_direction, partner_country, partner_iso3,
             value_usd, hs_code

  data/processed/upstream_top10_by_material.csv
    columns: mineral, partner_country, partner_iso3, value_usd, share_pct
    (cumulative 2015–2023 China imports per material, top 10)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_COMTRADE = ROOT / "data" / "raw" / "comtrade"
PROCESSED = ROOT / "data" / "processed"

OUT_ALL = PROCESSED / "china_trade_flows_all_materials.csv"
OUT_TOP10 = PROCESSED / "upstream_top10_by_material.csv"

# US CPI-U annual average — same anchor years and interpolation
# strategy as pipeline.transform.unify_prices. Used to deflate nominal
# Comtrade values into real 2015 USD so cross-year comparisons stay
# honest.
CPI_U_ANNUAL = {
    1998: 163.0,
    2000: 172.2,
    2005: 195.3,
    2010: 218.1,
    2015: 237.017,
    2020: 258.811,
    2021: 270.970,
    2022: 292.655,
    2023: 304.702,
    2024: 313.689,
}


def _cpi_for_year(year: int) -> float:
    if year in CPI_U_ANNUAL:
        return CPI_U_ANNUAL[year]
    anchors = sorted(CPI_U_ANNUAL.keys())
    if year < anchors[0]:
        return CPI_U_ANNUAL[anchors[0]]
    if year > anchors[-1]:
        return CPI_U_ANNUAL[anchors[-1]]
    lo = max(a for a in anchors if a <= year)
    hi = min(a for a in anchors if a >= year)
    if lo == hi:
        return CPI_U_ANNUAL[lo]
    frac = (year - lo) / (hi - lo)
    return CPI_U_ANNUAL[lo] + frac * (CPI_U_ANNUAL[hi] - CPI_U_ANNUAL[lo])


def _add_real_value(df: pd.DataFrame) -> pd.DataFrame:
    """Add `value_real_2015_usd` column = nominal × (CPI_2015 / CPI_year)."""
    cpi_2015 = CPI_U_ANNUAL[2015]
    df = df.copy()
    df["value_real_2015_usd"] = df.apply(
        lambda r: r["value_usd"] * (cpi_2015 / _cpi_for_year(int(r["year"])))
        if pd.notna(r["value_usd"]) and pd.notna(r["year"]) else None,
        axis=1,
    )
    return df


# Map raw-file prefix → (mineral, flow_direction, hs_form).
# `hs_form` is a short label describing the physical / processing stage of
# the traded good (e.g. "ore", "cathode", "sulfate"). It lets us preserve
# the multi-form view of each material in the combined CSV.
EXTENDED_FILES = {
    # Original May 2026 fetch — one principal upstream code per material.
    "china_copper_imports":            ("Copper",   "import", "concentrate"),
    "china_copper_exports":            ("Copper",   "export", "cathode"),
    "china_graphite_imports":          ("Graphite", "import", "natural_flake"),
    "china_graphite_exports":          ("Graphite", "export", "artificial"),
    "china_platinum_imports":          ("Platinum", "import", "unwrought"),
    "china_platinum_exports":          ("Platinum", "export", "semi_mfg"),
    # Full-form extension — fills the gaps surfaced by the HS audit.
    "china_copper_cathode_imports":    ("Copper",   "import", "cathode"),
    "china_copper_blister_imports":    ("Copper",   "import", "blister"),
    "china_copper_scrap_imports":      ("Copper",   "import", "scrap"),
    "china_cobalt_oxide_imports":      ("Cobalt",   "import", "oxide"),
    "china_cobalt_sulfate_imports":    ("Cobalt",   "import", "sulfate"),
    "china_lithium_hydroxide_imports": ("Lithium",  "import", "hydroxide"),
    "china_graphite_other_imports":    ("Graphite", "import", "natural_other"),
    "china_palladium_imports":         ("Palladium","import", "unwrought"),
    "china_palladium_exports":         ("Palladium","export", "semi_mfg"),
}


# Heuristic re-tag for HS 253090, "mineral substances n.e.s." — the
# catch-all heading that bundles REE ore, lithium spodumene, zirconium
# sand and other minor minerals. By partner-country production profile,
# the dominant material under 253090 differs sharply. This map covers
# the partners with a clear single-material story. Anything not listed
# stays tagged as 'Rare Earths' (the pipeline default).
HS253090_REASSIGN = {
    # Australia: Lynas Mt Weld ships REE concentrate, but the dominant
    # 253090 export tonnage is spodumene (lithium) from Greenbushes,
    # Pilgangoora and others.
    "Australia": "Lithium",
    # Zimbabwe: Bikita and Arcadia ship lithium feedstock under 253090.
    "Zimbabwe":  "Lithium",
    # Brazil: mixed; CBMM ships niobium under 261590, but 253090 from
    # Brazil into China is principally REE-bearing monazite. Stays REE.
    # Vietnam: REE under 253090. Stays REE.
    # Myanmar: heavy REE concentrate. Stays REE.
}


def _load_extended() -> pd.DataFrame:
    rows = []
    for prefix, (mineral, direction, hs_form) in EXTENDED_FILES.items():
        for path in sorted(RAW_COMTRADE.glob(f"{prefix}_*.csv")):
            year = int(path.stem.split("_")[-1])
            try:
                df = pd.read_csv(path)
            except pd.errors.EmptyDataError:
                continue
            if df.empty:
                continue
            # Drop the 'World' aggregate row (partnerCode == 0).
            df = df[df["partnerCode"] != 0]
            if df.empty:
                continue
            sub = pd.DataFrame({
                "mineral": mineral,
                "year": year,
                "flow_direction": direction,
                "partner_country": df["partnerDesc"],
                "partner_iso3": df.get("partnerISO", pd.Series([None] * len(df))),
                "value_usd": pd.to_numeric(df["primaryValue"], errors="coerce"),
                "quantity_tonnes": pd.to_numeric(df.get("netWgt", pd.Series([None] * len(df))), errors="coerce") / 1000.0,
                "hs_code": df.get("cmdCode", pd.Series([None] * len(df))),
                "hs_form": hs_form,
            })
            rows.append(sub)
    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def _load_existing() -> pd.DataFrame:
    """Pull the four already-covered minerals from master_supply_chain_trade."""
    src = PROCESSED / "master_supply_chain_trade.csv"
    df = pd.read_csv(src)
    df = df[df["record_type"] == "trade_flow"]
    df = df[df["country"] == "China"]

    # Collapse REE/Nd/Dy/Tb to single 'Rare Earths' (raw rows are duplicated).
    ree = {"Neodymium", "Dysprosium", "Terbium", "Rare Earths"}
    df.loc[df["mineral"].isin(ree), "mineral"] = "Rare Earths"
    df = df.drop_duplicates(
        subset=["mineral", "year", "flow_direction", "partner_country", "hs_code", "value_usd"]
    )

    # Re-tag HS 253090 by partner country. The catch-all heading carries
    # REE ore for most partners but spodumene (lithium) for Australia and
    # Zimbabwe. Without this, the upstream supplier map mis-credits the
    # Lynas concentrate flow and the Greenbushes / Pilgangoora flow to
    # rare earths instead of lithium.
    mask253090 = df["hs_code"] == 253090.0
    for partner, new_mineral in HS253090_REASSIGN.items():
        partner_mask = mask253090 & (df["partner_country"] == partner)
        df.loc[partner_mask, "mineral"] = new_mineral

    # Tag the HS form for the original 4 minerals so the combined CSV
    # carries the same column shape as the extended fetch.
    HS_FORM_MAP = {
        253090.0: "ore",       280530.0: "metal",     284610.0: "cerium_compounds",
        284690.0: "ree_compounds", 850511.0: "magnets",
        283691.0: "carbonate", 810520.0: "mattes",    811292.0: "unwrought",
    }
    df["hs_form"] = df["hs_code"].map(HS_FORM_MAP).fillna("unknown")

    keep = [
        "mineral", "year", "flow_direction", "partner_country",
        "partner_iso3", "value_usd", "quantity_tonnes", "hs_code", "hs_form",
    ]
    # Ensure both quantity columns exist
    if "quantity_tonnes" not in df.columns:
        df["quantity_tonnes"] = pd.NA
    return df[keep].copy()


def main() -> None:
    extended = _load_extended()
    existing = _load_existing()
    combined = pd.concat([existing, extended], ignore_index=True)
    combined = combined.dropna(subset=["value_usd"])
    combined = combined[combined["value_usd"] > 0]
    combined = combined.sort_values(["mineral", "year", "flow_direction", "value_usd"], ascending=[True, True, True, False])
    combined = _add_real_value(combined)
    combined.to_csv(OUT_ALL, index=False)
    print(f"[upstream] wrote {OUT_ALL.relative_to(ROOT)}  ({len(combined):,} rows)")

    # Upstream top-10 — China imports per material, cumulative 2015–2023
    imp = combined[(combined["flow_direction"] == "import") & combined["year"].between(2015, 2023)]
    grouped = (
        imp.groupby(["mineral", "partner_country", "partner_iso3"], dropna=False)["value_usd"]
        .sum().reset_index()
        .sort_values(["mineral", "value_usd"], ascending=[True, False])
    )
    # share %
    totals = grouped.groupby("mineral")["value_usd"].sum().rename("mineral_total")
    grouped = grouped.merge(totals, on="mineral")
    grouped["share_pct"] = grouped["value_usd"] / grouped["mineral_total"] * 100
    # take top 10 per mineral
    top10 = (
        grouped.sort_values(["mineral", "value_usd"], ascending=[True, False])
        .groupby("mineral", group_keys=False)
        .head(10)
        .reset_index(drop=True)
    )
    top10.to_csv(OUT_TOP10, index=False)
    print(f"[upstream] wrote {OUT_TOP10.relative_to(ROOT)}  ({len(top10):,} rows)")

    # Quick summary
    print()
    print("=== Top supplier per material (China imports 2015–2023) ===")
    print(
        top10.groupby("mineral").first()[["partner_country", "value_usd", "share_pct"]]
        .to_string()
    )


if __name__ == "__main__":
    main()
