"""Build first-draft section visualizations from processed datasets only.

This script exports standalone HTML assets under website/visualizations/
for the first-draft narrative website and supporting explainer notebook.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import folium
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from branca.element import Element, Figure
from folium.plugins import Fullscreen, HeatMap, MarkerCluster
from plotly.subplots import make_subplots


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from website.theme import COUNTRY_COLORS, MINERAL_COLORS, RAW_CHALK, apply_theme, country_color, mineral_color


PROCESSED = ROOT / "data" / "processed"
VIS_ROOT = ROOT / "website" / "visualizations"

ECONOMIC_PATH = PROCESSED / "master_economic_timeseries.csv"
TRADE_PATH = PROCESSED / "master_supply_chain_trade.csv"
DEPOSITS_PATH = PROCESSED / "master_geo_deposits.geojson"

TARGET_MINERALS = [
    "Copper",
    "Lithium",
    "Graphite",
    "Neodymium",
    "Dysprosium",
    "Terbium",
    "Cobalt",
    "Gallium",
    "Platinum",
    "Rare Earths",
]
# REE minerals consolidated into one map group
REE_MINERALS = {"Neodymium", "Dysprosium", "Terbium"}
REE_COLOR = "#A07850"   # earthy ochre/sandstone

# Map filter groups (Case 1 & 2 use per-mineral colors; REE uses REE_COLOR)
CASE1_MAP_MINERALS = ["Lithium", "Copper", "Graphite"]   # abundant, deposits spread
CASE2_MAP_MINERALS = ["Cobalt", "Gallium", "Platinum"]   # scarce, deposits concentrated

# Display order in layer control
MAP_MINERAL_ORDER = ["Copper", "Lithium", "Graphite", "Cobalt", "Gallium", "Platinum"]

# For economic/trade charts (includes REE individuals)
CASE1_MINERALS = ["Copper", "Lithium", "Graphite", "Neodymium"]
CASE2_MINERALS = ["Dysprosium", "Terbium", "Cobalt", "Gallium", "Platinum"]

LANDMARK_MINES = [
    {
        "name": "Bayan Obo",
        "lat": 41.77, "lon": 109.97,
        "mineral": "Neodymium",
        "country": "China — Inner Mongolia",
        "operator": "China Northern Rare Earth Group (Baogang)",
        "status": "Active",
        "deposit_type": "Carbonatite-hosted iron-REE",
        "scale": "World's largest REE mine — historically >50% of global annual output",
        "specs": "~1,000 Mt ore  ·  ~6% REO grade  ·  ~70,000 t REO/yr",
        "note": (
            "The backbone of China's REE dominance. Scale is unmatched — "
            "the processing city built around it is why China controls ~90% of global refining. "
            "Also a major iron ore operation. Produces primarily light REE (La, Ce, Pr, Nd)."
        ),
    },
    {
        "name": "Mountain Pass",
        "lat": 35.48, "lon": -115.53,
        "mineral": "Neodymium",
        "country": "United States — California",
        "operator": "MP Materials",
        "status": "Active",
        "deposit_type": "Carbonatite",
        "scale": "Only operating REE mine in the United States",
        "specs": "~43 Mt reserves  ·  7.7% REO grade  ·  ~45,000 t REO/yr",
        "note": (
            "Supplied most of the Western world's REE through the 1980s, then closed 2002 "
            "when China undercut prices. Reopened 2017 under MP Materials. "
            "Still ships concentrate to China for separation — domestic processing capacity under construction."
        ),
    },
    {
        "name": "Mt Weld",
        "lat": -28.07, "lon": 122.27,
        "mineral": "Neodymium",
        "country": "Australia — Western Australia",
        "operator": "Lynas Rare Earths",
        "status": "Active",
        "deposit_type": "Carbonatite (supergene enriched)",
        "scale": "World's highest-grade REE deposit — 2-3x the concentration of Bayan Obo",
        "specs": "~18% REO grade  ·  ~3,900 t NdPr oxide/yr  (NdPr = neodymium-praseodymium, key magnet input)",
        "note": (
            "The main non-Chinese supplier of separated rare earth products to Western markets. "
            "Ore is shipped to Lynas' processing plant in Malaysia for separation. "
            "Critical to any Western supply chain diversification strategy."
        ),
    },
    {
        "name": "Nolans Bore",
        "lat": -22.03, "lon": 133.63,
        "mineral": "Neodymium",
        "country": "Australia — Northern Territory",
        "operator": "Arafura Resources",
        "status": "Development stage",
        "deposit_type": "Phosphate-REE apatite vein",
        "scale": "Largest undeveloped NdPr project in the Western development pipeline",
        "specs": "~30 Mt ore  ·  2.6% REO grade  ·  target ~4,440 t NdPr oxide/yr",
        "note": (
            "REE is hosted in apatite — a phosphate mineral — alongside uranium, requiring complex processing. "
            "Feasibility completed 2023, now in financing phase. If built, would add ~10% to non-Chinese NdPr supply."
        ),
    },
    {
        "name": "Kvanefjeld",
        "lat": 60.83, "lon": -46.03,
        "mineral": "Dysprosium",
        "country": "Greenland — Ilimaussaq complex",
        "operator": "Energy Transition Minerals (halted)",
        "status": "Blocked — mining license rejected 2021",
        "deposit_type": "Peralkaline igneous intrusion",
        "scale": "Largest undeveloped heavy REE deposit globally — currently inaccessible",
        "specs": "~1,000 Mt ore  ·  significant HREE, uranium, zinc",
        "note": (
            "Unusually high heavy REE content. License revoked 2021 by the Greenlandic government "
            "over opposition to uranium co-mining. "
            "Illustrates how environmental and political barriers can lock out otherwise large strategic deposits."
        ),
    },
    {
        "name": "Bou Azzer",
        "lat": 30.53, "lon": -6.57,
        "mineral": "Cobalt",
        "country": "Morocco — Anti-Atlas Mountains",
        "operator": "Managem Group",
        "status": "Active",
        "deposit_type": "Cobaltite-arsenide hydrothermal vein",
        "scale": "World's oldest continuously operating cobalt mine — one of very few primary cobalt deposits",
        "specs": "~1,500 t Co/yr  ·  operating since 1930s",
        "note": (
            "Most cobalt globally is a byproduct of copper or nickel. "
            "Bou Azzer is rare in producing cobalt as the primary product, "
            "giving Western buyers a supply option independent of DRC politics."
        ),
    },
    {
        "name": "Tenke Fungurume",
        "lat": -10.59, "lon": 26.07,
        "mineral": "Cobalt",
        "country": "DRC — Lualaba Province",
        "operator": "CMOC Group (China, acquired 2016)",
        "status": "Active",
        "deposit_type": "Stratiform copper-cobalt sedimentary (Copperbelt)",
        "scale": "World's single largest cobalt producer — ~15% of global annual supply",
        "specs": "~25,000 t Co/yr  ·  ~200,000 t Cu/yr",
        "note": (
            "Originally a Western-owned mine (Freeport-McMoRan + Lundin), sold to Chinese CMOC in 2016. "
            "CMOC doubled output 2022-23, flooding the cobalt market and suppressing prices. "
            "A focal point of the supply chain geopolitics story."
        ),
    },
    {
        "name": "Pilgangoora",
        "lat": -21.28, "lon": 118.70,
        "mineral": "Lithium",
        "country": "Australia — Pilbara, Western Australia",
        "operator": "Pilbara Minerals",
        "status": "Active",
        "deposit_type": "Spodumene pegmatite (hard rock)",
        "scale": "Australia's largest hard-rock lithium deposit",
        "specs": "~214 Mt ore  ·  1.12% Li2O grade  ·  ~680,000 t spodumene concentrate/yr",
        "note": (
            "Textbook Case 1 supply chain: Australia mines the ore, China refines it. "
            "Ore is crushed and shipped as concentrate to Chinese converters "
            "who process it into lithium hydroxide for battery cathodes."
        ),
    },
    {
        "name": "Atacama Salt Flat",
        "lat": -23.50, "lon": -67.80,
        "mineral": "Lithium",
        "country": "Chile — Atacama Desert",
        "operator": "SQM & Albemarle (Chile/US)",
        "status": "Active",
        "deposit_type": "Lithium brine (salar evaporite)",
        "scale": "World's largest lithium resource — ~30% of global lithium production",
        "specs": "~180,000 t LCE/yr combined  ·  lowest-cost lithium globally (~$3,000/t LCE)",
        "note": (
            "Lithium brine is pumped from underground aquifers and solar-evaporated over 12-18 months "
            "in vast ponds, then processed into lithium carbonate. "
            "Part of the Lithium Triangle (Chile, Argentina, Bolivia) holding ~60% of global lithium resources."
        ),
    },
]

# Geological occurrence type explainer lookup
# Keys are lowercase substrings to match against deposit_type field
DEPOSIT_TYPE_EXPLAINERS = [
    ("ion adsorption",
     "Clay deposit — REE atoms are loosely bound to clay minerals in tropical soils and flushed out with water; no hard rock mining needed."),
    ("carbonatite",
     "Igneous rock — a rare magma type rich in carbonate minerals that naturally concentrates REE; mined like any hard rock."),
    ("placer",
     "Sedimentary accumulation — heavy minerals washed by rivers or waves and deposited as beach or river sand; surface-mined."),
    ("pegmatite",
     "Coarse igneous rock — slowly cooled granite that concentrates lithium, REE and rare metals in large crystals; underground or open-pit mined."),
    ("skarn",
     "Contact metamorphic rock — forms where magma bakes limestone and concentrates metals such as Cu, Fe, REE at the contact zone."),
    ("phosphorite",
     "Marine sedimentary rock — REE substitute into phosphate minerals deposited on ancient seafloors; often recovered as a byproduct of fertiliser production."),
    ("laterite",
     "Tropical weathering profile — metals like Ni and Co concentrate near the surface as rainwater dissolves surrounding rock over millions of years."),
    ("vein",
     "Hydrothermal vein — hot fluids circulating through rock fractures deposit metals as they cool; mined as narrow underground seams."),
    ("alkaline",
     "Alkaline igneous intrusion — a silica-poor magmatic body that hosts unusual REE and Nb minerals not found in typical granite."),
    ("porphyry",
     "Porphyry — large low-grade deposit where copper is disseminated throughout a volcanic rock body; accounts for ~75% of world copper production."),
    ("brine",
     "Brine / salar — lithium dissolved in underground saltwater beneath salt flats, pumped to surface and solar-evaporated over months."),
    ("stratiform",
     "Sedimentary layer — ore minerals deposited in flat horizontal beds in ancient basins; the Central African Copperbelt is the world's largest example."),
    ("apatite",
     "Phosphate mineral — REE substitute into the crystal structure of apatite, a common phosphate rock; requires complex chemical separation."),
]
STAGE_ORDER = ["mining", "processing", "trade_export", "trade_import"]

# ── Carousel configuration ───────────────────────────────────────────────────
# Display order of minerals in the end-use carousel
CAROUSEL_MINERAL_ORDER = [
    "Lithium", "Gallium", "Cobalt", "Copper", "Platinum",
    "Neodymium", "Dysprosium", "Graphite", "Terbium", "Rare Earths",
]

# Image filenames relative to website/visualizations/images/
MINERAL_IMAGES: dict[str, str] = {
    "Lithium":     "Lithium-Metal-chemical-element-with-the-symbol-Li-atomic-number-3.jpg",
    "Gallium":     "Gallium-Metal-chemical-element-with-the-symbol-Ga-atomic-number-31.jpg",
    "Cobalt":      "cobalt.png",
    "Copper":      "Copper-Metal-chemical-element-with-the-symbol-Cu-atomic-number-29.jpg",
    "Platinum":    "platinum.jpg",
    "Neodymium":   "Neodymium-Metal-chemical-element-with-the-symbol-Nd-atomic-number-60.jpg",
    "Dysprosium":  "Dysprosium-Metal-chemical-element-with-the-symbol-Dy-atomic-number-66.jpg",
    "Graphite":    "Graphite-Soft.jpg",
    "Terbium":     "Terbium-Metal-chemical-element-with-the-symbol-Tb-atomic-number-65.jpg",
    "Rare Earths": "Rare_Earths.jpg",
}

# Expert detail content — drawn from material_descript.txt (Wikipedia-inspired)
MINERAL_DETAIL: dict[str, dict[str, str]] = {
    "Lithium": {
        "symbol":       "Li · Atomic no. 3 · Alkali metal",
        "science":      "The lightest of all metals and the least dense solid element — density just 0.534 g/cm³, so it floats on water. Soft enough to cut with a knife. Holds the highest specific heat capacity of all solids. Reacts directly with nitrogen at room temperature, forming a black nitride tarnish. Produces a characteristic bright crimson flame. Must be stored in petroleum jelly to prevent reaction with air and moisture.",
        "application":  "Over three-quarters of global production goes to Li-ion batteries (EVs, smartphones, laptops) thanks to its high electrochemical potential and low atomic mass. Also used in high-temperature lithium grease for aircraft engines, as a ceramic and glass flux improving thermal shock resistance, as lithium carbonate — a WHO Essential Medicine for bipolar disorder — and in nuclear technology where Li-6 produces tritium and Li-7 serves as a reactor coolant.",
        "source":       "Mined as hard-rock spodumene in Australia and pumped as lithium-rich brine from beneath the Atacama salt flats in Chile and Argentina (the &#39;Lithium Triangle&#39;). Extraction faces significant environmental scrutiny over water consumption in arid regions and potential groundwater contamination.",
        "price_story":  "Prices surged roughly 10× between 2020 and 2022 on EV demand, then crashed more than 70% by 2024 as a wave of new supply from Australia and South America outpaced the market.",
    },
    "Gallium": {
        "symbol":       "Ga · Atomic no. 31 · Post-transition metal",
        "science":      "Melting point of just 29.76 °C — it liquefies in the palm of a human hand. One of the few substances (like water) that expands when it solidifies, requiring specialised storage to prevent container rupture. Famous for liquid metal embrittlement: it diffuses into aluminium grain boundaries causing the metal to shatter like glass. Boiling point of 2,676 K gives it one of the widest liquid ranges of any element. Wets glass and porcelain, making it ideal for high-quality mirror coatings.",
        "application":  "Approximately 98% of gallium goes into semiconductors. Gallium arsenide (GaAs) powers high-frequency microwave circuits and mobile phone switching; Gallium nitride (GaN) is the critical material behind blue LEDs, Blu-ray laser diodes, and 5G power electronics. Gallium-67 and Gallium-68 serve as PET scan tracers to detect inflammation and tumours. Galinstan (gallium-indium-tin alloy) remains liquid to −19 °C as a non-toxic mercury replacement in thermometers.",
        "source":       "Has no independent mines — produced exclusively as a byproduct of aluminium (bauxite) and zinc processing, tying its entire supply to those industries. China produces approximately 98% of the world&#39;s low-purity gallium.",
        "price_story":  "China imposed gallium export controls in August 2023, triggering immediate price spikes and emergency stockpiling across the semiconductor industry. Supply concentration makes price behaviour highly reactive to policy decisions.",
    },
    "Cobalt": {
        "symbol":       "Co · Atomic no. 27 · Transition metal",
        "science":      "Hard, lustrous, silver-gray metal. Ferromagnetic with a Curie temperature of 1,115 °C — retaining magnetic properties at higher temperatures than iron or nickel. Cobalt(II) salts form a characteristic pink complex in solution that turns an intense deep blue when dehydrated or combined with chloride, a property used in humidity indicators. Uniquely, cobalt is the central atom of Vitamin B12 (cobalamin), making it an essential micronutrient for all animals.",
        "application":  "Dominant use is in lithium-ion battery cathodes (LiCoO₂), providing energy density and thermal stability. Cobalt-chrome-tungsten superalloys create turbine blades for jet engines capable of withstanding temperatures above 1,000 °C. Acts as a binder in tungsten carbide cutting tools. Cobalt blue remains a standard pigment in ceramics and glass. Essential catalyst for hydrodesulfurization — removing sulfur from crude oil to prevent acid rain. Also used in biocompatible medical implants (hip and knee replacements).",
        "source":       "Over 80% of world supply comes from the Democratic Republic of Congo, typically as a byproduct of copper mining. Widespread artisanal and small-scale mining raises persistent human rights and child labour concerns, driving companies like Apple and Tesla to pursue cobalt-free battery alternatives.",
        "price_story":  "Hit historic highs around 2018 driven by EV battery demand, then fell sharply as cathode chemistry shifted toward lower-cobalt formulations (NMC, LFP). Cobalt is classified as a possible carcinogen when inhaled as dust.",
    },
    "Copper": {
        "symbol":       "Cu · Atomic no. 29 · Transition metal",
        "science":      "Known to humans since 8000 BC — one of the first metals used, and among the few found in nature as a pure mineral in native form. Freshly exposed copper has a distinctive pinkish-orange luster; it undergoes passivation in air, forming a protective green patina (verdigris) that prevents structural decay. The highest electrical conductivity of any base metal: 59.6 × 10⁶ S/m, second only to silver. Naturally antimicrobial — destroys bacteria and viruses on contact. 100% recyclable without quality loss; ~80% of all copper ever mined is still in use today.",
        "application":  "Roughly 60% of global copper goes to electrical wiring — the standard for power grids, telecommunications, and high-efficiency motors. Used in architecture for corrosion-resistant roofing, plumbing, and cladding in coastal environments. Essential for hospital touch surfaces due to antimicrobial properties. A single EV requires nearly four times as much copper as a combustion engine car; offshore wind turbines use up to 9 tonnes each.",
        "source":       "Chile is the world&#39;s largest producer (~27% of global output), followed by Peru, DRC, and China. Copper is the 26th most abundant element in the crust at 50 ppm. Ore grades at major mines are declining, pointing toward a structural supply deficit in the early 2030s.",
        "price_story":  "Copper prices closely track global industrial output. The 2020–2022 commodity super-cycle drove prices to all-time highs, with the energy transition providing a structural demand floor that previous cycles lacked.",
    },
    "Platinum": {
        "symbol":       "Pt · Atomic no. 78 · Platinum group metal",
        "science":      "The most ductile of all pure metals — more so than gold or copper — allowing it to be drawn into extremely fine wires. Density of 21.45 g/cm³, twice as dense as lead. Melting point 1,768 °C. Chemically imperishable: resists oxidation at all temperatures and is insoluble in individual acids, dissolving only in aqua regia. Average crustal abundance is only 0.005 ppm, making it among the rarest elements on Earth. Formerly used to define the international SI standards for the metre and kilogram.",
        "application":  "Approximately 45% of production goes into automotive catalytic converters, where platinum converts toxic CO, hydrocarbons, and NOx emissions into CO₂, H₂O, and N₂. Critical catalyst in Proton Exchange Membrane (PEM) fuel cells and green hydrogen electrolyzers. Platinum-based compounds cisplatin and carboplatin are foundational chemotherapy drugs for cancer treatment. Used in precision resistance thermometers (SPRTs) and in high-end jewellery (ISO code: XPT).",
        "source":       "South Africa&#39;s Bushveld Igneous Complex produces approximately 75% of world supply, often as a byproduct of nickel and copper mining. Persistent load-shedding power outages at South African mines are a structural supply risk.",
        "price_story":  "Historically priced above gold for most of the 20th century; trading below gold since 2015 as ICE vehicle demand softens. The hydrogen economy offers a potential second demand wave, creating significant long-term price uncertainty.",
    },
    "Neodymium": {
        "symbol":       "Nd · Atomic no. 60 · Rare earth · LREE (lanthanide)",
        "science":      "Fourth member of the lanthanide series. A hard, slightly malleable silvery metal that reacts quickly with moisture and air, producing a flaky oxide layer similar to iron rust — so NdFeB magnets must be plated with nickel or copper for protection. Exists in the +3 oxidation state, producing distinctive pink or purple/blue compounds. Energy product (BH_max) of ~52 MGOe — the industry benchmark for the strongest permanent magnets. Undergoes a crystal structure transformation from double hexagonal to body-centered cubic at 863 °C.",
        "application":  "Alloyed with iron and boron (Nd₂Fe₁₄B), it creates magnets capable of lifting thousands of times their own weight — essential for EV traction motors (1–3 kg per vehicle) and wind turbine generators (200–300 kg each). Neodymium-doped crystals (Nd:YAG) are the industry standard for infrared lasers used in medical surgery, industrial welding, and scientific research. Used as a glass dye producing a lavender hue (shifts to pale blue under fluorescent light), and in &#39;didymium&#39; goggles to protect glassblowers from sodium flare.",
        "source":       "Produced commercially by electrolysis of neodymium halides obtained from monazite sand and bastnäsite ores. China controls approximately 85% of global rare earth processing; the Bayan Obo mine in Inner Mongolia is the world&#39;s largest individual REE deposit.",
        "price_story":  "Prices spiked dramatically during China&#39;s 2010 rare earth export restrictions, then collapsed. They climbed sharply again after 2020 as clean energy deployment accelerated demand for EV motors and wind turbines. Neodymium dust is a significant fire and explosion hazard.",
    },
    "Dysprosium": {
        "symbol":       "Dy · Atomic no. 66 · Rare earth · HREE (lanthanide)",
        "science":      "Named from the Greek dysprositos — &#39;hard to get&#39; — reflecting the extraordinary difficulty of isolating it; pure dysprosium metal was not produced until 1950 after development of ion exchange techniques. Silvery-white, soft enough to machine. One of the highest magnetic moments of any element — second only to holmium. Below 90.5 K it is ferromagnetic, passing through a helical antiferromagnetic state before becoming paramagnetic at 179 K. Magnetic susceptibility χᵥ ≈ 5.44 × 10⁻³. Crustal abundance of 5.2 mg/kg — similar to tin or lead.",
        "application":  "Adding up to 6 weight percent dysprosium to NdFeB magnets maintains their strength at operating temperatures above 150 °C — essential for EV drive motors and wind turbine generators that run hot. Dysprosium-oxide cermets serve as nuclear reactor control rod material due to its exceptionally high thermal neutron capture cross-section. Key component of Terfenol-D — the material that changes shape in response to magnetic fields more than any other known substance — used in naval SONAR and high-precision fuel injectors.",
        "source":       "Never concentrated enough to mine as a primary product — found only in trace amounts within REE deposits, extracted as a byproduct of yttrium mining from xenotime and monazite. Supply is heavily concentrated in ion-adsorption clay deposits in southern China and Myanmar.",
        "price_story":  "Frequently cited as the most critical element for clean energy technology. Supply scarcity and inelastic specialised demand make it among the most price-volatile of all critical minerals, driving strong commercial interest in low-dysprosium or dysprosium-free magnet designs.",
    },
    "Graphite": {
        "symbol":       "C · Crystalline carbon · Hexagonal graphene layers",
        "science":      "The most stable form of carbon under standard conditions. Structurally, stacked graphene sheets — hexagonal honeycomb lattices of carbon — held together by weak van der Waals forces (interlayer spacing: 0.335 nm). Highly anisotropic: conducts heat and electricity excellently within the planes, but acts as an insulator perpendicular to them. Chemically inert and refractory, remaining stable in non-oxidising environments up to 3,000 °C, but oxidises to CO₂ in air above 700 °C. The weak interlayer bonds allow sheets to slide freely — the origin of graphite&#39;s self-lubricating character.",
        "application":  "The predominant anode material in all Li-ion EV batteries: lithium ions intercalate (&#39;sandwich&#39;) between graphene layers during charging without structural damage. Also used in high-temperature crucibles for steel furnaces, as a dry lubricant for locks and high-temperature machinery, as a neutron moderator in nuclear reactors, and — combined with clay — as the &#39;lead&#39; in pencils (from the Greek graphein, &#39;to write&#39;). Synthetic graphite exceeds 99.9% purity carbon.",
        "source":       "China produces approximately 80% of the world&#39;s natural graphite and dominates synthetic graphite production (manufactured from petroleum coke in Acheson furnaces above 2,100 °C). Natural graphite occurs in three forms: flake, amorphous, and lump. Inhalation of graphite dust can cause graphite pneumoconiosis.",
        "price_story":  "Historically more price-stable than other battery raw materials. However, anode-grade battery graphite demand is now growing faster than non-Chinese supply capacity can match, attracting significant investment in Mozambique, Madagascar, and North America.",
    },
    "Terbium": {
        "symbol":       "Tb · Atomic no. 65 · Rare earth · HREE (lanthanide)",
        "science":      "One of four elements named after Ytterby, a village on the island of Resarö near Stockholm, Sweden, where gadolinite was first quarried. Identified in 1843 by Carl Gustaf Mosander; pure metal not produced until 1945 with development of ion exchange techniques. Silvery-grey, malleable and ductile, relatively stable in open air, flexible enough to cut with a knife. Most common oxidation state +3 — the Tb³⁺ ion exhibits brilliant lemon-yellow fluorescence driven by a strong green emission line. Below 219 K it becomes ferromagnetic; its oxide is a dark brown powder and the metal dust is flammable and explosive.",
        "application":  "Primary use is in green phosphors: terbium-doped compounds provide the green component of trichromatic fluorescent lamps, CRT screens, LED bulbs, and flat-panel displays (combined with red and blue europium phosphors to create high-efficiency white light). Key component of Terfenol-D — the alloy that changes shape in a magnetic field more than any other known material — critical for naval sonar, precision actuators, and sensors. Also used with zirconia as a high-temperature fuel cell stabiliser, and as a Faraday rotator in optical isolators protecting lasers from back-reflections.",
        "source":       "Extracted from monazite, xenotime, and bastnäsite. Most global supply originates from ion-adsorption clay deposits in southern China; significant undersea deposits have recently been identified near Japan. China holds a near-monopoly on processing with no currently viable alternative commercial source.",
        "price_story":  "Among the most expensive critical minerals per kilogram. Price tracks dysprosium closely with amplified volatility, driven by extreme scarcity and almost entirely inelastic specialised demand from the phosphor and magnet industries.",
    },
    "Rare Earths": {
        "symbol":       "17 elements — La through Lu (lanthanides) + Sc + Y",
        "science":      "Not geochemically rare: cerium is more abundant in the Earth&#39;s crust than copper (66 ppm), and all REEs are more abundant than gold. The &#39;rare&#39; refers to the historic difficulty of finding economically mineable concentrations, not crustal abundance. What makes them uniquely valuable is the progressive filling of the inner 4f electron shell across the lanthanide series, producing sharply differentiated optical, magnetic, and catalytic properties that vary element by element and cannot be replicated by cheaper substitutes. REEs invariably co-occur in the same ore minerals — bastnäsite, monazite, xenotime — making separation into individual pure elements a chemically intensive process.",
        "application":  "Nearly every high-tech sector depends on at least one REE: cerium for self-cleaning ovens and glass polishing; lanthanum for camera lenses and NiMH hybrid batteries; europium and terbium for red and green phosphors in every colour screen; gadolinium as MRI contrast agents (thermal neutron cross-section: 259,000 barns); erbium for fibre-optic amplifiers (EDFA at 1,550 nm) that carry internet data across continents; samarium-cobalt magnets stable to 800 °C for aerospace and precision-guided weapons; yttrium for dental crowns and jet engine thermal barrier coatings.",
        "source":       "China produces approximately 60% of global mine output and refines approximately 85% of supply. Ion-adsorption clay deposits in southern China are the primary source of the scarcer heavy REEs (Dy, Tb, Ho, Er). The capital-intensive solvent extraction required to separate individual elements is dominated by Chinese industry.",
        "price_story":  "China&#39;s 2010 export quota restriction caused prices to spike 10–50× within months before collapsing after WTO rulings forced policy reversal. That single episode permanently reshaped how governments approach critical mineral supply chain risk. Further export controls on gallium and germanium in 2023 reinforced the established pattern.",
    },
}

# Fallback end-use data for minerals absent from master_economic_timeseries
MINERAL_FALLBACK_USES: dict[str, tuple[str, int]] = {
    "Terbium":     ("Phosphors &amp; permanent magnets", 35),
    "Rare Earths": ("Catalysts", 35),
}
TRADE_DEDUP_COLS = [
    "year",
    "country",
    "partner_country",
    "flow_direction",
    "hs_code",
    "value_usd",
    "quantity_tonnes",
]


def ensure_dirs() -> None:
    for name in ("stakes", "deposits", "supply-chain", "bifurcation", "conclusion"):
        (VIS_ROOT / name).mkdir(parents=True, exist_ok=True)


def read_economic() -> pd.DataFrame:
    df = pd.read_csv(ECONOMIC_PATH)
    return df[df["mineral"].isin(TARGET_MINERALS)].copy()


def read_trade() -> pd.DataFrame:
    df = pd.read_csv(TRADE_PATH)
    return df[df["mineral"].isin(TARGET_MINERALS)].copy()


def read_deposits() -> gpd.GeoDataFrame:
    gdf = gpd.read_file(DEPOSITS_PATH)
    display_minerals = set(MAP_MINERAL_ORDER) | REE_MINERALS
    return gdf[gdf["mineral"].isin(display_minerals)].copy()


def unique_trade_flows(df: pd.DataFrame) -> pd.DataFrame:
    trade = df[df["record_type"] == "trade_flow"].copy()
    trade["partner_group"] = trade["partner_group"].fillna("Other countries")
    trade["partner_country"] = trade["partner_country"].fillna("Unknown")
    trade["country"] = trade["country"].fillna("Unknown")
    return trade.drop_duplicates(subset=TRADE_DEDUP_COLS)


_FONT_INJECT = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap" rel="stylesheet">
<style>
html, body { font-family: 'Lato', -apple-system, BlinkMacSystemFont, sans-serif; background: #F7F4EE; }
.plotly, .plotly text, .js-plotly-plot text { font-family: 'Lato', sans-serif !important; }
</style>
"""

