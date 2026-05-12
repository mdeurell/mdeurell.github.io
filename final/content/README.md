# Authoring guide — Critical Earth

This directory holds the **editable source of the website**. The page you see at
`website/index.html` is **generated** from these YAML files plus the templates in
`/templates`. Never edit `website/index.html` by hand — your changes will be
overwritten on the next build.

This guide is written for two audiences: human collaborators editing prose and
agents (LLMs) inserting or modifying sections programmatically.

---

## TL;DR — the 60-second version

```
content/
├── site.yaml             ← page metadata, hero, nav, section order
└── sections/             ← one YAML file per section, in any order
    ├── 00_prologue.yaml
    ├── 01_fine_tech.yaml
    ├── …
    └── 07_conclusion.yaml
```

Each section file is a list of **blocks** — typed content units (`prose`,
`figure`, `factbox`, …). Every block becomes one or two `<section>` elements
in the HTML, with the global chrome (caption frames, font sizes, paper-warm
background) baked into the templates.

Workflow:

```bash
# Edit a YAML file, then:
python -m pipeline.build.build_index

# Or, while iterating:
python -m pipeline.build.build_index --watch
# (rebuilds on every save in content/ or templates/)
```

---

## How a section flows from YAML to HTML

```
content/sections/03_attractive.yaml      ┐
templates/blocks/prose.html.j2           │
templates/blocks/figure.html.j2          ├──► python -m pipeline.build.build_index
templates/blocks/factbox.html.j2         │       ↓
templates/index.html.j2                  ┘   website/index.html
```

The build script:

1. Loads `site.yaml`.
2. For each filename listed under `sections:`, loads the matching file from
   `sections/`.
3. For each `block` in that section, renders the partial
   `templates/blocks/<block.type>.html.j2`.
4. Splices everything into `templates/index.html.j2` and writes
   `website/index.html`.

You can add a new section by creating one YAML file and adding its filename to
`site.yaml`. **No code change needed.**

---

## site.yaml

Top-level page config. Edit when you change the page title, hero image,
primary nav, or want to add/remove/reorder sections.

```yaml
title: Critical Materials
description: A narrative website about critical material trade…

wordmark: Critical Earth                          # text in the top-left header
notebook_href: explainer_notebook.ipynb           # "Open notebook" button target

hero:
  bg_image: images/hero.webp
  kicker: A Critical Earth investigation
  title_html: |                                   # raw HTML allowed
    The Materials<br>of Civilization
    <em>The new mastery of the atom</em>
  byline: DTU 02806 · Social Data Analysis & Visualization

nav:                                              # primary nav links
  - { href: "#stakes",      label: "Why it matters" }
  - { href: "#deposits",    label: "Where they are" }
  - { href: "#case-1",      label: "Case 1" }

footer:
  title: Critical Earth
  body: Built from processed master datasets…

sections:                                         # ordered list of section files
  - 00_prologue.yaml
  - 01_fine_tech.yaml
  - 02_deposits.yaml
  - 003_attractive.yaml
  - …
```

Reorder by reordering the `sections:` list. Remove a section by deleting the
line. The filename prefix (`03_…`) is for **humans only** — the build doesn't
care about numbering, it follows the order in `sections:`.

---

## Section YAML structure

A section file has two top-level keys:

```yaml
id: attractive            # optional; becomes anchor id on the FIRST block
class: longform--econ     # optional; default class flows down to all blocks
                          # in this section (overrideable per-block)
blocks:
  - type: prose
    …
  - type: figure
    …
```

`id` and `class` flow into the first matching block. Most sections only need
`blocks:`.

`blocks:` is a list. Each entry has a required `type:` field that tells the
build which template to render. Order matters — blocks render top-to-bottom
in the page in the order you list them.

---

## Block types — quick reference

| Type | Use for |
|---|---|
| `prose` | Body text. Markdown supported. Eyebrow + heading + paragraphs. Most-used block. |
| `standfirst` | A single styled lede paragraph (e.g. the prologue at the top of the page). |
| `figure` | Chart / map iframe + Prussian-blue framed caption. |
| `figure_pair` | Two figures side-by-side (e.g. before/after). One shared caption. |
| `animation_toggle` | A figure with toggle buttons (e.g. Exports/Imports switch). |
| `image` | Static image (photo, diagram) with caption. |
| `carousel` | The horizontal-scroll material-rail. (Cards rendered by JS from data.) |
| `chapter_mark` | A "Part II" divider with eyebrow + italic Playfair title + standfirst. |
| `factbox` | Highlighted callout — key fact, percentage, or quote pull. |
| `pull_quote` | Big italic Playfair pull quote inside body text. |
| `margin_note` | Short aside that floats to the right of body text on wide screens. |
| `raw` | Escape hatch for one-off HTML that doesn't fit any block type. |

