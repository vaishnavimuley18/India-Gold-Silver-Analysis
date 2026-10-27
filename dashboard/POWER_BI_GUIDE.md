# Power BI build guide
Power BI Desktop runs on Windows. (No Power BI? Use Plotly Dash/Streamlit on the same CSVs.)

**Load** (Get Data > Text/CSV) from `dashboard/data/`: `master_dataset.csv` (quarterly gold), `annual_master.csv`, `mineral_resources_clean.csv`, `rbi_gold_clean.csv`, `relationships.csv`, `elasticity_gold.csv`, `model_comparison.csv`, `model_predictions.csv`, `feature_importance.csv`. Create a `Dim_Date` table and relate it to the quarterly tables by Date; keep annual/resource tables unrelated to quarterly ones (different grain).

## Pages
1. **Overview** - KPI cards (latest gold price, gold demand, RBI holdings, resources, production), price and demand trend lines; slicers Year, Quarter, Metal.
2. **Resources** - filled map (import a state GeoJSON; match state names), top-10 bar, share, reserves vs resources; slicers Mineral, Year, State.
3. **Price vs Demand** - three gold scatters (total, jewellery, investment) + silver scatter; cards from `relationships.csv` and `elasticity_gold.csv`; tooltips explaining correlation/elasticity.
4. **Supply & Imports** - production, imports, import dependency, stacked supply composition.
5. **RBI Gold** - tonnes line, value line (separate axes avoided: use two charts), share of reserves. Text box: *RBI gold holdings are monetary reserves, not geological resources.*
6. **Predictions** - model comparison table, actual vs predicted (mark "Predicted"), feature importance.

## Starter DAX measures
```
Latest Gold Price = CALCULATE(MAX(master_dataset[Gold_Price]), master_dataset[Date] = MAX(master_dataset[Date]))
Gold Demand (t) = SUM(master_dataset[Gold_Demand])
Gold YoY % = DIVIDE([Gold Demand (t)] - CALCULATE([Gold Demand (t)], SAMEPERIODLASTYEAR(Dim_Date[Date])), CALCULATE([Gold Demand (t)], SAMEPERIODLASTYEAR(Dim_Date[Date])))
Gold Price-Demand r = AVERAGEX(FILTER(relationships, relationships[analysis] = "Gold price vs total demand" && relationships[basis] = "levels"), relationships[pearson_r])
```
Design: restrained palette, no 3D, no gauges, no misleading dual axes; every chart answers one question.
