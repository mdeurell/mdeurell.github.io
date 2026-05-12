"""Fetch USGS MRDS copper deposit data and save to data/raw/H MRDS Copper/.

Downloads the MRDS flattened CSV (~23 MB), filters to copper deposits with
valid coordinates, and writes a cleaned CSV ready for build_master_data.py.

Usage:
    python pipeline/ingest/fetch_mrds_copper.py

Output:
    data/raw/H MRDS Copper/mrds_copper.csv
"""

from __future__ import annotations

import io
import zipfile
from pathlib import Path

import pandas as pd
import requests

RAW_DIR = Path(__file__).parents[2] / "data" / "raw" / "H MRDS Copper"
OUT_CSV = RAW_DIR / "mrds_copper.csv"

MRDS_ZIP_URL = "https://mrdata.usgs.gov/mrds/mrds-csv.zip"

COPPER_TERMS = {"cu", "copper"}

KEEP_COLS = [
    "site_name",        # deposit / mine name
    "latitude",
    "longitude",
    "country",
    "state",
    "commod1",          # primary commodity
    "commod2",
    "commod3",
    "dep_type",         # deposit type
    "ore_ctrl",         # ore controls / host material
    "other_matl",       # other materials / co-occurring
    "prod_size",        # relative production size (large/medium/small)
    "dev_stat",         # development status
    "oper_type",        # operation type (open pit, underground, ...)
    "hrock_unit",       # host rock unit
    "hrock_type",       # host rock type
    "arock_unit",
    "arock_type",
    "mrds_id",          # unique identifier
    "url",
]


def _copper_row(row: pd.Series) -> bool:
    for col in ("commod1", "commod2", "commod3"):
        val = str(row.get(col, "")).lower().strip()
        if val in COPPER_TERMS or "copper" in val:
            return True
    return False


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Downloading MRDS CSV from {MRDS_ZIP_URL} ...")
    resp = requests.get(MRDS_ZIP_URL, timeout=120, stream=True)
    resp.raise_for_status()

    raw_bytes = b"".join(resp.iter_content(chunk_size=1 << 20))
    print(f"  Downloaded {len(raw_bytes) / 1e6:.1f} MB")

    with zipfile.ZipFile(io.BytesIO(raw_bytes)) as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        if not csv_names:
            raise RuntimeError(f"No CSV found in zip. Contents: {zf.namelist()}")
        csv_name = csv_names[0]
        print(f"  Reading {csv_name} ...")
        with zf.open(csv_name) as f:
            df = pd.read_csv(f, low_memory=False, encoding="utf-8", on_bad_lines="skip")

    print(f"  Total rows: {len(df):,}  columns: {list(df.columns[:10])} ...")

    # Normalise column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Filter to copper
    mask = df.apply(_copper_row, axis=1)
    copper = df[mask].copy()
    print(f"  Copper rows: {len(copper):,}")

    # Drop rows without coordinates
    for col in ("latitude", "longitude"):
        copper[col] = pd.to_numeric(copper[col], errors="coerce")
    copper = copper.dropna(subset=["latitude", "longitude"])
    copper = copper[
        copper["latitude"].between(-90, 90)
        & copper["longitude"].between(-180, 180)
    ]
    print(f"  With valid coords: {len(copper):,}")

    # Keep only useful columns (those that exist)
    available = [c for c in KEEP_COLS if c in copper.columns]
    copper = copper[available]

    copper.to_csv(OUT_CSV, index=False)
    print(f"Saved -> {OUT_CSV}  ({len(copper):,} rows, {OUT_CSV.stat().st_size / 1e3:.0f} kB)")


if __name__ == "__main__":
    main()