Every block lives inside the page's global typography & color system. You don't
choose fonts, sizes, paper background, or caption-frame color in YAML — those
live in `website/css/site.css` and apply globally.

---

## Block reference — every type with an example

### `prose` — body text

The workhorse. A `.longform` section with a narrow `.longform-inner` column
(roughly 42rem / 65ch reading width).

```yaml
- type: prose
  id: deposits                    # optional; sets <section id="…"> for nav anchor
  eyebrow: "Section 2 · Where they are"   # small uppercase line above the heading
  heading: "The map is not the bottleneck"  # H2 in Lato extrabold
  dropcap: true                   # default true — first <p> gets the molten-orange dropcap
  text: |                         # markdown — multiple paragraphs OK
    The raw materials for the energy transition exist on every continent.
    Africa, Latin America, Australia all hold significant deposits…

    A country that mines a mineral does not automatically capture its
    value. **Deposits are everywhere; chokepoints are not.**

  rule_after: false               # optional — append <hr class="longform-rule">
  standfirst_after: |             # optional — append a styled italic lede paragraph
    The question today is whether…
  class: longform--econ           # optional — apply econ-chapter modifier
```

**Rendering**: markdown in `text` is converted to HTML. Bold, italic, links,
inline code, lists, raw HTML spans (e.g. `<span class="figure-takeaway">`) all
work. The first paragraph is wrapped in `class="dropcap"` unless you set
`dropcap: false`.

---

### `standfirst` — single lede paragraph

Used between the hero and Section 1, or as a closing pivot.

```yaml
- type: standfirst
  id: standfirst                  # optional
  eyebrow: "Section 0 · Prologue" # optional uppercase line above
  text: |
    The history of civilization is anchored by the materials we master.
```

---

### `figure` — chart / map with caption

Two `<section>` elements: the iframe wrapper and the caption frame. Caption
gets the global Prussian-blue top/bottom rule automatically.

```yaml
- type: figure
  src: visualizations/stakes/price_index.html   # iframe path (required)
  alt: "Price shock index — ten focal materials, 2015 = 100"
  title: "Price shock index"        # iframe title attribute
  aria_label: "Price index figure"  # outer story-section aria-label
  figure_number: "Figure 5.1"       # required for the bold "Figure 5.1." prefix
  frame_class: map-frame            # optional: 'map-frame' (21:9) or 'tall-frame' (4:3)
                                    # default is 16:9
  bleed: true                       # default — wraps in .viz-bleed for full-bleed sections
  frameless: true                   # default — no border around the iframe
  dark: false                       # set true for dark-card sections (e.g. world map)
  section_class: story-section--econ  # optional modifier on the outer story-section
  caption_id: deposits-caption       # optional <section id="…"> on the caption section
  caption_footnote_id: deposits-coverage   # optional <span> for JS to fill at runtime
  caption_in_margin: true            # optional — pull caption into right margin
                                     # (figure stays at its natural width)
  caption: |                        # markdown
    Annual price index for ten focal materials, 1995–2022, normalized
    on 2015 USD level. Source: USGS MCS 2025.
```

**Aspect ratios** are controlled by `frame_class`:
- (none) → 16:9 (default for charts)
- `map-frame` → 21:9 (for world maps)
- `tall-frame` → 4:3 (for tall layouts like Sankey)

**Figure width** is controlled by `figure_size`:
- `text` (default) → centred at 70vw — the global house style
- `text-wide` → text column + 50% on each side, centred (~95vw)
- `bleed` → full viewport, edge to edge

Maps (`frame_class: map-frame`) and wide-timeline charts
(`frame_class: wide-frame`) auto-opt-out of the 70vw default and render
at full bleed instead. Carousels are a separate block type
(`type: carousel`) and are not affected.

