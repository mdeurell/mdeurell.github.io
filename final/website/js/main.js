function numberWithCommas(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function renderHeroStats(context) {
  const mount = document.getElementById("hero-stats");
  if (!mount || !Array.isArray(context.hero_stats)) {
    return;
  }

  mount.innerHTML = context.hero_stats
    .map(
      (stat) => `
        <article class="stat-card">
          <p class="stat-number">${numberWithCommas(stat.value)}</p>
          <p class="stat-label">${stat.label}</p>
          <p class="stat-detail">${stat.detail}</p>
        </article>
      `,
    )
    .join("");
}

function leaderText(leader, connector) {
  if (!leader) {
    return "";
  }

  return `${leader.mining_country} leads mining at ${leader.mining_share.toFixed(0)}%, while ${leader.processing_country} ${connector} processing at ${leader.processing_share.toFixed(0)}%.`;
}

function writeText(id, text) {
  const node = document.getElementById(id);
  if (node) {
    node.textContent = text;
  }
}

function updateNotebookLinks(context) {
  if (!context.project || !context.project.notebook_href) {
    return;
  }

  document.querySelectorAll(".js-notebook-link").forEach((link) => {
    link.setAttribute("href", context.project.notebook_href);
  });
}

function renderNarrativeFacts(context) {
  const highlights = context.highlights || {};
  const price = highlights.price || {};
  const endUses = Array.isArray(highlights.end_uses) ? highlights.end_uses : [];
  const leaders = highlights.leaders_2023 || {};
  const concentration = highlights.concentration_2023 || {};
  const blocShare = highlights.china_bloc_share || {};

  const lithium = leaders.Lithium;
  const graphite = leaders.Graphite;
  const cobalt = leaders.Cobalt;
  const gallium = leaders.Gallium;
  const west2015 = blocShare["2015"] ? blocShare["2015"].western_bloc : null;
  const west2023 = blocShare["2023"] ? blocShare["2023"].western_bloc : null;

  writeText(
    "stakes-price-spike",
    `${price.top_mineral} recorded the steepest move: an index of ${price.top_index_vs_2015} (2015 = 100) by ${price.latest_year}. Lithium surged 10× in 2020–2022 on EV demand before a sharp 2024 correction. Clean-energy buildout keeps long-run demand structurally elevated.`,
  );

  // Legacy end-use card (kept for backward compatibility; id may no longer be in DOM)
  if (endUses.length > 0) {
    const lithiumUse = endUses.find((item) => item.mineral === "Lithium") || endUses[0];
    writeText(
      "stakes-end-use",
      `In ${lithiumUse.year}, ${lithiumUse.mineral} was dominated by ${lithiumUse.category.toLowerCase()} at ${lithiumUse.value.toFixed(0)}%.`,
    );
  }

  writeText(
    "deposits-coverage",
    `The deposits master maps ${numberWithCommas(context.hero_stats[1].value)} locations across ${numberWithCommas(context.hero_stats[2].value)} countries. The rocks are geographically broader than the bottlenecks.`,
  );
  writeText("case1-lithium", leaderText(lithium, "still dominates"));
    `Latest historical price year: ${price.latest_year}. ${price.top_mineral} shows the sharpest move at an index of ${price.top_index_vs_2015} when 2015 = 100.`,
  writeText("case2-cobalt", leaderText(cobalt, "still dominates"));
  writeText(
    "case2-gallium",
  );

  if (west2015 !== null && west2023 !== null) {
    writeText(
      "bifurcation-summary",
      `China's combined export share to the EU-27 and United States moved from ${west2015.toFixed(1)}% in 2015 to ${west2023.toFixed(1)}% in 2023. That is a shift, but not a clean two-bloc break.`,
    );
  }

  if (concentration.mining && concentration.processing) {
    writeText(
      "conclusion-summary",
      `${concentration.processing.high_count} of ${concentration.processing.total} processing stages and ${concentration.mining.high_count} of ${concentration.mining.total} mining stages are highly concentrated in the 2023 stage-share view.`,
    );
  }

  writeText("trade-note", highlights.trade_note || "");
}

// Periodic-table info (atomic number, mass, electron config, category)
// Rare Earths is a family (57–71 + Y, Sc) so it carries a range.
const ELEMENT_DATA = {
  "rare-earths": { num: "57–71", sym: "La–Lu", mass: "+ Y, Sc", config: "[Xe] 4f¹⁻¹⁴ 5d⁰⁻¹ 6s²", cat: "Lanthanides" },
  "neodymium":   { num: 60, sym: "Nd", mass: "144.24", config: "[Xe] 4f⁴ 6s²",      cat: "Lanthanide" },
  "dysprosium":  { num: 66, sym: "Dy", mass: "162.50", config: "[Xe] 4f¹⁰ 6s²",     cat: "Lanthanide" },
  "terbium":     { num: 65, sym: "Tb", mass: "158.93", config: "[Xe] 4f⁹ 6s²",      cat: "Lanthanide" },
  "lithium":     { num: 3,  sym: "Li", mass: "6.94",   config: "[He] 2s¹",          cat: "Alkali metal" },
  "cobalt":      { num: 27, sym: "Co", mass: "58.93",  config: "[Ar] 3d⁷ 4s²",      cat: "Transition metal" },
  "graphite":    { num: 6,  sym: "C",  mass: "12.01",  config: "[He] 2s² 2p²",      cat: "Nonmetal · allotrope" },
  "copper":      { num: 29, sym: "Cu", mass: "63.55",  config: "[Ar] 3d¹⁰ 4s¹",     cat: "Transition metal" },
  "gallium":     { num: 31, sym: "Ga", mass: "69.72",  config: "[Ar] 3d¹⁰ 4s² 4p¹", cat: "Post-transition metal" },
  "platinum":    { num: 78, sym: "Pt", mass: "195.08", config: "[Xe] 4f¹⁴ 5d⁹ 6s¹", cat: "Transition metal" },
};

const MATERIALS = [
  {
    id: "rare-earths",
    eyebrow: "Element family",
    name: "Rare Earths",
    symbol: "17 elements · La–Lu + Y, Sc",
    image: "visualizations/images/Rare_Earths.jpg",
    hook: "Seventeen elements, almost chemically identical, almost impossible to tell apart.",
    what: "The lanthanides plus yttrium and scandium — seventeen metals that share nearly identical valence shells. They are not actually rare in the crust, but they are seldom found in mineable concentrations and are notoriously difficult to separate from one another.",
    where: "Carbonatite-hosted orebodies (Bayan Obo, Mountain Pass, Mt Weld) and ion-adsorption clays in southern China and Myanmar. Major producers: China (~70 % of mining, ~90 % of refining), the United States, Australia.",
    use: "As a family they enable nearly every clean-energy technology — wind-turbine magnets, EV motors, fluorescent and LED phosphors, refining catalysts. The two dominant uses today are catalysis and permanent magnets.",
    endUses: [
      { label: "Catalysts", pct: 35 },
      { label: "Permanent magnets", pct: 29 },
      { label: "Ceramics & glass", pct: 15 },
      { label: "Metallurgy", pct: 12 },
      { label: "Polishing", pct: 9 },
    ],
  },
  {
    id: "neodymium",
    eyebrow: "Light rare earth",
    name: "Neodymium",
    symbol: "Nd · 60",
    image: "visualizations/images/Neodymium-Metal-chemical-element-with-the-symbol-Nd-atomic-number-60.jpg",
    hook: "The strongest permanent magnet ever produced was made with this metal.",
    what: "A silvery rare-earth metal that tarnishes quickly in air. The fourth lanthanide, valued for its unmatched magnetic properties when alloyed with iron and boron (Nd₂Fe₁₄B).",
    where: "Carbonatite-hosted deposits like Bayan Obo (China) and Mountain Pass (USA), and supergene-enriched ores like Mt Weld (Australia). Almost all separation and refining happens in China.",
    use: "NdFeB magnets dominate every modern motor — EV drivetrains, wind-turbine generators, hard drives, headphones. A small share goes to Nd:YAG lasers used in surgery and industrial welding.",
    endUses: [
      { label: "Permanent magnets", pct: 76 },
      { label: "Catalysts", pct: 12 },
      { label: "Lasers", pct: 6 },
      { label: "Glass & optics", pct: 6 },
    ],
  },
  {
    id: "dysprosium",
    eyebrow: "Heavy rare earth",
    name: "Dysprosium",
    symbol: "Dy · 66",
    image: "visualizations/images/Dysprosium-Metal-chemical-element-with-the-symbol-Dy-atomic-number-66.jpg",
    hook: "Without it, neodymium magnets fail at high temperatures.",
    what: "A heavy lanthanide with a high magnetic moment. Added in small amounts to NdFeB magnets, it dramatically raises their thermal stability — without it, the magnets demagnetize as they heat up under load.",
    where: "Almost exclusively from ion-adsorption clays in southern China and Myanmar. There is essentially no commercial mining or separation outside East Asia.",
    use: "Magnet stabilization is essentially the entire market. Trace amounts also appear in nuclear control rods (high neutron-absorption cross-section) and specialty lasers.",
    endUses: [
      { label: "Magnet stabilization", pct: 80 },
      { label: "Nuclear control rods", pct: 10 },
      { label: "Lasers & electronics", pct: 10 },
    ],
  },
  {
    id: "terbium",
    eyebrow: "Heavy rare earth",
    name: "Terbium",
    symbol: "Tb · 65",
    image: "visualizations/images/Terbium-Metal-chemical-element-with-the-symbol-Tb-atomic-number-65.jpg",
    hook: "The green of every fluorescent screen.",
    what: "A soft, silvery rare-earth metal. The Tb³⁺ ion fluoresces a brilliant lemon-green — a strong emission line that gives fluorescent lamps and displays their colour rendering. Named after Ytterby, a Swedish village whose feldspar quarry produced four lanthanides.",
    where: "Recovered from monazite, xenotime and bastnäsite. Roughly 99 % of refined supply originates in southern China; recently identified seabed deposits near Japan are not yet mined.",
    use: "Green phosphors for fluorescent lamps, LEDs and flat-screen displays. Also a key component of Terfenol-D — a magnetostrictive alloy used in naval sonar and precision actuators.",
    endUses: [
      { label: "Green phosphors", pct: 60 },
      { label: "Magnetostrictive alloys", pct: 25 },
      { label: "Magnet alloys", pct: 10 },
      { label: "Solid-state devices", pct: 5 },
    ],
  },
  {
    id: "lithium",
    eyebrow: "Battery metal",
    name: "Lithium",
    symbol: "Li · 3",
    image: "visualizations/images/Lithium-Metal-chemical-element-with-the-symbol-Li-atomic-number-3.jpg",
    hook: "The lightest metal — and the densest store of consumer power.",
    what: "A soft, silvery alkali metal. Lightest of all metals and the least dense solid element under standard conditions. Highly reactive — never found in elemental form in nature.",
    where: "The South American \"Lithium Triangle\" (Chile, Argentina, Bolivia) where it is extracted by brine evaporation. Australia mines hard-rock spodumene; China holds dominant refining capacity.",
    use: "Over three-quarters of global production goes to lithium-ion batteries — phones, laptops, EVs, grid storage. Also as ceramic flux, high-temperature lubricants, and a foundational psychiatric medicine.",
    endUses: [
      { label: "Batteries", pct: 87 },
      { label: "Ceramics & glass", pct: 5 },
      { label: "Other industrial", pct: 8 },
    ],
  },
  {
    id: "cobalt",
    eyebrow: "Battery metal",
    name: "Cobalt",
    symbol: "Co · 27",
    image: "visualizations/images/cobalt.png",
    hook: "A blue-tinted byproduct that became geopolitically essential.",
    what: "A hard, lustrous transition metal with strong ferromagnetism. Stable at high temperatures — retains magnetism above 1100 °C — which underpins its role in jet engines and high-density batteries.",
    where: "Mostly a byproduct of copper and nickel mining. The Democratic Republic of the Congo produces ~70 % of mined cobalt; China refines most of it.",
    use: "Superalloys for aircraft turbines, lithium-ion battery cathodes (NMC, LCO chemistries), cemented carbides, and chemical catalysts. Also still a pigment — \"cobalt blue\" — though that is a rounding error in the modern market.",
    endUses: [
      { label: "Superalloys (turbines)", pct: 51 },
      { label: "Chemicals & batteries", pct: 25 },
      { label: "Other metallics", pct: 15 },
      { label: "Carbides", pct: 9 },
    ],
  },
  {
    id: "graphite",
    eyebrow: "Battery material",
    name: "Graphite",
    symbol: "C · 6",
    image: "visualizations/images/Graphite-Soft.jpg",
    hook: "Pure carbon, layered just so — and required to make a battery anode.",
    what: "A native crystalline form of carbon, layered into hexagonal sheets that slide easily over each other. The same element as diamond, with radically different properties because of how the atoms are arranged.",
    where: "Natural graphite is mined in flake or amorphous form, dominantly in China, Mozambique and Brazil. Synthetic graphite — required for high-end battery anodes — is made in petroleum-coke reactors, also dominantly in China.",
    use: "The standard anode material for lithium-ion batteries. Also refractory linings for furnaces, steelmaking electrodes, brake linings and dry lubricants.",
    endUses: [
      { label: "Batteries", pct: 35 },
      { label: "Refractories", pct: 25 },
      { label: "Steelmaking", pct: 15 },
      { label: "Brake linings", pct: 10 },
      { label: "Lubricants", pct: 8 },
      { label: "Powdered metals", pct: 7 },
    ],
  },
  {
    id: "copper",
    eyebrow: "Base metal",
    name: "Copper",
    symbol: "Cu · 29",
    image: "visualizations/images/Copper-Metal-chemical-element-with-the-symbol-Cu-atomic-number-29.jpg",
    hook: "The metal of the electric age — and four times more of it per electric car.",
    what: "A reddish-pink transition metal with the highest electrical conductivity of any base metal. Highly ductile, fully recyclable, and one of the few metals continuously used by humanity since 8000 BC.",
    where: "Porphyry deposits — vast, low-grade ore bodies in Chile, Peru and the Andes. China is the largest refiner; Chile remains the largest miner.",
    use: "Electrical wiring, motors, plumbing and roofing, electronics. Demand is rising sharply with the energy transition: an EV uses roughly four times the copper of a combustion-engine car.",
    endUses: [
      { label: "Building construction", pct: 42 },
      { label: "Electrical", pct: 23 },
      { label: "Transport", pct: 18 },
      { label: "Consumer", pct: 10 },
      { label: "Industrial", pct: 7 },
    ],
  },
  {
    id: "gallium",
    eyebrow: "Semiconductor element",
    name: "Gallium",
    symbol: "Ga · 31",
    image: "visualizations/images/Gallium-Metal-chemical-element-with-the-symbol-Ga-atomic-number-31.jpg",
    hook: "Liquid in your hand — and silicon's high-frequency successor.",
    what: "A soft silvery metal that melts at 30 °C — low enough to liquefy in a warm palm. Recovered as a byproduct of bauxite processing. Compounds (especially gallium nitride and gallium arsenide) outperform silicon at high frequencies and high voltages.",
    where: "Almost entirely a byproduct of aluminium refining. China produces ~98 % of refined gallium globally; export controls were tightened in 2023.",
    use: "Integrated circuits — particularly GaAs and GaN chips for radar, 5G and EV power electronics. Also LEDs, laser diodes and thin-film solar cells.",
    endUses: [
      { label: "Integrated circuits", pct: 79 },
      { label: "Optoelectronics (LEDs/lasers)", pct: 20 },
      { label: "Research", pct: 1 },
    ],
  },
  {
    id: "platinum",
    eyebrow: "Precious / catalyst",
    name: "Platinum",
    symbol: "Pt · 78",
    image: "visualizations/images/platinum.jpg",
    hook: "Catalysing the chemistry of pollution control — and rarer than gold.",
    what: "A silvery-white precious metal, dense and chemically inert. Resists corrosion at any temperature; melts at 1768 °C. Among the rarest naturally occurring elements in the crust.",
    where: "Roughly 70 % of global production comes from South Africa's Bushveld Igneous Complex. Russia, Zimbabwe and Canada supply most of the remainder. The supply geography is the inverse of nearly every other critical material — China is barely involved.",
    use: "Catalytic converters absorbing automotive exhaust, jewelry, chemical-industry catalysts, electronics, dental and medical instruments. Hydrogen fuel cells will likely be its largest growth market.",
    endUses: [
      { label: "Catalytic converters", pct: 40 },
      { label: "Jewelry", pct: 25 },
      { label: "Chemical catalysts", pct: 10 },
      { label: "Electronics", pct: 10 },
      { label: "Other", pct: 15 },
    ],
  },
];

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// Prussian-blue tonal ramp, ordered dark → light.
// Major slice gets the deepest tint, smaller slices step lighter.
const TM_TINTS = [
  "#0F3D5C", // deepest Prussian — dominant slice
  "#2A5A78", // mid Prussian
  "#4F7B95", // medium blue-grey
  "#7B9DB1", // soft blue-grey
  "#A9C0CD", // pale blue
  "#CED9E0", // very pale blue
];

function renderPlotlyTreemap(node, cells) {
  if (!node || !window.Plotly || !cells || !cells.length) return;
  // Sort by pct desc so darker slices read as dominant
  const ordered = [...cells].sort((a, b) => b.pct - a.pct);
  const labels = ordered.map((c) => c.label);
  const parents = ordered.map(() => "");
  const values = ordered.map((c) => c.pct);
  const colors = ordered.map((_, i) => TM_TINTS[Math.min(i, TM_TINTS.length - 1)]);

  Plotly.newPlot(
    node,
    [
      {
        type: "treemap",
        labels,
        parents,
        values,
        text: ordered.map((c) => `${c.pct}%`),
        textinfo: "label+text",
        textposition: "middle center",
        textfont: {
          family: "'Lato', -apple-system, BlinkMacSystemFont, sans-serif",
          size: 16,
          weight: 700,
          color: "#fbf8f1",
        },
        marker: {
          colors,
          line: { color: "#fbf8f1", width: 2 },
        },
        hovertemplate: "<b>%{label}</b><br>%{value}%<extra></extra>",
        pathbar: { visible: false },
        tiling: { packing: "squarify", squarifyratio: 1.4 },
      },
    ],
    {
      margin: { l: 0, r: 0, t: 0, b: 0 },
      paper_bgcolor: "#fbf8f1",
      plot_bgcolor: "#fbf8f1",
      font: { family: "'Lato', -apple-system, BlinkMacSystemFont, sans-serif", color: "#14110D" },
      hoverlabel: {
        bgcolor: "#14110D",
        bordercolor: "#0F3D5C",
        font: { family: "'Lato', -apple-system, BlinkMacSystemFont, sans-serif", color: "#fbf8f1" },
      },
    },
    { displayModeBar: false, responsive: true },
  );
}

function renderPeriodicTile(m) {
  const e = ELEMENT_DATA[m.id];
  if (!e) return "";
  return `
    <div class="mc-pt">
      <div class="mc-pt-row mc-pt-top">
        <span class="mc-pt-num">${escapeHtml(String(e.num))}</span>
        <span class="mc-pt-cat">${escapeHtml(e.cat)}</span>
      </div>
      <div class="mc-pt-sym">${escapeHtml(e.sym)}</div>
      <div class="mc-pt-name">${escapeHtml(m.name)}</div>
      <div class="mc-pt-row mc-pt-bottom">
        <span class="mc-pt-mass">${escapeHtml(e.mass)}</span>
        <span class="mc-pt-cfg">${escapeHtml(e.config)}</span>
      </div>
    </div>`;
}

function renderMaterialCard(m) {
  return `
    <article class="material-card" id="mc-${m.id}">
      <div class="mc-left">
        <div class="mc-img-wrap">
          <img class="mc-img" src="${m.image}" alt="${escapeHtml(m.name)}" loading="lazy">
        </div>
        ${renderPeriodicTile(m)}
      </div>
      <div class="mc-text">
        <header class="mc-head">
          <p class="mc-eyebrow">${escapeHtml(m.eyebrow)}</p>
          <h3 class="mc-name">${escapeHtml(m.name)}</h3>
          <p class="mc-hook">${escapeHtml(m.hook)}</p>
        </header>
        <div class="mc-body">
          <section><h4>What it is</h4><p>${escapeHtml(m.what)}</p></section>
          <section><h4>Where it's found</h4><p>${escapeHtml(m.where)}</p></section>
          <section><h4>How it's used</h4><p>${escapeHtml(m.use)}</p></section>
        </div>
      </div>
      <div class="mc-chart">
        <p class="mc-chart-cap">End-use breakdown · 2025</p>
        <div class="mc-chart-plot" data-treemap></div>
        <p class="mc-chart-source">Source: USGS Mineral Commodity Summaries 2025</p>
      </div>
    </article>`;
}

function buildMaterialRail() {
  const rail = document.getElementById("material-rail");
  const nav = document.getElementById("material-nav");
  if (!rail || !nav) return;

  rail.innerHTML = MATERIALS.map(renderMaterialCard).join("");
  nav.innerHTML = MATERIALS.map(
    (m) =>
      `<a href="#mc-${m.id}" class="material-nav-chip" data-target="mc-${m.id}">${escapeHtml(m.name)}</a>`,
  ).join("");

  // Mount a Plotly treemap into each card's chart slot
  MATERIALS.forEach((m) => {
    const card = document.getElementById(`mc-${m.id}`);
    if (!card) return;
    const slot = card.querySelector("[data-treemap]");
    renderPlotlyTreemap(slot, m.endUses);
  });

  const cards = [...rail.querySelectorAll(".material-card")];
  const chips = nav.querySelectorAll(".material-nav-chip");
  let activeIndex = 0;

  // Spacers allow first and last cards to scroll to center
  const spacerStart = Object.assign(document.createElement("div"), { className: "rail-spacer" });
  const spacerEnd   = Object.assign(document.createElement("div"), { className: "rail-spacer" });
  rail.prepend(spacerStart);
  rail.append(spacerEnd);

  function updateSpacers() {
    const cardWidth = cards[0]?.offsetWidth ?? 0;
    const space = Math.max(0, (rail.clientWidth - cardWidth) / 2);
    spacerStart.style.width = space + "px";
    spacerEnd.style.width   = space + "px";
  }

  function scrollToCard(index, behavior = "smooth") {
    const card = cards[index];
    if (!card) return;
    const offset = card.offsetLeft - (rail.clientWidth - card.offsetWidth) / 2;
    rail.scrollTo({ left: offset, behavior });
  }

  // Wait for layout before sizing spacers and centering
  requestAnimationFrame(() => {
    updateSpacers();
    scrollToCard(0, "instant");
    if (cards[0]) cards[0].classList.add("is-active");
  });

  window.addEventListener("resize", () => {
    updateSpacers();
    scrollToCard(activeIndex, "instant");
  });

  // Click chip → scroll to that card
  nav.addEventListener("click", (e) => {
    const a = e.target.closest("[data-target]");
    if (!a) return;
    e.preventDefault();
    const idx = cards.findIndex((c) => c.id === a.dataset.target);
    if (idx !== -1) scrollToCard(idx);
  });

  // Track active card: update chip highlight + card opacity
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const id = e.target.id;
          activeIndex = cards.findIndex((c) => c.id === id);
          chips.forEach((c) =>
            c.classList.toggle("is-active", c.dataset.target === id),
          );
          cards.forEach((c) =>
            c.classList.toggle("is-active", c.id === id),
          );
        }
      });
    },
    { root: rail, threshold: 0.6 },
  );
  cards.forEach((c) => obs.observe(c));

  // Prev / next buttons — one card at a time
  document.querySelectorAll("[data-rail-arrow]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = btn.dataset.railArrow === "next" ? 1 : -1;
      scrollToCard(Math.max(0, Math.min(cards.length - 1, activeIndex + dir)));
    });
  });

  // Keyboard arrows when rail focused
  rail.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const dir = e.key === "ArrowRight" ? 1 : -1;
    scrollToCard(Math.max(0, Math.min(cards.length - 1, activeIndex + dir)));
  });
}

