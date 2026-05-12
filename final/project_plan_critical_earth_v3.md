# Critical Earth — Project Plan (v3 — Final)
## DTU 02806 Social Data Analysis & Visualization — Final Project

---

## 1. Research Question

**"Is the global critical minerals supply chain splitting into two blocs?"**

As the energy transition accelerates demand for rare earths, lithium, cobalt, and other
critical minerals, a single country — China — dominates processing for nearly all of them.
In response, the US, EU, and allied nations are pursuing "friend-shoring" strategies to
build alternative supply chains. But is this bifurcation actually happening in the trade
data, or is it still more aspiration than reality?

**Expected finding (honest and nuanced):** The data will likely show that bifurcation is
*beginning* — new Western mines, new trade agreements, declining US-China rare earth
trade share — but that China's structural dominance remains overwhelming. The world
*wants* to split but *can't yet*. This tension between political intention and industrial
reality is what makes the question interesting.

**How the research question drives every section:**

| Section | Role in answering the RQ |
|---------|--------------------------|
| 1. What are critical minerals? | Stakes: what's at risk if supply chains fracture |
| 2. Where they are (geology) | Possibility: deposits exist globally — diversification is geologically feasible |
| 3. Case 1: Abundant but captive | Barrier: processing concentration makes splitting structurally hard |
| 4. Case 2: Scarce and captured | Extreme: some minerals can't be decoupled from China at all today |
| 5. The trade map: Is it splitting? | **The answer:** Comtrade data comparison 2015 vs 2023 — partial bifurcation |
| 6. Conclusion | Synthesis: the split is beginning but incomplete |
| Bonus: Where does Europe stand? | Raised as a forward-looking reflection, not core to the analysis |

---

## 2. Scope: 10 Selected Critical Minerals

| Mineral | Case | Why critical | Top mining | Top processing | End use |
|---------|------|-------------|------------|----------------|---------|
| **Rare Earths** (aggregate) | Overlay | Historical & policy lens for the full REE group | China ~70%, Myanmar | China ~90% | All magnet + catalyst + phosphor applications |
| **Neodymium** (LREE) | Case 1 | Strongest permanent magnets | China, Myanmar, Australia | China (~90%) | EVs, wind turbines, F-35 |
| **Dysprosium** (HREE) | Case 2 | Heat-resistant magnet additive | China | China (100%) | EV motors, missile guidance |
| **Terbium** (HREE) | Case 2 | Magnets + green phosphors | China | China (~99%) | EV motors, LED lighting, sonar |
| **Lithium** | Case 1 | Battery chemistry backbone | Australia, Chile | China (~60%) | EV batteries, grid storage |
| **Cobalt** | Case 2 | Battery cathode stabilizer | DRC (~70%) | China (~70%) | Batteries, jet engines |
| **Gallium** | Case 2 | Semiconductor fabrication | China (~98%) | China (~98%) | Chips, 5G, radar |
| **Copper** | Case 1 | Electrification conductor | Chile, Peru, DRC | China (~44%) | Wiring, EVs, renewables |
| **Graphite** | Case 1 | Battery anode material | China (~77%) | China (~100%) | Batteries, nuclear |
| **Platinum** | Case 2 | Hydrogen fuel cells, catalysts | South Africa (~70%) | South Africa, UK | Catalytic converters, H₂ |

**Case 1 (Abundant but captive):** Copper, Lithium, Graphite, Neodymium — widely mined
but processing funnels through China. Bottleneck = industrial.

**Case 2 (Scarce and captured):** Dysprosium, Terbium, Cobalt, Gallium, Platinum — mining
itself is concentrated. Bottleneck = geological + industrial.

**The REE Overlay:** Rare earths are not just two minerals in the list — they are the
*spine of the story*. Within a single mineral family, the full Case 1→Case 2 spectrum
plays out: Neodymium (abundant globally, only refining is captive) sits at the Case 1 end;
Dysprosium and Terbium (China dominates even primary mining) sit at the Case 2 extreme.
The aggregate "Rare Earths" series provides the 120-year historical lens — the 2010
export crisis, the WTO ruling, the Mountain Pass boom-and-bust — that contextualises
the bifurcation question. Using LREE/HREE deposit classification from the USGS REE
occurrence database, the deposit map can also show *why* HREE concentration is not just
an industrial choice but a geological reality.

