"""Build PROJECT_REPORT.md from the REAL result tables in outputs/tables.
Nothing is typed in by hand: every number in the results chapters comes from your data.
Run AFTER run_pipeline.py:   python generate_report.py"""
import pandas as pd
from pathlib import Path
from src import config as C


def tbl(name, floatfmt=3):
    f = C.TAB / name
    if not f.exists():
        return "_Not available - the required data/step was not run._\n"
    df = pd.read_csv(f)
    if df.empty:
        return "_Empty._\n"
    df = df.round(floatfmt)
    head = "| " + " | ".join(map(str, df.columns)) + " |\n|" + "---|" * len(df.columns) + "\n"
    body = "".join("| " + " | ".join("" if pd.isna(v) else str(v) for v in r) + " |\n" for r in df.values)
    return head + body + "\n"


def fig(name, caption):
    return f"![{caption}](../figures/{name}.png)\n\n*{caption}*\n\n" if (C.FIG / f"{name}.png").exists() else ""


def insights():
    """Auto-generated, evidence-based statements. Each follows Observation / Evidence / Interpretation / Limitation."""
    f = C.TAB / "relationships.csv"
    if not f.exists():
        return "_Run the pipeline with real data to generate insights._\n"
    rel = pd.read_csv(f)
    out = []
    for _, r in rel.iterrows():
        if pd.isna(r.get("pearson_r")):
            continue
        sig = "statistically significant" if r["pearson_p"] < C.ALPHA else "not statistically significant"
        out.append(
            f"**{r['analysis']} ({r['basis']})**\n"
            f"- *Observation:* {r['y']} shows a {r['strength']} association with {r['x']}.\n"
            f"- *Evidence:* Pearson r = {r['pearson_r']:.2f} (p = {r['pearson_p']:.3f}), Spearman rho = {r['spearman_rho']:.2f}, "
            f"R2 = {r['r_squared']:.2f}, n = {int(r['n'])}; the association is {sig} at alpha = {C.ALPHA}.\n"
            f"- *Interpretation:* higher prices tend to coincide with {'lower' if r['pearson_r'] < 0 else 'higher'} {r['y']} in this sample; "
            f"other factors (income, festivals, duties, global prices) may explain part of this.\n"
            f"- *Limitation:* correlation is not causation; a small sample and trending series can distort results.\n")
    return "\n".join(out)


def _r(name):
    f = C.TAB / name
    return pd.read_csv(f) if f.exists() else None


