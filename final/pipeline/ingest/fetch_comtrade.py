"""Fetch UN Comtrade trade-flow data for the Critical Earth project.

The script is intentionally idempotent: by default it skips CSVs that already
exist under data/raw/comtrade/.
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd
from pandas.errors import EmptyDataError


ROOT = Path(__file__).resolve().parents[2]
RAW_COMTRADE = ROOT / "data" / "raw" / "comtrade"
ENV_PATH = RAW_COMTRADE / ".env"

YEARS = ("2015", "2023")


@dataclass(frozen=True)
class ComtradeQuery:
    name: str
    reporter_code: str
    flow_code: str
    cmd_code: str
    description: str


ALL_TARGET_CODES = "253090,280530,284610,284690,850511,283691,810520,811292"
REE_CODES = "253090,280530,284610,284690"
CODE_GROUPS = (
    ("ree", REE_CODES),
    ("magnet", "850511"),
    ("lithium", "283691"),
    ("cobalt", "810520"),
    ("gallium", "811292"),
)
PUBLIC_PREVIEW_LIMIT = 500

EU27_REPORTERS = (
    ("austria", "40"),
    ("belgium", "56"),
    ("bulgaria", "100"),
    ("croatia", "191"),
    ("cyprus", "196"),
    ("czechia", "203"),
    ("denmark", "208"),
    ("estonia", "233"),
    ("finland", "246"),
    ("france", "251"),
    ("germany", "276"),
    ("greece", "300"),
    ("hungary", "348"),
    ("ireland", "372"),
    ("italy", "380"),
    ("latvia", "428"),
    ("lithuania", "440"),
    ("luxembourg", "442"),
    ("malta", "470"),
    ("netherlands", "528"),
    ("poland", "616"),
    ("portugal", "620"),
    ("romania", "642"),
    ("slovakia", "703"),
    ("slovenia", "705"),
    ("spain", "724"),
    ("sweden", "752"),
)

NORDIC_REPORTERS = (
    ("denmark", "208"),
    ("sweden", "752"),
    ("norway", "579"),
    ("finland", "246"),
    ("iceland", "352"),
    ("greenland", "304"),
    ("faroe_islands", "234"),
)

# Swing-states fetch: trace whether each "playing both sides" upstream
# country actually ships more to China or more to the Western alliance.
# Each reporter's exports are pulled across the original 8 HS codes
# (REE bundle + lithium + cobalt + gallium); split logic kicks in if a
# year exceeds the public preview limit.
SWING_STATE_REPORTERS = (
    ("australia", "36"),
    ("chile",     "152"),
    ("indonesia", "360"),
    ("india",     "699"),
    ("drc",       "180"),
)


CORE_QUERIES = (
    ComtradeQuery(
        name="china_ree_exports",
        reporter_code="156",
        flow_code="X",
        cmd_code="253090,280530,284610,284690",
        description="China rare-earth exports to all partners",
    ),
    ComtradeQuery(
        name="china_magnet_exports",
        reporter_code="156",
        flow_code="X",
        cmd_code="850511",
        description="China permanent magnet exports to all partners",
    ),
    ComtradeQuery(
        name="china_gallium_exports",
        reporter_code="156",
        flow_code="X",
        cmd_code="811292",
        description="China gallium exports to all partners",
    ),
    ComtradeQuery(
        name="usa_ree_imports",
        reporter_code="842",
        flow_code="M",
        cmd_code="253090,280530,284610,284690",
        description="United States rare-earth imports from all partners",
    ),
    ComtradeQuery(
        name="usa_lithium_imports",
        reporter_code="842",
        flow_code="M",
        cmd_code="283691",
        description="United States lithium carbonate imports from all partners",
    ),
    ComtradeQuery(
        name="usa_cobalt_imports",
        reporter_code="842",
        flow_code="M",
        cmd_code="810520",
        description="United States cobalt intermediate imports from all partners",
    ),
)

RECIPROCAL_QUERIES = (
    ComtradeQuery(
        name="china_all_imports",
        reporter_code="156",
        flow_code="M",
        cmd_code=ALL_TARGET_CODES,
        description="China imports of all selected HS codes from all partners",
    ),
    ComtradeQuery(
        name="usa_all_exports",
        reporter_code="842",
        flow_code="X",
        cmd_code=ALL_TARGET_CODES,
        description="United States exports of all selected HS codes to all partners",
    ),
)

EU_QUERIES = tuple(
    ComtradeQuery(
        name=f"eu27_{country}_{flow_name}",
        reporter_code=code,
        flow_code=flow_code,
        cmd_code=ALL_TARGET_CODES,
        description=f"EU-27 member {country} {flow_name.replace('_', ' ')} of all selected HS codes",
    )
    for country, code in EU27_REPORTERS
    for flow_name, flow_code in (("imports", "M"), ("exports", "X"))
)

NORDIC_QUERIES = tuple(
    ComtradeQuery(
        name=f"nordic_{country}_{flow_name}",
        reporter_code=code,
        flow_code=flow_code,
        cmd_code=ALL_TARGET_CODES,
        description=f"Nordic reporter {country} {flow_name.replace('_', ' ')} of all selected HS codes",
    )
    for country, code in NORDIC_REPORTERS
    for flow_name, flow_code in (("imports", "M"), ("exports", "X"))
)

# Swing-states queries — exports only (we want to see *who they sell to*,
# not what they buy). One query per (country, all-target-codes) per year.
SWING_STATE_QUERIES = tuple(
    ComtradeQuery(
        name=f"swing_{country}_exports",
        reporter_code=code,
        flow_code="X",
        cmd_code=ALL_TARGET_CODES,
        description=f"Swing-state reporter {country} exports of all selected HS codes",
    )
    for country, code in SWING_STATE_REPORTERS
)

BONUS_QUERIES = (
    ComtradeQuery(
        name="japan_ree_imports",
        reporter_code="392",
        flow_code="M",
        cmd_code="253090,280530,284610,284690",
        description="Japan rare-earth imports from all partners",
    ),
    ComtradeQuery(
        name="germany_ree_imports",
        reporter_code="276",
        flow_code="M",
        cmd_code="253090,280530,284610,284690",
        description="Germany rare-earth imports from all partners",
    ),
    ComtradeQuery(
        name="china_lithium_imports",
        reporter_code="156",
        flow_code="M",
        cmd_code="283691",
        description="China lithium carbonate imports from all partners",
    ),
)


# Coverage extension for Copper / Graphite / Platinum — China as reporter,
# both directions. Adds the three focal materials that were not in the
# original ALL_TARGET_CODES bundle. HS codes chosen for upstream (ore /
# unwrought) vs downstream (refined / semi-manufactured) flows.
EXTENDED_MATERIAL_QUERIES = (
    # Copper
    ComtradeQuery(
        name="china_copper_imports",
        reporter_code="156",
        flow_code="M",
        cmd_code="260300",
        description="China copper ore and concentrate imports (raw upstream)",
    ),
    ComtradeQuery(
        name="china_copper_exports",
        reporter_code="156",
        flow_code="X",
        cmd_code="740311",
        description="China refined copper cathode exports (downstream)",
    ),
    # Graphite
    ComtradeQuery(
        name="china_graphite_imports",
        reporter_code="156",
        flow_code="M",
        cmd_code="250410",
        description="China natural graphite (powder/flake) imports (raw upstream)",
    ),
    ComtradeQuery(
        name="china_graphite_exports",
        reporter_code="156",
        flow_code="X",
        cmd_code="380110",
        description="China artificial / battery-grade graphite exports (downstream)",
    ),
    # Platinum / PGM
    ComtradeQuery(
        name="china_platinum_imports",
        reporter_code="156",
        flow_code="M",
        cmd_code="711011",
        description="China platinum unwrought imports (upstream-refined)",
    ),
    ComtradeQuery(
        name="china_platinum_exports",
        reporter_code="156",
        flow_code="X",
        cmd_code="711019",
        description="China platinum semi-manufactured exports (downstream)",
    ),

    # ── Full-form coverage fetch, May 2026 ──────────────────────────
    # Materials almost never trade in a single form; this batch picks
    # up the load-bearing physical forms that the original fetches
    # missed so the supply-chain story isn't shaped by HS-code accident.

    # Copper — refined cathodes inbound (DRC/Zambia ship cathode, not
    # concentrate, to China); plus scrap and blister.
    ComtradeQuery(
        name="china_copper_cathode_imports",
        reporter_code="156", flow_code="M", cmd_code="740311",
        description="China refined copper cathode imports (HS 740311) — picks up DRC/Zambia/Chile cathode shipments",
    ),
    ComtradeQuery(
        name="china_copper_blister_imports",
        reporter_code="156", flow_code="M", cmd_code="740200",
        description="China unrefined / blister copper imports (HS 740200)",
    ),
    ComtradeQuery(
        name="china_copper_scrap_imports",
        reporter_code="156", flow_code="M", cmd_code="740400",
        description="China copper waste and scrap imports (HS 740400)",
    ),

    # Cobalt — battery-precursor chemistries (oxide + sulfate) that
    # the 810520 view does not see.
    ComtradeQuery(
        name="china_cobalt_oxide_imports",
        reporter_code="156", flow_code="M", cmd_code="282200",
        description="China cobalt oxides and hydroxides imports (HS 282200) — battery precursor",
    ),
    ComtradeQuery(
        name="china_cobalt_sulfate_imports",
        reporter_code="156", flow_code="M", cmd_code="283329",
        description="China cobalt sulfate imports (HS 283329) — cathode chemistry",
    ),

    # Lithium — hydroxide (the high-energy-density battery feedstock)
    # that the 283691 carbonate view misses.
    ComtradeQuery(
        name="china_lithium_hydroxide_imports",
        reporter_code="156", flow_code="M", cmd_code="282520",
        description="China lithium hydroxide imports (HS 282520) — high-energy battery feedstock",
    ),

    # Graphite — natural in 'other forms' (HS 250490) on top of the
    # flake/powder 250410 already fetched.
    ComtradeQuery(
        name="china_graphite_other_imports",
        reporter_code="156", flow_code="M", cmd_code="250490",
        description="China natural graphite, other forms imports (HS 250490)",
    ),

    # PGM beyond platinum — palladium (711021/29) is critical for
    # autocatalysts and electronics. Both directions for the dual view.
    ComtradeQuery(
        name="china_palladium_imports",
        reporter_code="156", flow_code="M", cmd_code="711021",
        description="China palladium unwrought imports (HS 711021)",
    ),
    ComtradeQuery(
        name="china_palladium_exports",
        reporter_code="156", flow_code="X", cmd_code="711029",
        description="China palladium semi-manufactured exports (HS 711029)",
    ),
)


def load_subscription_key(required: bool) -> str | None:
    env_key = os.environ.get("COMTRADE_KEY")
    if env_key:
        return env_key.strip()
    if not ENV_PATH.exists():
        if required:
            raise FileNotFoundError(
                "Missing Comtrade key. Create data/raw/comtrade/.env with "
                "COMTRADE_KEY=<your-key>, or set the COMTRADE_KEY environment variable."
            )
        return None
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        if name.strip() == "COMTRADE_KEY" and value.strip():
            return value.strip()
    if required:
        raise ValueError(f"No COMTRADE_KEY entry found in {ENV_PATH}")
    return None


def output_path(query: ComtradeQuery, year: str) -> Path:
    return RAW_COMTRADE / f"{query.name}_{year}.csv"


def csv_row_count(path: Path) -> int:
    try:
        return len(pd.read_csv(path))
    except EmptyDataError:
        return 0


def fetch_query(
    subscription_key: str | None,
    query: ComtradeQuery,
    year: str,
    *,
    max_records: int,
) -> pd.DataFrame:
    import comtradeapicall

    fetch = (
        comtradeapicall.getFinalData
        if subscription_key
        else comtradeapicall.previewFinalData
    )
    if subscription_key:
        return fetch(
            subscription_key,
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=year,
            reporterCode=query.reporter_code,
            cmdCode=query.cmd_code,
            flowCode=query.flow_code,
            partnerCode=None,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            maxRecords=max_records,
            format_output="JSON",
            aggregateBy=None,
            breakdownMode="classic",
            countOnly=None,
            includeDesc=True,
        )

    return fetch(
        typeCode="C",
        freqCode="A",
        clCode="HS",
        period=year,
        reporterCode=query.reporter_code,
        cmdCode=query.cmd_code,
        flowCode=query.flow_code,
        partnerCode=None,
        partner2Code=None,
        customsCode=None,
        motCode=None,
        maxRecords=max_records,
        format_output="JSON",
        aggregateBy=None,
        breakdownMode="classic",
        countOnly=None,
        includeDesc=True,
    )


def count_query(
    subscription_key: str | None,
    query: ComtradeQuery,
    year: str,
) -> int | None:
    import comtradeapicall

    if subscription_key:
        df = comtradeapicall.getCountFinalData(
            subscription_key,
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=year,
            reporterCode=query.reporter_code,
            cmdCode=query.cmd_code,
            flowCode=query.flow_code,
            partnerCode=None,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            aggregateBy=None,
            breakdownMode="classic",
        )
    else:
        df = comtradeapicall.previewCountFinalData(
            typeCode="C",
            freqCode="A",
            clCode="HS",
            period=year,
            reporterCode=query.reporter_code,
            cmdCode=query.cmd_code,
            flowCode=query.flow_code,
            partnerCode=None,
            partner2Code=None,
            customsCode=None,
            motCode=None,
            aggregateBy=None,
            breakdownMode="classic",
        )
    if df is None or df.empty or "count" not in df.columns:
        return None
    return int(df["count"].iloc[0])


def fetch_with_retry(
    subscription_key: str | None,
    query: ComtradeQuery,
    year: str,
    *,
    max_records: int,
    retries: int,
    retry_delay_seconds: float,
) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            df = fetch_query(
                subscription_key,
                query,
                year,
                max_records=max_records,
            )
            if df is None:
                raise RuntimeError(
                    "Comtrade returned no dataframe. This usually means the public "
                    "API quota is exhausted or the API returned an error response."
                )
            return df
        except Exception as exc:  # pragma: no cover - depends on remote API
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(retry_delay_seconds)
    assert last_error is not None
    raise last_error


def selected_queries(query_set: str, include_bonus: bool) -> tuple[ComtradeQuery, ...]:
    if query_set == "core":
        queries = CORE_QUERIES
    elif query_set == "reciprocal":
        queries = RECIPROCAL_QUERIES
    elif query_set == "eu27":
        queries = EU_QUERIES
    elif query_set == "nordics":
        queries = NORDIC_QUERIES
    elif query_set == "extended":
        queries = EXTENDED_MATERIAL_QUERIES
    elif query_set == "swing-states":
        queries = SWING_STATE_QUERIES
    elif query_set == "full-picture":
        queries = CORE_QUERIES + RECIPROCAL_QUERIES + EU_QUERIES + NORDIC_QUERIES + EXTENDED_MATERIAL_QUERIES + SWING_STATE_QUERIES
    else:
        raise ValueError(f"Unsupported query set: {query_set}")
    if include_bonus:
        queries = queries + BONUS_QUERIES
    return queries


def split_if_needed(
    subscription_key: str | None,
    query: ComtradeQuery,
    year: str,
    *,
    max_records: int,
) -> tuple[ComtradeQuery, ...]:
    if query.cmd_code != ALL_TARGET_CODES:
        return (query,)
    if subscription_key is not None:
        count = count_query(subscription_key, query, year)
        if count is None or count < min(max_records, PUBLIC_PREVIEW_LIMIT):
            return (query,)

    split_queries = []
    for suffix, cmd_code in CODE_GROUPS:
        split_queries.append(
            ComtradeQuery(
                name=f"{query.name}_{suffix}",
                reporter_code=query.reporter_code,
                flow_code=query.flow_code,
                cmd_code=cmd_code,
                description=f"{query.description}; split code group: {suffix}",
            )
        )
    return tuple(split_queries)


def split_queries_for(query: ComtradeQuery) -> tuple[ComtradeQuery, ...]:
    return tuple(
        ComtradeQuery(
            name=f"{query.name}_{suffix}",
            reporter_code=query.reporter_code,
            flow_code=query.flow_code,
            cmd_code=cmd_code,
            description=f"{query.description}; split code group: {suffix}",
        )
        for suffix, cmd_code in CODE_GROUPS
    )


def should_split_after_fetch(
    subscription_key: str | None,
    query: ComtradeQuery,
    *,
    row_count: int,
    max_records: int,
) -> bool:
    if subscription_key is not None:
        return False
    if query.cmd_code != ALL_TARGET_CODES:
        return False
    return row_count >= min(max_records, PUBLIC_PREVIEW_LIMIT)


def has_existing_split_files(query: ComtradeQuery, year: str) -> bool:
    if query.cmd_code != ALL_TARGET_CODES:
        return False
    return any(output_path(split_query, year).exists() for split_query in split_queries_for(query))


def all_known_queries() -> tuple[ComtradeQuery, ...]:
    base_queries = (
        CORE_QUERIES
        + RECIPROCAL_QUERIES
        + EU_QUERIES
        + NORDIC_QUERIES
        + BONUS_QUERIES
        + EXTENDED_MATERIAL_QUERIES
        + SWING_STATE_QUERIES
    )
    split_queries = tuple(
        split_query
        for query in base_queries
        if query.cmd_code == ALL_TARGET_CODES
        for split_query in split_queries_for(query)
    )
    return base_queries + split_queries


def manifest_row_for_file(
    path: Path,
    query_lookup: dict[str, ComtradeQuery],
) -> dict[str, object] | None:
    query_name, separator, year = path.stem.rpartition("_")
    if not separator or not year.isdigit():
        return None
    query = query_lookup.get(query_name)
    return {
        "file": path.name,
        "query_name": query_name,
        "year": year,
        "reporter_code": query.reporter_code if query else None,
        "flow_code": query.flow_code if query else None,
        "cmd_code": query.cmd_code if query else None,
        "description": query.description if query else None,
        "rows": csv_row_count(path),
    }


def write_manifest() -> None:
    query_lookup = {query.name: query for query in all_known_queries()}
    rows = []
    for path in sorted(RAW_COMTRADE.glob("*.csv")):
        if path.name == "manifest.csv":
            continue
        row = manifest_row_for_file(path, query_lookup)
        if row is not None:
            rows.append(row)
    if not rows:
        return
    manifest = pd.DataFrame(rows).sort_values(["query_name", "year"], kind="stable")
    manifest.to_csv(RAW_COMTRADE / "manifest.csv", index=False)


def run_fetch(
    *,
    years: Iterable[str],
    include_bonus: bool,
    force: bool,
    dry_run: bool,
    sleep_seconds: float,
    retries: int,
    retry_delay_seconds: float,
    max_records: int,
    mode: str,
    query_set: str,
    query_names: set[str] | None,
) -> None:
    RAW_COMTRADE.mkdir(parents=True, exist_ok=True)
    queries = selected_queries(query_set, include_bonus)
    if query_names:
        queries = tuple(query for query in queries if query.name in query_names)
        if not queries:
            raise ValueError(f"No queries matched --query-name: {', '.join(sorted(query_names))}")
    planned = [(query, str(year)) for query in queries for year in years]

    if dry_run:
        for query, year in planned:
            status = "exists" if output_path(query, year).exists() else "missing"
            print(f"{query.name}_{year}.csv [{status}] - {query.description}")
        return

    if mode == "full":
        subscription_key = load_subscription_key(required=True)
    elif mode == "auto":
        subscription_key = load_subscription_key(required=False)
    elif mode == "public":
        subscription_key = None
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    mode_label = "full keyed API" if subscription_key else "public preview API"
    print(f"Using {mode_label}.")
    expanded_planned: list[tuple[ComtradeQuery, str]] = list(planned)
    index = 0
    while index < len(expanded_planned):
        query, year = expanded_planned[index]
        path = output_path(query, year)
        fetched = False
        if has_existing_split_files(query, year) and not force:
            expanded_planned[index : index + 1] = [
                (split_query, year) for split_query in split_queries_for(query)
            ]
            continue
        if path.exists() and not force:
            print(f"Skipping existing {path.relative_to(ROOT)}")
            row_count = csv_row_count(path)
            if should_split_after_fetch(
                subscription_key,
                query,
                row_count=row_count,
                max_records=max_records,
            ):
                split_queries = [
                    (split_query, year)
                    for split_query in split_if_needed(
                        subscription_key,
                        query,
                        year,
                        max_records=max_records,
                    )
                ]
                if len(split_queries) > 1:
                    expanded_planned[index : index + 1] = split_queries
                    continue
        else:
            print(f"Fetching {query.name} for {year}...")
            df = fetch_with_retry(
                subscription_key,
                query,
                year,
                max_records=max_records,
                retries=retries,
                retry_delay_seconds=retry_delay_seconds,
            )
            row_count = len(df)
            if should_split_after_fetch(
                subscription_key,
                query,
                row_count=row_count,
                max_records=max_records,
            ):
                split_queries = [
                    (split_query, year)
                    for split_query in split_if_needed(
                        subscription_key,
                        query,
                        year,
                        max_records=max_records,
                    )
                ]
                if len(split_queries) > 1:
                    print(
                        f"Splitting {query.name} for {year} into "
                        f"{len(split_queries)} code-group queries to avoid preview truncation."
                    )
                    expanded_planned[index : index + 1] = split_queries
                    continue

            df.to_csv(path, index=False)
            fetched = True
            print(f"Wrote {path.relative_to(ROOT)} ({row_count:,} rows)")
        if fetched and index < len(expanded_planned) - 1 and sleep_seconds > 0:
            time.sleep(sleep_seconds)
        index += 1
    write_manifest()


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch Critical Earth Comtrade data.")
    parser.add_argument(
        "--years",
        default=None,
        help=(
            "Comma-separated years to fetch. If omitted, uses --start-year, "
            "--end-year, and --year-step; default range is 2015,2023."
        ),
    )
    parser.add_argument(
        "--start-year",
        type=int,
        default=None,
        help="First annual period to fetch when --years is omitted.",
    )
    parser.add_argument(
        "--end-year",
        type=int,
        default=None,
        help="Last annual period to fetch when --years is omitted.",
    )
    parser.add_argument(
        "--year-step",
        type=int,
        default=1,
        help="Year interval for ranged fetches. Use 3 for every third year.",
    )
    parser.add_argument(
        "--include-end-year",
        action="store_true",
        help="Append --end-year if it is not already included by --year-step.",
    )
    parser.add_argument(
        "--include-bonus",
        action="store_true",
        help="Also fetch Japan/Germany REE imports and China lithium imports.",
    )
    parser.add_argument(
        "--query-set",
        choices=("core", "reciprocal", "eu27", "nordics", "extended", "swing-states", "full-picture"),
        default="core",
        help=(
            "core = China exports + US imports; reciprocal = China imports + US exports; "
            "eu27 = EU member-state imports/exports; nordics = Nordic reporters "
            "including Greenland/Faroe Islands; full-picture = all of these."
        ),
    )
    parser.add_argument(
        "--query-name",
        action="append",
        default=None,
        help=(
            "Restrict to exact query name(s), such as nordic_finland_imports. "
            "Can be repeated or passed as comma-separated names."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refetch and overwrite existing raw Comtrade CSVs.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List planned API calls without requiring a key or fetching data.",
    )
    parser.add_argument(
        "--sleep-seconds",
        type=float,
        default=2.0,
        help="Delay between API calls to avoid throttling.",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="Number of retries after a failed API call.",
    )
    parser.add_argument(
        "--retry-delay-seconds",
        type=float,
        default=5.0,
        help="Delay before retrying a failed API call.",
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=500,
        help=(
            "Maximum records requested per API call. Public preview mode is capped "
            "by the API preview limit; use --mode full with a key for larger pulls."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("public", "auto", "full"),
        default="public",
        help=(
            "public = no-key preview API; auto = use COMTRADE_KEY if present, "
            "otherwise public; full = require COMTRADE_KEY and use keyed API."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> None:
    args = parse_args(argv)
    if args.years:
        years = [year.strip() for year in args.years.split(",") if year.strip()]
    elif args.start_year is not None or args.end_year is not None:
        if args.start_year is None or args.end_year is None:
            raise ValueError("--start-year and --end-year must be provided together.")
        if args.year_step < 1:
            raise ValueError("--year-step must be >= 1.")
        years = [str(year) for year in range(args.start_year, args.end_year + 1, args.year_step)]
        if args.include_end_year and str(args.end_year) not in years:
            years.append(str(args.end_year))
    else:
        years = list(YEARS)
    query_names = None
    if args.query_name:
        query_names = {
            name.strip()
            for item in args.query_name
            for name in item.split(",")
            if name.strip()
        }
    run_fetch(
        years=years,
        include_bonus=args.include_bonus,
        force=args.force,
        dry_run=args.dry_run,
        sleep_seconds=args.sleep_seconds,
        retries=args.retries,
        retry_delay_seconds=args.retry_delay_seconds,
        max_records=args.max_records,
        mode=args.mode,
        query_set=args.query_set,
        query_names=query_names,
    )


if __name__ == "__main__":
    main()