**US dependency lens (new):** For all 7 USGS-tracked minerals, Dataset D now provides
US-specific annual series: imports, exports, domestic production, consumption, and
derived net import reliance (NIR = (imports − exports) / consumption × 100). For REEs,
NIR runs near 100% for most of the 2000s, drops sharply when Mountain Pass reopens
post-2012, then climbs again as the Freeport mine shuttered. For Gallium and Graphite,
NIR is near 100% throughout — a clean quantitative statement about US vulnerability.

---

## 3. Data Sources — Verified Links

### DATASET A: Global Deposit Map
**USGS Global Distribution of Critical Minerals**
- **What:** Point locations of mines/deposits/districts for 22 critical minerals globally
- **Records:** ~2,000+ points with lat/lon, commodity type, deposit type, country
- **Format:** ESRI Geodatabase (.gdb)
- **Download:** https://www.sciencebase.gov/catalog/item/594d3c8ee4b062508e39b332
- **License:** Public domain (USGS)
- **Use:** The backbone "one global map" — filter to your 8 minerals, convert to GeoJSON

### DATASET B: Rare Earth Deep Dive
**USGS Global Rare Earth Element Occurrence Database**
- **What:** 3,100+ REE deposits with mineralogy, grade, tonnage, status
- **Format:** ESRI Geodatabase (.gdb)
- **Download:** https://www.sciencebase.gov/catalog/item/6193209ad34eb622f691aca7
- **License:** Public domain (USGS)
- **Use:** Deep dive on REE specifically — enables dot-size scaling by grade/tonnage

### DATASET C: Production by Country Over Time
**Our World in Data — Global Mine Production**
- **What:** Clean CSV of mine production by country × year × mineral, 88+ commodities
- **Source:** Pre-processed from USGS MCS + BGS World Mineral Statistics
- **Download:** https://ourworldindata.org/grapher/global-mine-production-minerals → Download tab
- **License:** CC-BY-4.0
- **Use:** Time series charts, China production share calculations

### DATASET D: Prices + End Uses
**USGS Historical Statistics for Mineral Commodities**
- **What:** ~90 mineral commodities with production, trade, consumption, and **unit value
  (nominal and real price in $/metric ton)** — many going back to 1900
- **Format:** Individual Excel worksheets per mineral
- **Download:** https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities
  (Click the letter index → download XLS per commodity)
- **License:** Public domain (USGS)
- **Use:** Normalized price index chart (all 8 minerals indexed to 100 at baseline year 2015)
- **End uses:** From USGS MCS 2-page data sheets (already in the CSV data releases at
  https://www.sciencebase.gov/catalog/item/6798f08bd34ea8c18376e7ec).
  Each mineral's sheet includes end-use distribution (e.g., rare earths: catalysts 25%,
  magnets 29%, metallurgy 18%, glass 8%). Visualize as treemap or stacked bar.

**Price data note:** USGS unit values cover rare earths as a group (1900–2020) plus
Terbium, Dysprosium, Neodymium, Cerium, and Lanthanum individually from USGS MCS 2025
(2020–2024). The aggregate series is sufficient for long-run price history. Individual
element prices from MCS 2025 let you show the HREE vs LREE price gap — Terbium at
~$810/kg in 2024 vs. Cerium at ~$1/kg.

**US dependency data (Dataset D, now extracted):** All 7 USGS Historical Stats files
now provide annual US-specific series: imports, exports, domestic production, apparent
consumption, and derived net import reliance (NIR). Use NIR to quantify US vulnerability
by mineral, and the production series to tell the Mountain Pass reopening story for REEs.

### DATASET E: Mining vs. Processing Shares
**USGS Fact Sheet: Global Maps of Critical Mineral Production 2023**
- **What:** Country shares of global mining AND processing — the key insight dataset
- **Format:** PDF (requires ~30 min manual extraction to CSV)
- **Download:** https://pubs.usgs.gov/fs/2025/3038/fs20253038.pdf
- **License:** Public domain (USGS)
- **Key data:** China's mining→processing gap: Cobalt 1%→80%, Copper 8%→44%,
  Aluminum 21%→59%, Tin 23%→50%, Titanium 34%→69%, REE ~70%→~90%

### DATASET F: Trade Flows (the bifurcation evidence)
**UN Comtrade — Bilateral Trade Data**
- **What:** Bilateral import/export by HS code × country pair × year
- **Access:** https://comtradeplus.un.org/TradeFlow (free account, ~250k records/query)
- **Backup:** https://wits.worldbank.org/ (friendlier bulk download)
- **License:** Free for academic use
- **HS codes:** 253090 (REE ores), 280530 (REE metals), 284610/284690 (REE compounds),
  850511 (permanent magnets), 283691 (lithium), 810520 (cobalt), 811292 (gallium)
