"""
Generates website/visualizations/deposits/deposit_map.html
Country-level choropleth: deposit count per mineral, switchable via dropdown.
"""
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Load ──────────────────────────────────────────────────────────────────────
with open(ROOT / 'data/processed/master_geo_deposits.geojson', encoding='utf-8') as f:
    gj = json.load(f)

records = []
for feat in gj['features']:
    p = feat['properties']
    if p.get('iso3'):
        records.append({
            'mineral':  p['mineral'],
            'iso3':     p['iso3'],
            'country':  p['country'],
            'dep_name': p.get('deposit_name') or '',
        })
df = pd.DataFrame(records)
minerals = sorted(df['mineral'].unique())

# ── Colour palette ─────────────────────────────────────────────────────────────
MINERAL_HEX = {
    'Lithium':     '#4C9BE8',
    'Cobalt':      '#B44FE8',
    'Copper':      '#F97316',
    'Graphite':    '#94A3B8',
    'Neodymium':   '#10D98B',
    'Dysprosium':  '#EC4899',
    'Terbium':     '#A3E635',
    'Gallium':     '#06B6D4',
    'Platinum':    '#FBBF24',
    'Rare Earths': '#F87171',
}
DARK_BG    = '#16213e'
OCEAN_BG   = '#0f1a35'
LAND_BASE  = '#1e2845'
BORDER_COL = '#2a3560'

