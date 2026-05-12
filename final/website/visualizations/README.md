# Visualization Manifest

All first-draft visualization exports are built from `data/processed` only.

## Section 0

- No exported hero asset in the first draft. This remains website composition work.

## Stakes

- Datasets: master_economic_timeseries.csv
- `website\visualizations\stakes\mineral_grid.html`: Mineral overview
- `website\visualizations\stakes\price_index.html`: 5.1 Price shock opener (1900-2024, real/nominal toggle)
- `website\visualizations\stakes\price_index_zoom.html`: 5.1b Modern-era zoom (2000-2024)
- `website\visualizations\stakes\production_history.html`: 5.2 World mine production 1900-2024
- `website\visualizations\stakes\end_uses.html`: End-use framing (treemap)
- `website\visualizations\stakes\end_use_carousel.html`: End-use framing (3D carousel)

## Deposits

- Datasets: master_geo_deposits.geojson
- `website\visualizations\deposits\deposit_map.html`: Global geology map

## Supply-Chain

- Datasets: master_supply_chain_trade.csv
- `website\visualizations\supply-chain\slope_chart.html`: Case 1 mining vs processing gap
- `website\visualizations\supply-chain\production_series.html`: Case 1 scaling over time
- `website\visualizations\supply-chain\sankey_cobalt.html`: 5.3 carousel - Cobalt
- `website\visualizations\supply-chain\sankey_lithium.html`: 5.3 carousel - Lithium
- `website\visualizations\supply-chain\sankey_graphite.html`: 5.3 carousel - Graphite
- `website\visualizations\supply-chain\sankey_copper.html`: 5.3 carousel - Copper
- `website\visualizations\supply-chain\sankey_platinum.html`: 5.3 carousel - Platinum
- `website\visualizations\supply-chain\sankey_gallium.html`: 5.3 carousel - Gallium
- `website\visualizations\supply-chain\sankey_rare_earths.html`: 5.3 carousel - Rare Earths
- `website\visualizations\supply-chain\sankey_master.html`: 5.5 All-material chokepoint Sankey

## Bifurcation

- Datasets: master_supply_chain_trade.csv
- `website\visualizations\bifurcation\trade_flows_2015.html`: 2015 China export destinations
- `website\visualizations\bifurcation\trade_flows_2023.html`: 2023 China export destinations
- `website\visualizations\bifurcation\china_timeline.html`: China export destination timeline

## Conclusion

- Datasets: master_supply_chain_trade.csv
- `website\visualizations\conclusion\hhi_heatmap.html`: Concentration synthesis