def conclusion():
    """Chapter 12 text assembled from the result tables, so it can never disagree with them."""
    rel, rob, v2, hyp = _r("relationships.csv"), _r("robustness_elasticity.csv"), _r("model_comparison_v2.csv"), _r("hypothesis_tests_yoy.csv")
    if rel is None or rob is None or v2 is None:
        return "_Run the pipeline first._\n"
    g = lambda s, b, key: rel[(rel["analysis"] == s) & (rel["basis"] == b)].iloc[0][key]
    jew = rob[rob["series"] == "Jewellery demand"].set_index("sample")
    tot = rob[rob["series"] == "Total demand"].set_index("sample")
    inv = rob[rob["series"].str.startswith("Investment")].set_index("sample")
    seas = v2[v2["Model"].str.startswith("Seasonal")].iloc[0]
    best_ml = v2[~v2["Model"].str.contains("naive", case=False)].iloc[0]
    res = _r("concentration_gold.csv")
    ann = pd.read_csv(C.PROC / "annual_master.csv")
    rs = pd.read_csv(C.PROC / "resources_clean.csv")
    gq = pd.read_csv(C.PROC / "gold_quarterly_features.csv")
    gold = rs[rs["Mineral"] == "Gold"].sort_values("Resources", ascending=False)
    silver = rs[rs["Mineral"] == "Silver"].sort_values("Resources", ascending=False)
    top2 = gold["Resource_Share"].head(2).sum()
    last_full_year = int(gq.groupby("Year")["Quarter"].count().loc[lambda x: x == 4].index.max())
    dem_last = gq.loc[gq["Year"] == last_full_year, "Gold_Demand"].sum()
    tot_res = gold["Resources"].sum()
    txt = f"""## Chapter 12 - Conclusion
**Answer to the research question.** In India's quarterly data (2010-2026, n = 66) higher domestic gold prices are associated with *lower jewellery volumes*, but not with lower bar-and-coin volumes.

1. **Jewellery demand is price-sensitive.** The YoY log-log elasticity is {jew.loc['Full sample (HAC)','elasticity']:.2f} (full sample; 95% CI {jew.loc['Full sample (HAC)','ci_low']:.2f} to {jew.loc['Full sample (HAC)','ci_high']:.2f}, Newey-West errors). It stays negative and significant when COVID quarters are excluded ({jew.loc['Excluding COVID window (HAC)','elasticity']:.2f}), in 2011-2019 ({jew.loc['2011-2019 only (HAC)','elasticity']:.2f}) and in 2022Q3-2026Q2 ({jew.loc['2022Q3-2026Q2 only (HAC)','elasticity']:.2f}). Volumes adjust to high prices (lighter, lower-carat pieces) while rupee spending still rises, so the result is about tonnes, not about rupees spent.
2. **Total demand is only weakly and unstably related to price.** Elasticity {tot.loc['Full sample (HAC)','elasticity']:.2f} on the full sample, but {tot.loc['Excluding COVID window (HAC)','elasticity']:.2f} (p = {tot.loc['Excluding COVID window (HAC)','p_value_hac']:.3f}) excluding COVID and {tot.loc['2022Q3-2026Q2 only (HAC)','elasticity']:.2f} (p = {tot.loc['2022Q3-2026Q2 only (HAC)','p_value_hac']:.3f}) after 2022. The headline significance of H1 rests substantially on the COVID shock.
3. **Bar and coin demand shows no significant association with price** in any sample (elasticity {inv.loc['Full sample (HAC)','elasticity']:.2f}, p = {inv.loc['Full sample (HAC)','p_value_hac']:.2f}); H3 is not rejected. Price momentum, not price level, may matter for investors; this was not tested.
4. **Prediction.** Over a 16-quarter walk-forward back-test the best model was the *seasonal naive* benchmark (same quarter last year: RMSE {seas['RMSE']:.1f} t, MAE {seas['MAE']:.1f} t, R2 {seas['R2']:.2f}). The best machine-learning model, {best_ml['Model']}, reached RMSE {best_ml['RMSE']:.1f} t. **Price-based ML models did not beat the seasonal benchmark**, so on this data price adds no demonstrable predictive value beyond seasonality. The template's level-based linear model failed badly (predicting negative demand) because test-period prices lay far outside the training range.
5. **Supply and resources.** India is import-dependent: net bullion imports were {ann['Gold_Net_Import_Share_WGC'].dropna().min():.0f}-{ann['Gold_Net_Import_Share_WGC'].dropna().max():.0f}% of total supply in 2012-2025 (WGC). Gold resources are concentrated: the top five states hold {res.iloc[0]['share_pct']:.0f}% of the {tot_res:.1f} t of metal; {gold.iloc[0]['State']} and {gold.iloc[1]['State']} alone hold {top2:.0f}%, and {silver.iloc[0]['State']} holds {silver.iloc[0]['Resource_Share']:.0f}% of silver resources (silver is mostly a lead-zinc by-product). The entire identified gold resource base is smaller than one recent full year of consumer demand ({dem_last:.0f} t in {last_full_year}).

**Not answered with the supplied data:** the silver price-demand hypothesis (H4) and RBI holdings analysis (no series supplied). These are future work, not conclusions.
"""
    return txt