def hex_to_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def mineral_scale(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    # 5-stop scale: dark base → dim → mid → bright mineral colour
    return [
        [0.00, LAND_BASE],
        [0.10, f'rgb({int(r*.15)},{int(g*.15)},{int(b*.15)})'],
        [0.35, f'rgb({int(r*.4)},{int(g*.4)},{int(b*.4)})'],
        [0.65, f'rgb({int(r*.7)},{int(g*.7)},{int(b*.7)})'],
        [1.00, f'rgb({r},{g},{b})'],
    ]

ALL_SCALE = [
    [0.00, LAND_BASE],
    [0.10, '#2d3a6e'],
    [0.30, '#6b4c1a'],
    [0.55, '#c47a1a'],
    [0.80, '#f0a500'],
    [1.00, '#fff5cc'],
]

def log_ticks(max_val):
    candidates = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
    vals = [v for v in candidates if v <= max_val]
    return (
        [np.log1p(v) for v in vals],
        [str(v) for v in vals],
    )

def colorbar_cfg(title, max_val, hex_color=None):
    tv, tt = log_ticks(max_val)
    return dict(
        title=dict(text=title, font=dict(color='white', size=11)),
        tickvals=tv, ticktext=tt,
        tickfont=dict(color='white', size=9),
        bgcolor='rgba(22,33,62,0.85)',
        bordercolor='#444',
        borderwidth=1,
        thickness=12,
        len=0.6,
        x=1.01,
    )

# ── Build traces ───────────────────────────────────────────────────────────────
traces = []

# ── "All" trace (unique deposit locations deduplicated by mineral_group = REE shares)
# Count each deposit only once by grouping on (iso3, dep_name) and taking first mineral
all_dedup = (
    df.groupby(['iso3', 'dep_name'])
    .first()
    .reset_index()[['iso3', 'country']]
)
all_counts = all_dedup.groupby(['iso3', 'country']).size().reset_index(name='count')
all_max    = all_counts['count'].max()
tv, tt = log_ticks(all_max)

traces.append(go.Choropleth(
    name='All minerals',
    locations=all_counts['iso3'],
    z=np.log1p(all_counts['count']),
    zmin=0, zmax=np.log1p(all_max),
    customdata=np.stack([all_counts['country'], all_counts['count']], axis=-1),
    hovertemplate='<b>%{customdata[0]}</b><br>Total deposits: %{customdata[1]}<extra></extra>',
    colorscale=ALL_SCALE,
    showscale=True,
    colorbar=dict(
        title=dict(text='Total deposits', font=dict(color='white', size=11)),
        tickvals=tv, ticktext=tt,
        tickfont=dict(color='white', size=9),
        bgcolor='rgba(22,33,62,0.85)',
        bordercolor='#444', borderwidth=1,
        thickness=12, len=0.6, x=1.01,
    ),
    visible=True,
    marker_line_color=BORDER_COL,
    marker_line_width=0.4,
))

# ── Per-mineral traces
for mineral in minerals:
    sub    = df[df['mineral'] == mineral]
    counts = sub.groupby(['iso3', 'country']).size().reset_index(name='count')
    mmax   = counts['count'].max()
    hex_c  = MINERAL_HEX.get(mineral, '#888888')
    tv, tt = log_ticks(mmax)

    traces.append(go.Choropleth(
        name=mineral,
        locations=counts['iso3'],
        z=np.log1p(counts['count']),
        zmin=0, zmax=np.log1p(mmax),
        customdata=np.stack([counts['country'], counts['count']], axis=-1),
        hovertemplate=f'<b>%{{customdata[0]}}</b><br>{mineral}: %{{customdata[1]}} deposits<extra></extra>',
        colorscale=mineral_scale(hex_c),
        showscale=True,
        colorbar=dict(
            title=dict(text=f'{mineral}<br>deposits', font=dict(color='white', size=11)),
            tickvals=tv, ticktext=tt,
            tickfont=dict(color='white', size=9),
            bgcolor='rgba(22,33,62,0.85)',
            bordercolor='#444', borderwidth=1,
            thickness=12, len=0.6, x=1.01,
        ),
        visible=False,
        marker_line_color=BORDER_COL,
        marker_line_width=0.4,
    ))

# ── Dropdown buttons ───────────────────────────────────────────────────────────
n_traces = len(traces)  # 1 all + 10 minerals

buttons = []
# "All" button
vis_all = [True] + [False] * len(minerals)
buttons.append(dict(label='All minerals', method='update',
                    args=[{'visible': vis_all}]))

# Per-mineral buttons (coloured label via html not supported in Plotly dropdown,
# so we just use plain labels)
for i, mineral in enumerate(minerals):
    vis = [False] * n_traces
    vis[i + 1] = True
    buttons.append(dict(label=mineral, method='update', args=[{'visible': vis}]))

# ── Layout ─────────────────────────────────────────────────────────────────────
fig = go.Figure(data=traces)
fig.update_layout(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=DARK_BG,
    margin=dict(l=0, r=60, t=0, b=0),
    height=480,
    geo=dict(
        showframe=False,
        showcoastlines=True,  coastlinecolor='#3a4878',
        showland=True,        landcolor=LAND_BASE,
        showocean=True,       oceancolor=OCEAN_BG,
        showcountries=True,   countrycolor=BORDER_COL,
        showlakes=False,
        bgcolor=DARK_BG,
        projection_type='natural earth',
        lonaxis_range=[-180, 180],
        lataxis_range=[-90, 90],
    ),
    updatemenus=[dict(
        type='dropdown',
        direction='down',
        x=0.01, y=0.98,
        xanchor='left', yanchor='top',
        bgcolor='#1a1a2e',
        bordercolor='#3a4878',
        font=dict(color='white', size=12),
        buttons=buttons,
        active=0,
        showactive=True,
        pad=dict(t=4, b=4),
    )],
    annotations=[dict(
        text='Select mineral:',
        x=0.01, y=1.01,
        xref='paper', yref='paper',
        showarrow=False,
        font=dict(color='#aaa', size=11),
        xanchor='left',
    )],
)

# ── Write ──────────────────────────────────────────────────────────────────────
out = ROOT / 'website/visualizations/deposits/deposit_choroplethMD.html'
fig.write_html(
    out,
    include_plotlyjs='cdn',
    config={'scrollZoom': True, 'displayModeBar': False},
    full_html=True,
)
print(f'Written: {out}')