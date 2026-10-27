# DATA_SOURCES

Files below were supplied in `DAV_DATASETS.zip`. **Fill your own download/access date** in the last column before submission. URLs are those listed in the original template (not re-opened by the assistant).

| Dataset | Source and exact file / table used | Period | Variables used | Status | Access date |
|---|---|---|---|---|---|
| India gold demand (quarterly) | WGC *Gold Demand Trends* Q2 2026 data tables, `GDT_Tables_Q2'26_EN.xlsx`, sheets **Jewellery** (row India) and **Bar and Coin** (row India) | Q1 2010 - Q2 2026 (66 quarters) | Jewellery demand (t, gross), bar & coin demand (t, net) | Used | ____ |
| Gold price (quarterly avg) | Same workbook, sheet **Gold Prices**: rows US$/oz (LBMA PM) and Rs/10g | Q1 2010 - Q2 2026 | LBMA US$/oz; domestic Rs/10 g (MCX-based) | Used. `Gold_Price` = Rs/10 g | ____ |
| India supply (annual) | Same workbook, sheet **India Supply** | 2012 - 2025 | Gross bullion imports, net bullion imports, scrap, other domestic supply, total supply (t) | Used | ____ |
| Cross-check | WGC *Gold Demand Trends: India Focus Q2 2026* (PDF), Table 1; and `GDT_Tables_Q1'26_EN.xlsx` | Q1 2025 - Q2 2026 | Jewellery, bar & coin, ETF, industrial, total; prices | Used for validation only (`outputs/tables/crosscheck_*.csv`) | ____ |
| Resources / reserves (state-wise) | IBM, *NMI At a Glance 2025*, Chapter 5, **Table 5.15 (gold)** and **Table 5.37 (silver)**, as on 01.04.2025; metal content, tonnes | 1 Apr 2025 snapshot | Total resources (A+B), reserves (A) | Used. State sums reconcile to published all-India totals. Kerala gold placer (5.42 t) not added | ____ |
| Production (gold, silver metal) | IBM *Indian Mineral Industry at a Glance 2022-23*, Table 17 (FY2013-14 to FY2020-21); *Indian Minerals Yearbook 2024*, Table 6 (FY2021-22 to FY2023-24 provisional) | FY2013-14 - FY2023-24 | Metal production (kg to t); fiscal year labelled by start year | Used. Gold includes by-product recovery from imported copper. IMIG prints silver FY2021-22 = 647,156 kg (a different IMYB series); revised 713,653 kg used | ____ |
| Silver foreign trade | IMYB 2024, Table 4 (exports) and Table 11 (imports) | FY2021-22 - FY2023-24 | Silver imports/exports (t) | Used (3 years only) | ____ |
| Primary gold production note | Ministry of Mines national mineral scenario page (PDF print) | 2023-24 (provisional) | Primary gold 1,552 kg; Karnataka > 93% | Context only (different definition from metal production) | ____ |
| Silver demand and price (annual) | Silver Institute *World Silver Survey* | - | - | **NOT SUPPLIED**. Hypothesis H4 and silver ML not performed | ____ |
| RBI gold holdings (time series) | RBI | - | - | **NOT SUPPLIED**. India Focus says only that holdings were steady at ~880 t since mid-2025 | ____ |
| India state boundaries (GeoJSON) | - | - | - | **NOT SUPPLIED**. Needed only for a filled map in Power BI | ____ |

## Definitions and caveats (read before the viva)
- `Gold_Demand` = Jewellery + Bar & coin. WGC's headline India total also includes ETFs and industrial demand; the gap is 3-15% in the six quarters where it can be checked. No India ETF series exists in the supplied workbooks, so ETF was left blank for all quarters rather than filled for only six.
- WGC jewellery is gross (includes recycled gold); bar & coin is net.
- Production is fiscal-year (April-March) and imports/demand are calendar-year; FY is labelled by its start year, so the match is approximate.
- Resource figures are a single snapshot (1 April 2025), not a time series.
- Resources/reserves (geology), RBI holdings (monetary reserves) and demand (consumption) are different things and are never mixed.