def write_plotly(fig: go.Figure, path: Path) -> None:
    fig.write_html(
        path,
        full_html=True,
        include_plotlyjs=True,
        config={"displayModeBar": False, "responsive": True},
    )
    # Inject Lato + Playfair Display webfonts so axis ticks/titles render in
    # the site typeface instead of falling back to a system sans.
    html = path.read_text(encoding="utf-8")
    if "<head>" in html and _FONT_INJECT not in html:
        html = html.replace("<head>", "<head>\n" + _FONT_INJECT, 1)
        path.write_text(html, encoding="utf-8")


def build_mineral_grid(economic: pd.DataFrame) -> Path:
    df = economic[
        (economic["metric"] == "world_production_tonnes")
        & (economic["country"] == "World")
    ].copy()
    latest = df.sort_values("year").groupby("mineral", as_index=False).tail(1)
    latest["label"] = latest["mineral"] + "<br>" + latest["case_group"]

    fig = px.treemap(
        latest,
        path=["case_group", "mineral"],
        values="value",
        color="mineral",
        color_discrete_map=MINERAL_COLORS,
        custom_data=["year", "unit", "mineral_group"],
        title="Critical Minerals at a Glance",
    )
    fig.update_traces(
        textinfo="label+value",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Latest year: %{customdata[0]}<br>"
            "Production: %{value:,.0f} %{customdata[1]}<br>"
            "Group: %{customdata[2]}<extra></extra>"
        ),
        root_color="rgba(0,0,0,0)",
    )
    apply_theme(fig)
    fig.update_layout(margin=dict(l=20, r=20, t=70, b=20))

    path = VIS_ROOT / "stakes" / "mineral_grid.html"
    write_plotly(fig, path)
    return path