- **Queries needed for the bifurcation analysis:**
  1. Reporter=China, Partner=All, HS=REE codes, Year=2015, Flow=Export
  2. Same but Year=2023 (or latest available)
  3. Reporter=EU-27, Partner=All, same HS, Years=2015+2023, Flow=Import
  4. Reporter=USA, Partner=All, same HS, Years=2015+2023, Flow=Import
  ~6–8 queries total, within the free tier.
- **Note:** Comtrade data lags 1–2 years. Your "after" snapshot may be 2022 or 2023.
  Supplement with news-sourced annotations for 2025 events.

### DATASET G: Base Map
**Natural Earth — Country Polygons**
- **Download:** https://www.naturalearthdata.com/downloads/110m-cultural-vectors/
  → "Admin 0 – Countries" at 110m resolution
- **License:** Public domain

---

## 4. Website Structure

### Section 0: Hero / Landing
- Dark map with glowing deposit dots (preview of Dataset A)
- Title: *"Critical Earth"*
- Subtitle: *"Is the world's mineral supply chain splitting in two?"*
- Scroll indicator

### Section 1: "What Powers the Modern World?"
**Role in RQ: Establish the stakes — what's at risk if supply chains fracture.**

- Brief intro (≤150 words): critical minerals are in your phone, your car, your power grid.
  Most people have never heard of neodymium — but without it, there are no EVs.
- **Viz 1 — Mineral overview grid (static):** 8 selected minerals, each cell showing: name,
  key end-use icon, top producer flag, Case 1 or Case 2 badge. Orients the reader.
- **Viz 2 — Normalized price index (Plotly, interactive):** All 8 minerals indexed to 100 at
  2015, plotted together on one chart. Hover for mineral name and price. Immediately shows:
  lithium's spike and crash, the 2010 REE spike, cobalt's rollercoaster, gallium's 2025 surge.
  Annotated with key events.
- **Viz 3 — End-use treemaps or stacked bars (static/Plotly):** For each mineral, what it's
  used for. Data from USGS MCS end-use tables. Shows the reader *why* each mineral matters.
  Can be small multiples — 8 mini treemaps in a grid.

### Section 2: "Where They Are" — The Geology
**Role in RQ: Diversification is geologically possible — deposits exist on every continent.**

- **Viz 4 — Interactive Folium map:** Global deposit locations from Dataset A + B.
  Toggle layers by mineral type. Color-code REE deposits by LREE (warm) vs HREE (cool)
  subgroup — this is now in the `ree_subgroup` field. Symbol or opacity by `deposit_status`
  (Deposit/Producer vs. Occurrence/Showing). Popups with deposit name and country.
- Key text: "The raw materials for the energy transition exist on every continent. The
  problem isn't geology — it's what happens after the ore leaves the ground."
- **REE callout:** "China holds ~35–40% of rare earth reserves — but for Heavy REEs
  (Dysprosium, Terbium), the geological concentration is genuinely more extreme. HREE
  deposits are fewer, smaller, and disproportionately located in southern China. This is
  not just industrial policy — it is mineralogy. The HREE map looks fundamentally
  different from the LREE map."
- This section plants the LREE/HREE distinction in the reader's mind before Cases 1 & 2
  make the strategic implications explicit.

### Section 3: "Case 1 — Abundant But Captive"
**Role in RQ: Processing concentration makes splitting structurally hard.**

- Focus: Copper, Lithium, Graphite, Neodymium
- **Viz 5 — Mining vs. Processing slope chart (Plotly):** Side-by-side comparison from
  Dataset E. Left column = mining share per country, right column = processing share.
  Lines connect each country across the two stages. The visual punchline: mining is
  distributed, but lines converge on China in the processing column.
- Narrative: Australian lithium gets shipped to Chinese refineries and returns as battery
  cells. Why? Decades of state investment, lower costs, lax environmental regulation.
  This is the structural lock-in that makes supply chain splitting so hard.
  **REE connection:** Neodymium here represents the LREE end of the spectrum — deposits
  exist on every continent (Mountain Pass, Bayan Obo, Lynas in Australia), but refining
  is still overwhelmingly Chinese. The deposit map LREE layer illustrates this directly.
- **Viz 6 — Production time series + US dependency (Plotly):** Growth over time for
  Case 1 minerals from Dataset C, showing the demand explosion. Overlay US net import
  reliance (NIR) series for Nd/REE: near-100% dependence, a brief dip when Mountain Pass
  reopened, then climbing back. Annotations for EV milestones and policy events.

