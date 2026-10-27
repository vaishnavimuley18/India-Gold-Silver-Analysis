# India's Gold & Silver Reserves: Trends, Market Analysis and Resource Insights
*A Data-Driven Analysis of Precious Metal Resources, Prices, Demand, Production and Market Behaviour in India* - Data Analytics and Visualization project.

## Overview and problem statement
How do fluctuations in gold and silver prices relate to demand and market behaviour in India, and how do mineral resources, production and import dependence contribute?

## Objectives and research questions
Describe resources, production, imports, prices, demand; measure price-demand association (gold total / jewellery / investment, silver); estimate elasticity; test four hypotheses; predict quarterly gold demand; build a dashboard. (25 research questions: see the master prompt.)

## Important distinctions
Mineral **resources/reserves** (IBM) vs **RBI gold holdings** (forex reserves) vs **demand** (market consumption). Never mix them.

## Status of this repository
The pipeline has been run on **real data** from the supplied WGC and IBM documents (see `DATA_SOURCES.md`). Gold demand/price (66 quarters), India supply, and gold/silver resources by state are complete. **Missing: Silver Institute silver price/demand and an RBI gold-holdings series**, so hypothesis H4 and the RBI chapter are not yet analysed. Nothing was estimated or fabricated; gaps are left blank.

**Headline results** (details in `PROJECT_REPORT.md`): jewellery demand is price-sensitive (YoY elasticity -1.06, robust to Newey-West errors, COVID exclusion and sub-periods); total demand is only weakly related to price after excluding COVID; bar & coin shows no significant association; the seasonal-naive benchmark beats all price-based ML models in a 16-quarter walk-forward back-test.

## Technology stack
Python (pandas, numpy, scipy, scikit-learn, matplotlib, seaborn, statsmodels optional), Jupyter, Power BI Desktop.

## Architecture
raw CSV -> `src/data_cleaning.py` -> `src/feature_engineering.py` -> `src/analysis.py` / `visualization.py` -> `src/model.py` -> `outputs/` -> `dashboard/data/` -> Power BI. `generate_report.py` writes the report from the result tables.

## Folder structure
`data/raw` (inputs) | `data/processed` | `notebooks` (01-06) | `src` | `outputs/{figures,tables,models,reports}` | `dashboard` | `DATA_SOURCES.md` | `DATA_DOWNLOAD_CHECKLIST.md` | `PRESENTATION_OUTLINE.md` | `VIVA_QA.md`

## Installation
```
pip install -r requirements.txt
```
## How to run (exact order)
1. `python -m src.build_raw_from_sources` rebuilds the raw CSVs from `data/source/` (WGC workbooks) and the transcribed IBM tables. Add missing files per `DATA_DOWNLOAD_CHECKLIST.md`.
2. `python -m src.crosscheck` validates the extraction against the India Focus report and the Q1 workbook.
3. `python run_pipeline.py` (clean -> features -> EDA -> statistics -> robustness -> ML v1 and v2 -> export). Or run notebooks 01-07.
4. `python generate_report.py` -> `PROJECT_REPORT.md` (conclusion is generated from the result tables).
5. `python dashboard/build_dashboard.py` -> `dashboard/dashboard.html` (open in a browser; needs internet for the Chart.js CDN). For Power BI use `dashboard/data/` and `dashboard/POWER_BI_GUIDE.md`.

## Method summary
- **Preprocessing:** numeric coercion, duplicates, state names, units, flags (outliers flagged not deleted).
- **EDA:** descriptive stats, trends, growth, distributions, concentration.
- **Statistics:** Pearson, Spearman, linear regression, log-log elasticity, t-test on correlation; run on levels *and* YoY log changes.
- **ML v1 (template):** Linear Regression vs Random Forest vs last-quarter naive, single chronological split. Kept for transparency; unreliable here (price levels leave the training range).
- **ML v2 (recommended):** YoY-change features, 16-quarter walk-forward back-test, seasonal-naive benchmark, conditional scenario table.
- **Robustness:** Newey-West (HAC) errors, COVID-window exclusion, pre-/post-2020 sub-samples.

## Limitations
Small samples; mixed frequencies; periodic resource snapshots; gross vs net definitions; revisions; correlation is not causation; predictions are estimates.

## Future scope
Monthly data, macro variables (FX, inflation, rates, income), festivals, global price, SARIMA.

## Authors
Vaishnavi Muley