def _build_price_index_series(
    economic: pd.DataFrame, metric: str
) -> pd.DataFrame:
    """Build a per-mineral price index (2015 = 100) from one of the price metrics.

    Stitches USGS MCS 2023-2024 unit values onto the back of each historical
    series so every line lands at 2024 where MCS coverage exists. Where MCS
    publishes more than one price category per (mineral, year) - Cobalt
    (LME cash / US spot cathode), Copper (COMEX / LME / US producer cathode),
    Gallium and Graphite (multiple unit-value series) - the categories are
    collapsed to a per-year median before stitching, so the line carries one
    canonical value per year.
    """
    hist = economic[economic["metric"] == metric].copy()
    mcs = economic[economic["metric"] == "mcs_price_usd_per_tonne"].copy()

    # MCS is nominal USD; only stitch onto the nominal historical series.
    if metric == "historical_price_usd_per_tonne":
        # Collapse multi-category MCS rows to median per (mineral, year)
        mcs_dedup = (
            mcs.groupby(["mineral", "year"], as_index=False)["value"]
            .median()
        )
        for mineral, g in mcs_dedup.groupby("mineral"):
            hist_last = hist[hist["mineral"] == mineral]["year"].max()
            if pd.isna(hist_last):
                continue
            extra = g[g["year"] > hist_last][["mineral", "year", "value"]].copy()
            if extra.empty:
                continue
            extra = extra.assign(
                metric=metric,
                country="World",
                unit="USD per metric tonne",
                source="USGS MCS 2025 splice (median)",
            )
            hist = pd.concat([hist, extra[hist.columns.intersection(extra.columns)]], ignore_index=True)

    # Defensive: collapse any (mineral, year) duplicates left over to median
    hist = (
        hist.groupby(["mineral", "year"], as_index=False)["value"]
        .median()
    )

    base = (
        hist[hist["year"] == 2015][["mineral", "value"]]
        .rename(columns={"value": "base_value"})
    )
    indexed = hist.merge(base, on="mineral", how="inner")
    indexed = indexed[indexed["base_value"] > 0].copy()
    indexed["price_index"] = indexed["value"] / indexed["base_value"] * 100
    return indexed[["mineral", "year", "price_index", "value"]].sort_values(["mineral", "year"])


def _render_price_index_figure(
    nominal: pd.DataFrame,
    real: pd.DataFrame,
    *,
    year_range: tuple[int, int],
    title_main: str,
    title_sub: str,
    rebase_year: int = 2015,
    show_focus_band: bool = True,
) -> go.Figure:
    """Shared renderer for the price-index chart and its 2000-2024 zoom.

    Each frame is rebased on `rebase_year = 100` and clipped to year_range.
    Linear y-axis (no log scale).
    """
    y0, y1 = year_range

    def _clip(df: pd.DataFrame) -> pd.DataFrame:
        out = df[(df["year"] >= y0) & (df["year"] <= y1)].copy()
        if out.empty:
            return out
        # Re-rebase on rebase_year within this clip
        base = (
            out[out["year"] == rebase_year][["mineral", "price_index"]]
            .rename(columns={"price_index": "rebase_value"})
        )
        out = out.merge(base, on="mineral", how="inner")
        out["price_index"] = out["price_index"] / out["rebase_value"] * 100
        return out

    nominal_clip = _clip(nominal)
    real_clip = _clip(real)

    minerals = sorted(set(nominal_clip["mineral"]).union(real_clip["mineral"]))

    fig = go.Figure()
    nominal_count = 0
    for mineral in minerals:
        sub = nominal_clip[nominal_clip["mineral"] == mineral]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub["price_index"],
                mode="lines",
                name=mineral,
                line=dict(width=3, color=MINERAL_COLORS.get(mineral)),
                legendgroup=mineral,
                hovertemplate=f"<b>{mineral}</b><br>%{{x}} · index %{{y:.0f}}<extra></extra>",
                visible=True,
            )
        )
        nominal_count += 1

    real_count = 0
    for mineral in minerals:
        sub = real_clip[real_clip["mineral"] == mineral]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub["price_index"],
                mode="lines",
                name=mineral,
                line=dict(width=3, color=MINERAL_COLORS.get(mineral)),
                legendgroup=mineral,
                hovertemplate=f"<b>{mineral}</b><br>%{{x}} · real index %{{y:.0f}}<extra></extra>",
                visible=False,
                showlegend=True,
            )
        )
        real_count += 1

    nominal_visible = [True] * nominal_count + [False] * real_count
    real_visible = [False] * nominal_count + [True] * real_count

    fig.add_hline(y=100, line_dash="dot", line_color="rgba(20,17,13,0.35)")
    if show_focus_band and y0 < 1995 < y1:
        fig.add_vrect(
            x0=1995, x1=y1,
            fillcolor="rgba(15, 61, 92, 0.06)",
            line_width=0, layer="below",
        )

    apply_theme(fig)
    fig.update_layout(
        title=dict(
            text=(
                f"<b>{title_main}</b>"
                f"<br><span style='font-size:18px;font-weight:400;color:#5a544c'>{title_sub}</span>"
            ),
        ),
        xaxis=dict(title=dict(text="<b>Year</b>"), range=[y0, y1]),
        yaxis=dict(title=dict(text=f"Index ({rebase_year} = 100)")),
        legend=dict(
            orientation="h",
            yanchor="top", y=1.06,
            xanchor="right", x=1.0,
        ),
        legend_title_text=None,
        annotations=[],
        margin=dict(l=80, r=40, t=170, b=140),
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.0, xanchor="left",
                y=-0.22, yanchor="top",
                bgcolor="#F7F4EE",
                bordercolor="rgba(15, 61, 92, 0.55)",
                buttons=[
                    dict(label="Nominal USD",     method="update", args=[{"visible": nominal_visible}]),
                    dict(label="Real (1998 USD)", method="update", args=[{"visible": real_visible}]),
                ],
            )
        ],
    )
    return fig


def build_price_index(economic: pd.DataFrame) -> Path:
    nominal = _build_price_index_series(economic, "historical_price_usd_per_tonne")
    real = _build_price_index_series(economic, "historical_real_price_1998_usd_per_tonne")
    latest_year = int(max(nominal["year"].max(), real["year"].max()))

    fig = _render_price_index_figure(
        nominal, real,
        year_range=(1900, latest_year),
        title_main="The Price Shocks That Made Critical Minerals Critical",
        title_sub=(
            f"Annual price index 1900–{latest_year}, rebased so 2015 = 100. "
            "1995–2024 highlighted; toggle nominal / real (1998 USD) below."
        ),
    )
    path = VIS_ROOT / "stakes" / "price_index.html"
    write_plotly(fig, path)
    return path


def build_price_index_zoom(economic: pd.DataFrame) -> Path:
    """5.1b - Modern-era zoom: 2000-2024 only, rebased on 2015 = 100."""
    nominal = _build_price_index_series(economic, "historical_price_usd_per_tonne")
    real = _build_price_index_series(economic, "historical_real_price_1998_usd_per_tonne")
    latest_year = int(max(nominal["year"].max(), real["year"].max()))

    fig = _render_price_index_figure(
        nominal, real,
        year_range=(2000, latest_year),
        title_main="The Modern Era, in Closer Focus",
        title_sub=(
            f"Annual price index 2000–{latest_year}, rebased so 2015 = 100. "
            "Same materials, same 2015 = 100 base, no 1900–2000 shoulder."
        ),
        show_focus_band=False,
    )
    path = VIS_ROOT / "stakes" / "price_index_zoom.html"
    write_plotly(fig, path)
    return path


def build_end_uses(economic: pd.DataFrame) -> Path:
    end_use = economic[economic["metric"] == "end_use_share_pct"].copy()
    latest_year = int(end_use["year"].max())
    end_use = end_use[end_use["year"] == latest_year].copy()

    fig = px.treemap(
        end_use,
        path=["mineral", "category"],
        values="value",
        color="mineral",
        color_discrete_map=MINERAL_COLORS,
        title=f"How the Minerals Are Used ({latest_year})",
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Share: %{value:.1f}%<extra></extra>"
        )
    )
    apply_theme(fig)
    fig.update_layout(margin=dict(l=20, r=20, t=70, b=20))

    path = VIS_ROOT / "stakes" / "end_uses.html"
    write_plotly(fig, path)
    return path


def build_end_use_carousel(economic: pd.DataFrame) -> Path:
    """Generate the 3D end-use carousel as a standalone HTML file.

    Data-driven top use + percentage per mineral; expert detail text comes
    from MINERAL_DETAIL.  Minerals absent from the timeseries fall back to
    MINERAL_FALLBACK_USES so the carousel always shows all ten minerals.
    """
    end_use = economic[economic["metric"] == "end_use_share_pct"].copy()
    latest_year = int(end_use["year"].max()) if not end_use.empty else 2025

    # Build lookup: mineral → (top_category, pct)
    top_use_by_mineral: dict[str, tuple[str, int]] = {}
    for mineral, grp in end_use[end_use["year"] == latest_year].groupby("mineral"):
        row = grp.sort_values("value", ascending=False).iloc[0]
        top_use_by_mineral[str(mineral)] = (str(row["category"]), int(row["value"]))

    def _card(mineral: str) -> str:
        color = mineral_color(mineral)
        image = MINERAL_IMAGES.get(mineral, "")
        detail = MINERAL_DETAIL.get(mineral, {})
        top_use, pct = top_use_by_mineral.get(
            mineral, MINERAL_FALLBACK_USES.get(mineral, ("Various", 0))
        )
        symbol      = detail.get("symbol",      "")
        science     = detail.get("science",     "")
        application = detail.get("application", "")
        source      = detail.get("source",      "")
        price_story = detail.get("price_story", "")
        return f"""
      <figure>
        <div class="mineral-card" style="--mc: {color}">
          <img class="mc-icon" src="../images/{image}" alt="{mineral}">
          <div class="mc-name">{mineral}</div>
          <div class="mc-use">{top_use}</div>
          <div class="mc-pct">{pct}%</div>
          <div class="mc-bar-wrap"><div class="mc-bar" style="width:{pct}%"></div></div>
          <div class="mc-label">of demand · {latest_year}</div>
          <div class="mc-detail">
            <strong>Symbol:</strong> {symbol}<br>
            <strong>Science:</strong> {science}<br>
            <strong>Application:</strong> {application}<br>
            <strong>Source:</strong> {source}<br>
            <strong>Price story:</strong> {price_story}
          </div>
        </div>
      </figure>"""

    cards_html = "".join(_card(m) for m in CAROUSEL_MINERAL_ORDER)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Critical Mineral End Uses</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Lato:wght@300;400;700;900&family=Playfair+Display:ital,wght@0,400..900;1,400..900&display=swap">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    html, body {{
      height: 100%;
    }}

    body {{
      min-height: 100%;
      overflow-x: hidden;
      overflow-y: auto;
      background: #0D1B2A;
      font-family: 'Lato', -apple-system, BlinkMacSystemFont, sans-serif;
      color: #F0EDE5;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      gap: 0;
      padding: 1.5rem 1rem 1rem;
      user-select: none;
    }}

    #carousel {{
      perspective: 1600px;
      width: 100%;
      height: 420px;
      margin-bottom: 100px;
      position: relative;
      flex-shrink: 0;
    }}

    figure#spinner {{
      width: 100%;
      height: 100%;
      transform-style: preserve-3d;
      transform-origin: 50% 50% -600px;
      transition: transform 0.9s cubic-bezier(0.16, 1, 0.3, 1);
      position: relative;
      pointer-events: none;
    }}

    figure#spinner > figure {{
      position: absolute;
      width: 22%;
      height: 88%;
      top: 6%;
      left: 39%;
      transform-origin: 50% 50% -600px;
      border-radius: 12px;
      overflow: hidden;
      cursor: default;
      pointer-events: none;
      outline: 2px solid transparent;
      outline-offset: 2px;
      transition: width 0.9s cubic-bezier(0.16,1,0.3,1),
                  height 0.9s cubic-bezier(0.16,1,0.3,1),
                  top 0.9s cubic-bezier(0.16,1,0.3,1),
                  left 0.9s cubic-bezier(0.16,1,0.3,1),
                  outline-color 0.3s;
    }}

    figure#spinner > figure.current {{
      outline-color: rgba(15, 61, 92, 0.7);
      pointer-events: auto;
      cursor: pointer;
    }}

    figure#spinner > figure.focus {{
      width: 68%;
      height: 158%;
      top: -30%;
      left: 17%;
    }}

    .mineral-card {{
      width: 100%;
      height: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: flex-start;
      gap: 0.55rem;
      padding: 1.5rem 0.9rem 1.1rem;
      background: linear-gradient(160deg, #1B3A4B 0%, #0D1B2A 100%);
      border-top: 4px solid var(--mc);
      text-align: center;
      overflow-y: auto;
    }}

    .mc-icon {{
      width: 64px;
      height: 64px;
      object-fit: cover;
      border-radius: 8px;
      border: 2px solid var(--mc);
    }}

    .mc-name {{
      font-size: 1.25rem;
      font-weight: 700;
      color: #fff;
      letter-spacing: 0.02em;
    }}

    .mc-use {{
      font-size: 0.82rem;
      font-weight: 400;
      color: rgba(240, 237, 229, 0.72);
      line-height: 1.35;
    }}

    .mc-pct {{
      font-size: 1.9rem;
      font-weight: 800;
      color: var(--mc);
      line-height: 1;
    }}

    .mc-bar-wrap {{
      width: 78%;
      height: 4px;
      background: rgba(255, 255, 255, 0.1);
      border-radius: 9999px;
      overflow: hidden;
    }}

    .mc-bar {{
      height: 100%;
      background: var(--mc);
      border-radius: 9999px;
    }}

    .mc-label {{
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.07em;
      color: rgba(240, 237, 229, 0.42);
    }}

    .mc-detail {{
      display: none;
      font-size: 0.9rem;
      color: rgba(240, 237, 229, 0.88);
      line-height: 1.7;
      padding-top: 0.5rem;
      border-top: 1px solid rgba(255,255,255,0.1);
      width: 90%;
      text-align: left;
    }}

    figure#spinner > figure.focus .mc-detail {{
      display: block;
    }}

    figcaption {{
      position: absolute;
      bottom: 0;
      width: 100%;
      padding: 0.45rem 0.6rem;
      font-size: 0.72rem;
      background: rgba(13, 27, 42, 0);
      color: rgba(240, 237, 229, 0.9);
      text-align: center;
      transition: background 0.5s;
      pointer-events: none;
    }}

    figure#spinner > figure.current:hover figcaption,
    figure#spinner > figure.current.caption figcaption {{
      background: rgba(13, 27, 42, 0.85);
    }}

    .controls {{
      display: flex;
      align-items: center;
      gap: 2rem;
      margin-top: 1.1rem;
      flex-shrink: 0;
    }}

    .ctrl-btn {{
      background: rgba(15, 61, 92, 0.1);
      border: 1px solid rgba(15, 61, 92, 0.35);
      color: #0F3D5C;
      border-radius: 50%;
      width: 2.4rem;
      height: 2.4rem;
      font-size: 1.5rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      transition: background 0.2s, border-color 0.2s;
      padding-bottom: 1px;
    }}

    .ctrl-btn:hover {{
      background: rgba(15, 61, 92, 0.22);
      border-color: rgba(15, 61, 92, 0.65);
    }}

    .ctrl-hint {{
      font-size: 0.62rem;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: rgba(240, 237, 229, 0.35);
      text-align: center;
    }}
  </style>