**Caption position** is controlled separately by `caption_in_margin`:
- `false` (default) → caption sits below the figure at matching width
- `true` → caption pulled into the right margin; figure stays at its
  `figure_size` width

> **Note** — the legacy `figure_size: margin` value is now an alias for
> `figure_size: bleed, caption_in_margin: true`. It used to shrink the
> iframe to ~28rem, but Plotly chart text (titles, axis labels) is SVG and
> doesn't reflow with the iframe — the result was clipped titles and
> overlapping ticks. Author new figures with the explicit
> `caption_in_margin: true` field instead.

---

### `figure_pair` — two figures side-by-side

For before/after comparisons (e.g. trade flows 2015 vs 2023). One shared
caption below.

```yaml
- type: figure_pair
  aria_label: "Bilateral trade flow comparison"
  section_class: story-section--econ
  left:
    eyebrow: "2015 · Pre-shock baseline"
    src: visualizations/bifurcation/trade_flows_2015.html
    title: "China critical-mineral exports, 2015"
  right:
    eyebrow: "2023 · Latest available"
    src: visualizations/bifurcation/trade_flows_2023.html
    title: "China critical-mineral exports, 2023"
  figure_number: "Figure 5.3"
  caption_footnote_id: bifurcation-summary
  caption: |
    Bilateral export flows of the eight critical-mineral HS codes used
    in this study, with China as reporter…
```

---

### `animation_toggle` — figure with switcher buttons

Used for the China-flow animation (Exports / Imports). The toggle wires up
via `main.js`: each button changes the iframe src.

```yaml
- type: animation_toggle
  aria_label: "China flow animation"
  section_class: story-section--econ
  frame_id: china-flow-frame              # iframe id (referenced by JS)
  frame_class: tall-frame
  default_src: visualizations/bifurcation/china_flow_exports.html
  title: "China critical-mineral trade flows, animated 2000–2024"
  toggles:
    - { label: "Exports", flow: "exports", src: "visualizations/bifurcation/china_flow_exports.html", active: true }
    - { label: "Imports", flow: "imports", src: "visualizations/bifurcation/china_flow_imports.html", active: false }
  figure_number: "Figure 6"
  caption: |
    Animated bilateral trade flows with China as reporter, 2000–2024…
```

---

### `image` — static image with caption

```yaml
- type: image
  src: images/diagram.png
  alt: "Cobalt supply chain schematic"
  aspect: 16/9                    # optional CSS aspect-ratio
  bleed: true                     # default true — full-bleed
  figure_number: "Figure 1"
  caption: |
    A schematic of the cobalt supply chain.
```

---

### `carousel` — material-rail (horizontal-scroll)

The actual cards are rendered by `main.js` from `data/story_context.js`.
This block emits the shell.

```yaml
- type: carousel
  aria_label: "The portfolio"
  eyebrow: "Section 1 · The portfolio"
  heading: "Ten materials, one fragile system"
  standfirst: |
    A scrolling encyclopedia of the elements at the heart of this story.
  rail_id: material-rail          # default; change only if you have multiple
  nav_id: material-nav
```

---

### `chapter_mark` — Part II divider

```yaml
- type: chapter_mark
  aria_label: "Part II opener"
  eyebrow: "Part II"
  title: "The economics of dependence"
  standfirst: |
    From geology to the ledger…
```

---

### `factbox` — highlighted callout

Sits inside `.longform-inner` like prose; left border in Prussian blue (or
oxblood / orange via `tone:`).

```yaml
- type: factbox
  heading: "The Cobalt Trap"
  tone: oxblood                   # 'neutral' (default) | 'orange' | 'oxblood'
  align: right                    # optional: omit | 'left' | 'right'
                                  # omit  → renders inline within the prose column
                                  # right → floats into the right margin
                                  # left  → floats into the left margin (mirror)
  body: |
    **DRC mines 76%** of global cobalt as crude hydroxide; the material
    ships out as a partially processed export. **China refines 80%** of it.

    The ore-holder earns the extraction risk. The refiner captures the value.
```

**Margin positioning.** When a factbox immediately follows a long-enough
prose block (≥ 2 paragraphs OR ≥ 600 chars), `build_index` automatically
absorbs it into that prose and renders it as a margin aside. The same
`align: left | right` field controls which margin it floats into; the
default is `right` to match historical behaviour. Set `align: left` when
you want the box to wrap text on its right side instead.

