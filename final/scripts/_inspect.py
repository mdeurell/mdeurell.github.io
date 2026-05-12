import json, sys
with open('data/data/processed/master_geo_deposits.geojson', encoding='utf-8') as f:
    gj = json.load(f)

copper = [feat for feat in gj['features'] if feat['properties'].get('mineral') == 'Copper']
print('Copper count:', len(copper))
for feat in copper:
    p = feat['properties']
    print(' ', p.get('deposit_name'), '|', p.get('country'), '|', p.get('source'), '|', p.get('source_mineral'))

print()
src_counts = {}
for feat in gj['features']:
    p = feat['properties']
    k = str(p.get('source','?')) + ' | ' + str(p.get('mineral','?'))
    src_counts[k] = src_counts.get(k, 0) + 1
print('Source x Mineral:')
for k,v in sorted(src_counts.items()):
    print(' ', k, ':', v)