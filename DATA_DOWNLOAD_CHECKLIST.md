# Data checklist - status after processing your DAV_DATASETS.zip

Raw CSVs are now filled by `python -m src.build_raw_from_sources` (WGC workbooks parsed; IBM tables transcribed with table references).

| # | Raw file | Status |
|---|---|---|
| 1 | `data/raw/gold/gold_quarterly_raw.csv` | DONE - 66 quarters (Q1 2010-Q2 2026). ETF column intentionally blank |
| 2 | `data/raw/silver/silver_annual_raw.csv` | **MISSING** - need Silver Institute *World Silver Survey* (annual price INR/kg, demand, category split) |
| 3 | `data/raw/resources/mineral_resources_raw.csv` | DONE - gold (13 states) and silver (12 states), 1 Apr 2025 |
| 4 | `data/raw/rbi/rbi_gold_raw.csv` | **MISSING** - need RBI gold tonnes / value / total reserves (Weekly Statistical Supplement or Bulletin) |
| 5 | `data/raw/imports_exports/annual_supply_raw.csv` | PARTLY - gold supply 2012-2025 (WGC), production 2013-2023 and silver trade 2021-2023 (IBM). Gold exports only for 3 fiscal years; gold production after FY2023-24 and silver imports before FY2021-22 not supplied |

After adding files 2 and 4, run `python run_pipeline.py`, `python generate_report.py` and `python dashboard/build_dashboard.py` again. H4 and the RBI chapter will then populate automatically.
