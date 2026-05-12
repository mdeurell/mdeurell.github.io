"""
Critical Earth — Plotly Theme.

Import this in any notebook or script:
    from theme import LAYOUT, COLORS, MINERAL_COLORS, COUNTRY_COLORS
"""
from pathlib import Path

# ── Font ────────────────────────────────────────────────────
FONT_FAMILY        = "Lato, -apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif"
FONT_SERIF         = "'Playfair Display', Georgia, 'Times New Roman', serif"
FONT_BODY          = "Georgia, 'Times New Roman', Times, serif"

# ── Core Palette ────────────────────────────────────────────
MIDNIGHT      = "#0D1B2A"
DEEP_SLATE    = "#1B3A4B"
# Primary accent — Prussian blue (cartographic, editorial). The legacy
# variable name is kept so the 100+ existing references still resolve.
MOLTEN_ORANGE = "#0F3D5C"
PRUSSIAN      = "#0F3D5C"   # alias for clarity
OXBLOOD       = "#7B2D26"   # secondary accent — used sparingly for emphasis
RAW_CHALK     = "#F0EDE5"
WARM_WHITE    = "#FAF9F6"
OFF_BLACK     = "#1A1A1A"

# Newspaper / paper-aesthetic palette (matches website CSS tokens)
PAPER_WARM   = "#F7F4EE"
PAPER_COOL   = "#F1EEE7"
PAPER_INK    = "#14110D"
PAPER_RULE   = "rgba(15, 61, 92, 0.55)"
PAPER_RULE_S = "rgba(15, 61, 92, 0.18)"  # subtle gridline

# ── Mineral Colors ──────────────────────────────────────────
MINERAL_COLORS = {
    # Case 1: Abundant but captive
    "Neodymium":    "#3AAFA9",  # teal   — LREE flagship
    "Lithium":      "#45B7D1",  # sky blue
    "Copper":       "#8B5A2B",  # deep bronze — desaturated to avoid orange read
    "Graphite":     "#5C5C5C",  # dark grey
    # Case 2: Scarce and captured
    "Dysprosium":   "#C49A02",  # amber  — HREE flagship
    "Terbium":      "#E040A0",  # magenta — HREE, paired with Dy
    "Cobalt":       "#3A5EA5",  # blue
    "Gallium":      "#6E8898",  # slate blue-grey — distinct from Cobalt/Lithium/Graphite
    "Platinum":     "#A8A8A8",  # silver
    # REE aggregate (overlay / macro lens)
    "Rare Earths":  "#A07850",  # earthy ochre — canonical REE colour (matches deposit map)
}

# Ordered for chart color sequences
COLORS = list(MINERAL_COLORS.values())

# ── Country Colors ──────────────────────────────────────────
COUNTRY_COLORS = {
    "China":        "#DE2910",
    "United States":"#3C3B6E",
    "EU":           "#003399",
    "Australia":    "#FFD700",
    "South Africa": "#007A4D",
    "Democratic Republic of the Congo": "#007FFF",
    "Congo (Kinshasa)": "#007FFF",
    "Chile":        "#D52B1E",
    "Japan":        "#BC002D",
    "Russia":       "#6B6B6B",
    "Other":        "#888888",
}

# ── Plotly Layout (dark theme) ──────────────────────────────
LAYOUT = dict(
    font=dict(
        family=FONT_FAMILY,
        color=RAW_CHALK,
        size=14,
    ),
    title_font=dict(
        family=FONT_FAMILY,
        size=22,
    ),
    paper_bgcolor=MIDNIGHT,
    plot_bgcolor=MIDNIGHT,
    margin=dict(l=60, r=30, t=80, b=60),
    legend=dict(
        font=dict(size=12),
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
    ),
    xaxis=dict(
        gridcolor="rgba(240,237,229,0.08)",
        zerolinecolor="rgba(240,237,229,0.15)",
        tickfont=dict(size=12),
    ),
    yaxis=dict(
        gridcolor="rgba(240,237,229,0.08)",
        zerolinecolor="rgba(240,237,229,0.15)",
        tickfont=dict(size=12),
    ),
    hoverlabel=dict(
        bgcolor=DEEP_SLATE,
        font_size=13,
        font_family=FONT_FAMILY,
        bordercolor="rgba(255,255,255,0.45)",
    ),
    colorway=COLORS,
)

