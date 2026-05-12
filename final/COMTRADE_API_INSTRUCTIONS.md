
## Dataset F: Comtrade Trade Flows — API Access

**DO NOT use the Comtrade web interface.** Use the `comtradeapicall` Python package instead.
The core project queries use the free public preview API and do not require a key.

### Setup

```bash
uv sync
```

The fetcher defaults to public/no-key mode:

```powershell
python pipeline\ingest\fetch_comtrade.py
```

Optional keyed mode is still supported for larger pulls:

```powershell
python pipeline\ingest\fetch_comtrade.py --mode full --max-records 250000
```

If using keyed mode, store the subscription key in `data/raw/comtrade/.env` as
`COMTRADE_KEY=...`.

### API Pattern

For the free public API, use `previewFinalData()`. It returns a pandas DataFrame
directly and is sufficient for the current partner-level annual queries. For
keyed full pulls, use `getFinalData()`.

```python
import comtradeapicall

df = comtradeapicall.previewFinalData(
    typeCode='C',           # C = Commodities (not services)
    freqCode='A',           # A = Annual
    clCode='HS',            # HS classification
    period='2023',          # Year (string). Multiple: '2015,2023'
    reporterCode='156',     # Reporter country code (156 = China)
    cmdCode='253090,280530,284610,284690',  # HS commodity codes
    flowCode='X',           # X = Export, M = Import
    partnerCode=None,       # None = all partners
    partner2Code=None,
    customsCode=None,
    motCode=None,
    maxRecords=500,
    format_output='JSON',
    aggregateBy=None,
    breakdownMode='classic',
    countOnly=None,
    includeDesc=True        # Include human-readable descriptions
)
```

Public release metadata can be checked without a key:

```text
https://comtradeapi.un.org/public/v1/getComtradeReleases
```

### Country Codes

| Country | Code | ISO3 |
|---------|------|------|
| China | 156 | CHN |
| United States | 842 | USA |
| Japan | 392 | JPN |
| Germany | 276 | DEU |
| South Korea | 410 | KOR |
| Australia | 36 | AUS |
| France | 251 | FRA |
| Netherlands | 528 | NLD |
| United Kingdom | 826 | GBR |
| India | 699 | IND |

Helper: `comtradeapicall.convertCountryIso3ToCode('CHN,USA,JPN')`

**EU note:** There is no single "EU-27" reporter code. Instead, query with
`reporterCode='156'` (China as exporter) and `partnerCode=None` (all partners),
then filter the result DataFrame for EU country names. Or query key EU importers
individually: Germany (276), France (251), Netherlands (528).

### HS Codes for Our Minerals

| HS Code | Description | Mineral |
|---------|-------------|---------|
| 253090 | Rare earth ores and concentrates | REE |
| 280530 | Rare earth metals, intermixtures/interalloys | REE |
| 284610 | Cerium compounds | REE |
| 284690 | Compounds of other rare earth metals | REE |
| 850511 | Permanent magnets, metal (contains NdFeB) | REE magnets |
| 283691 | Lithium carbonates | Lithium |
| 810520 | Cobalt mattes and intermediate products | Cobalt |
| 811292 | Gallium, unwrought | Gallium |

All REE codes combined: `'253090,280530,284610,284690'`
All codes combined: `'253090,280530,284610,284690,850511,283691,810520,811292'`

### Queries to Run

The research question is: "Is the supply chain splitting into two blocs?"
We need to compare trade patterns at two time points: **2015 vs 2023**.

**Core queries (6 total):**

```python
queries = [
    # China's REE exports — who does China sell to?
    ("china_ree_exports", "156", "X", "253090,280530,284610,284690"),
    # China's magnet exports
    ("china_magnet_exports", "156", "X", "850511"),
    # China's gallium exports (the 2023 export controls story)
    ("china_gallium_exports", "156", "X", "811292"),
    # US REE imports — where does the US source from?
    ("usa_ree_imports", "842", "M", "253090,280530,284610,284690"),
    # US lithium imports
    ("usa_lithium_imports", "842", "M", "283691"),
    # US cobalt imports
    ("usa_cobalt_imports", "842", "M", "810520"),
]

years = ["2015", "2023"]
```

Run each query for both years → 12 API calls total → 12 CSV files.

**Bonus queries (if time permits):**
- Japan REE imports (392, M) — Japan is the 2nd largest REE consumer
- Germany REE imports (276, M) — proxy for EU
- China lithium imports (156, M) — China imports lithium from Australia/Chile

### Rate Limits

- Public preview API: limited records per call and subject to fair use
- Add `time.sleep(2)` between API calls to avoid throttling
- If a call fails, retry once after 5 seconds
- Each of our queries returns ~50-200 rows (one per partner country), well
  within the public preview limit

### Expected Output Columns

The DataFrame will include:
- `reporterCode`, `reporterDesc` — who reported the trade
- `partnerCode`, `partnerDesc` — trading partner
- `cmdCode`, `cmdDesc` — HS commodity code and description
- `flowCode`, `flowDesc` — Export or Import
- `period` — year
- `primaryValue` — trade value in USD (this is what you use for Sankey widths)
- `netWgt` — net weight in kg
- `grossWgt` — gross weight in kg
- `qty`, `qtyUnitAbbr` — quantity and unit

### What to Look For (Bifurcation Analysis)

After downloading, calculate for each year:
1. China's top 10 REE export destinations by value
2. Share of China's REE exports going to US+EU+Japan vs ASEAN+Belt-and-Road
3. US import sources: share from China vs non-China (Australia, Canada, etc.)

Compare 2015 vs 2023. If bifurcation is happening:
- China→US share should be declining
- China→ASEAN share should be increasing
- US imports from non-China sources should be growing

### Script Location

Save output CSVs to `data/raw/comtrade/`.
The fetch script is `pipeline/ingest/fetch_comtrade.py`.
The script is idempotent — it checks if files exist before re-fetching.
