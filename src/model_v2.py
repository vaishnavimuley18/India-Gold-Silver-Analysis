"""STEP 5b - Improved gold-demand prediction: walk-forward (rolling-origin) back-test with HONEST baselines.

WHY v2: (1) Gold demand is strongly seasonal, so 'same as last quarter' is a weak yardstick; the SEASONAL NAIVE
forecast (same quarter last year) is the benchmark a model must beat. (2) Raw price LEVELS are non-stationary: test-period
prices lie far outside the training range, so level-based linear models extrapolate badly (v1 predicted negative demand).
We therefore model the YEAR-ON-YEAR change. (3) One 12-quarter hold-out is a noisy verdict, so we refit and predict one quarter
at a time over the last 16 quarters.

NOTE: the quarter's own price is used as a regressor, so this is a CONDITIONAL model ('given the price path, what demand?'),
suitable for scenario analysis, not an unconditional forecast."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from . import config as C

N_TEST = 16
SETB = ["Gold_Price_LogChg", "Price_QoQ_Log", "Gold_Demand_Lag_1", "Gold_Demand_Lag_4", "Quarter_Number"]


def prep(g):
    d = g.copy()
    d["Price_QoQ_Log"] = np.log(d["Gold_Price"]).diff(1)
    d["Demand_YoY_Log"] = np.log(d["Gold_Demand"]).diff(4)
    d = d.dropna(subset=SETB + ["Gold_Demand", "Demand_YoY_Log"]).reset_index(drop=True)
    return d


def _metrics(y, p):
    y, p = np.asarray(y), np.asarray(p)
    return dict(MAE=mean_absolute_error(y, p), RMSE=float(np.sqrt(mean_squared_error(y, p))),
                MAPE_pct=float(np.mean(np.abs((y - p) / y)) * 100), R2=r2_score(y, p))


def walk_forward(g):
    d = prep(g)
    start = len(d) - N_TEST
    rows = []
    for t in range(start, len(d)):
        tr, te = d.iloc[:t], d.iloc[[t]]
        rec = dict(Date=te["Date"].iloc[0], Actual=te["Gold_Demand"].iloc[0])
        rec["Seasonal naive (same quarter last year)"] = te["Gold_Demand_Lag_4"].iloc[0]
        rec["Naive (last quarter)"] = te["Gold_Demand_Lag_1"].iloc[0]
        # YoY-elasticity model: ln(D_t/D_t-4) = a + b ln(P_t/P_t-4)
        lr = LinearRegression().fit(tr[["Gold_Price_LogChg"]], tr["Demand_YoY_Log"])
        rec["Price-adjusted seasonal (YoY elasticity)"] = te["Gold_Demand_Lag_4"].iloc[0] * np.exp(lr.predict(te[["Gold_Price_LogChg"]])[0])
        rid = make_pipeline(StandardScaler(), Ridge(alpha=5.0)).fit(tr[SETB], tr["Gold_Demand"])
        rec["Ridge (YoY features)"] = rid.predict(te[SETB])[0]
        rf = RandomForestRegressor(n_estimators=300, max_depth=4, min_samples_leaf=2, random_state=C.RANDOM_STATE).fit(tr[SETB], tr["Gold_Demand"])
        rec["Random Forest (YoY features)"] = rf.predict(te[SETB])[0]
        rows.append(rec)
    pred = pd.DataFrame(rows)
    models = [c for c in pred.columns if c not in ("Date", "Actual")]
    res = pd.DataFrame([dict(Model=m, **_metrics(pred["Actual"], pred[m])) for m in models]).sort_values("RMSE")
    res.insert(1, "n_test_quarters", len(pred))
    res.to_csv(C.TAB / "model_comparison_v2.csv", index=False)
    pred.to_csv(C.TAB / "model_predictions_v2.csv", index=False)
    return d, pred, res


def scenario_next_quarter(g, d, rmse_model):
    """Conditional scenarios for the first quarter after the data ends. Price assumptions are NOT forecasts.
    Two elasticity regimes are shown because the full-sample slope (dominated by 2011-2019 and COVID) is much steeper
    than the post-2022 slope; the truth is uncertain, so we report both. Interval = +/-1.96 x back-test RMSE of the
    price-adjusted model (rough, assumes similar error size)."""
    last = g.iloc[-1]
    nxt_q = int(last["Quarter"] % 4 + 1)
    nxt_year = int(last["Year"] + (1 if last["Quarter"] == 4 else 0))
    ref = g[(g["Year"] == nxt_year - 1) & (g["Quarter"] == nxt_q)].iloc[0]
    fits = {"full_sample": LinearRegression().fit(d[["Gold_Price_LogChg"]], d["Demand_YoY_Log"]),
            "post_2022Q2": LinearRegression().fit(d[d["Date"] > "2022-06-30"][["Gold_Price_LogChg"]], d[d["Date"] > "2022-06-30"]["Demand_YoY_Log"])}
    rows = []
    for lbl, mult in (("Price 10% below latest quarter", 0.90), ("Price flat at latest quarter", 1.00), ("Price 10% above latest quarter", 1.10)):
        p = last["Gold_Price"] * mult
        x = np.log(p / ref["Gold_Price"])
        rec = dict(period=f"{nxt_year}Q{nxt_q}", scenario=lbl, assumed_price_INR_10g=round(p), yoy_log_price_change=round(x, 3),
                   seasonal_naive_t=round(ref["Gold_Demand"], 1))
        for k, f in fits.items():
            dem = ref["Gold_Demand"] * np.exp(f.predict(pd.DataFrame({"Gold_Price_LogChg": [x]}))[0])
            rec[f"demand_{k}_t"] = round(dem, 1)
            rec[f"range_{k}_t"] = f"{dem - 1.96 * rmse_model:.0f} to {dem + 1.96 * rmse_model:.0f}"
        rows.append(rec)
    out = pd.DataFrame(rows)
    out["max_historical_yoy_log_price_change"] = round(d["Gold_Price_LogChg"].max(), 3)
    out.to_csv(C.TAB / "scenario_next_quarter.csv", index=False)
    return out