### Section 4: "Case 2 — Scarce and Captured"
**Role in RQ: Some minerals can't be decoupled from China at all today.**

- Focus: Dysprosium, Terbium, Cobalt, Gallium, Platinum
- **Viz 7 — Sankey diagram (Plotly):** For cobalt: DRC mines → China refineries → battery
  manufacturers → consumer markets. Data from Datasets E + F.
- Narrative: DRC produces 70% of cobalt but captures almost none of the value. Gallium
  is the extreme case: 98% Chinese, and in 2025 China restricted exports. No alternative
  supply exists. Contrast with Platinum: South Africa's supply chain is already
  Western-aligned — showing that not all minerals are "China-captured."
  **REE connection:** Dysprosium and Terbium are the HREE extreme — China doesn't just
  refine them, it mines most of them too. HREE deposits outside China are rare (the
  deposit map HREE layer makes this visible). Even if the West built refining capacity,
  the ore would still come from China. NIR for Dy/Tb has been near 100% with almost
  no domestic US production ever recorded.
- This section's message for the RQ: for Case 2 minerals, bifurcation is essentially
  impossible in the near term. Any "Western" supply chain would still have critical gaps.

### Section 5: "Is It Splitting?" — The Trade Evidence
**Role in RQ: This is where you directly answer the research question.**

- **Viz 8 — Side-by-side trade flow maps (Plotly geo / Folium arcs):** Two panels.
  Left = 2015 rare earth trade flows. Right = 2023 trade flows. Arcs from exporters to
  importers, width proportional to trade value. Data from Dataset F.
  What to look for: Are arcs from China→US thinning? Are new arcs appearing
  (Australia→US, Canada→EU)? Is China→ASEAN thickening?
- **Viz 9 — China's share timeline (Plotly, annotated):** Two-panel or dual-axis chart.
  Top: China's share of global REE production 1990–2024 from Dataset C, annotated with
  geopolitical events. Bottom (or overlay): US net import reliance for REEs 1980–2020
  from the USGS Historical Stats series. This pairing tells the whole story in one view:
  as China's share of production climbed through the 1990s–2000s, US domestic production
  collapsed and import reliance hit 100%. The Mountain Pass reopening (2012–2015) shows
  as a brief dip. Recent years show the US trying — and still failing — to escape
  structural dependence.
  Annotated events:
  - 2010: China-Japan maritime dispute → REE export embargo → prices spike 10x
  - 2014: WTO rules against China's export quotas
  - 2017: Mountain Pass mine reopens under MP Materials
  - 2023: MP Materials suspends Chinese sales contract
  - 2025: China restricts REE + gallium + germanium exports
  - 2025: US launches "Project Vault" ($12B strategic stockpile)
  - 2025: EU selects 60 strategic mineral projects
- Narrative synthesis: "The answer is: partially. Trade patterns are beginning to shift.
  New mines in Australia, Canada, and Africa are coming online. Western governments
  are spending billions. But China still refines 90% of rare earths and 80% of cobalt.
  For Heavy REEs — the magnets inside every EV motor — there is no alternative supply
  chain, and the geology makes one hard to build. The world wants to split but the HREE
  bottleneck is the hardest wall to climb."

### Section 6: Conclusion
- **Viz 10 — HHI concentration heatmap (Plotly/matplotlib):** Minerals on y-axis, supply
  chain stages (Mining → Processing → End products) on x-axis, color = HHI concentration.
  One chart that summarizes the entire story. The message: the most concentrated stages
  are the most vulnerable to geopolitical disruption — and those are exactly where
  bifurcation is hardest.
- Brief synthesis (≤200 words): the energy transition is replacing oil dependency with
  mineral dependency, but the concentration is worse — one country instead of a cartel.
  The split has begun, but it will take decades to complete, if it ever does.

### Bonus Section: "Where Does This Leave Europe?"
**Standalone reflection — not part of the core research argument.**

- Raised as a forward-looking question after the main analysis is complete.
- Europe has almost no domestic mining, almost no processing capacity, and unlike the
  US, hasn't historically maintained strategic stockpiles. If the world splits, Europe
  risks being squeezed between both blocs.
- **Optional viz:** EU import dependency bar chart from Comtrade — what % of EU rare
  earth imports come from China vs. other sources, 2015 vs. 2023. Or: EU's 2030
  targets (10% domestic mining, 40% domestic processing, 25% recycling) vs. current
  position as a gap chart.