# ── Plotly Layout (newspaper / paper aesthetic) ─────────────
# Used as the default site-wide theme. Paper-warm background, ink text,
# Prussian-blue thin rules, Playfair Display titles, Lato chrome.
# Sizes are calibrated for the site's 70vw default figure width
# (~900px iframe). Charts displayed at full bleed still look fine; charts
# squeezed below ~600px will start to crowd.
LAYOUT_NEWSPAPER = dict(
    font=dict(
        family=FONT_FAMILY,
        color=PAPER_INK,
        size=14,
    ),
    title=dict(
        font=dict(family=FONT_SERIF, size=28, color=PAPER_INK),
        x=0.0,
        xanchor="left",
        y=0.97,
        yanchor="top",
        pad=dict(l=4, t=10, b=10),
    ),
    paper_bgcolor=PAPER_WARM,
    plot_bgcolor=PAPER_WARM,
    margin=dict(l=70, r=40, t=110, b=90),
    legend=dict(
        font=dict(family=FONT_FAMILY, size=13, color=PAPER_INK),
        bgcolor="rgba(0,0,0,0)",
        borderwidth=0,
        orientation="h",
        yanchor="top",
        y=-0.18,
        xanchor="left",
        x=0,
        title=dict(text=""),
    ),
    xaxis=dict(
        gridcolor=PAPER_RULE_S,
        zerolinecolor=PAPER_RULE,
        linecolor=PAPER_RULE,
        tickcolor=PAPER_RULE,
        tickfont=dict(family=FONT_FAMILY, size=13, color=PAPER_INK),
        title=dict(font=dict(family=FONT_FAMILY, size=13, color=PAPER_INK)),
    ),
    yaxis=dict(
        gridcolor=PAPER_RULE_S,
        zerolinecolor=PAPER_RULE,
        linecolor=PAPER_RULE,
        tickcolor=PAPER_RULE,
        tickfont=dict(family=FONT_FAMILY, size=13, color=PAPER_INK),
        title=dict(font=dict(family=FONT_FAMILY, size=13, color=PAPER_INK)),
    ),
    hoverlabel=dict(
        bgcolor=PAPER_INK,
        font=dict(family=FONT_FAMILY, size=13, color=PAPER_WARM),
        bordercolor=MOLTEN_ORANGE,
    ),
    colorway=COLORS,
)

# Backwards-compat alias — older callers expect LAYOUT_LIGHT
LAYOUT_LIGHT = LAYOUT_NEWSPAPER


# ── Helper: Apply theme to a figure ─────────────────────────
def apply_theme(fig, dark=False):
    """Apply Critical Earth newspaper theme to a Plotly figure.

    dark=True falls back to the legacy navy theme (used by maps with
    dark basemaps). Default is the newspaper / paper-warm aesthetic.
    """
    if dark:
        fig.update_layout(template="plotly_dark", **LAYOUT)
    else:
        fig.update_layout(template="plotly_white", **LAYOUT_NEWSPAPER)
    return fig


