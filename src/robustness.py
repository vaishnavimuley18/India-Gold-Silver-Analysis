"""STEP 3b - Robustness checks for the price-demand elasticity.
WHY: YoY changes of quarterly data overlap (3 of every 4 quarters are shared), so consecutive observations are
autocorrelated and ordinary p-values are too optimistic. We therefore add (a) Newey-West (HAC) standard errors,
(b) a sample that excludes the COVID window, (c) pre-/post-2020 sub-samples."""
import numpy as np
import pandas as pd
import statsmodels.api as sm

COVID_START, COVID_END = pd.Timestamp("2020-03-31"), pd.Timestamp("2022-06-30")  # quarters whose YoY change touches 2020Q1-2021Q2


def _fit(d, y, x="Gold_Price_LogChg", lags=4):
    X = sm.add_constant(d[x])
    m = sm.OLS(d[y], X).fit(cov_type="HAC", cov_kwds={"maxlags": lags})
    ci = m.conf_int().loc[x]
    return dict(n=int(m.nobs), elasticity=m.params[x], hac_se=m.bse[x], p_value_hac=m.pvalues[x],
                ci_low=ci[0], ci_high=ci[1], r_squared=m.rsquared)


def elasticity_robustness(g):
    samples = {
        "Full sample (HAC)": g,
        "Excluding COVID window (HAC)": g[(g["Date"] < COVID_START) | (g["Date"] > COVID_END)],
        "2011-2019 only (HAC)": g[g["Date"] <= pd.Timestamp("2019-12-31")],
        "2022Q3-2026Q2 only (HAC)": g[g["Date"] > COVID_END],
    }
    rows = []
    for lbl, y in (("Total demand", "Gold_Demand_LogChg"), ("Jewellery demand", "Jewellery_Demand_LogChg"),
                   ("Investment (bar & coin) demand", "Investment_Demand_LogChg")):
        for sname, d in samples.items():
            d = d[["Gold_Price_LogChg", y]].dropna()
            if len(d) >= 8:
                rows.append(dict(series=lbl, sample=sname, **_fit(d, y)))
    out = pd.DataFrame(rows)
    out["significant_5pct"] = out["p_value_hac"] < 0.05
    return out