- **The Greenland hook:** Greenland has significant rare earth deposits (the Kvanefjeld
  project was halted in 2021 over environmental concerns). These deposits appear on your
  global map. Could Greenland be part of Europe's answer? A genuine connection between
  the global story and Denmark's own backyard — memorable for a DTU audience.
- This section is explicitly framed as: "Our research focused on global supply chain
  bifurcation. But the findings raise a question we leave for future work: where does
  Europe fit in a two-bloc world?"

---

## 5. Visualization Inventory

| # | Viz | Data | Tool | Type |
|---|-----|------|------|------|
| 1 | Mineral overview grid (10 minerals) | Manual | HTML/CSS or matplotlib | Static |
| 2 | Normalized price index | master_economic_timeseries (historical_price) | Plotly | Interactive |
| 3 | End-use treemaps | master_economic_timeseries (end_use_share_pct) | Plotly or matplotlib | Static / small multiples |
| 4 | Global deposit map with LREE/HREE layer | master_geo_deposits (ree_subgroup, deposit_status) | Folium + MarkerCluster | Interactive map |
| 5 | Mining vs. Processing slope chart | master_supply_chain_trade (stage_share) | Plotly | Interactive |
| 6 | Production + US NIR time series | master_economic_timeseries (OWID + us_net_import_reliance_pct) | Plotly | Interactive |
| 7 | Supply chain Sankey (cobalt) | master_supply_chain_trade (stage_share + trade_flow) | Plotly Sankey | Interactive |
| 8 | Trade flow comparison (2015 vs 2023) | master_supply_chain_trade (trade_flow, Comtrade) | Plotly geo or Folium | Interactive |
| 9 | China share + US dependency dual timeline | master_economic_timeseries (OWID + us_net_import_reliance_pct) | Plotly | Interactive |
| 10 | HHI concentration heatmap | master_supply_chain_trade (hhi) | Plotly heatmap | Static/hover |

**10 visualizations total.** ≥5 interactive Plotly, ≥1 Folium map, ≥2 static.
Exceeds course requirements. If time is short, Viz 3 (treemaps) and Viz 7 (Sankey)
are the first to simplify or cut.

All visualizations now read from the three master datasets in `data/processed/`:
- `master_geo_deposits.geojson` — 13,723 deposit features, 10 minerals
- `master_economic_timeseries.csv` — 9,202 rows, includes US dependency metrics
- `master_supply_chain_trade.csv` — 704,034 rows, trade flows + stage shares + HHI

---

## 6. Explainer Notebook Outline

### 1. Motivation
- Research question: "Is the global critical minerals supply chain splitting into two blocs?"
- Dataset descriptions: USGS geodata, USGS prices, OWID production, Comtrade trade flows
- Why now? 2025 China export controls, US Project Vault, EU CRM Act, energy transition
- Goal: test whether trade data shows emerging bifurcation

### 2. Basic Stats
- Dataset sizes: ~2,000+ deposit points, 8 mineral price series spanning 20+ years,
  bilateral trade flows for ~200 countries across 7 HS codes
- Cleaning: GDB→GeoJSON conversion, USGS price XLS standardization to common index,
  Comtrade HS code filtering, handling missing/estimated values
- Exploratory distributions: deposits per continent, production Lorenz curves, top-10
  producers, price volatility by mineral

### 3. Data Analysis
- HHI concentration index per mineral × supply chain stage
- Mining→processing gap quantification per country
- **Bifurcation analysis:** For each HS code, calculate China's export share to
  US/EU/Japan vs. ASEAN/Belt-and-Road partners at two time points. Test whether
  the ratio has shifted. Simple but defensible.
- Price event analysis: overlay geopolitical events on price series, test whether
  concentration predicts volatility
- Optional ML: k-means clustering of minerals by supply chain profile

### 4. Genre (Segel & Heer)
- Martini Glass: author-driven narrative → reader-driven interactive map
- Visual Narrative: consistent platform (map), annotations, stepper/scroll
- Narrative Structure: linear (intro → geology → Case 1 → Case 2 → trade → conclusion),
  messaging (annotated callouts), interactivity (mineral filter, hover, time comparison)

### 5. Visualizations
- Justify each of the 10 visualizations
- Why normalized price index as opener (immediate engagement, shows stakes)
- Why slope chart for mining/processing (the "aha" moment of the project)
- Why side-by-side trade flows for the RQ (direct visual answer to bifurcation)

