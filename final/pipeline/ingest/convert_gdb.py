"""Convert USGS .gdb geodatabase to filtered GeoJSON for the 8 selected minerals."""

import geopandas as gpd
from pathlib import Path

RAW = Path("data/raw")
OUT = Path("data/processed")

TARGET_MINERALS = [
    "REE", "Rare earth", "Lithium", "Cobalt", "Graphite",
    "PGE", "Platinum", "Gallium", "Copper"
]

def convert_critical_minerals():
    """Convert the USGS PP1802 critical minerals geodatabase."""
    gdb_path = RAW / "usgs_critical_minerals.gdb"
    if not gdb_path.exists():
        print(f"ERROR: {gdb_path} not found. Download from:")
        print("https://www.sciencebase.gov/catalog/item/594d3c8ee4b062508e39b332")
        return

    print(f"Reading {gdb_path}...")
    gdf = gpd.read_file(gdb_path)
    print(f"  Total records: {len(gdf)}")
    print(f"  Columns: {list(gdf.columns)}")

    # Filter to target minerals (adjust column name after inspecting data)
    pattern = "|".join(TARGET_MINERALS)
    # Try common column names
    for col in ["commodity", "Commodity", "COMMODITY", "Mineral", "mineral"]:
        if col in gdf.columns:
            filtered = gdf[gdf[col].str.contains(pattern, case=False, na=False)]
            print(f"  Filtered on '{col}': {len(filtered)} records")
            break
    else:
        print("  WARNING: Could not find commodity column. Columns are:")
        print(f"  {list(gdf.columns)}")
        print("  Exporting full dataset — filter manually.")
        filtered = gdf

    out_path = OUT / "deposits.geojson"
    filtered.to_file(out_path, driver="GeoJSON")
    print(f"  Saved to {out_path}")

if __name__ == "__main__":
    convert_critical_minerals()