# ── Helper: Canonical write (modebar off, legend top, fonts enforced) ──
def write_chart(fig, path, *, static=False, legend_pos="top", legend_y=None):
    """Apply theme + enforce site-wide visual code + write HTML.

    - Disables Plotly modebar entirely (no zoom/pan/download UI).
    - Forces legend position (default: above plot, horizontal, left-aligned).
    - Re-applies Lato to all ticks and Playfair to subplot titles.
    - `static=True` disables ALL interactions (used for Sankey).
    """
    # Snapshot any chart-specific margin BEFORE apply_theme — otherwise
    # LAYOUT_NEWSPAPER's default margin clobbers what the builder set.
    user_margin = None
    try:
        m = fig.layout.margin
        if m and (m.l is not None or m.r is not None or m.t is not None or m.b is not None):
            user_margin = dict(l=m.l, r=m.r, t=m.t, b=m.b)
    except Exception:
        pass

    apply_theme(fig)

    if user_margin is not None:
        fig.update_layout(margin={k: v for k, v in user_margin.items() if v is not None})

    if legend_pos == "top":
        ly = 1.06 if legend_y is None else legend_y
        fig.update_layout(legend=dict(
            orientation="h", yanchor="bottom", y=ly,
            xanchor="right", x=1.0,
            font=dict(family=FONT_FAMILY, size=14, color=PAPER_INK),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            title=dict(text=""),
        ))
    elif legend_pos == "top-center":
        ly = 1.06 if legend_y is None else legend_y
        # xref="container" puts the anchor into iframe-pixel coords
        # instead of paper coords, so x=0.5 is the geometric centre of
        # the visible chart regardless of asymmetric margins.
        fig.update_layout(legend=dict(
            orientation="h", yanchor="bottom", y=ly,
            xanchor="center", x=0.5, xref="container",
            font=dict(family=FONT_FAMILY, size=14, color=PAPER_INK),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            title=dict(text=""),
        ))
        # apply_theme's LAYOUT_NEWSPAPER stamps r=40 onto every chart,
        # which leaves the plot off-axis from a paper-centred legend.
        # Re-symmetrize after the fact.
        try:
            ml = int(fig.layout.margin.l or 80)
            fig.update_layout(margin=dict(r=ml))
        except Exception:
            pass
    elif legend_pos == "bottom":
        ly = -0.22 if legend_y is None else legend_y
        fig.update_layout(legend=dict(
            orientation="h", yanchor="top", y=ly,
            xanchor="right", x=1.0,
            font=dict(family=FONT_FAMILY, size=14, color=PAPER_INK),
            bgcolor="rgba(0,0,0,0)", borderwidth=0,
            title=dict(text=""),
        ))
    elif legend_pos == "none":
        fig.update_layout(showlegend=False)

    # Indent the title so it visually aligns with the start of the plot
    # area (not the iframe edge). Plotly's title.x is paper-fractional;
    # we pad it by the left margin in pixels.
    try:
        left_margin_px = int(fig.layout.margin.l or 70)
    except Exception:
        left_margin_px = 70
    fig.update_layout(title=dict(
        x=0.0, xanchor="left",
        pad=dict(l=left_margin_px, t=10, b=10),
    ))

    # Enforce axis fonts on every axis (including subplots)
    fig.update_xaxes(
        tickfont=dict(family=FONT_FAMILY, size=13, color=PAPER_INK),
        title_font=dict(family=FONT_FAMILY, size=14, color=PAPER_INK),
        gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE, zerolinecolor=PAPER_RULE,
    )
    fig.update_yaxes(
        tickfont=dict(family=FONT_FAMILY, size=13, color=PAPER_INK),
        title_font=dict(family=FONT_FAMILY, size=14, color=PAPER_INK),
        gridcolor=PAPER_RULE_S, linecolor=PAPER_RULE, zerolinecolor=PAPER_RULE,
    )

    # Subplot titles (make_subplots) live in fig.layout.annotations and
    # default to Open Sans — force Playfair.
    for ann in fig.layout.annotations or []:
        # Heuristic: subplot titles have no xref/yref or use paper refs and
        # were not explicitly styled by the caller (no bgcolor/border).
        if ann.font is None or ann.font.family is None:
            ann.font = dict(family=FONT_SERIF, size=16, color=PAPER_INK)

    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=PAPER_INK),
        paper_bgcolor=PAPER_WARM, plot_bgcolor=PAPER_WARM,
        hoverlabel=dict(
            bgcolor=PAPER_INK,
            font=dict(family=FONT_FAMILY, size=13, color=PAPER_WARM),
            bordercolor=PRUSSIAN,
        ),
    )

    config = {
        "displayModeBar": False,
        "displaylogo": False,
        "responsive": True,
        "staticPlot": bool(static),
        "scrollZoom": False,
        "doubleClick": False if static else "reset",
    }
    fig.update_layout(autosize=True)
    fig.write_html(path, include_plotlyjs="cdn", full_html=True, config=config)
    # Suppress scrollbars on the embedded body and force the plot to fill
    # the iframe — site CSS handles the outer aspect ratio.
    html = Path(path).read_text(encoding="utf-8")
    inject_css = (
        "<style>html,body{margin:0;padding:0;overflow:hidden;height:100%;}"
        ".plotly-graph-div{width:100% !important;height:100% !important;}</style>"
    )
    # ResizeObserver — Plotly's autosize only fires on window.resize, which
    # doesn't trigger when the iframe is sized by CSS aspect-ratio after
    # initial render. Without this, charts render at the iframe's first
    # observed pixel width and never grow — visible as plots squeezed into
    # the left half of the iframe even though the iframe itself spans full
    # width.
    inject_js = (
        "<script>window.addEventListener('load',function(){"
        "var d=document.querySelector('.plotly-graph-div');"
        "if(!d||!window.Plotly)return;"
        "var resize=function(){Plotly.Plots.resize(d);};"
        "resize();"
        "if(window.ResizeObserver){new ResizeObserver(resize).observe(document.body);}"
        "window.addEventListener('resize',resize);"
        "});</script>"
    )
    html = html.replace("</head>", inject_css + inject_js + "</head>", 1)
    Path(path).write_text(html, encoding="utf-8")
    return path


# ── Helper: Get mineral color ────────────────────────────────
def mineral_color(name):
    """Get hex color for a mineral name (case-insensitive)."""
    for key, val in MINERAL_COLORS.items():
        if key.lower() == name.lower():
            return val
    return MOLTEN_ORANGE  # fallback


# ── Helper: Get country color ────────────────────────────────
def country_color(name):
    """Get hex color for a country name."""
    for key, val in COUNTRY_COLORS.items():
        if key.lower() in name.lower():
            return val
    return "#888888"  # fallback