</head>
<body>

  <div id="carousel">
    <figure id="spinner">
{cards_html}
    </figure>
  </div>

  <div class="controls">
    <button class="ctrl-btn" onclick="galleryspin('-')" aria-label="Previous mineral">&#8249;</button>
    <span class="ctrl-hint">&#8592; &#8594; to rotate &middot; click card to zoom</span>
    <button class="ctrl-btn" onclick="galleryspin('')" aria-label="Next mineral">&#8250;</button>
  </div>

  <script>
    document.querySelectorAll('img.mc-icon').forEach(function(img) {{
      img.addEventListener('error', function() {{
        var color = getComputedStyle(this.closest('.mineral-card')).getPropertyValue('--mc').trim();
        this.style.display = 'none';
        var fallback = document.createElement('div');
        fallback.className = 'mc-icon mc-icon-fallback';
        fallback.style.cssText = 'width:64px;height:64px;border-radius:8px;background:' + color + ';opacity:0.35;border:2px solid ' + color;
        this.parentNode.insertBefore(fallback, this);
      }});
    }});

    var spinner  = document.querySelector('#spinner');
    var cards    = document.querySelectorAll('#spinner > figure');
    var n        = cards.length;
    var degInt   = 360 / n;
    var angle    = 0;
    var current  = 1;

    cards.forEach(function(fig, i) {{
      var rot = -(i * degInt);
      fig.style.webkitTransform = 'rotateY(' + rot + 'deg)';
      fig.style.transform       = 'rotateY(' + rot + 'deg)';
      fig.addEventListener('click', function() {{
        if (this.classList.contains('current')) {{
          this.classList.toggle('focus');
        }}
      }});
    }});

    function setCurrent(idx) {{
      var el = document.querySelector('figure#spinner > figure:nth-child(' + idx + ')');
      if (el) el.classList.add('current');
    }}

    function galleryspin(sign) {{
      cards.forEach(function(fig) {{
        fig.classList.remove('current', 'focus', 'caption');
      }});

      if (!sign) {{
        angle  += degInt;
        current = current < n ? current + 1 : 1;
      }} else {{
        angle  -= degInt;
        current = current > 1 ? current - 1 : n;
      }}

      spinner.style.webkitTransform = 'rotateY(' + angle + 'deg)';
      spinner.style.transform       = 'rotateY(' + angle + 'deg)';
      setCurrent(current);
    }}

    document.addEventListener('keydown', function(e) {{
      var cur;
      switch (e.which) {{
        case 37: galleryspin('-'); break;
        case 39: galleryspin('');  break;
        case 90:
          cur = document.querySelector('#spinner > figure.current');
          if (cur) cur.classList.toggle('focus');
          break;
        case 67:
          cur = document.querySelector('#spinner > figure.current');
          if (cur) cur.classList.toggle('caption');
          break;
        default: return;
      }}
      e.preventDefault();
    }});

    setCurrent(1);
  </script>

</body>
</html>"""

    path = VIS_ROOT / "stakes" / "end_use_carousel.html"
    path.write_text(html, encoding="utf-8")
    return path


def _nan(val: object) -> bool:
    if val is None:
        return True
    if isinstance(val, float) and pd.isna(val):
        return True
    return str(val).strip() in ("nan", "None", "")


def _deposit_type_explainer(dep_type: object) -> str | None:
    """Return a plain-English explainer for a geological deposit type string."""
    if _nan(dep_type):
        return None
    dt = str(dep_type).lower()
    for keyword, explanation in DEPOSIT_TYPE_EXPLAINERS:
        if keyword in dt:
            return explanation
    return None


def _deposit_style(production_status: object, deposit_status: object) -> tuple[int, float]:
    """Return (base_radius, fill_opacity). Radii scaled by zoom via JS.

    All default-shown markers share the same base radius; opacity signals activity.
    REE uses production_status; non-REE uses deposit_status.
    """
    ps = str(production_status).lower() if not _nan(production_status) else ""
    ds = str(deposit_status).lower() if not _nan(deposit_status) else ""

    if ps and "producer" in ps and "past" not in ps:
        return 3, 0.95   # active mine — crisp, opaque
    if ds == "centroid":
        return 3, 0.75   # country-level fallback (e.g. copper)
    if "deposit" in ds:
        return 3, 0.88   # known deposit
    return 3, 0.62        # occurrence/showing/unknown


def _opt_line(label: str, val: object, color: str = "#aaa", val_color: str = "") -> str:
    if _nan(val):
        return ""
    vc_open = f"<b style='color:{val_color}'>" if val_color else ""
    vc_close = "</b>" if val_color else ""
    return f"<br><span style='color:{color}'>{label}:</span> {vc_open}{val}{vc_close}"


def _pill_list(items_str: str, border_color: str = "") -> str:
    # border_color kept for signature compatibility — colour now lives in .tt-pill CSS.
    return "".join(
        f"<span class='tt-pill'>{m.strip()}</span>"
        for m in items_str.split(",") if m.strip()
    )


def _row(label: str, value: object, note: str = "") -> str:
    """Single table-style tooltip row — styled by .tt-row in shared CSS."""
    if _nan(value):
        return ""
    note_html = f"<div class='tt-note'>{note}</div>" if note else ""
    return (
        f"<div class='tt-row'>"
        f"<span class='tt-label'>{label.upper()}</span>"
        f"<div class='tt-val'>{value}</div>"
        f"{note_html}</div>"
    )


def _tooltip_non_ree(row: object) -> str:
    mineral = getattr(row, "mineral", "") or ""
    color = mineral_color(mineral)
    name = getattr(row, "deposit_name", "") or "Unnamed deposit"
    country = getattr(row, "country", "") or ""
    dep_status = getattr(row, "deposit_status", None)
    dep_type = getattr(row, "deposit_type", None)
    location = getattr(row, "location_detail", None)
    host_lith = getattr(row, "host_lithology", None)
    source = getattr(row, "source", None)

    is_centroid = str(dep_status) == "centroid"
    centroid_html = (
        "<div class='tt-warn'>&#9888; Country-level estimate — no deposit geometry in source data</div>"
        if is_centroid else ""
    )

    explainer = _deposit_type_explainer(dep_type) if not _nan(dep_type) else None

    return (
        f"<div class='tt'>"
        f"<div class='tt-title' style='color:{color}'>{name}</div>"
        + _row("Mineral", mineral)
        + _row("Country", f"{country}{(' · ' + str(location)) if not _nan(location) else ''}")
        + _row("Deposit type", dep_type, note=explainer)
        + _row("Host material", host_lith)
        + centroid_html
        + (f"<div class='tt-source'>Dataset: {source}</div>" if not _nan(source) else "")
        + "</div>"
    )


_REE_ELEMENT_NAMES = {"la", "ce", "pr", "nd", "pm", "sm", "eu", "gd",
                      "tb", "dy", "ho", "er", "tm", "yb", "lu", "y", "sc",
                      "lree", "hree", "ree"}


def _notable_cooccurring(commods: object) -> str | None:
    """Return co-occurring commodities string only if it contains non-REE metals."""
    if _nan(commods):
        return None
    parts = [p.strip() for p in str(commods).split(";") if p.strip()]
    notable = [p for p in parts if p.lower() not in _REE_ELEMENT_NAMES]
    return "; ".join(notable) if notable else None


def _tooltip_ree(row: object) -> str:
    name = getattr(row, "deposit_name", "") or "Unnamed deposit"
    country = getattr(row, "country", "") or ""
    ree_sub = getattr(row, "ree_subgroup", None)
    minerals_list = getattr(row, "minerals_at_deposit", "") or ""
    production_status = getattr(row, "production_status", None)
    dep_type = getattr(row, "deposit_type", None)
    host_lith = getattr(row, "host_lithology", None)
    ore_mins = getattr(row, "ore_minerals", None)
    commods = getattr(row, "commodities", None)
    source = getattr(row, "source", None)

    # REE subgroup
    ree_sub_clean = str(ree_sub).strip() if not _nan(ree_sub) else None
    if ree_sub_clean:
        badge_color = {"LREE": "#3AAFA9", "HREE": "#C49A02", "mixed": REE_COLOR}.get(ree_sub_clean, REE_COLOR)
        ree_type_val = f"<span style='color:{badge_color}'>{ree_sub_clean}</span>"
    else:
        ree_type_val = None

    # Element pills (Nd / Dy / Tb present)
    pills_html = _pill_list(minerals_list, REE_COLOR) if minerals_list else None

    # Production status
    ps_clean = str(production_status).strip() if not _nan(production_status) else None
    if ps_clean:
        ps_lower = ps_clean.lower()
        if "producer" in ps_lower and "past" not in ps_lower:
            ps_cls = "tt-status-active"
        elif "past" in ps_lower:
            ps_cls = "tt-status-past"
        else:
            ps_cls = ""
        ps_val = f"<span class='{ps_cls}'>{ps_clean}</span>" if ps_cls else ps_clean
    else:
        ps_val = None

    explainer = _deposit_type_explainer(dep_type) if not _nan(dep_type) else None
    notable_commods = _notable_cooccurring(commods)

    return (
        f"<div class='tt'>"
        f"<div class='tt-title' style='color:{REE_COLOR}'>{name}</div>"
        + _row("Country", country)
        + _row("Mine status", ps_val)
        + _row("REE type", ree_type_val)
        + _row("Elements present", pills_html)
        + _row("Deposit type", dep_type, note=explainer)
        + _row("Host material", host_lith)
        + _row("Ore form", ore_mins)
        + _row("Also contains", notable_commods)
        + (f"<div class='tt-source'>Dataset: {source}</div>" if not _nan(source) else "")
        + "</div>"
    )


def _legend_html() -> str:
    def dot(color: str, size: int = 10, opacity: float = 1.0) -> str:
        return (
            f"<span style='display:inline-block;width:{size}px;height:{size}px;"
            f"border-radius:50%;background:{color};opacity:{opacity};"
            f"margin-right:8px;flex-shrink:0;vertical-align:middle'></span>"
        )

    def mrow(color: str, label: str) -> str:
        return (
            f"<div style='display:flex;align-items:center;margin-bottom:5px;padding-left:10px'>"
            f"{dot(color)}{label}</div>"
        )

    def section(title: str) -> str:
        return (
            f"<div style='font-weight:700;margin:9px 0 5px;font-size:12px;"
            f"color:#0F3D5C;letter-spacing:.4px'>{title}</div>"
        )

    return f"""
<style>
.mcl-panel {{
  position: absolute; bottom: 16px; right: 16px; z-index: 1000;
  background: rgba(247, 244, 238, 0.96);
  border: 1px solid rgba(20, 17, 13, 0.35);
  border-radius: 0;
  font-family: 'Lato', -apple-system, sans-serif;
  font-size: 11.5px; color: #1A1A1A;
  min-width: 200px;
  box-shadow: 0 2px 0 rgba(20, 17, 13, 0.18);
  overflow: hidden;
}}
.mcl-header {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 14px; cursor: pointer; user-select: none;
  background: transparent;
  border-bottom: 1px solid rgba(20, 17, 13, 0.18);
}}
.mcl-header:hover {{ background: rgba(15, 61, 92, 0.10); }}
.mcl-header-title {{
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic; font-weight: 600;
  font-size: 12px; letter-spacing: 0.04em;
  color: #0F3D5C; text-transform: none;
}}
.mcl-chevron {{
  width: 7px; height: 7px;
  border-right: 1.5px solid #0F3D5C;
  border-bottom: 1.5px solid #0F3D5C;
  transform: rotate(45deg); transition: transform 0.2s ease;
  margin-top: -3px;
}}
.mcl-collapsed .mcl-chevron {{ transform: rotate(-45deg); margin-top: 1px; }}
.mcl-body {{ padding: 9px 14px 11px; max-height: 60vh; overflow-y: auto; }}
.mcl-collapsed .mcl-body {{ display: none; }}
.mcl-row {{ display: flex; align-items: center; margin-bottom: 5px; }}
.mcl-foot {{
  margin-top: 8px; padding-top: 7px;
  border-top: 1px solid rgba(20, 17, 13, 0.10);
  font-size: 10.5px; letter-spacing: 0.04em;
  color: rgba(20, 17, 13, 0.55);
}}
</style>
<div id='mcl-panel' class='mcl-panel mcl-collapsed'>
  <div class='mcl-header' onclick="this.parentElement.classList.toggle('mcl-collapsed')">
    <span class='mcl-header-title'>Icons</span>
    <span class='mcl-chevron'></span>
  </div>
  <div class='mcl-body'>
    <div class='mcl-row'>{dot("#1A1A1A", 6, 0.95)}Active mine</div>
    <div class='mcl-row'>{dot("#1A1A1A", 6, 0.88)}Confirmed reserve</div>
    <div class='mcl-row'>{dot("#1A1A1A", 6, 0.75)}Country estimate</div>
    <div class='mcl-row'>{dot("#1A1A1A", 6, 0.62)}Exploration target</div>
    <div class='mcl-foot'>&#9733; landmark mine &nbsp;·&nbsp; colour = mineral</div>
  </div>
</div>
"""


def _landmark_table_html() -> str:
    def _status_badge(status: str) -> str:
        color = "#2ecc71" if status.lower().startswith("active") else "#e67e22"
        return f"<span style='color:{color};font-weight:600'>{status}</span>"

    rows = "".join(
        f"<tr style='border-top:1px solid rgba(255,255,255,0.06)'>"
        f"<td style='padding:8px 10px;font-weight:600;white-space:nowrap'>★ {m['name']}</td>"
        f"<td style='padding:8px 10px;white-space:nowrap'>{m['mineral']}</td>"
        f"<td style='padding:8px 10px'>{m['country']}</td>"
        f"<td style='padding:8px 10px'>{m['operator']}</td>"
        f"<td style='padding:8px 10px'>{_status_badge(m['status'])}</td>"
        f"<td style='padding:8px 10px;font-size:12px;color:#bbb'>{m['specs']}</td>"
        f"<td style='padding:8px 10px;font-size:12px;color:#aaa;max-width:380px'>{m['note']}</td>"
        f"</tr>"
        for m in LANDMARK_MINES
    )
    return f"""
<div style="margin-top:24px;font-family:'Lato',sans-serif">
  <h3 style="color:#0F3D5C;margin-bottom:10px">Landmark Mines</h3>
  <div style="overflow-x:auto">
  <table style="width:100%;border-collapse:collapse;font-size:13px;color:#F0EDE5;
                background:#1B3A4B;border-radius:8px;overflow:hidden">
    <thead>
      <tr style="background:#0D1B2A;color:#0F3D5C;text-align:left">
        <th style="padding:8px 10px">Mine</th>
        <th style="padding:8px 10px">Mineral</th>
        <th style="padding:8px 10px">Country</th>
        <th style="padding:8px 10px">Operator</th>
        <th style="padding:8px 10px">Status</th>
        <th style="padding:8px 10px">Specs</th>
        <th style="padding:8px 10px">Notes</th>
      </tr>
    </thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</div>
"""


def _zoom_radius_js(map_var: str) -> str:
    """JS that scales CircleMarker radii with zoom — integer pixels for crispness."""
    return f"""
<script>
(function() {{
    function init() {{
        var map = {map_var};
        if (!map) {{ setTimeout(init, 50); return; }}
        var _circles = [];

        function collectCircles(layer) {{
            if (layer instanceof L.CircleMarker && !(layer instanceof L.Circle)) {{
                if (layer.options._baseRadius === undefined) {{
                    layer.options._baseRadius = layer.options.radius;
                }}
                _circles.push(layer);
            }}
            if (typeof layer.eachLayer === 'function') {{
                layer.eachLayer(collectCircles);
            }}
        }}

        function applyZoom() {{
            var zoom = map.getZoom();
            // Integer-rounded scale → crisp dots, growing with zoom.
            var scale = Math.max(1.0, Math.min(2.2, 0.18 * zoom + 0.5));
            _circles.forEach(function(c) {{
                c.setRadius(Math.max(2, Math.round(c.options._baseRadius * scale)));
            }});
        }}

        map.on('layeradd', function(e) {{ collectCircles(e.layer); applyZoom(); }});
        map.on('zoomend', applyZoom);
        map.eachLayer(collectCircles);
        applyZoom();
    }}
    if (document.readyState === 'complete') init();
    else window.addEventListener('load', init);
}})();
</script>
"""


def _heatmap_cap_js(map_var: str, heat_var: str, km_cap: float) -> str:
    """Cap heatmap pixel reach to ~km_cap when zoomed out; keep originals otherwise."""
    return f"""