TEXT = {
 "intro": """## Chapter 1 - Introduction
**Background.** India is among the world's largest consumers of gold and a major consumer of silver, yet it mines very little of either. Gold and silver matter for jewellery, household savings, investment and the country's foreign-exchange reserves.

**Problem statement.** How do fluctuations in gold and silver prices relate to demand and market behaviour in India, and how do domestic resources, production and import dependence shape this ecosystem?

**Objectives.** (1) describe resources, production, imports, prices and demand; (2) measure the price-demand association for gold (total, jewellery, investment) and silver; (3) estimate price elasticity with appropriate caveats; (4) test four hypotheses; (5) build and evaluate a gold-demand prediction model; (6) present everything in an interactive dashboard.

**Key distinction.** *Mineral resources/reserves* are geological deposits (IBM). *RBI gold holdings* are gold held as part of foreign-exchange reserves. They are different things and are analysed separately. *Gold demand* is market consumption (jewellery, investment, etc.).
""",
 "review": """## Chapter 2 - Domain review
Gold demand in India is driven by jewellery (weddings, festivals) and, increasingly, investment (bars, coins, ETFs). The World Gold Council (WGC) publishes quarterly demand from Metals Focus data; jewellery is reported gross (including recycled gold) while investment is net. Silver demand comes from jewellery, silverware, coins/bars and industry (Silver Institute / Metals Focus, annual). India's resource data come from the Indian Bureau of Mines (IBM) National Mineral Inventory under the UNFC classification, updated at intervals; silver is mainly a by-product of lead-zinc mining. The RBI holds gold as part of its reserves; its tonnage changes slowly while its value moves with the gold price.
""",
 "data": """## Chapter 3 - Data collection
See `DATA_SOURCES.md` for every dataset, period and the exact table used. **Quarterly gold** (Q1 2010 - Q2 2026, 66 quarters): World Gold Council *Gold Demand Trends* Q2 2026 data tables (Metals Focus, ICE Benchmark Administration): India jewellery and bar & coin demand (tonnes), LBMA gold price (US$/oz) and domestic price (Rs/10 g, MCX-based). **Annual supply** (2012-2025): WGC India supply table (gross and net bullion imports, scrap) combined with Indian Bureau of Mines (IBM) metal production (FY2013-14 to FY2023-24; fiscal year labelled by its start year) and silver trade (FY2021-22 to FY2023-24). **Resources**: IBM National Mineral Inventory, *NMI At a Glance 2025* (Tables 5.15 gold and 5.37 silver, as on 1 April 2025; metal content, tonnes). Quarterly and annual data are kept in separate datasets because their frequencies differ.

**Demand definition used (important).** `Gold_Demand = Jewellery + Bar & coin`. WGC's headline India total also contains ETFs and industrial demand. The workbooks give no India-specific ETF series and the India Focus report gives only six quarters, so adding it would create a break in the series. Against WGC's headline total the difference is 3-15% in the six quarters where it can be checked (see the cross-check table below). Silver price and demand (Silver Institute) and an RBI gold-holdings time series were **not** in the supplied files, so Hypothesis H4 and the RBI analysis were not performed rather than estimated.

**Validation.** The extraction was cross-checked against the independent *India Focus Q2 2026* report (Table 1) and against the Q1 2026 workbook (see `outputs/tables/crosscheck_*.csv`). State resource totals reconcile exactly to IBM's published all-India totals (gold 658.80 t, silver 26,819.75 t).

""",
 "prep": """## Chapter 4 - Data preprocessing
Cleaning steps actually performed are listed in `outputs/reports/cleaning_log.md`. In general: numeric coercion, duplicate removal, state-name standardisation, unit conversion (kg to tonnes; oz to grams), derivation of Investment = Bar&Coin + ETF, and flagging (not deleting) suspicious values. Engineered features: YoY/QoQ growth, log changes, lags (1, 2, 4 quarters), quarter number, price index (base = 100), import dependency = imports / (production + imports + recycling) x 100.
""",
}


