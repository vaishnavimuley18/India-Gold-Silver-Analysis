"""STEP 5 - Gold demand prediction (quarterly).

LEAKAGE NOTE: Gold_Demand = Jewellery + Investment, so same-quarter Jewellery/Investment would let the model
'see' the answer. We therefore only use information known BEFORE the quarter being predicted (lags) plus the
quarter's price and calendar quarter. This is the honest set-up."""
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from . import config as C

TARGET = "Gold_Demand"
FEATURES = ["Gold_Price", "Gold_Price_Change", "Gold_Demand_Lag_1", "Gold_Demand_Lag_2",
            "Gold_Demand_Lag_4", "Quarter_Number"]


def prepare(df):
    cols = [c for c in FEATURES if c in df.columns]
    d = df.dropna(subset=cols + [TARGET]).reset_index(drop=True)
    return d, cols


def chronological_split(d, test_frac=C.TEST_FRACTION):
    k = max(2, int(round(len(d) * (1 - test_frac))))
    return d.iloc[:k], d.iloc[k:]


def metrics(y, p):
    return dict(MAE=mean_absolute_error(y, p), RMSE=float(np.sqrt(mean_squared_error(y, p))),
                R2=r2_score(y, p) if len(y) > 1 else np.nan)


def train_and_evaluate(df):
    d, cols = prepare(df)
    if len(d) < 12:
        print(f"[skip model] only {len(d)} usable rows after lagging - need more quarters")
        return None
    train, test = chronological_split(d)
    models = {
        "Linear Regression": make_pipeline(StandardScaler(), LinearRegression()),
        "Random Forest": RandomForestRegressor(n_estimators=300, max_depth=4, min_samples_leaf=2, random_state=C.RANDOM_STATE),
    }
    rows, preds = [], {}
    n_splits = min(5, max(2, len(train) // 5))
    for name, m in models.items():
        cv = -cross_val_score(m, train[cols], train[TARGET], cv=TimeSeriesSplit(n_splits=n_splits),
                              scoring="neg_root_mean_squared_error").mean()
        m.fit(train[cols], train[TARGET])
        p = m.predict(test[cols])
        preds[name] = p
        rows.append(dict(Model=name, **metrics(test[TARGET], p), CV_RMSE_train=cv))
        joblib.dump(m, C.MOD / f"{name.lower().replace(' ', '_')}.joblib")
    # Naive baseline: 'same as last quarter'. A model must beat this to be useful.
    base = test["Gold_Demand_Lag_1"] if "Gold_Demand_Lag_1" in test else test[TARGET].shift(1).bfill()
    rows.append(dict(Model="Naive baseline (last quarter)", **metrics(test[TARGET], base), CV_RMSE_train=np.nan))
    res = pd.DataFrame(rows)
    best = res.loc[res["RMSE"].idxmin(), "Model"]
    rf = models["Random Forest"]
    imp = pd.Series(rf.feature_importances_, index=cols, name="importance").sort_values(ascending=False)
    pred_df = test[["Date", TARGET]].copy()
    for k, v in preds.items():
        pred_df[f"Predicted_{k}"] = v
    pred_df.to_csv(C.TAB / "model_predictions.csv", index=False)
    res.to_csv(C.TAB / "model_comparison.csv", index=False)
    imp.to_csv(C.TAB / "feature_importance.csv")
    return dict(results=res, best=best, importance=imp, test=test, preds=preds, n_train=len(train), n_test=len(test), features=cols)