<script>
(function() {{
    function init() {{
        var map = {map_var};
        var heat = window['{heat_var}'];
        if (!map || !heat) {{ setTimeout(init, 50); return; }}
        var origRadius = heat.options.radius;
        var origBlur   = heat.options.blur;
        var origTotal  = origRadius + origBlur;

        function applyCap() {{
            var z = map.getZoom();
            var kmPerPx = 156543.03 * Math.cos(0) / Math.pow(2, z) / 1000;
            var maxPx = {km_cap} / kmPerPx;
            if (origTotal <= maxPx) {{
                heat.setOptions({{ radius: origRadius, blur: origBlur }});
            }} else {{
                var ratio = maxPx / origTotal;
                heat.setOptions({{
                    radius: Math.max(2, Math.round(origRadius * ratio)),
                    blur:   Math.max(2, Math.round(origBlur   * ratio)),
                }});
            }}
        }}
        map.on('zoomend', applyCap);
        applyCap();
    }}
    if (document.readyState === 'complete') init();
    else window.addEventListener('load', init);
}})();
</script>
"""


def _scroll_zoom_toggle_js(map_var: str) -> str:
    """Inject a Leaflet control button to toggle scroll-wheel zoom on/off."""
    return f"""
<script>
(function() {{
    function init() {{
        var map = {map_var};
        if (!map || !window.L) {{ setTimeout(init, 50); return; }}
        var Toggle = L.Control.extend({{
            options: {{ position: 'topleft' }},
            onAdd: function(m) {{
                var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control sw-toggle');
                var a   = L.DomUtil.create('a', '', div);
                a.href  = '#';
                a.role  = 'button';
                a.title = 'Click to enable scroll-wheel zoom (currently OFF)';
                a.textContent = 'Wheel: off';
                L.DomEvent.disableClickPropagation(div);
                L.DomEvent.on(a, 'click', L.DomEvent.preventDefault);
                L.DomEvent.on(a, 'click', function() {{
                    if (m.scrollWheelZoom.enabled()) {{
                        m.scrollWheelZoom.disable();
                        a.classList.remove('is-active');
                        a.textContent = 'Wheel: off';
                        a.title = 'Click to enable scroll-wheel zoom (currently OFF)';
                    }} else {{
                        m.scrollWheelZoom.enable();
                        a.classList.add('is-active');
                        a.textContent = 'Wheel: on';
                        a.title = 'Click to disable scroll-wheel zoom (currently ON)';
                    }}
                }});
                return div;
            }}
        }});
        new Toggle().addTo(map);
    }}
    if (document.readyState === 'complete') init();
    else window.addEventListener('load', init);
}})();
</script>
"""


def _map_chrome_css() -> str:
    """Cream/ink chrome to match the newspaper redesign + shared tooltip classes."""
    return """
<style>
/* Hide leaflet attribution — sources documented in the explainer notebook. */
.leaflet-control-attribution { display: none !important; }

/* Match Leaflet's empty-tile background to the page so noWrap pillarboxing
   reads as cream rather than grey. */