// 5.3 - Per-material supply-chain Sankey carousel.
// Reuses the visual language of the §1 material rail: paper card, prussian rule,
// hook line, chip nav, prev/next arrows. Each card iframes a prebuilt Plotly
// Sankey from visualizations/supply-chain/.
const SANKEY_DECK = [
  {
    id: "cobalt",
    eyebrow: "Battery metal",
    name: "Cobalt",
    hook: "70 % mined in the DRC, 80 % refined in China — the metal travels several thousand miles between the two stages.",
  },
  {
    id: "lithium",
    eyebrow: "Battery metal",
    name: "Lithium",
    hook: "Mining diversified across Australia, Chile, China and Argentina; refining concentrated in China at 60 %.",
  },
  {
    id: "graphite",
    eyebrow: "Battery material",
    name: "Graphite",
    hook: "Mined in three countries; every commercial-grade refined gram comes through Chinese facilities.",
  },
  {
    id: "copper",
    eyebrow: "Base metal",
    name: "Copper",
    hook: "The most diversified mining base in the panel — and still 44 % of refining sits in China.",
  },
  {
    id: "platinum",
    eyebrow: "Precious / catalyst",
    name: "Platinum",
    hook: "The exception to the pattern: 70 % South African mining, with refining fanned out across seven countries.",
  },
  {
    id: "gallium",
    eyebrow: "Semiconductor element",
    name: "Gallium",
    hook: "98 % to 98 % at both stages. There is no second supplier on either side of the chain.",
  },
  {
    id: "rare_earths",
    eyebrow: "Element family",
    name: "Rare Earths",
    hook: "70 % mined in China, 90 % processed in China — Nd, Dy and Tb folded into the basket because their shares are statistically identical.",
  },
];

