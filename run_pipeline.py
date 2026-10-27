"""Run the whole analysis end-to-end:   python run_pipeline.py
Order: clean -> features -> EDA -> statistics -> ML -> exports for Power BI.
Steps are skipped (with a message) when the raw file for them is still empty."""
import pandas as pd
from src import config as C
from src import data_cleaning as dc, feature_engineering as fe, analysis as an, visualization as vz, model as ml
from src import robustness as rb, model_v2 as ml2, extra_figures as xf


def step_clean():
    out = {}
    cleaners = {"gold_quarterly": dc.clean_gold_quarterly, "silver_annual": dc.clean_silver_annual,
                "resources": dc.clean_resources, "rbi_gold": dc.clean_rbi, "annual_supply": dc.clean_annual_supply}
    for key, fn in cleaners.items():
        raw = dc.load_data(key)
        if raw is None:
            continue
        df = fn(raw)
        dc.validate(df, key)
        df.to_csv(C.PROC / f"{key}_clean.csv", index=False)
        out[key] = df
    dc.write_cleaning_log()
    return out


def step_features(d):
    g = fe.build_gold_quarterly_features(d["gold_quarterly"]) if "gold_quarterly" in d else None
    if g is not None and "rbi_gold" in d:
        rq = fe.rbi_to_quarterly(d["rbi_gold"])[["Year", "Quarter", "RBI_Gold_Holdings", "Gold_Share_FX_Reserves"]]
        g = g.merge(rq, on=["Year", "Quarter"], how="left")
    annual = fe.build_annual_master(d.get("annual_supply"), d.get("silver_annual"))
    if g is not None:
        g.to_csv(C.PROC / "gold_quarterly_features.csv", index=False)
        g.to_csv(C.PROC / "master_dataset.csv", index=False)
    if annual is not None:
        annual.to_csv(C.PROC / "annual_master.csv", index=False)
    return g, annual


def step_eda(g, annual, res):
    if g is not None:
        cols = ["Gold_Price", "Gold_Demand", "Jewellery_Demand", "Investment_Demand", "Bar_Coin_Demand", "ETF_Demand"]
        an.describe(g, cols).to_csv(C.TAB / "descriptive_gold.csv")
        vz.line_plot(g, "Date", ["Gold_Price"], "Gold price over time", g["Gold_Price_Unit"].iloc[0], "gold_price_trend")
        vz.line_plot(g, "Date", ["Gold_Price_YoY"], "Gold price YoY growth (%)", "%", "gold_price_yoy")
        vz.hist_plot(g, "Gold_Price", "Gold price distribution", "gold_price_hist")
        vz.box_by_quarter(g, "Gold_Price", "Gold price by quarter", "gold_price_by_quarter")
        vz.line_plot(g, "Date", ["Gold_Demand"], "India gold demand", "tonnes", "gold_demand_trend")
        vz.stacked_bar(g.assign(Period=g["Year"].astype(int).astype(str) + "Q" + g["Quarter"].astype(int).astype(str)),
                       "Period", ["Jewellery_Demand", "Investment_Demand"], "Demand composition", "tonnes", "gold_demand_composition")
        vz.line_plot(g, "Date", ["Jewellery_Demand", "Investment_Demand"], "Jewellery vs investment demand", "tonnes", "jewellery_vs_investment")
        vz.line_plot(g, "Date", ["Gold_Demand_YoY"], "Gold demand YoY growth (%)", "%", "gold_demand_yoy")
        an.seasonality_by_quarter(g, "Gold_Demand").to_csv(C.TAB / "seasonality_gold_demand.csv")
    if annual is not None:
        an.describe(annual, [c for c in annual.columns if c != "Year"]).to_csv(C.TAB / "descriptive_annual.csv")
        dep = [c for c in ("Gold_Import_Dependency", "Silver_Import_Dependency") if c in annual.columns]
        if dep:
            vz.line_plot(annual, "Year", dep, "Import dependency (%)", "% of total supply", "import_dependency")
        idx = [c for c in ("Silver_Price_Index",) if c in annual.columns]
        if idx:
            vz.line_plot(annual, "Year", idx, "Silver price index (first year = 100)", "index", "silver_price_index")
    if res is not None:
        for mineral in res["Mineral"].unique():
            latest = res[(res["Mineral"] == mineral) & (res["Year"] == res[res["Mineral"] == mineral]["Year"].max())]
            vz.hbar(latest, "State", "Resources", f"Top 10 states - {mineral} resources", "tonnes of metal", f"top_states_{mineral.lower()}")
            an.concentration(res, mineral).to_csv(C.TAB / f"concentration_{mineral.lower()}.csv", index=False)