.leaflet-container { background: #f7f4ee !important; }

/* Native leaflet bar (zoom + fullscreen) — square, paper backdrop, ink rule */
.leaflet-bar {
  box-shadow: 0 2px 0 rgba(20, 17, 13, 0.18) !important;
  border: none !important;
  border-radius: 0 !important;
}
.leaflet-bar a {
  background-color: rgba(247, 244, 238, 0.96) !important;
  border: 1px solid rgba(20, 17, 13, 0.35) !important;
  border-bottom-width: 0 !important;
  color: #1A1A1A !important;
  border-radius: 0 !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: geometricPrecision;
}
.leaflet-bar a:last-child { border-bottom-width: 1px !important; }
.leaflet-bar a:hover {
  background-color: #0F3D5C !important;
  color: #F7F4EE !important;
}

/* Zoom + / − — crisp text glyphs at the right size */
.leaflet-control-zoom a {
  font-size: 20px !important;
  font-weight: 400 !important;
  line-height: 26px !important;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Fullscreen — keep the dark sprite (it's already ink on transparent) */
.leaflet-control-fullscreen a:hover {
  filter: invert(1) brightness(2);
}

/* Square scale bar — paper backdrop, ink rule */
.leaflet-control-scale-line {
  background: rgba(247, 244, 238, 0.94) !important;
  border: 1px solid rgba(20, 17, 13, 0.35) !important;
  border-top: none !important;
  border-radius: 0 !important;
  color: #1A1A1A !important;
  font-family: 'Lato', sans-serif !important;
  font-size: 10px !important;
  font-weight: 600 !important;
  letter-spacing: 0.16em !important;
  text-transform: uppercase;
  padding: 1px 8px !important;
  text-shadow: none !important;
}

/* Custom scroll-zoom toggle button */
.sw-toggle a {
  font-family: 'Lato', sans-serif !important;
  font-size: 10px !important;
  font-weight: 700 !important;
  letter-spacing: 0.16em !important;
  text-decoration: none !important;
  width: auto !important;
  padding: 0 11px !important;
  height: 26px !important;
  line-height: 26px !important;
  text-transform: uppercase;
  border-bottom-width: 1px !important;
}
.sw-toggle a.is-active {
  background-color: #0F3D5C !important;
  color: #F7F4EE !important;
  border-color: #0F3D5C !important;
}
.sw-toggle a.is-active:hover {
  background-color: #0A2D44 !important;
}

/* ── Shared tooltip classes (replace per-marker inline styles) ─────── */
.leaflet-tooltip.tt-wrap {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  padding: 0 !important;
  white-space: normal !important;
}
.leaflet-tooltip.tt-wrap::before { display: none !important; }
.tt {
  font-family: 'Lato', -apple-system, sans-serif;
  min-width: 200px; max-width: 280px;
  background: #0D1B2A; color: #F0EDE5;
  padding: 10px 12px; border-radius: 6px;
  word-wrap: break-word; white-space: normal;
  box-shadow: 0 6px 18px rgba(0,0,0,0.25);
}
.tt-title { font-size: 13px; font-weight: 600; margin-bottom: 6px; }
.tt-row {
  border-top: 1px solid rgba(255,255,255,0.12);
  padding: 4px 0;
}
.tt-row:first-of-type { border-top: 0; }
.tt-label {
  color: #888; font-size: 10px; letter-spacing: .3px;
  text-transform: uppercase;
}
.tt-val { color: #F0EDE5; margin-top: 1px; }
.tt-note {
  color: #bbb; font-size: 10px; font-style: italic;
  line-height: 1.4; margin-top: 2px;
}
.tt-warn { color: #FFD700; font-size: 10px; margin-top: 4px; }
.tt-source { color: #555; font-size: 9px; margin-top: 6px; }
.tt-pill {
  display: inline-block;
  background: rgba(160,120,80,0.25);
  border: 1px solid #A07850;
  border-radius: 3px; padding: 1px 5px;
  font-size: 10px; margin: 1px 2px 1px 0;
}
.tt-mine-light {
  background: #F7F4EE !important; color: #1A1A1A !important;
  min-width: 240px; max-width: 320px;
}
.tt-mine-light .tt-row { border-top: 1px solid rgba(20,17,13,0.15); }
.tt-mine-light .tt-label { color: #777; }
.tt-mine-light .tt-val { color: #1A1A1A; }
.tt-mine-light .tt-note { color: #444; font-style: normal; line-height: 1.5; font-size: 11px; }
.tt-mine-light .tt-source { color: #888; }
.tt-status-active { color: #1f8f4a; }
.tt-status-past { color: #c25a13; }
</style>
"""


def _control_panel_html(specs: list, map_var: str) -> str:
    """Custom layer-toggle panel — replaces folium.LayerControl with a themed UI."""
    titles = {
        "case1":  "Case 1 — Abundant",
        "case2":  "Case 2 — Scarce",
        "ree":    "Rare Earth Elements",
        "extras": "Layers",
    }
    groups: dict[str, list[str]] = {}
    for label, fg, color, group, default_on in specs:
        is_heatmap = label.lower().startswith("density")
        dot = (
            f"<span class='mcp-dot' style='background:{color}'></span>"
            if color else "<span class='mcp-dot mcp-dot-grad'></span>"
        )
        checked = "checked" if default_on else ""
        role_attr = " data-role='heatmap'" if is_heatmap else ""
        groups.setdefault(group, []).append(
            f"<label class='mcp-row'>"
            f"<input type='checkbox' data-layer='{fg.get_name()}'{role_attr} {checked}>"
            f"{dot}<span class='mcp-label'>{label}</span></label>"
        )

    sections = "".join(
        f"<div class='mcp-section'><div class='mcp-title'>{titles[g]}</div>{''.join(rows)}</div>"
        for g, rows in groups.items() if g in titles
    )

    style_block = """
<style>
.mcp-panel {
  position: absolute; top: 16px; right: 16px; z-index: 1000;
  background: rgba(247, 244, 238, 0.96);
  border: 1px solid rgba(20, 17, 13, 0.35);
  border-radius: 0;
  font-family: 'Lato', -apple-system, sans-serif;
  font-size: 11.5px;
  color: #1A1A1A;
  min-width: 220px;
  max-height: calc(100% - 32px);
  overflow: hidden;
  box-shadow: 0 2px 0 rgba(20, 17, 13, 0.18);
}
.mcp-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 14px; cursor: pointer; user-select: none;
  background: transparent;
  border-bottom: 1px solid rgba(20, 17, 13, 0.18);
}
.mcp-header:hover { background: rgba(15, 61, 92, 0.10); }
.mcp-header-title {
  font-family: 'Playfair Display', Georgia, serif;
  font-style: italic; font-weight: 600;
  font-size: 12px; letter-spacing: 0.04em;
  color: #0F3D5C; text-transform: none;
}
.mcp-chevron {
  width: 7px; height: 7px;
  border-right: 1.5px solid #0F3D5C;
  border-bottom: 1.5px solid #0F3D5C;
  transform: rotate(45deg); transition: transform 0.2s ease;
  margin-top: -3px;
}
.mcp-collapsed .mcp-chevron { transform: rotate(-45deg); margin-top: 1px; }
.mcp-body { padding: 10px 14px 10px; max-height: calc(80vh - 40px); overflow-y: auto; }
.mcp-collapsed .mcp-body { display: none; }
.mcp-section + .mcp-section {
  margin-top: 9px; padding-top: 8px;
  border-top: 1px solid rgba(20, 17, 13, 0.10);
}
.mcp-title {
  font-family: 'Lato', sans-serif;
  font-weight: 700; font-size: 9.5px; letter-spacing: 0.16em;
  color: #0F3D5C; text-transform: uppercase;
  margin-bottom: 6px;
}
.mcp-row {
  display: flex; align-items: center; padding: 3px 0;
  cursor: pointer; user-select: none;
  transition: opacity 0.15s ease;
}
.mcp-row:hover .mcp-label { color: #14110D; }
.mcp-row input[type=checkbox] {
  appearance: none; -webkit-appearance: none;
  width: 12px; height: 12px;
  border: 1px solid rgba(20, 17, 13, 0.45);
  border-radius: 0;
  margin: 0 9px 0 0;
  cursor: pointer; position: relative;
  background: transparent; flex-shrink: 0;
  transition: all 0.15s ease;
}
.mcp-row input[type=checkbox]:checked {
  background: #0F3D5C; border-color: #0F3D5C;
}
.mcp-row input[type=checkbox]:checked::after {
  content: ''; position: absolute;
  left: 3px; top: -1px;
  width: 4px; height: 8px;
  border: solid #F7F4EE;
  border-width: 0 2px 2px 0;
  transform: rotate(45deg);
}
.mcp-dot {
  display: inline-block; width: 8px; height: 8px;
  border-radius: 50%; margin-right: 6px; flex-shrink: 0;
}
.mcp-dot-grad {
  background: linear-gradient(135deg, #B8C9D6 0%, #5C8AA6 35%, #0F3D5C 70%, #7B2D26 100%);
}
.mcp-label { flex: 1; transition: color 0.15s ease; line-height: 1.3; }
</style>
"""

    js = f"""
<script>
(function() {{
    function bindMcp() {{
        var map = {map_var};
        if (!map) {{ setTimeout(bindMcp, 50); return; }}
        var checkboxes = document.querySelectorAll('#mcp-panel input[type=checkbox]');

        function bringDotsToFront() {{
            // After heatmap toggle, push dot/marker layers above heatmap canvas.
            checkboxes.forEach(function(cb) {{
                if (cb.dataset.role === 'heatmap') return;
                var l = window[cb.getAttribute('data-layer')];
                if (l && map.hasLayer(l)) {{
                    if (typeof l.bringToFront === 'function') l.bringToFront();
                    if (typeof l.eachLayer === 'function') {{
                        l.eachLayer(function(c) {{
                            if (c && typeof c.bringToFront === 'function') c.bringToFront();
                        }});
                    }}
                }}
            }});
        }}

        checkboxes.forEach(function(cb) {{
            var name = cb.getAttribute('data-layer');
            var layer = window[name];
            if (!layer) return;
            // Sync initial state to checkbox
            if (cb.checked && !map.hasLayer(layer)) map.addLayer(layer);
            if (!cb.checked && map.hasLayer(layer)) map.removeLayer(layer);
            cb.addEventListener('change', function() {{
                if (cb.checked) map.addLayer(layer);
                else map.removeLayer(layer);
                // Heatmap can mask dots — re-elevate them after any change.
                bringDotsToFront();
            }});
        }});

        // Initial pass once everything is wired up.
        bringDotsToFront();
    }}
    if (document.readyState === 'complete') bindMcp();
    else window.addEventListener('load', bindMcp);
}})();
</script>
"""
    panel_html = (
        f"<div id='mcp-panel' class='mcp-panel mcp-collapsed'>"
        f"<div class='mcp-header' onclick=\"this.parentElement.classList.toggle('mcp-collapsed')\">"
        f"<span class='mcp-header-title'>Layers</span>"
        f"<span class='mcp-chevron'></span>"
        f"</div>"
        f"<div class='mcp-body'>{sections}</div>"
        f"</div>"
    )
    return f"<div>{style_block}{panel_html}{js}</div>"


def build_deposit_map(deposits: gpd.GeoDataFrame) -> Path:
    deposits = deposits.dropna(subset=["latitude", "longitude"]).copy()

    # ── Split REE vs non-REE ────────────────────────────────────
    ree_mask = deposits["mineral"].isin(REE_MINERALS)
    non_ree = deposits[~ree_mask].copy()

    # ── Aggregate REE: one row per unique lat/lon ────────────────
    ree_raw = deposits[ree_mask].copy()

    def _clean_str_set(vals):
        return sorted({str(v).strip() for v in vals if not _nan(v) and str(v).strip() not in ("nan", "None")})

    def _agg_ree_subgroup(vals):
        clean = _clean_str_set(vals)
        return "/".join(clean) if clean else None

    def _agg_minerals(vals):
        order = ["Neodymium", "Dysprosium", "Terbium"]
        present = sorted({v for v in vals if v in order}, key=order.index)
        return ", ".join(present)

    def _agg_first_nonnull(vals):
        for v in vals:
            if not _nan(v):
                return str(v).strip()
        return None

    def _best_production_status(vals):
        # Pick the most active status across rows (all rows same deposit → same value)
        priority = ["Producer", "Byproduct producer", "Producer(?)", "Byproduct producer(?)",
                    "Past producer", "Past byproduct producer", "Past byproduct producer(?)",
                    "No production", "No production(?)", "Not known"]
        clean = _clean_str_set(vals)
        for p in priority:
            if p in clean:
                return p
        return clean[0] if clean else None

    ree_agg = (
        ree_raw.groupby(["latitude", "longitude"])
        .agg(
            deposit_name=("deposit_name", _agg_first_nonnull),
            deposit_type=("deposit_type", _agg_first_nonnull),
            deposit_status=("deposit_status", _agg_first_nonnull),
            production_status=("production_status", _best_production_status),
            country=("country", _agg_first_nonnull),
            location_detail=("location_detail", _agg_first_nonnull),
            source=("source", _agg_first_nonnull),
            ree_subgroup=("ree_subgroup", _agg_ree_subgroup),
            minerals_at_deposit=("mineral", _agg_minerals),
            host_lithology=("host_lithology", _agg_first_nonnull),
            ore_minerals=("ore_minerals", _agg_first_nonnull),
            significant_minerals=("significant_minerals", _agg_first_nonnull),
            commodities=("commodities", _agg_first_nonnull),
        )
        .reset_index()
    )
    ree_agg["mineral"] = "Rare Earths"

    # ── REE layer routing ────────────────────────────────────────
    def _ree_is_active(ps: object) -> bool:
        if _nan(ps):
            return False
        ps_l = str(ps).lower()
        return "producer" in ps_l and "past" not in ps_l

    def _ree_is_known_deposit(row) -> bool:
        ds = getattr(row, "deposit_status", None)
        ps = getattr(row, "production_status", None)
        if _ree_is_active(ps):
            return False
        return not _nan(ds) and "deposit" in str(ds).lower()

    def _ree_is_prospective(row) -> bool:
        ds = getattr(row, "deposit_status", None)
        if _nan(ds):
            return True
        ds_l = str(ds).lower()
        return "occurrence" in ds_l or "showing" in ds_l

    # ── Map setup ───────────────────────────────────────────────
    # noWrap on the tile layer + maxBounds on the map prevents the world from
    # tiling horizontally on ultrawide viewports.
    fmap = folium.Map(
        location=[20, 10],
        zoom_start=3,
        min_zoom=3,
        max_bounds=True,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
        scrollWheelZoom=False,
    )
    folium.TileLayer(
        "CartoDB positron",
        no_wrap=True,
        control=False,
    ).add_to(fmap)
    Fullscreen(position="topleft").add_to(fmap)

    # Per-mineral FeatureGroups (shown by default)
    mineral_fgs = {m: folium.FeatureGroup(name=m, show=True) for m in MAP_MINERAL_ORDER}
    ree_fg = folium.FeatureGroup(name="Rare Earth Elements", show=True)
    # Hidden layers
    known_deposits_fg = folium.FeatureGroup(name="Confirmed Reserves — unmined (REE)", show=False)
    prospective_fg = folium.FeatureGroup(name="Exploration Targets — unconfirmed (REE)", show=False)
    prospects_metals_fg = folium.FeatureGroup(name="Exploration Targets (metals)", show=False)
    heatmap_fg = folium.FeatureGroup(name="Density heatmap", show=True)

    _ACTIVE_STATUSES = {"producer", "plant"}

    # ── Non-REE: route by deposit status ─────────────────────────
    for row in non_ree.itertuples(index=False):
        mineral = getattr(row, "mineral", "")
        color = mineral_color(mineral)
        ps = getattr(row, "production_status", None)
        ds = getattr(row, "deposit_status", None)
        ds_lower = str(ds).lower().strip() if ds else ""
        radius, opacity = _deposit_style(ps, ds)
        marker = folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=opacity,
            weight=0.8,
            tooltip=folium.Tooltip(_tooltip_non_ree(row), sticky=True, class_name="tt-wrap"),
        )
        if ds_lower in _ACTIVE_STATUSES or ds_lower in ("deposit", "centroid"):
            # PP1802 deposits, centroids, and active MRDS producers → default shown layer
            marker.add_to(mineral_fgs.get(mineral, ree_fg))
        else:
            # Prospect, Occurrence, Unknown
            marker.add_to(prospects_metals_fg)

    # ── REE: route by production status ─────────────────────────
    for row in ree_agg.itertuples(index=False):
        ps = getattr(row, "production_status", None)
        ds = getattr(row, "deposit_status", None)
        radius, opacity = _deposit_style(ps, ds)
        marker = folium.CircleMarker(
            location=[row.latitude, row.longitude],
            radius=radius,
            color=REE_COLOR,
            fill=True,
            fill_color=REE_COLOR,
            fill_opacity=opacity,
            weight=0.8,
            tooltip=folium.Tooltip(_tooltip_ree(row), sticky=True, class_name="tt-wrap"),
        )
        if _ree_is_active(ps):
            marker.add_to(ree_fg)
        elif _ree_is_known_deposit(row):
            marker.add_to(known_deposits_fg)
        else:
            marker.add_to(prospective_fg)

    # ── Density heatmap added FIRST so it sits beneath the dot layers ──
    heat_points = deposits[["latitude", "longitude"]].dropna().values.tolist()
    heat_layer = HeatMap(
        heat_points,
        radius=14,
        blur=22,
        min_opacity=0.22,
        max_zoom=6,
        gradient={0.35: "#B8C9D6", 0.55: "#5C8AA6", 0.75: "#0F3D5C", 0.9: "#7B2D26", 1.0: "#14110D"},
    )
    heat_layer.add_to(heatmap_fg)
    heatmap_fg.add_to(fmap)

    # Add dot layers AFTER heatmap so they render on top in the canvas pane
    for fg in mineral_fgs.values():
        fg.add_to(fmap)
    ree_fg.add_to(fmap)
    prospects_metals_fg.add_to(fmap)

    # ── Landmark mines ───────────────────────────────────────────
    landmarks_fg = folium.FeatureGroup(name="&#9733; Landmark Mines", show=True)
    for mine in LANDMARK_MINES:
        star_color = REE_COLOR if mine["mineral"] in REE_MINERALS else mineral_color(mine["mineral"])
        icon_html = (
            f"<div style='font-size:20px;color:{star_color};"
            f"text-shadow:0 0 5px #000,0 0 3px #000;line-height:1;cursor:pointer'>&#9733;</div>"
        )
        status_cls = "tt-status-active" if mine["status"].lower().startswith("active") else "tt-status-past"
        status_html = f"<span class='{status_cls}'>{mine['status']}</span>"

        tip_html = (
            f"<div class='tt tt-mine-light'>"
            f"<div class='tt-title' style='color:{star_color}'>&#9733; {mine['name']}</div>"
            + _row("Mineral", mine["mineral"])
            + _row("Country", mine["country"])
            + _row("Operator", mine["operator"])
            + _row("Status", status_html)
            + _row("Deposit type", mine["deposit_type"])
            + _row("Global scale", mine["scale"])
            + _row("Specs", mine["specs"])
            + f"<div class='tt-row tt-note'>{mine['note']}</div>"
            + "</div>"
        )
        folium.Marker(
            location=[mine["lat"], mine["lon"]],
            icon=folium.DivIcon(html=icon_html, icon_size=(22, 22), icon_anchor=(11, 11)),
            tooltip=folium.Tooltip(tip_html, sticky=True, class_name="tt-wrap"),
        ).add_to(landmarks_fg)
    landmarks_fg.add_to(fmap)
    known_deposits_fg.add_to(fmap)
    prospective_fg.add_to(fmap)

    # ── Custom layer-toggle panel (replaces folium LayerControl) ─
    panel_specs = [
        ("Copper",     mineral_fgs["Copper"],   mineral_color("Copper"),   "case1", True),
        ("Lithium",    mineral_fgs["Lithium"],  mineral_color("Lithium"),  "case1", True),
        ("Graphite",   mineral_fgs["Graphite"], mineral_color("Graphite"), "case1", True),
        ("Cobalt",     mineral_fgs["Cobalt"],   mineral_color("Cobalt"),   "case2", True),
        ("Gallium",    mineral_fgs["Gallium"],  mineral_color("Gallium"),  "case2", True),
        ("Platinum",   mineral_fgs["Platinum"], mineral_color("Platinum"), "case2", True),
        ("Rare Earths (active)",     ree_fg,           REE_COLOR, "ree", True),
        ("Confirmed reserves (REE)", known_deposits_fg, REE_COLOR, "ree", False),
        ("Exploration targets (REE)", prospective_fg,   REE_COLOR, "ree", False),
        ("Landmark mines",            landmarks_fg,    "#0F3D5C", "extras", True),
        ("Exploration targets (metals)", prospects_metals_fg, "#888888", "extras", False),
        ("Density heatmap",           heatmap_fg,       None,     "extras", True),
    ]
    fig = Figure(width="100%", height="600px")
    fig.add_child(fmap)
    fig.header.add_child(Element(_control_panel_html(panel_specs, fmap.get_name())))
    fig.header.add_child(Element(_legend_html()))
    fig.header.add_child(Element(_zoom_radius_js(fmap.get_name())))
    fig.header.add_child(Element(_heatmap_cap_js(fmap.get_name(), heat_layer.get_name(), 500)))
    fig.header.add_child(Element(_scroll_zoom_toggle_js(fmap.get_name())))
    fig.header.add_child(Element(_map_chrome_css()))
    fig.add_child(Element(_landmark_table_html()))

    path = VIS_ROOT / "deposits" / "deposit_map.html"
    fig.save(str(path))
    return path


def build_slope_chart(trade: pd.DataFrame) -> Path:
    stage_shares = trade[trade["record_type"] == "stage_share"].copy()
    stage_shares = stage_shares[
        stage_shares["mineral"].isin(CASE1_MINERALS)
        & stage_shares["stage"].isin(["mining", "processing"])
        & (stage_shares["country"] != "Other")
    ].copy()

    rows = []
    for mineral, group in stage_shares.groupby("mineral"):
        ranked = (
            group.groupby("country")["share_pct"].max().sort_values(ascending=False).head(4)
        )
        keep = group[group["country"].isin(ranked.index)].copy()
        rows.append(keep)
    slope = pd.concat(rows, ignore_index=True)
    slope["stage"] = pd.Categorical(slope["stage"], ["mining", "processing"], ordered=True)

    fig = px.line(
        slope.sort_values(["mineral", "country", "stage"]),
        x="stage",
        y="share_pct",
        color="country",
        line_group="country",
        facet_col="mineral",
        facet_col_wrap=2,
        markers=True,
        category_orders={"stage": ["mining", "processing"]},
        title="Case 1: Mining vs Processing Leadership",
        color_discrete_map={name: country_color(name) for name in slope["country"].unique()},
        hover_data=["mineral"],
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=9))
    apply_theme(fig)
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="Share of global stage (%)",
        legend_title_text=None,
    )
    fig.for_each_annotation(lambda ann: ann.update(text=ann.text.split("=")[-1]))

    path = VIS_ROOT / "supply-chain" / "slope_chart.html"
    write_plotly(fig, path)
    return path


def build_production_history(economic: pd.DataFrame) -> Path:
    """5.2 - World mine production 1900-2024, focal materials, linear y.

    Lithium has three categories from 2000+ (gross weight, LCE, lithium content);
    we pin to "gross weight" for a continuous 1925-2021 series and skip the MCS
    stitch (2024 MCS reports lithium content - different unit basis).
    Cobalt has both mine and refinery series; we pin to mine production.
    """
    src = economic[
        (economic["metric"] == "world_production_tonnes")
        & (economic["country"] == "World")
        & (economic["mineral"].isin(TARGET_MINERALS))
    ].copy()

    # Pin Lithium to "gross weight" (the only category that runs 1925-2021)
    li_mask = src["mineral"] == "Lithium"
    src = src[~li_mask | (src["category"] == "World production (gross weight)")]

    # Pin Cobalt to mine production (drop the refinery-production duplicate)
    co_mask = src["mineral"] == "Cobalt"
    src = src[~co_mask | (src["category"] == "World mine production")]

    hist = src[["mineral", "year", "value"]].copy()

    # MCS 2024 stitch where unit basis matches historical:
    # - Lithium: SKIP (MCS reports lithium content, historical is gross weight)
    # - All others: stitch
    SKIP_MCS_STITCH = {"Lithium"}

    est = economic[economic["metric"] == "mine_production_tonnes_estimate"].copy()
    if not est.empty:
        est_world = est.groupby(["mineral", "year"], as_index=False)["value"].sum()
        for _, r in est_world.iterrows():
            mineral = r["mineral"]
            if mineral not in TARGET_MINERALS or mineral in SKIP_MCS_STITCH:
                continue
            hist_last = hist[hist["mineral"] == mineral]["year"].max()
            if pd.notna(hist_last) and r["year"] > hist_last:
                hist = pd.concat(
                    [hist, pd.DataFrame([{"mineral": mineral, "year": int(r["year"]), "value": r["value"]}])],
                    ignore_index=True,
                )

    hist = hist[hist["value"] > 0].sort_values(["mineral", "year"])

    # Drop any mineral that has fewer than 5 data points - they would clutter the legend
    counts = hist.groupby("mineral").size()
    keep_minerals = counts[counts >= 5].index.tolist()
    hist = hist[hist["mineral"].isin(keep_minerals)]

    latest_year = int(hist["year"].max())

    # Order traces by 2020 production so the legend reads top-to-bottom
    order = (
        hist[hist["year"] == 2020]
        .sort_values("value", ascending=False)["mineral"]
        .tolist()
    )
    remaining = [m for m in TARGET_MINERALS if m not in order]
    legend_order = order + remaining

    fig = go.Figure()
    for mineral in legend_order:
        sub = hist[hist["mineral"] == mineral]
        if sub.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=sub["year"],
                y=sub["value"],
                mode="lines",
                name=mineral,
                line=dict(width=3, color=MINERAL_COLORS.get(mineral)),
                hovertemplate=(
                    f"<b>{mineral}</b><br>%{{x}} · %{{y:,.0f}} t<extra></extra>"
                ),
            )
        )

    fig.add_vrect(
        x0=1995,
        x1=latest_year,
        fillcolor="rgba(15, 61, 92, 0.06)",
        line_width=0,
        layer="below",
    )

    apply_theme(fig)
    fig.update_layout(
        title=dict(
            text=(
                "<b>A Hundred-Fold Industrial Expansion</b>"
                f"<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                f"World annual mine production 1900–{latest_year}, log scale, metric tonnes</span>"
            ),
        ),
        xaxis=dict(title=dict(text="<b>Year</b>"), range=[1900, latest_year]),
        yaxis=dict(
            type="log",
            title=dict(text="Tonnes (log scale)"),
        ),
        legend=dict(
            orientation="h",
            yanchor="top", y=1.06,
            xanchor="right", x=1.0,
        ),
        legend_title_text=None,
        margin=dict(l=80, r=40, t=170, b=110),
    )

    path = VIS_ROOT / "stakes" / "production_history.html"
    write_plotly(fig, path)
    return path


def build_production_series(economic: pd.DataFrame) -> Path:
    prod = economic[
        (economic["metric"] == "world_production_tonnes")
        & (economic["country"] == "World")
        & (economic["mineral"].isin(CASE1_MINERALS))
        & (economic["year"] >= 2000)
    ].copy()

    fig = px.line(
        prod,
        x="year",
        y="value",
        color="mineral",
        color_discrete_map=MINERAL_COLORS,
        title="Case 1 Production Has Scaled, Even as Processing Stayed Concentrated",
    )
    fig.update_traces(mode="lines", line=dict(width=3))
    apply_theme(fig)
    fig.update_layout(
        xaxis_title=None,
        yaxis_title="World production (metric tonnes)",
        legend_title_text=None,
    )

    path = VIS_ROOT / "supply-chain" / "production_series.html"
    write_plotly(fig, path)
    return path


CAROUSEL_MINERALS = [
    "Cobalt",
    "Lithium",
    "Graphite",
    "Copper",
    "Platinum",
    "Gallium",
    "Rare Earths",
]


def _sankey_for_mineral(trade: pd.DataFrame, mineral: str) -> go.Figure:
    """Return a 2-stage (mining -> processing) Sankey for one mineral, 2023."""
    sub = trade[
        (trade["record_type"] == "stage_share")
        & (trade["mineral"] == mineral)
        & (trade["year"] == 2023)
        & (trade["stage"].isin(["mining", "processing"]))
    ].copy()
    mining = sub[sub["stage"] == "mining"].sort_values("share_pct", ascending=False)
    processing = sub[sub["stage"] == "processing"].sort_values("share_pct", ascending=False)

    # Drop zero-share rows (countries listed for context with no flow).
    mining = mining[mining["share_pct"] > 0]
    processing = processing[processing["share_pct"] > 0]

    # The middle bridge nodes carry no label — the carousel card header
    # already names the mineral, and the stages read from left = mining,
    # right = processing. An explainer in the section intro covers that.
    mining_label = ""
    processing_label = ""

    # Abbreviate long country names so Sankey labels don't bleed into the
    # bridge bars. Plotly draws node labels to the right of the node and
    # the full DRC / Russian Federation strings overlap the middle stage.
    _SHORT_COUNTRY = {
        "Democratic Republic of the Congo": "DR Congo",
        "Russian Federation": "Russia",
        "Korea, Republic of": "South Korea",
        "Korea, Rep.": "South Korea",
        "United States of America": "USA",
        "United States": "USA",
        "United Kingdom": "UK",
        "Saudi Arabia": "Saudi Arabia",
        "South Africa": "S. Africa",
    }
    def _short(name: str) -> str:
        return _SHORT_COUNTRY.get(name, name)

    node_labels = (
        [_short(c) for c in mining["country"]]
        + [mining_label, processing_label]
        + [_short(c) for c in processing["country"]]
    )
    node_colors = (
        [country_color(name) for name in mining["country"]]
        + ["#5C5C5C", "#8B5A2B"]
        + [country_color(name) for name in processing["country"]]
    )

    mining_stage_idx = len(mining)
    processing_stage_idx = len(mining) + 1

    sources = (
        list(range(len(mining)))
        + [mining_stage_idx]
        + [processing_stage_idx] * len(processing)
    )
    targets = (
        [mining_stage_idx] * len(mining)
        + [processing_stage_idx]
        + list(range(processing_stage_idx + 1, processing_stage_idx + 1 + len(processing)))
    )
    values = (
        list(mining["share_pct"])
        + [float(mining["share_pct"].sum())]
        + list(processing["share_pct"])
    )

    fig = go.Figure(
        go.Sankey(
            arrangement="snap",
            node=dict(
                pad=20,
                thickness=18,
                line=dict(color="rgba(20,17,13,0.15)", width=1),
                label=node_labels,
                color=node_colors,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color="rgba(15, 61, 92, 0.35)",
            ),
        )
    )
    apply_theme(fig)
    # Inner title intentionally omitted - the carousel card header already
    # shows the mineral name + hook, so a duplicate inside the iframe reads
    # as visual repetition.
    fig.update_layout(
        title=None,
        margin=dict(l=40, r=40, t=30, b=40),
    )
    return fig


def build_sankey_carousel(trade: pd.DataFrame) -> dict[str, Path]:
    """5.3 - Build seven per-material 2-stage Sankeys for the carousel."""
    paths: dict[str, Path] = {}
    for mineral in CAROUSEL_MINERALS:
        fig = _sankey_for_mineral(trade, mineral)
        slug = mineral.lower().replace(" ", "_")
        path = VIS_ROOT / "supply-chain" / f"sankey_{slug}.html"
        write_plotly(fig, path)
        paths[slug] = path
    return paths


EU27_MEMBERS = {"Belgium", "Finland", "Germany"}  # only EU-27 nodes in stage_share
EU27_LABEL = "EU-27"


def _eu27_collapse(country: str) -> str:
    return EU27_LABEL if country in EU27_MEMBERS else country


OTHER_COUNTRIES_LABEL = "Other countries"
TOP_N_COUNTRIES = 10


def _topn_with_other(
    totals: dict[str, float], n: int
) -> tuple[list[str], set[str]]:
    """Return (top_n_named_countries_in_rank_order, set_of_pooled_residuals).

    The dataset's existing "Other" bucket is always pooled into the residual.
    Anything outside the top-n named countries is also pooled. The
    "Other countries" label is used for the displayed bucket node.
    """
    named = {c: v for c, v in totals.items() if c != "Other"}
    ranked = sorted(named.items(), key=lambda kv: -kv[1])
    top = [c for c, _ in ranked[:n]]
    pooled = {c for c, _ in ranked[n:]} | {"Other"} if "Other" in totals else {c for c, _ in ranked[n:]}
    return top, pooled


def build_master_sankey(trade: pd.DataFrame) -> Path:
    """5.5 - All-material chokepoint Sankey, locked layout.

    Three columns, fixed positions (Plotly arrangement="fixed", explicit
    node.x and node.y so nodes do not drift):

      Left   - top 10 mining countries (+ "Other countries" residual)
      Centre - 7 material trunks
      Right  - top 10 processing countries (after EU-27 grouping)
               (+ "Other countries" residual)

    Two real flows from the dataset - no synthesised joint distribution:
      - mining country -> material   (the material's mining-country share)
      - material -> processing country (the material's processing-country share)

    Each material contributes 100 units of flow on each side, so the canvas
    reads as control concentration. The China processing node will visibly
    carry the bulk of the right-hand fan; that's the headline.
    """
    rows = trade[
        (trade["record_type"] == "stage_share")
        & (trade["mineral"].isin(CAROUSEL_MINERALS))
        & (trade["year"] == 2023)
        & (trade["stage"].isin(["mining", "processing"]))
        & (trade["share_pct"] > 0)
    ].copy()

    # EU-27 collapse on processing side only (mining side has no EU members)
    rows.loc[rows["stage"] == "processing", "country"] = (
        rows.loc[rows["stage"] == "processing", "country"].apply(_eu27_collapse)
    )

    # --- Aggregate per material per stage, normalised to 100 per material ---
    mining_per_material: dict[str, list[tuple[str, float]]] = {}
    processing_per_material: dict[str, list[tuple[str, float]]] = {}
    for mineral in CAROUSEL_MINERALS:
        for stage, target in (("mining", mining_per_material), ("processing", processing_per_material)):
            agg = (
                rows[(rows["mineral"] == mineral) & (rows["stage"] == stage)]
                .groupby("country", as_index=False)["share_pct"].sum()
            )
            total = agg["share_pct"].sum()
            if total > 0:
                target[mineral] = [
                    (r.country, r.share_pct / total * 100.0) for r in agg.itertuples()
                ]

    # --- Cross-material totals to pick top-N per side ---
    def _total(per_material: dict[str, list[tuple[str, float]]]) -> dict[str, float]:
        out: dict[str, float] = {}
        for lst in per_material.values():
            for c, v in lst:
                out[c] = out.get(c, 0.0) + v
        return out

    mining_total = _total(mining_per_material)
    processing_total = _total(processing_per_material)

    mining_top, mining_pooled = _topn_with_other(mining_total, TOP_N_COUNTRIES)
    processing_top, processing_pooled = _topn_with_other(processing_total, TOP_N_COUNTRIES)

    def _resolve(country: str, pooled: set[str]) -> str:
        return OTHER_COUNTRIES_LABEL if country in pooled else country

    # Re-aggregate flows per material, applying the residual pool
    def _apply_pool(
        per_material: dict[str, list[tuple[str, float]]],
        pooled: set[str],
    ) -> dict[str, list[tuple[str, float]]]:
        out: dict[str, list[tuple[str, float]]] = {}
        for mineral, lst in per_material.items():
            agg: dict[str, float] = {}
            for country, val in lst:
                key = _resolve(country, pooled)
                agg[key] = agg.get(key, 0.0) + val
            out[mineral] = list(agg.items())
        return out

    mining_per_material = _apply_pool(mining_per_material, mining_pooled)
    processing_per_material = _apply_pool(processing_per_material, processing_pooled)

    # --- Build node lists in fixed column order ---
    # Left: top-N mining (rank-ordered) + "Other countries" at bottom
    left_nodes = list(mining_top)
    if any(country == OTHER_COUNTRIES_LABEL for lst in mining_per_material.values() for country, _ in lst):
        left_nodes.append(OTHER_COUNTRIES_LABEL)

    # Centre: material trunks
    centre_nodes = list(CAROUSEL_MINERALS)

    # Right: China pinned to top, then rest by rank, "Other countries" at bottom
    right_nodes = [c for c in processing_top if c != "China"]
    right_nodes.sort(key=lambda c: -processing_total.get(c, 0))
    if "China" in processing_top:
        right_nodes = ["China"] + right_nodes
    if any(country == OTHER_COUNTRIES_LABEL for lst in processing_per_material.values() for country, _ in lst):
        right_nodes.append(OTHER_COUNTRIES_LABEL)

    node_labels = left_nodes + centre_nodes + right_nodes

    # --- Compute total flow per node so y stacking respects node heights ---
    # Each material contributes 100 units on each side, so the left column
    # and right column each total ~ 7 * 100 = 700. Sort each column's nodes
    # by total flow descending; place node centres at the midpoint of their
    # cumulative vertical range so that no node visually overlaps its neighbour.
    def _column_flows(nodes: list[str], totals: dict[str, float], side_total_dict: dict[str, list[tuple[str, float]]] | None = None) -> list[float]:
        return [totals.get(node, 0.0) for node in nodes]

    # Re-derive aggregated totals for the displayed nodes (post-pooling)
    left_totals: dict[str, float] = {n: 0.0 for n in left_nodes}
    for lst in mining_per_material.values():
        for c, v in lst:
            if c in left_totals:
                left_totals[c] += v

    right_totals: dict[str, float] = {n: 0.0 for n in right_nodes}
    for lst in processing_per_material.values():
        for c, v in lst:
            if c in right_totals:
                right_totals[c] += v

    centre_totals: dict[str, float] = {m: 100.0 for m in centre_nodes}

    def _cumulative_centres(flows: list[float], top: float = 0.03, bottom: float = 0.97, gap: float = 0.012) -> list[float]:
        """Return the centre-y of each node given flow magnitudes.

        Nodes are stacked top-to-bottom in order; each node's vertical extent
        is proportional to its flow share of the column total. A small gap
        is left between consecutive nodes for visual separation.
        """
        n = len(flows)
        if n == 0:
            return []
        total = sum(flows)
        if total <= 0:
            return [0.5] * n
        gap_total = gap * (n - 1) if n > 1 else 0.0
        usable = max(bottom - top - gap_total, 0.05)
        cursor = top
        centres: list[float] = []
        for f in flows:
            height = f / total * usable
            centres.append(cursor + height / 2)
            cursor += height + gap
        return centres

    left_y = _cumulative_centres([left_totals[n] for n in left_nodes])
    centre_y = _cumulative_centres([centre_totals[n] for n in centre_nodes])
    right_y = _cumulative_centres([right_totals[n] for n in right_nodes])

    node_x: list[float] = []
    node_y: list[float] = []
    for ys, x in ((left_y, 0.001), (centre_y, 0.5), (right_y, 0.999)):
        for y in ys:
            node_x.append(x)
            node_y.append(y)

    def _node_color(label: str) -> str:
        if label in CAROUSEL_MINERALS:
            return MINERAL_COLORS.get(label, "#5C5C5C")
        if label == OTHER_COUNTRIES_LABEL:
            return "#9aa0a6"
        if label == EU27_LABEL:
            return "#003399"  # EU blue
        return country_color(label)

    node_colors = [_node_color(lbl) for lbl in node_labels]

    # Resolve indices - duplicates of "Other countries" (left + right) are
    # disambiguated by their column position, so we look up by (label, x).
    def _idx(label: str, x_pos: float) -> int:
        for i, (lbl, x) in enumerate(zip(node_labels, node_x)):
            if lbl == label and abs(x - x_pos) < 1e-6:
                return i
        raise KeyError(f"Node not found: {label} at x={x_pos}")

    sources: list[int] = []
    targets: list[int] = []
    values: list[float] = []
    link_colors: list[str] = []

    for mineral in CAROUSEL_MINERALS:
        material_color = MINERAL_COLORS.get(mineral, "#5C5C5C")
        material_idx = _idx(mineral, 0.5)

        # Mining country -> material (left fan)
        for country, val in mining_per_material.get(mineral, []):
            sources.append(_idx(country, 0.001))
            targets.append(material_idx)
            values.append(val)
            link_colors.append(_hex_to_rgba(material_color, 0.32))

        # Material -> processing country (right fan)
        for country, val in processing_per_material.get(mineral, []):
            sources.append(material_idx)
            targets.append(_idx(country, 0.999))
            values.append(val)
            if country == "China":
                link_colors.append("rgba(222, 41, 16, 0.32)")
            else:
                link_colors.append(_hex_to_rgba(material_color, 0.22))

    fig = go.Figure(
        go.Sankey(
            arrangement="fixed",
            node=dict(
                pad=22,
                thickness=22,
                line=dict(color="rgba(20,17,13,0.15)", width=1),
                label=node_labels,
                color=node_colors,
                x=node_x,
                y=node_y,
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=link_colors,
            ),
        )
    )
    apply_theme(fig)
    fig.update_layout(
        title=dict(
            text=(
                "<b>Where the Chokepoint Lives</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "Mining country → material → processing country, 2023. "
                "Top 10 + Other countries on each side; each material = 100 units of flow.</span>"
            ),
        ),
        margin=dict(l=40, r=40, t=160, b=80),
        height=1400,
    )

    path = VIS_ROOT / "supply-chain" / "sankey_master.html"
    write_plotly(fig, path)
    return path


def build_dependency_chart(economic: pd.DataFrame, trade: pd.DataFrame) -> Path:
    """7 - Manufacturing-dependency view.

    For each of the seven focal materials, render a dual horizontal bar:
      - China processing share (%) - the chokepoint
      - US net-import-reliance (%) - one Western consumer's exposure
    With a text annotation showing the dominant end-use category - so the
    reader can read 'X is Y % chinese-processed, the US imports Z % of its
    supply, and it goes mainly into [end-use].'
    """
    # China processing share per material (2023)
    proc = trade[
        (trade["record_type"] == "stage_share")
        & (trade["stage"] == "processing")
        & (trade["country"] == "China")
        & (trade["year"] == 2023)
        & (trade["mineral"].isin(CAROUSEL_MINERALS))
    ][["mineral", "share_pct"]].rename(columns={"share_pct": "china_proc"})

    # US net-import reliance: latest available year per material (positive only)
    nir = economic[economic["metric"] == "us_net_import_reliance_pct"].copy()
    nir["year"] = pd.to_numeric(nir["year"], errors="coerce")
    nir = nir.dropna(subset=["year"])
    nir = nir.sort_values(["mineral", "year"]).groupby("mineral", as_index=False).tail(1)
    nir = nir[["mineral", "value", "year"]].rename(columns={"value": "us_nir", "year": "nir_year"})
    nir["us_nir"] = nir["us_nir"].clip(lower=0, upper=100)

    # Dominant end-use per material (latest year)
    eu = economic[economic["metric"] == "end_use_share_pct"].copy()
    eu = eu.sort_values(["mineral", "value"], ascending=[True, False])
    top_eu = eu.groupby("mineral", as_index=False).head(1)[["mineral", "category", "value"]]
    top_eu = top_eu.rename(columns={"category": "top_use", "value": "top_use_pct"})

    df = (
        pd.DataFrame({"mineral": CAROUSEL_MINERALS})
        .merge(proc, on="mineral", how="left")
        .merge(nir, on="mineral", how="left")
        .merge(top_eu, on="mineral", how="left")
    )
    # Sort by China processing share descending - chokepoints at the top
    df = df.sort_values("china_proc", ascending=True)

    fig = go.Figure()

    # China processing share - red bar (the chokepoint)
    fig.add_trace(go.Bar(
        x=df["china_proc"],
        y=df["mineral"],
        orientation="h",
        name="China processing share (2023)",
        marker=dict(color="rgba(222, 41, 16, 0.78)", line=dict(color="rgba(20,17,13,0.2)", width=1)),
        text=[f"{v:.0f}%" if pd.notna(v) else "" for v in df["china_proc"]],
        textposition="inside",
        textfont=dict(color="#fff", size=14),
        hovertemplate="<b>%{y}</b><br>China refines <b>%{x:.0f}%</b> of global supply<extra></extra>",
        offsetgroup=0,
    ))

    # US net-import reliance - prussian bar
    fig.add_trace(go.Bar(
        x=df["us_nir"],
        y=df["mineral"],
        orientation="h",
        name="US net-import reliance (latest)",
        marker=dict(color="rgba(15, 61, 92, 0.72)", line=dict(color="rgba(20,17,13,0.2)", width=1)),
        text=[f"{v:.0f}%" if pd.notna(v) else "—" for v in df["us_nir"]],
        textposition="inside",
        textfont=dict(color="#fff", size=14),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "US imports <b>%{x:.0f}%</b> of consumption (year %{customdata[0]})<extra></extra>"
        ),
        customdata=df[["nir_year"]].fillna("—").astype(str).values,
        offsetgroup=1,
    ))

    # Right-side text annotation: dominant manufacturing application
    annotations = []
    for _, r in df.iterrows():
        if pd.notna(r["top_use"]):
            annotations.append(dict(
                x=104, y=r["mineral"],
                text=f"<i>{r['top_use']} ({r['top_use_pct']:.0f}%)</i>",
                xref="x", yref="y",
                showarrow=False,
                xanchor="left",
                font=dict(size=13, color="#5a544c"),
            ))

    apply_theme(fig)
    fig.update_layout(
        title=dict(
            text=(
                "<b>What a Processing Blockade Would Choke</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "China processing share vs. US net-import reliance, with the dominant manufacturing application</span>"
            ),
        ),
        barmode="group",
        bargap=0.18,
        bargroupgap=0.08,
        xaxis=dict(title=dict(text="<b>Share (%)</b>"), range=[0, 220], ticksuffix="%", tickvals=[0, 25, 50, 75, 100]),
        yaxis=dict(title=None),
        annotations=annotations,
        legend=dict(
            orientation="h",
            yanchor="top", y=1.06,
            xanchor="right", x=1.0,
        ),
        legend_title_text=None,
        margin=dict(l=140, r=40, t=160, b=110),
        height=620,
    )

    path = VIS_ROOT / "supply-chain" / "dependency_chart.html"
    write_plotly(fig, path)
    return path


def build_bifurcation_blocs(trade: pd.DataFrame) -> Path:
    """8 - Bloc-split view: where China's exports actually go.

    Custom bloc grouping that goes finer than the dataset's partner_group:
      - Western alliance: USA, EU-27, UK, Japan, South Korea, Canada, Australia, NZ
      - India (called out separately - the BRICS+ heavyweight outside China)
      - BRICS+ (excluding India and China themselves)
      - Belt-and-Road (BRI signatories not already classified)
      - Other
    Stacked area chart of China's annual export value, 2010-2024, by bloc.
    The argument for or against bipolarity reads off the slopes of the bands.
    """
    WESTERN = {
        # Non-EU democratic allies. Norway/Switzerland/Iceland have moved
        # into the EU-27+ bloc since they share the EU's regulatory and
        # ideological space (EEA + EFTA + bilateral agreements).
        "United States of America", "Japan", "Republic of Korea", "Korea, Rep.",
        "Canada", "Australia", "New Zealand", "United Kingdom",
    }
    EU27_PLUS = {
        # EU-27 + EEA (Norway, Iceland, Liechtenstein) + Switzerland.
        # Treated as one ideological / regulatory bloc.
        "Austria", "Belgium", "Bulgaria", "Croatia", "Cyprus", "Czech Republic", "Czechia",
        "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary", "Ireland",
        "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta", "Netherlands", "Poland",
        "Portugal", "Romania", "Slovakia", "Slovenia", "Spain", "Sweden",
        "Norway", "Switzerland", "Iceland", "Liechtenstein",
    }
    INDIA = {"India"}
    BRICS_PLUS = {
        "Brazil", "Russian Federation", "South Africa", "Egypt", "Iran", "Iran (Islamic Rep. of)",
        "Saudi Arabia", "United Arab Emirates", "Ethiopia", "Indonesia",
    }
    # BRI: a representative subset of BRI signatories not already in the Western/BRICS lists
    BRI = {
        "Pakistan", "Kazakhstan", "Türkiye", "Turkey", "Viet Nam", "Vietnam", "Malaysia",
        "Thailand", "Philippines", "Argentina", "Chile", "Peru", "Hungary", "Greece",
    }

    def _bloc(name: str) -> str:
        if not isinstance(name, str):
            return "Other"
        if name in WESTERN:
            return "Western alliance"
        if name in EU27_PLUS:
            return "EU-27+"
        if name in INDIA:
            return "India"
        if name in BRICS_PLUS:
            return "BRICS+ (ex-India, ex-China)"
        if name in BRI:
            return "Belt and Road"
        return "Other"

    tf = trade[
        (trade["record_type"] == "trade_flow")
        & (trade["country"] == "China")
        & (trade["flow_direction"] == "export")
    ].copy()
    tf = tf.drop_duplicates(subset=["year", "partner_country", "hs_code", "value_usd"])
    tf["bloc"] = tf["partner_country"].apply(_bloc)
    grouped = tf.groupby(["year", "bloc"], as_index=False)["value_usd"].sum()
    grouped = grouped[grouped["year"] >= 2010]

    # Total per year for share normalisation
    totals = grouped.groupby("year")["value_usd"].transform("sum")
    grouped["share_pct"] = grouped["value_usd"] / totals * 100

    bloc_order = [
        "Western alliance", "EU-27+", "Belt and Road", "India",
        "BRICS+ (ex-India, ex-China)", "Other",
    ]
    bloc_colors = {
        "Western alliance":              "#3C3B6E",
        "EU-27+":                        "#003399",
        "Belt and Road":                 "#A07850",
        "India":                         "#FF9933",  # India saffron
        "BRICS+ (ex-India, ex-China)":   "#7B2D26",  # oxblood
        "Other":                         "#9aa0a6",
    }

    fig = go.Figure()
    for bloc in bloc_order:
        sub = grouped[grouped["bloc"] == bloc].sort_values("year")
        if sub.empty:
            continue
        fig.add_trace(go.Scatter(
            x=sub["year"],
            y=sub["share_pct"],
            mode="lines",
            stackgroup="one",
            groupnorm="percent",
            name=bloc,
            line=dict(width=0.5, color=bloc_colors.get(bloc, "#888")),
            fillcolor=bloc_colors.get(bloc, "#888"),
            hovertemplate=f"<b>{bloc}</b><br>%{{x}} · %{{y:.1f}}%<extra></extra>",
        ))

    apply_theme(fig)
    fig.update_layout(
        title=dict(
            text=(
                "<b>Two Supply Chains, or One?</b>"
                "<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                "China's critical-mineral export value, share by bloc, 2010–2024</span>"
            ),
        ),
        xaxis=dict(title=dict(text="<b>Year</b>")),
        yaxis=dict(title=None, ticksuffix="%", range=[0, 100]),
        legend=dict(
            orientation="h",
            yanchor="top", y=1.06,
            xanchor="right", x=1.0,
        ),
        legend_title_text=None,
        margin=dict(l=80, r=40, t=170, b=110),
        height=620,
    )

    path = VIS_ROOT / "bifurcation" / "bloc_split.html"
    write_plotly(fig, path)
    return path


def _hex_to_rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def build_trade_flows(trade: pd.DataFrame, year: int) -> Path:
    china = unique_trade_flows(trade)
    china = china[
        (china["country"] == "China")
        & (china["flow_direction"] == "export")
        & (china["year"] == year)
    ].copy()
    grouped = (
        china.groupby("partner_country", as_index=False)["value_usd"]
        .sum()
        .sort_values("value_usd", ascending=False)
        .head(15)
    )
    grouped = grouped.sort_values("value_usd", ascending=True)

    fig = px.bar(
        grouped,
        x="value_usd",
        y="partner_country",
        orientation="h",
        title=f"China's Top Critical-Mineral Export Destinations ({year})",
    )
    fig.update_traces(
        marker_color=COUNTRY_COLORS["China"],
        hovertemplate="<b>%{y}</b><br>Value: $%{x:,.0f}<extra></extra>",
    )
    apply_theme(fig)
    fig.update_layout(xaxis_title="Trade value (USD)", yaxis_title=None, showlegend=False)

    path = VIS_ROOT / "bifurcation" / f"trade_flows_{year}.html"
    write_plotly(fig, path)
    return path


def build_china_timeline(trade: pd.DataFrame) -> Path:
    china = unique_trade_flows(trade)
    china = china[
        (china["country"] == "China")
        & (china["flow_direction"] == "export")
        & (china["partner_group"].isin(["EU-27", "United States", "Other countries"]))
    ].copy()
    grouped = (
        china.groupby(["year", "partner_group"], as_index=False)["value_usd"].sum()
    )
    totals = grouped.groupby("year")["value_usd"].transform("sum")
    grouped["share_pct"] = grouped["value_usd"] / totals * 100

    year_min = int(grouped["year"].min())
    year_max = int(grouped["year"].max())
    fig = px.line(
        grouped,
        x="year",
        y="share_pct",
        color="partner_group",
        color_discrete_map={
            "EU-27": COUNTRY_COLORS["EU"],
            "United States": COUNTRY_COLORS["United States"],
            "Other countries": COUNTRY_COLORS["Other"],
        },
    )
    fig.update_traces(mode="lines+markers", line=dict(width=3), marker=dict(size=8))
    apply_theme(fig)
    fig.update_layout(
        title=dict(
            text=(
                "<b>Where China's Critical-Mineral Exports Are Going</b>"
                f"<br><span style='font-size:18px;font-weight:400;color:#5a544c'>"
                f"Share of China's export value by partner bloc, {year_min}–{year_max}</span>"
            ),
        ),
        xaxis=dict(title=dict(text="<b>Year</b>")),
        yaxis_title=None,
        legend=dict(
            orientation="h",
            yanchor="top", y=1.06,
            xanchor="right", x=1.0,
        ),
        legend_title_text=None,
        annotations=[],
        yaxis=dict(ticksuffix="%"),
        margin=dict(l=80, r=40, t=170, b=110),
    )

    path = VIS_ROOT / "bifurcation" / "china_timeline.html"
    write_plotly(fig, path)
    return path


def build_hhi_heatmap(trade: pd.DataFrame) -> Path:
    hhi = trade[
        (trade["record_type"] == "hhi")
        & (trade["year"] == 2023)
        & (trade["stage"].isin(STAGE_ORDER))
    ].copy()
    pivot = (
        hhi.pivot_table(index="mineral", columns="stage", values="hhi", aggfunc="max")
        .reindex(TARGET_MINERALS)
        .reindex(columns=STAGE_ORDER)
    )

    fig = px.imshow(
        pivot,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale="YlOrRd",
        title="Concentration Heatmap by Mineral and Supply-Chain Stage (HHI, 2023)",
    )
    apply_theme(fig)
    fig.update_layout(
        xaxis_title=None,
        yaxis_title=None,
        coloraxis_colorbar_title="HHI",
    )

    path = VIS_ROOT / "conclusion" / "hhi_heatmap.html"
    write_plotly(fig, path)
    return path


def build_manifest(paths: dict[str, str]) -> None:
    manifest = {
        "hero": {
            "decision": "No exported hero visualization in the first draft; the hero is narrative/layout work for the website goal."
        },
        "sections": [
            {
                "section": "stakes",
                "datasets": ["master_economic_timeseries.csv"],
                "outputs": [
                    {"file": paths["mineral_grid"],       "purpose": "Mineral overview"},
                    {"file": paths["price_index"],        "purpose": "5.1 Price shock opener (1900-2024, real/nominal toggle)"},
                    {"file": paths["price_index_zoom"],   "purpose": "5.1b Modern-era zoom (2000-2024)"},
                    {"file": paths["production_history"], "purpose": "5.2 World mine production 1900-2024"},
                    {"file": paths["end_uses"],           "purpose": "End-use framing (treemap)"},
                    {"file": paths["end_use_carousel"],   "purpose": "End-use framing (3D carousel)"},
                ],
            },
            {
                "section": "deposits",
                "datasets": ["master_geo_deposits.geojson"],
                "outputs": [{"file": paths["deposit_map"], "purpose": "Global geology map"}],
            },
            {
                "section": "supply-chain",
                "datasets": ["master_supply_chain_trade.csv"],
                "outputs": [
                    {"file": paths["slope_chart"], "purpose": "Case 1 mining vs processing gap"},
                    {"file": paths["production_series"], "purpose": "Case 1 scaling over time"},
                    {"file": paths.get("sankey_cobalt", ""), "purpose": "5.3 carousel - Cobalt"},
                    {"file": paths.get("sankey_lithium", ""), "purpose": "5.3 carousel - Lithium"},
                    {"file": paths.get("sankey_graphite", ""), "purpose": "5.3 carousel - Graphite"},
                    {"file": paths.get("sankey_copper", ""), "purpose": "5.3 carousel - Copper"},
                    {"file": paths.get("sankey_platinum", ""), "purpose": "5.3 carousel - Platinum"},
                    {"file": paths.get("sankey_gallium", ""), "purpose": "5.3 carousel - Gallium"},
                    {"file": paths.get("sankey_rare_earths", ""), "purpose": "5.3 carousel - Rare Earths"},
                    {"file": paths["sankey_master"], "purpose": "5.5 All-material chokepoint Sankey"},
                ],
            },
            {
                "section": "bifurcation",
                "datasets": ["master_supply_chain_trade.csv"],
                "outputs": [
                    {"file": paths["trade_flows_2015"], "purpose": "2015 China export destinations"},
                    {"file": paths["trade_flows_2023"], "purpose": "2023 China export destinations"},
                    {"file": paths["china_timeline"], "purpose": "China export destination timeline"},
                ],
            },
            {
                "section": "conclusion",
                "datasets": ["master_supply_chain_trade.csv"],
                "outputs": [{"file": paths["hhi_heatmap"], "purpose": "Concentration synthesis"}],
            },
        ],
    }
    (VIS_ROOT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    lines = [
        "# Visualization Manifest",
        "",
        "All first-draft visualization exports are built from `data/processed` only.",
        "",
        "## Section 0",
        "",
        "- No exported hero asset in the first draft. This remains website composition work.",
        "",
    ]
    for section in manifest["sections"]:
        lines.append(f"## {section['section'].title()}")
        lines.append("")
        lines.append(f"- Datasets: {', '.join(section['datasets'])}")
        for output in section["outputs"]:
            lines.append(f"- `{output['file']}`: {output['purpose']}")
        lines.append("")
    (VIS_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    ensure_dirs()
    economic = read_economic()
    trade = read_trade()
    deposits = read_deposits()

    carousel_paths = build_sankey_carousel(trade)

    outputs = {
        "mineral_grid": str(build_mineral_grid(economic).relative_to(ROOT)),
        "price_index": str(build_price_index(economic).relative_to(ROOT)),
        "price_index_zoom": str(build_price_index_zoom(economic).relative_to(ROOT)),
        "production_history": str(build_production_history(economic).relative_to(ROOT)),
        "end_uses": str(build_end_uses(economic).relative_to(ROOT)),
        "end_use_carousel": str(build_end_use_carousel(economic).relative_to(ROOT)),
        "deposit_map": str(build_deposit_map(deposits).relative_to(ROOT)),
        "slope_chart": str(build_slope_chart(trade).relative_to(ROOT)),
        "production_series": str(build_production_series(economic).relative_to(ROOT)),
        "sankey_master": str(build_master_sankey(trade).relative_to(ROOT)),
        "trade_flows_2015": str(build_trade_flows(trade, 2015).relative_to(ROOT)),
        "trade_flows_2023": str(build_trade_flows(trade, 2023).relative_to(ROOT)),
        "china_timeline": str(build_china_timeline(trade).relative_to(ROOT)),
        "hhi_heatmap": str(build_hhi_heatmap(trade).relative_to(ROOT)),
    }
    for slug, path in carousel_paths.items():
        outputs[f"sankey_{slug}"] = str(path.relative_to(ROOT))
    build_manifest(outputs)

    print("Built visualization exports:")
    for key, value in outputs.items():
        print(f"- {key}: {value}")
    print("- manifest: website/visualizations/manifest.json")
    print("- readme: website/visualizations/README.md")


if __name__ == "__main__":
    main()
