# Critical Earth

**DTU 02806 — Social Data Analysis & Visualization — Final Project**

> *"Is the global critical minerals supply chain splitting into two blocs?"*

A data-driven narrative website exploring rare earth elements, lithium, cobalt, gallium, and other critical minerals — who mines them, who refines them, and whether Western friend-shoring strategies are actually changing anything.

---

## Quick start — local preview

The website is a static site that mirrors what gets deployed to GitHub Pages.
A small Flask server serves it locally so all navigation and embedded visualizations work identically.

```bash
# Start the dev server (uv handles the venv automatically)
uv run python main.py
```

Open **http://localhost:5000** in your browser.

Flask's `debug=True` is on — the server auto-reloads when you edit files in `website/`.

**Options:**

```bash
uv run python main.py --port 8080        # use a different port
uv run python main.py --host 0.0.0.0    # expose on local network (mobile testing)
```

### Without uv

```bash
pip install -r requirements.txt
python main.py
```

---

## Editing content

`website/index.html` is **generated** from YAML files in `content/` plus
Jinja templates in `templates/`. Don't edit it by hand — your changes get
overwritten on the next build.

```bash
# Edit a YAML file in content/sections/, then:
python -m pipeline.build.build_index

# Or run watch mode while iterating:
python -m pipeline.build.build_index --watch
```

**Full authoring guide** — block types, YAML structure, how to add a section
or a new component — lives at **[`content/README.md`](content/README.md)**.

---

## Project structure

```
.
├── main.py                        # Flask dev server — run this to preview locally
├── requirements.txt               # pip dependencies
├── pyproject.toml                 # uv project config
│
├── content/                       # EDITABLE SOURCE — YAML per section
│   ├── README.md                  # Authoring guide (block types, YAML reference)
│   ├── site.yaml                  # Page metadata, hero, nav, section order
│   └── sections/                  # One YAML file per section
│       ├── 00_prologue.yaml
│       ├── 01_fine_tech.yaml
│       ├── 01_portfolio.yaml
│       ├── 02_deposits.yaml
│       ├── 03_attractive.yaml
│       ├── 04_processing.yaml
│       ├── 05_chapter_mark.yaml
│       ├── 05_economics.yaml
│       ├── 06_china_flow.yaml
│       └── 07_conclusion.yaml
│
├── templates/                     # Jinja templates — render YAML to HTML
│   ├── index.html.j2              # Outer page skeleton
│   └── blocks/                    # One partial per block type
│       ├── prose.html.j2
│       ├── figure.html.j2
│       ├── factbox.html.j2
│       └── …                       (13 block types total — see content/README.md)
│
├── website/                       # GENERATED — GitHub Pages deliverable
│   ├── index.html                 # ← built by pipeline/build/build_index.py
│   ├── css/
│   ├── js/
│   ├── images/
│   └── visualizations/            # Exported interactive HTML files
│       ├── stakes/                # price_index.html, end_uses.html, mineral_grid.html
│       ├── deposits/              # deposit_map.html
│       ├── supply-chain/          # slope_chart.html, production_series.html, sankey_cobalt.html
│       ├── attractive/            # Section 3: slope_mining_vs_processing, concentration_type2
│       ├── processing/            # Section 4: ree_value_cliff
│       ├── bifurcation/           # trade_flows_*, china_timeline, china_flow_*
│       └── conclusion/            # hhi_heatmap.html
│
├── pipeline/
│   ├── build/
│   │   ├── build_index.py             # Assembles website/index.html from content/ + templates/
│   │   ├── build_visualizations.py    # Builds Plotly chart HTMLs (Figs 5.1–6)
│   │   ├── build_attractive_charts.py # Builds Section 3+4 figures (Figs 3.1, 3.2, 4.1)
│   │   └── build_master_data.py       # Builds the three master datasets from raw sources
│   ├── ingest/
│   │   └── fetch_comtrade.py      # Downloads Comtrade trade flow CSVs
│   └── transform/
│       └── normalize_prices.py
│
├── data/
│   ├── raw/                       # Original source files — never edit these
│   └── processed/                 # Master datasets — single source of truth for all vizs
│       ├── master_geo_deposits.geojson       # 13,723 deposit features, 10 minerals
│       ├── master_economic_timeseries.csv    # 9,202 rows — prices, production, US dependency
│       └── master_supply_chain_trade.csv     # 704,034 rows — trade flows, stage shares, HHI
│
└── notebooks/
    ├── explainer_notebook.ipynb   # Academic deliverable
    └── exploration/               # Working notebooks
```