---

### `pull_quote` — big italic Playfair quote

```yaml
- type: pull_quote
  text: |
    Concentration in *processing*, not in mining, is the layer where
    strategic vulnerability lives.
  source: Conclusion of Section 7    # optional attribution
```

---

### `margin_note` — sidebar aside

Floats to the right on wide screens, falls inline below 768px.

```yaml
- type: margin_note
  heading: "Method note"
  body: |
    All percentages are rounded to the nearest integer. See the
    explainer notebook for source data.
```

---

### `raw` — HTML escape hatch

Use sparingly — for one-off layouts that don't fit any block type.

```yaml
- type: raw
  html: |
    <div class="custom-thing">
      <p>Anything goes here.</p>
    </div>
```

---

## Markdown in YAML — what's supported

Inside `text`, `caption`, `body`, `standfirst`, etc., the build runs the
content through [mistune](https://mistune.lepture.com/). Supported:

- `**bold**`, `*italic*`, `~~strikethrough~~`
- `[link text](https://example.com)`
- `` `inline code` ``
- Numbered and bulleted lists
- Tables (GitHub-flavoured)
- Raw HTML (e.g. `<span class="figure-takeaway">…</span>`,
  `<em>n</em>`, `<strong>` — useful for inline classes the body markdown
  can't express)
- Em-dash `—`, en-dash `–`, ellipsis `…`, smart quotes — paste UTF-8 directly

The first paragraph in a `prose` block is wrapped with `.dropcap` automatically.
Set `dropcap: false` to opt out.

For **inline-only** rendering (e.g. inside a `<p class="figure-caption">`,
which mustn't contain its own `<p>` from markdown), the build uses
`md_inline` which strips the wrapping `<p>`.

### Special characters

YAML's block scalar `|` preserves newlines verbatim:

```yaml
text: |
  Line one.
  Line two.
```

If your text contains a colon, quote it or use the block scalar:

```yaml
heading: 'When geology and industry pull the same way'
```

---

## How to add a new section

1. Create `content/sections/08_my_section.yaml`:

   ```yaml
   id: my-section
   blocks:
     - type: prose
       id: my-section
       eyebrow: "Section 8 · My new chapter"
       heading: "A new heading"
       text: |
         Body paragraph one.

         Body paragraph two.
   ```

2. Add to `content/site.yaml` under `sections:` in the position you want it:

   ```yaml
   sections:
     - 07_conclusion.yaml
     - 08_my_section.yaml          # new
   ```

3. Optionally add a nav link:

   ```yaml
   nav:
     - …
     - { href: "#my-section", label: "My new chapter" }
   ```

4. Rebuild:

   ```bash
   python -m pipeline.build.build_index
   ```

That's it. No template change, no JS change, no CSS change.

---

## How to add a new figure (visualization)

1. Generate the iframe HTML — typically by adding a function to
   `pipeline/build/build_visualizations.py` (or `build_attractive_charts.py`)
   that uses `apply_theme(fig)` and writes to
   `website/visualizations/<chapter>/<name>.html`.

2. Reference it from a section YAML:

   ```yaml
   - type: figure
     src: visualizations/<chapter>/<name>.html
     alt: "Description for screen readers"
     title: "Title for hover tooltip"
     figure_number: "Figure X.Y"
     caption: |
       Markdown body of the caption with sources and takeaway.
   ```

3. Run both build steps:

   ```bash
   python -m pipeline.build.build_visualizations    # regenerate the chart
   python -m pipeline.build.build_index             # regenerate index.html
   ```

The locked theme (`website/theme.py` → `LAYOUT_NEWSPAPER`) gives every chart
the same look: paper-warm bg, Lato/Playfair, big Playfair title with subtitle,
legend top-right, axis ticks 17px, `tickprefix`/`ticksuffix` for units. Do not
override these in the chart-specific code — change `theme.py` if you want a
global shift.

---

## How to add a new block type

If none of the existing blocks fit, you can add a new type:

1. Drop a Jinja template in `templates/blocks/<my_type>.html.j2`.
2. Reference it from any section YAML with `type: my_type`.

The build's dynamic include picks it up automatically — no code change to
`build_index.py`.

The template receives:
- `block` — the YAML dict for this block
- `section` — the surrounding section dict (for inherited `class`, etc.)
- `site` — the top-level site config

Style new block types by adding CSS classes to `website/css/site.css`.

---

## Build commands

```bash
# One-shot build
python -m pipeline.build.build_index

# Watch mode — rebuilds on every YAML or template change. Recommended while
# iterating on copy or layout.
python -m pipeline.build.build_index --watch

# Regenerate the data-bound visualizations (Figs 5.1 – 6)
python -m pipeline.build.build_visualizations

# Regenerate Sections 3 + 4 figures (data is hardcoded, no CSV needed)
python -m pipeline.build.build_attractive_charts
```

Each build prints the output filename and length, plus the asset version
(used as cache-busting query string on the CSS links).

---

## Common pitfalls

**"My change isn't showing in the browser."**
1. Did you rebuild? `python -m pipeline.build.build_index`. Watch mode helps.
2. Browser cache. The build emits a fresh `?v=<timestamp>` on every CSS link,
   but if you've cached the HTML itself, hard-refresh (Ctrl+F5).

**"YAML parser error on my section."**
A colon in a heading or eyebrow is the most common cause:
```yaml
heading: When geology meets: industry        # ✗ breaks YAML
heading: "When geology meets: industry"      # ✓ quoted
heading: |                                   # ✓ block scalar
  When geology meets: industry
```

**"My block renders but with weird whitespace / a broken `<p>`."**
Check that `dropcap` isn't being applied to a non-prose-style block. If your
first paragraph starts with raw HTML, set `dropcap: false`.

**"My iframe shows a blank chart."**
The iframe `src` is relative to `website/index.html`. So
`visualizations/stakes/price_index.html` (no leading slash) is correct. The
file must exist — verify with `ls website/visualizations/<chapter>/`.

**"The caption width doesn't match the figure width."**
Both should max at `var(--bleed)` (= 2400px). If your figure has an unusual
container, make sure it stays inside `.viz-bleed` or `.story-section`.

**"I changed `theme.py` but my chart still looks old."**
Plotly bakes the layout into the HTML at build time. Re-run
`python -m pipeline.build.build_visualizations` (or
`build_attractive_charts.py`) to regenerate the chart files.

---

## Files an editor never needs to touch

- `website/index.html` — generated, overwritten on every build
- `website/css/critical-earth.css` — global tokens (colours, fonts, widths)
- `website/css/site.css` — block styles (longform, figure, factbox, …)
- `website/js/main.js` — interactivity (toggles, story_context wiring)
- `pipeline/build/build_index.py` — the build script itself
- `templates/**/*.j2` — block partials

If you need to change one of these, you're doing something more ambitious than
authoring content — see the comments at the top of each file for context.

---

## File ownership at a glance

| What you're doing | Edit this |
|---|---|
| Fixing a typo in body text | `content/sections/<n>.yaml` |
| Adding a new paragraph | `content/sections/<n>.yaml` |
| Reordering sections | `content/site.yaml` (`sections:` list) |
| Changing the page title or hero | `content/site.yaml` |
| Adding a new figure | new function in `pipeline/build/*.py`, then reference in YAML |
| Adding a new block type | new file in `templates/blocks/`, optional CSS in `site.css` |
| Changing fonts or colours globally | `website/css/critical-earth.css` |
| Changing chart fonts / sizes globally | `website/theme.py` (`LAYOUT_NEWSPAPER`) |
| Changing the Prussian-blue caption frame | `website/css/site.css` (search for `.figure-caption`) |

---

## For agents working in this repo

- **Never edit `website/index.html` directly.** It is regenerated from
  `content/` + `templates/`. Edit the YAML or template instead, then run
  `python -m pipeline.build.build_index`.
- **Per-section YAMLs are the unit of context.** When asked to modify
  Section N, load only that one YAML — typically 50–150 lines — instead of
  the whole `index.html`.
- **Block types are extension points.** If you need a new content shape,
  prefer adding a new template under `templates/blocks/` and a CSS rule in
  `site.css` over inlining HTML via `raw`.
- **Charts are data-bound and theme-locked.** Don't override fonts,
  colors, or background per-chart. If you want a global change, edit
  `website/theme.py` and rerun the chart build.
- **Cache-busting is automatic.** The build stamps a UTC timestamp into
  the CSS link's `?v=…` query, so a rebuild forces clients to reload styles
  on next page load.