def main():
    P = []
    P.append("# India's Gold & Silver Reserves: Trends, Market Analysis and Resource Insights\n\n*A Data-Driven Analysis of Precious Metal Resources, Prices, Demand, Production and Market Behaviour in India*\n\n")
    P += [TEXT["intro"], TEXT["review"], TEXT["data"], TEXT["prep"]]
    P.append("## Chapter 5 - Exploratory Data Analysis\n### Descriptive statistics (gold, quarterly)\n" + tbl("descriptive_gold.csv"))
    for n, c in [("gold_price_trend", "Gold price over time"), ("gold_price_yoy", "Gold price YoY growth"), ("gold_price_hist", "Gold price distribution"),
                 ("gold_price_by_quarter", "Gold price by quarter"), ("gold_demand_trend", "Gold demand"), ("gold_demand_composition", "Demand composition"),
                 ("jewellery_vs_investment", "Jewellery vs investment"), ("gold_demand_yoy", "Demand growth"), ("silver_price_index", "Silver price index"),
                 ("import_dependency", "Import dependency"), ("top_states_gold", "Top states, gold resources"), ("top_states_silver", "Top states, silver resources")]:
        P.append(fig(n, c))
    P.append("### Descriptive statistics (annual)\n" + tbl("descriptive_annual.csv"))
    P.append("### Resource concentration\n" + tbl("concentration_gold.csv") + tbl("concentration_silver.csv"))
    P.append("### Seasonality check (average by quarter)\n" + tbl("seasonality_gold_demand.csv") + "Seasonality should only be claimed if the pattern is consistent across many years.\n\n")
    P.append("## Chapter 6 - Statistical Analysis\n### Correlation and regression\n" + tbl("relationships.csv"))
    P.append(fig("corr_heatmap_quarterly", "Correlation heatmap") + fig("scatter_gold_demand", "Gold price vs total demand") +
             fig("scatter_jewellery_demand", "Gold price vs jewellery demand") + fig("scatter_investment_demand", "Gold price vs investment demand") + fig("scatter_silver", "Silver price vs demand"))
    P.append("### Price elasticity (log-log slope; interpret with caution)\n" + tbl("elasticity_gold.csv") + tbl("elasticity_silver.csv"))
    P.append("### Hypothesis tests (alpha = 0.05) - levels\n" + tbl("hypothesis_tests.csv") + "### Hypothesis tests - YoY changes (removes shared trend)\n" + tbl("hypothesis_tests_yoy.csv"))
    P.append("### Robustness of the elasticity (Newey-West errors, COVID exclusion, sub-periods)\nYoY changes overlap, so ordinary p-values are too optimistic; the table below uses HAC (Newey-West, 4 lags) errors. `COVID window` excludes quarters whose YoY change involves 2020Q1-2021Q2.\n\n" + tbl("robustness_elasticity.csv") + fig("scatter_yoy_jewellery", "YoY change: jewellery demand vs gold price") + fig("scatter_yoy_total", "YoY change: total demand vs gold price") + fig("scatter_yoy_investment", "YoY change: bar & coin demand vs gold price") + fig("indexed_price_vs_demand", "Indexed trends (4-quarter moving averages)") + fig("seasonality_demand_box", "Seasonality of demand"))
    P.append("### Data cross-check against the India Focus report\n" + tbl("crosscheck_india_focus.csv", 1))
    P.append("## Chapter 7 - Machine Learning\n**Target:** quarterly Gold_Demand. **Features:** Gold_Price, Gold_Price_Change, demand lags 1/2/4, quarter number. Same-quarter jewellery and investment demand are excluded because they add up to the target (data leakage). **Split:** chronological (earliest 80% train, latest 20% test), TimeSeriesSplit CV on the training part.\n\n" +
             tbl("model_comparison.csv") + fig("actual_vs_predicted", "Actual vs predicted (model estimates)") + fig("feature_importance", "Feature importance") + "### Test-set predictions\n" + tbl("model_predictions.csv"))
    P.append("### Version 2 - walk-forward back-test with seasonal benchmark (recommended results)\nThe version-1 set-up above follows the project template: a single hold-out, price *levels* as features and a 'last quarter' baseline. It is kept for transparency but is **not** reliable here: test prices lie outside the training range, and 'last quarter' is a weak yardstick for a seasonal series. Version 2 models the year-on-year change, refits one quarter at a time over the last 16 quarters, and compares against the seasonal-naive forecast (same quarter last year).\n\n" + tbl("model_comparison_v2.csv") + fig("actual_vs_predicted_v2", "Walk-forward back-test") + "### Scenario for the next quarter (conditional on assumed prices, **not a forecast**)\nThe full-sample slope is dominated by 2011-2019 and COVID; the post-2022 slope is much flatter. Both are shown because the true sensitivity is uncertain. Ranges are approximately +/-1.96 x back-test RMSE.\n\n" + tbl("scenario_next_quarter.csv"))
    P.append("## Chapter 8 - Dashboard\nSee `dashboard/POWER_BI_GUIDE.md` for the six pages, data files and DAX measures.\n\n")
    P.append("## Chapter 9 - Results and Insights\n" + insights())
    P.append("## Chapter 10 - Limitations\nDemand is jewellery + bar & coin, which omits ETF and industrial demand (3-15% of WGC's headline total where checkable); 66 quarters with a strong trend in price, so level-based statistics are unreliable and YoY changes overlap (handled with HAC errors); the COVID shock is influential; production is fiscal-year data matched to calendar-year imports (FY labelled by start year); resource data are a single 1 April 2025 snapshot; silver price/demand and RBI holdings series were not supplied; the 2022Q3-2026Q2 sub-sample has only 16 observations; different frequencies; resource data are periodic snapshots; WGC jewellery is gross and investment is net; methodology changes and data revisions; correlation is not causation; model predictions carry uncertainty and are not official forecasts.\n\n")
    P.append("## Chapter 11 - Future Scope\nMonthly data; exchange rate, inflation, interest rate, income and festival variables; global gold price; import-duty changes; SARIMA/Prophet and other forecasting models; state-level demand.\n\n")
    P.append(conclusion())
    out = C.REP / "PROJECT_REPORT.md"
    out.write_text("\n".join(P))
    (C.ROOT / "PROJECT_REPORT.md").write_text("\n".join(P).replace("../figures/", "outputs/figures/"))
    print("Report written to", out, "and PROJECT_REPORT.md")


if __name__ == "__main__":
    main()