### 6. Discussion
- What worked: USGS data excellent; mining→processing gap is a powerful visual;
  Comtrade comparison shows early signs of bifurcation
- Limitations: Comtrade lags 1–2 years (can't fully capture 2025 events); processing
  data manually compiled from PDFs; "bifurcation" is a spectrum, not binary;
  the project covers macro flows, not company-level supply chains
- Honest answer: "The world is *beginning* to split, but China's dominance is structural
  and built over 30 years. Replacing it will take at least a decade."

### 7. Contributions
- Per group member

---

## 7. Timeline

| Week | Milestone | Deliverable |
|------|-----------|-------------|
| 1 | Data acquisition | Download Datasets A–G. Convert GDB→GeoJSON. Load OWID CSV. Run initial Comtrade queries (2015 + 2023 for China/US/EU). Download USGS price XLS files for 8 minerals. Manually compile Dataset E CSV from PDF. |
| 1 | Project Assignment A | 1-minute video: research question, mock-up of map + slope chart, preliminary price index and production distributions |
| 2 | Core analysis | Normalized price index calculated. HHI per mineral × stage. Mining/processing CSV finalized. Comtrade bifurcation comparison (2015 vs 2023 export shares). |
| 2 | Website skeleton | GitHub Pages with section layout, navigation, placeholder text |
| 3 | Visualizations 1–6 | Mineral grid, price index, end-use treemaps, deposit map, slope chart, production series |
| 3 | Narrative writing | Sections 0–4 text drafted on website |
| 4 | Visualizations 7–10 | Sankey, trade flow comparison, annotated timeline, HHI heatmap |
| 4 | Bonus Europe section | EU import dependency chart or gap chart, Greenland callout |
| 4 | Polish & notebook | Explainer notebook, website refinement, mobile check, peer review |
| 4 | Submission | Upload link to DTU Learn |

---

## 8. Dataset Download Checklist

| # | Dataset | Priority | URL | Effort |
|---|---------|----------|-----|--------|
| A | USGS Critical Minerals GDB | Essential | https://www.sciencebase.gov/catalog/item/594d3c8ee4b062508e39b332 | Medium |
| B | USGS Global REE DB | Enrichment | https://www.sciencebase.gov/catalog/item/6193209ad34eb622f691aca7 | Medium |
| C | Our World in Data production CSV | Essential | https://ourworldindata.org/grapher/global-mine-production-minerals | None |
| D | USGS Historical Stats (prices) | Essential | https://www.usgs.gov/centers/national-minerals-information-center/historical-statistics-mineral-and-material-commodities | Low (8 XLS files) |
| D+ | USGS MCS 2025 CSVs (end uses) | Essential | https://www.sciencebase.gov/catalog/item/6798f08bd34ea8c18376e7ec | Low |
| E | USGS Fact Sheet (mining vs processing) | Essential | https://pubs.usgs.gov/fs/2025/3038/fs20253038.pdf | Low (30 min) |
| F | UN Comtrade (trade flows) | Essential | https://comtradeplus.un.org/TradeFlow | Medium |
| G | Natural Earth (base map) | Essential | https://www.naturalearthdata.com/downloads/110m-cultural-vectors/ | None |

---

## 9. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| USGS .gdb won't open | `geopandas` + `fiona` with GDAL. Fallback: older USGS REE shapefile (577 points) at mrdata.usgs.gov |
| Comtrade rate limits | Use WITS (wits.worldbank.org) as backup. Pre-download all queries in week 1. |
| Comtrade data lag (no 2024/2025) | Use 2022/2023 as "after" snapshot. Annotate 2025 events from news sources. |
| Processing data only in PDF | ~20 data points, 30 min manual work. Cross-check with IEA data explorer. |
| Bifurcation signal is weak in data | Frame as "beginning but incomplete" — the honest nuance is a strength, not a weakness. |
| Scope creep | Hard cap: 10 minerals, 10 visualizations. If short on time, cut Viz 3 (treemaps) and Viz 7 (Sankey) first. |
| Folium map slow with many points | Use MarkerCluster plugin. For REEs, default view shows only Deposit/Producer status; Occurrences loadable on demand. |
| Price data missing for individual REEs | Resolved: Terbium, Dysprosium, and Neodymium now have individual MCS2025 price series (2020–2024). Long-run aggregate from USGS 1900–2020. No external supplement needed. |
| US NIR extreme values (e.g. −482% for REE 2020) | Mountain Pass export surge — real data. Visualizations should note this and optionally clamp display range to [−100%, 150%] with an explanatory tooltip. |