function renderSankeyCard(m) {
  const src = `visualizations/supply-chain/sankey_${m.id}.html`;
  return `
    <article class="sankey-card" id="sk-${m.id}">
      <header class="sk-head">
        <p class="sk-eyebrow">${escapeHtml(m.eyebrow)}</p>
        <h3 class="sk-name">${escapeHtml(m.name)}</h3>
        <p class="sk-hook">${escapeHtml(m.hook)}</p>
      </header>
      <div class="sk-frame-wrap">
        <iframe class="sk-frame" src="${src}" title="${escapeHtml(m.name)} supply chain Sankey, 2023" loading="lazy"></iframe>
      </div>
    </article>`;
}

function buildSankeyRail() {
  const rail = document.getElementById("sankey-rail");
  const nav = document.getElementById("sankey-nav");
  if (!rail || !nav) return;

  rail.innerHTML = SANKEY_DECK.map(renderSankeyCard).join("");
  nav.innerHTML = SANKEY_DECK.map(
    (m) =>
      `<a href="#sk-${m.id}" class="sankey-nav-chip" data-target="sk-${m.id}">${escapeHtml(m.name)}</a>`,
  ).join("");

  // Chip click → scroll the rail to that card
  nav.addEventListener("click", (e) => {
    const a = e.target.closest("[data-target]");
    if (!a) return;
    e.preventDefault();
    const card = document.getElementById(a.dataset.target);
    if (!card) return;
    const offset = card.offsetLeft - (rail.clientWidth - card.offsetWidth) / 2;
    rail.scrollTo({ left: offset, behavior: "smooth" });
  });

  // Active-chip tracking
  const chips = nav.querySelectorAll(".sankey-nav-chip");
  const obs = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          const id = e.target.id;
          chips.forEach((c) =>
            c.classList.toggle("is-active", c.dataset.target === id),
          );
        }
      });
    },
    { root: rail, threshold: 0.6 },
  );
  rail.querySelectorAll(".sankey-card").forEach((c) => obs.observe(c));

  // Prev / next arrows scoped to the sankey rail
  document.querySelectorAll("[data-sankey-arrow]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const dir = btn.dataset.sankeyArrow === "next" ? 1 : -1;
      const card = rail.querySelector(".sankey-card");
      if (!card) return;
      const step = card.offsetWidth + 24;
      rail.scrollBy({ left: dir * step, behavior: "smooth" });
    });
  });

  // Keyboard arrows when rail focused
  rail.addEventListener("keydown", (e) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const dir = e.key === "ArrowRight" ? 1 : -1;
    const card = rail.querySelector(".sankey-card");
    if (!card) return;
    rail.scrollBy({ left: dir * (card.offsetWidth + 24), behavior: "smooth" });
  });
}