---

## Rebuilding the data pipeline

The master datasets in `data/processed/` are pre-built and committed. Only re-run if you change the pipeline or add raw data.

```bash
# Rebuild all three master datasets and write to data/processed/
python pipeline/build/build_master_data.py

# Dry-run: validate outputs without writing files
python pipeline/build/build_master_data.py --check

# Rebuild visualizations from master datasets
python pipeline/build/build_visualizations.py
```

---

## Master datasets — field reference

### `master_geo_deposits.geojson`
| Field | Description |
|-------|-------------|
| `mineral` | One of the 10 target minerals |
| `ree_subgroup` | `LREE` / `HREE` / `mixed` / null — REE occurrence DB classification |
| `deposit_status` | `Deposit` / `Occurrence` / `Showing` / `Producer` etc. |
| `country`, `iso3` | Country name and ISO-3 code |
| `deposit_name`, `deposit_type` | From USGS GDB or REE occurrence DB |

### `master_economic_timeseries.csv`
| `metric` value | Description |
|----------------|-------------|
| `historical_price_usd_per_tonne` | USGS nominal price 1900–2020 |
| `historical_real_price_1998_usd_per_tonne` | USGS real price (1998 USD) |
| `global_mine_production_tonnes` | World total from OWID |
| `mine_production_tonnes` | Per-country from USGS MCS 2025 |
| `us_imports_tonnes` | US annual imports (USGS Historical Stats) |
| `us_exports_tonnes` | US annual exports |
| `us_production_tonnes` | US domestic mine output |
| `us_consumption_tonnes` | US apparent/estimated consumption |
| `us_net_import_reliance_pct` | `(imports − exports) / consumption × 100` |
| `end_use_share_pct` | Share by application (MCS 2025) |
| `reserves_tonnes` | Country reserves (MCS 2025) |

### `master_supply_chain_trade.csv`
| `record_type` | Description |
|---------------|-------------|
| `trade_flow` | Bilateral Comtrade trade record |
| `stage_share` | Country share of mining or processing stage |
| `hhi` | Herfindahl–Hirschman Index per mineral × stage × year |

---

## Selected minerals (10)

| Mineral | Case | Key fact |
|---------|------|----------|
| Rare Earths (aggregate) | Overlay | 120-year USGS series; US net import reliance near 100% most of 2000s |
| Neodymium (LREE) | Case 1 | Abundant globally, refining captive to China (~90%) |
| Dysprosium (HREE) | Case 2 | China dominates both mining and refining (100%) |
| Terbium (HREE) | Case 2 | ~$810/kg (2024); China ~99%; used in same EV magnets as Dy |
| Lithium | Case 1 | Australia mines, China refines ~60% |
| Cobalt | Case 2 | DRC 70% mining, China 70% refining |
| Gallium | Case 2 | China ~98%; 2025 export controls |
| Copper | Case 1 | Chile/Peru mine, China processes ~44% |
| Graphite | Case 1 | China ~77% mining, ~100% spherical processing |
| Platinum | Case 2 | South Africa ~70% — not China-dominated |

The REE group spans the full Case 1→Case 2 spectrum within one mineral family,
making it the narrative spine of the project.

---

## Deployment

The site deploys automatically to GitHub Pages from the `website/` directory.
Push to `master` — no build step needed (it's pure static HTML/CSS/JS).
