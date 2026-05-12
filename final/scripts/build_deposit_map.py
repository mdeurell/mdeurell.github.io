"""
Generates website/visualizations/deposits/deposit_map.html
Point map: individual mine locations as dots, filterable by mineral.
"""
import json
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path

ROOT = Path(__file__).parent.parent

# ── Load ──────────────────────────────────────────────────────────────────────
with open(ROOT / 'data/processed/master_geo_deposits.geojson', encoding='utf-8') as f:
    gj = json.load(f)

records = []
for feat in gj['features']:
    p    = feat['properties']
    geom = feat.get('geometry')
    if geom and geom['type'] == 'Point' and p.get('latitude') is not None:
        records.append({
            'mineral':      p['mineral'],
            'country':      p.get('country', ''),
            'deposit_name': p.get('deposit_name') or '',
            'deposit_type': p.get('deposit_type') or '',
            'latitude':     float(p['latitude']),
            'longitude':    float(p['longitude']),
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

# ── Build one trace per mineral ────────────────────────────────────────────────
traces = []
for mineral in minerals:
    sub   = df[df['mineral'] == mineral].copy()
    color = MINERAL_HEX.get(mineral, '#888888')

    hover = (
        '<b>' + sub['deposit_name'].where(sub['deposit_name'] != '', sub['country']) + '</b>'
        + '<br>' + mineral
        + '<br>' + sub['country']
        + sub['deposit_type'].apply(lambda t: f'<br><span style="color:#aaa">{t}</span>' if t else '')
    )

    traces.append(go.Scattermap(
        name=mineral,
        lat=sub['latitude'],
        lon=sub['longitude'],
        mode='markers',
        marker=dict(size=5, color=color, opacity=0.75),
        text=hover,
        hoverinfo='text',
        visible=True,
        legendgroup=mineral,
    ))

# ── Dropdown buttons ───────────────────────────────────────────────────────────
n = len(traces)

def vis_for(indices):
    v = [False] * n
    for i in indices:
        v[i] = True
    return v

buttons = [
    dict(label='All minerals', method='update',
         args=[{'visible': [True] * n}]),
]
for i, mineral in enumerate(minerals):
    buttons.append(dict(
        label=mineral, method='update',
        args=[{'visible': vis_for([i])}],
    ))

# ── Layout ─────────────────────────────────────────────────────────────────────
fig = go.Figure(data=traces)
fig.update_layout(
    paper_bgcolor='#16213e',
    margin=dict(l=0, r=140, t=28, b=0),
    height=520,
    map=dict(
        style='carto-darkmatter',
        center=dict(lat=20, lon=10),
        zoom=1.1,
    ),
    legend=dict(
        bgcolor='rgba(22,33,62,0.88)',
        bordercolor='#3a4878',
        borderwidth=1,
        font=dict(color='white', size=11),
        title=dict(text='Mineral', font=dict(color='#aaa', size=11)),
        x=1.01,
        xanchor='left',
        y=0.5,
        yanchor='middle',
        itemsizing='constant',
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
        text='Filter by mineral:',
        x=0.01, y=1.04,
        xref='paper', yref='paper',
        showarrow=False,
        font=dict(color='#aaa', size=11),
        xanchor='left',
    )],
)

# ── Write ──────────────────────────────────────────────────────────────────────
out = ROOT / 'website/visualizations/deposits/deposit_mapMD.html'
fig.write_html(
    out,
    include_plotlyjs='cdn',
    config={
        'scrollZoom': True,
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['toImage', 'sendDataToCloud'],
    },
    full_html=True,
)
print(f'Written: {out}')