function bindChromeScrollState() {
  const chrome = document.querySelector(".site-chrome");
  if (!chrome) return;
  const threshold = 0;
  let raf = null;
  function update() {
    raf = null;
    const scrolled = window.scrollY > threshold;
    chrome.classList.toggle("is-scrolled", scrolled);
  }
  window.addEventListener(
    "scroll",
    () => {
      if (raf === null) raf = requestAnimationFrame(update);
    },
    { passive: true },
  );
  update();
}

function bindFlowToggles() {
  const groups = document.querySelectorAll(".flow-toggle");
  groups.forEach((group) => {
    const btns = group.querySelectorAll(".flow-toggle-btn");
    btns.forEach((btn) => {
      btn.addEventListener("click", () => {
        const targetId = btn.dataset.target;
        const flow = btn.dataset.flow;
        const frame = document.getElementById(targetId);
        if (!frame) return;
        const nextSrc = frame.dataset[flow === "exports" ? "srcExports" : "srcImports"];
        if (nextSrc && frame.getAttribute("src") !== nextSrc) {
          frame.setAttribute("src", nextSrc);
        }
        btns.forEach((b) => {
          const on = b === btn;
          b.classList.toggle("is-active", on);
          b.setAttribute("aria-selected", on ? "true" : "false");
        });
      });
    });
  });
}

function init() {
  bindChromeScrollState();
  bindFlowToggles();
  buildMaterialRail();
  buildSankeyRail();

  const context = window.STORY_CONTEXT;
  if (!context) {
    return;
  }

  renderHeroStats(context);
  updateNotebookLinks(context);
  renderNarrativeFacts(context);
}

init();
