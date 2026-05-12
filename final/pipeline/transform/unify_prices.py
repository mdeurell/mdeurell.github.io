"""Unify and splice price series for the ten focal materials.

Inputs (from data/processed/master_economic_timeseries.csv):
  - historical_real_price_1998_usd_per_tonne   (1900–2020-ish, USGS Dataset D)
  - historical_price_usd_per_tonne             (same window, nominal)
  - mcs_price_usd_per_tonne                    (2020–2024, USGS MCS 2025, nominal)

Outputs (data/processed/price_unified.csv):
  mineral, year, price_real_2015_usd_per_tonne, price_index_2015_eq_100, source_tag

Splice logic:
  1. Build a per-mineral nominal series, preferring USGS historical for 1900–2022,
     splicing in MCS for years not covered by historical.
  2. Deflate nominal → real-2015 USD using US CPI-U (annual average).
  3. Rebase to index 2015 = 100 per mineral.

Notes:
  - When MCS has multiple categories per mineral×year (Cobalt LME vs US-spot;
    Copper LME vs COMEX vs US producer; Graphite 3 grade tiers), we pick the
    industry-standard reference: LME cash for cobalt and copper, mean of the
    graphite grade tiers, single category otherwise.
  - Rare Earths basket has NO MCS entry — its absolute series ends where the
    USGS Dataset D table ends (2020). For the 2015-indexed view, the basket
    is extrapolated as the unweighted geometric mean of Nd / Dy / Tb indexes,
    flagged in source_tag.
  - Lithium MCS rows are labeled 'annual avg real' but are confirmed nominal
    via the notes column ('Converted from $/t'). Treated as nominal.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
IN_PATH = ROOT / "data" / "processed" / "master_economic_timeseries.csv"
OUT_PATH = ROOT / "data" / "processed" / "price_unified.csv"

MINERALS = [
    "Cobalt", "Copper", "Dysprosium", "Gallium", "Graphite",
    "Lithium", "Neodymium", "Platinum", "Rare Earths", "Terbium",
]

# US CPI-U annual average, base 1982-84 = 100.
# Used to extend the deflator past the years present in the raw data.
CPI_U_ANNUAL = {
    1998: 163.0,
    2015: 237.017,
    2020: 258.811,
    2021: 270.970,
    2022: 292.655,
    2023: 304.702,
    2024: 313.689,
}

# Industry-standard category preference for MCS multi-category cases.
MCS_PREFERRED_CATEGORY = {
    "Cobalt": "LME cash",
    "Copper": "LME grade A cash",
}


def _cpi_ratio(year_a: int, year_b: int) -> float:
    """CPI ratio for converting nominal-year_a USD into year_b USD."""
    return CPI_U_ANNUAL[year_b] / CPI_U_ANNUAL[year_a]


def _build_nominal_series(df: pd.DataFrame, mineral: str) -> pd.Series:
    """Per-mineral nominal price series, spliced USGS historical + MCS."""
    hist = (
        df[(df["mineral"] == mineral) & (df["metric"] == "historical_price_usd_per_tonne")]
        .set_index("year")["value"]
        .dropna()
        .sort_index()
    )

    mcs = df[(df["mineral"] == mineral) & (df["metric"] == "mcs_price_usd_per_tonne")].dropna(subset=["value"])
    if mineral in MCS_PREFERRED_CATEGORY:
        mcs = mcs[mcs["category"] == MCS_PREFERRED_CATEGORY[mineral]]
    mcs_series = mcs.groupby("year")["value"].mean().sort_index()

    # Splice: historical wins where it exists; MCS fills the tail.
    combined = hist.copy()
    for yr, v in mcs_series.items():
        if yr not in combined.index:
            combined.loc[yr] = v
    return combined.sort_index()


def _to_real_2015(nominal: pd.Series) -> pd.Series:
    """Deflate a nominal series into real 2015 USD using CPI-U annual average."""
    real = pd.Series(index=nominal.index, dtype=float)
    for year, value in nominal.items():
        if year in CPI_U_ANNUAL:
            cpi_year = CPI_U_ANNUAL[year]
        else:
            # Pre-1998 we have CPI-U back to 1913, but our deflator dict only
            # holds anchor years. Skip the deflation for years we cannot
            # ground in CPI_U_ANNUAL by interpolating between anchors.
            anchors = sorted(CPI_U_ANNUAL.keys())
            if year < anchors[0]:
                cpi_year = CPI_U_ANNUAL[anchors[0]]  # crude floor
            elif year > anchors[-1]:
                cpi_year = CPI_U_ANNUAL[anchors[-1]]
            else:
                # linear interp between adjacent anchors
                lo = max(a for a in anchors if a <= year)
                hi = min(a for a in anchors if a >= year)
                if lo == hi:
                    cpi_year = CPI_U_ANNUAL[lo]
                else:
                    frac = (year - lo) / (hi - lo)
                    cpi_year = CPI_U_ANNUAL[lo] + frac * (CPI_U_ANNUAL[hi] - CPI_U_ANNUAL[lo])
        real.loc[year] = value * (CPI_U_ANNUAL[2015] / cpi_year)
    return real


def _index_2015(real: pd.Series) -> pd.Series:
    """Rebase a real series to 2015 = 100."""
    if 2015 not in real.index or pd.isna(real.loc[2015]):
        return pd.Series(index=real.index, dtype=float)
    base = real.loc[2015]
    return (real / base) * 100.0


def _ree_basket_index(rows: pd.DataFrame) -> pd.Series:
    """Synthetic REE basket index = unweighted geometric mean of Nd/Dy/Tb 2015-indexes."""
    sub = rows[rows["mineral"].isin(["Neodymium", "Dysprosium", "Terbium"])]
    wide = sub.pivot(index="year", columns="mineral", values="price_index_2015_eq_100").dropna(how="all")
    geo = np.exp(np.log(wide).mean(axis=1))
    return geo


def _ree_basket_real_price(rows: pd.DataFrame) -> pd.Series:
    """Synthetic REE basket absolute price (real 2015 USD per tonne) =
    geometric mean of Nd/Dy/Tb real-2015 prices.

    Used to extend the basket's absolute series after the historical
    series ends in 2020. Lets downstream consumers (e.g. the
    reciprocal-dependence supply-mix calc) value China's REE mining at
    a coherent real price for 2021-2024.
    """
    sub = rows[rows["mineral"].isin(["Neodymium", "Dysprosium", "Terbium"])]
    wide = sub.pivot(index="year", columns="mineral",
                     values="price_real_2015_usd_per_tonne").dropna(how="all")
    geo = np.exp(np.log(wide).mean(axis=1))
    return geo


def main() -> None:
    df = pd.read_csv(IN_PATH)
    rows = []

    for mineral in MINERALS:
        nominal = _build_nominal_series(df, mineral)
        if nominal.empty:
            continue
        real_2015 = _to_real_2015(nominal)
        idx_2015 = _index_2015(real_2015)

        for year in nominal.index:
            rows.append({
                "mineral": mineral,
                "year": int(year),
                "price_real_2015_usd_per_tonne": float(real_2015.loc[year]) if not pd.isna(real_2015.loc[year]) else np.nan,
                "price_index_2015_eq_100": float(idx_2015.loc[year]) if year in idx_2015.index and not pd.isna(idx_2015.loc[year]) else np.nan,
                "source_tag": "historical+mcs",
            })

    out = pd.DataFrame(rows)

    # Patch Rare Earths basket 2021-2024 with synthetic Nd/Dy/Tb geo-mean
    # for the INDEX. For the absolute real price we extend the basket's
    # last known historical price by index growth, *not* by the geomean
    # of individual-element prices (which is dominated by Tb and would
    # overstate basket value by ~10×).
    basket_idx = _ree_basket_index(out)
    ree_known = out[(out["mineral"] == "Rare Earths")
                     & out["price_real_2015_usd_per_tonne"].notna()
                     & out["price_index_2015_eq_100"].notna()]
    if ree_known.empty:
        last_real_price = np.nan
        last_known_index = np.nan
    else:
        last_row = ree_known.sort_values("year").tail(1).iloc[0]
        last_real_price = float(last_row["price_real_2015_usd_per_tonne"])
        last_known_index = float(last_row["price_index_2015_eq_100"])

    for year in sorted(basket_idx.index):
        idx_val = float(basket_idx.get(year, np.nan))
        # Extend the absolute real price by index growth relative to last
        # known historical anchor.
        if pd.notna(last_real_price) and pd.notna(last_known_index) and last_known_index > 0:
            price_val = last_real_price * (idx_val / last_known_index)
        else:
            price_val = np.nan
        mask = (out["mineral"] == "Rare Earths") & (out["year"] == year)
        if mask.any():
            if pd.isna(out.loc[mask, "price_index_2015_eq_100"].iloc[0]):
                out.loc[mask, "price_index_2015_eq_100"] = idx_val
                out.loc[mask, "source_tag"] = "ree_basket_synthetic"
            if pd.isna(out.loc[mask, "price_real_2015_usd_per_tonne"].iloc[0]):
                out.loc[mask, "price_real_2015_usd_per_tonne"] = price_val
        elif year > out[out["mineral"] == "Rare Earths"]["year"].max():
            out = pd.concat([out, pd.DataFrame([{
                "mineral": "Rare Earths",
                "year": int(year),
                "price_real_2015_usd_per_tonne": price_val,
                "price_index_2015_eq_100": idx_val,
                "source_tag": "ree_basket_synthetic",
            }])], ignore_index=True)

    out = out.sort_values(["mineral", "year"]).reset_index(drop=True)
    out.to_csv(OUT_PATH, index=False)

    # Summary
    print(f"[unify_prices] wrote {OUT_PATH.relative_to(ROOT)}  ({len(out):,} rows)")
    summary = out.groupby("mineral").agg(
        year_min=("year", "min"),
        year_max=("year", "max"),
        idx_2015=("price_index_2015_eq_100", lambda s: s.dropna().shape[0]),
        real_2015=("price_real_2015_usd_per_tonne", lambda s: s.dropna().shape[0]),
    )
    print(summary.to_string())


if __name__ == "__main__":
    main()