def step_stats(g, annual):
    rel = []
    if g is not None:
        pairs = {"Gold price vs total demand": ("Gold_Price", "Gold_Demand"),
                 "Gold price vs jewellery demand": ("Gold_Price", "Jewellery_Demand"),
                 "Gold price vs investment demand": ("Gold_Price", "Investment_Demand")}
        rel.append(an.relationship_table(g, pairs, "levels"))
        yoy = {k + " (YoY log change)": (v[0] + "_LogChg", v[1] + "_LogChg") for k, v in pairs.items()}
        rel.append(an.relationship_table(g, yoy, "yoy_log_change"))
        for k, (x, y) in pairs.items():
            vz.scatter_regression(g, x, y, k, "scatter_" + y.lower())
        corr_cols = ["Gold_Price", "Gold_Demand", "Jewellery_Demand", "Investment_Demand", "Gold_Price_YoY", "Gold_Demand_YoY"]
        vz.corr_heatmap(an.correlation_matrix(g, corr_cols), "Correlation matrix (quarterly)", "corr_heatmap_quarterly")
        el = []
        for lbl, y in (("Gold total demand", "Gold_Demand"), ("Gold jewellery demand", "Jewellery_Demand"), ("Gold investment demand", "Investment_Demand")):
            for tag, r in an.elasticity(g, "Gold_Price", y).items():
                el.append(dict(series=lbl, basis=tag, **r))
        pd.DataFrame(el).to_csv(C.TAB / "elasticity_gold.csv", index=False)
    if annual is not None and {"Silver_Price", "Silver_Demand"} <= set(annual.columns):
        rel.append(an.relationship_table(annual, {"Silver price vs silver demand": ("Silver_Price", "Silver_Demand")}, "levels (annual)"))
        vz.scatter_regression(annual, "Silver_Price", "Silver_Demand", "Silver price vs silver demand", "scatter_silver")
        el = [dict(series="Silver demand", basis=t, **r) for t, r in an.elasticity(annual, "Silver_Price", "Silver_Demand").items()]
        pd.DataFrame(el).to_csv(C.TAB / "elasticity_silver.csv", index=False)
    if rel:
        rel = pd.concat(rel, ignore_index=True)
        rel.to_csv(C.TAB / "relationships.csv", index=False)
        lv = rel[rel["basis"].str.startswith("levels")]
        hy = {"H1 gold price vs gold demand": "Gold price vs total demand",
              "H2 gold price vs jewellery demand": "Gold price vs jewellery demand",
              "H3 gold price vs investment demand": "Gold price vs investment demand",
              "H4 silver price vs silver demand": "Silver price vs silver demand"}
        an.hypothesis_tests(lv, hy).to_csv(C.TAB / "hypothesis_tests.csv", index=False)
        hy2 = {k + " [YoY]": v + " (YoY log change)" for k, v in list(hy.items())[:3]}
        an.hypothesis_tests(rel[rel["basis"] == "yoy_log_change"], hy2).to_csv(C.TAB / "hypothesis_tests_yoy.csv", index=False)


def step_model(g):
    if g is None:
        return
    r = ml.train_and_evaluate(g)
    if r is None:
        return
    vz.actual_vs_pred(r["test"]["Date"], r["test"]["Gold_Demand"], r["preds"], "Gold demand: actual vs predicted", "actual_vs_predicted")
    vz.importance_plot(r["importance"], "Random Forest feature importance", "feature_importance")
    print(r["results"].round(3).to_string(index=False))
    print("Best by RMSE:", r["best"])


def step_robust(g):
    if g is not None:
        rb.elasticity_robustness(g).to_csv(C.TAB / "robustness_elasticity.csv", index=False)
        xf.run(g)


def step_model_v2(g):
    if g is None:
        return
    d, pred, res = ml2.walk_forward(g)
    best = res.iloc[0]
    print(res.round(3).to_string(index=False))
    cols = [c for c in pred.columns if c not in ("Date", "Actual")]
    keep = {k: pred[k] for k in ("Seasonal naive (same quarter last year)", "Price-adjusted seasonal (YoY elasticity)", "Random Forest (YoY features)")}
    vz.actual_vs_pred(pred["Date"], pred["Actual"], keep, "Walk-forward back-test: actual vs predicted", "actual_vs_predicted_v2")
    print(ml2.scenario_next_quarter(g, d, res.loc[res["Model"].str.startswith("Price-adjusted"), "RMSE"].iloc[0]).to_string(index=False))


def step_export():
    """Copy tidy CSVs where the Power BI guide expects them."""
    for f in list(C.PROC.glob("*.csv")) + [C.TAB / n for n in ("relationships.csv", "elasticity_gold.csv", "model_comparison.csv",
                                                              "model_predictions.csv", "feature_importance.csv", "hypothesis_tests.csv",
                                                              "robustness_elasticity.csv", "model_comparison_v2.csv", "model_predictions_v2.csv", "scenario_next_quarter.csv")]:
        if f.exists():
            (C.DASH / "data").mkdir(exist_ok=True)
            pd.read_csv(f).to_csv(C.DASH / "data" / f.name, index=False)


def main():
    d = step_clean()
    g, annual = step_features(d)
    step_eda(g, annual, d.get("resources"))
    step_stats(g, annual)
    step_robust(g)
    step_model(g)
    step_model_v2(g)
    step_export()
    print("Done. See outputs/ and dashboard/data/.")


if __name__ == "__main__":
    main()
