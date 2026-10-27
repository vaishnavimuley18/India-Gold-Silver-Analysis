"""STEP 2 - Create new columns (features) from the cleaned data.
Each function documents the formula so you can explain it in the viva."""
import numpy as np
import pandas as pd


def add_growth(df, cols, periods, label):
    """Growth % = (current - previous) / previous x 100.  periods=1 -> QoQ, periods=4 -> YoY (quarterly data)."""
    for c in cols:
        if c in df.columns:
            df[f"{c}_{label}"] = df[c].pct_change(periods) * 100
    return df


def add_log_change(df, cols, periods=4):
    """Log difference ln(x_t) - ln(x_{t-4}). ~ percentage change, but symmetric and good for elasticity."""
    for c in cols:
        if c in df.columns:
            v = df[c].where(df[c] > 0)
            df[f"{c}_LogChg"] = np.log(v).diff(periods)
    return df


def add_lags(df, col, lags=(1, 2, 4)):
    """Lag k = value k periods ago. Lag 1 = previous quarter, lag 4 = same quarter last year."""
    for k in lags:
        df[f"{col}_Lag_{k}"] = df[col].shift(k)
    return df


def add_time_features(df):
    df["Quarter_Number"] = df["Quarter"]
    return df


def add_price_index(df, col, base_row=0):
    """Index = value / value at base period x 100, so metals with different units can be compared."""
    base = df[col].iloc[base_row]
    df[f"{col}_Index"] = df[col] / base * 100
    return df


def build_gold_quarterly_features(df):
    df = df.copy()
    df = add_growth(df, ["Gold_Price", "Gold_Demand", "Jewellery_Demand", "Investment_Demand"], 4, "YoY")
    df = add_growth(df, ["Gold_Price", "Gold_Demand"], 1, "QoQ")
    df = add_log_change(df, ["Gold_Price", "Gold_Demand", "Jewellery_Demand", "Investment_Demand"], 4)
    df["Gold_Price_Change"] = df["Gold_Price"].diff(1)
    df = add_lags(df, "Gold_Demand", (1, 2, 4))
    df = add_time_features(df)
    df = add_price_index(df, "Gold_Price")
    return df


def build_annual_master(supply, silver, rbi_q=None):
    """Annual dataset: merge on Year only (never merge annual with quarterly rows)."""
    m = supply.copy() if supply is not None else None
    if silver is not None:
        m = silver if m is None else m.merge(silver, on="Year", how="outer")
    if m is None:
        return None
    m = m.sort_values("Year").reset_index(drop=True)
    # Total supply (our definition) = domestic production + imports + recycling
    for metal, rec in (("Gold", "Gold_Recycling_t"), ("Silver", None)):
        p, i = f"{metal}_Production_t", f"{metal}_Imports_t"
        if p in m.columns and i in m.columns:
            parts = m[[p, i] + ([rec] if rec in m.columns else [])]
            m[f"{metal}_Total_Supply_t"] = parts.sum(axis=1, min_count=parts.shape[1])  # ALL components must exist (no partial sums)
            tot = m[f"{metal}_Total_Supply_t"]
            m[f"{metal}_Import_Dependency"] = m[i] / tot * 100
            m[f"{metal}_Domestic_Share"] = m[p] / tot * 100
            if rec in m.columns:
                m[f"{metal}_Recycling_Share"] = m[rec] / tot * 100
    # WGC-only view (2012+): share of India's total gold supply that is net bullion imports / recycled scrap.
    if {"Gold_Net_Imports_t", "Gold_WGC_Total_Supply_t"} <= set(m.columns):
        m["Gold_Net_Import_Share_WGC"] = m["Gold_Net_Imports_t"] / m["Gold_WGC_Total_Supply_t"] * 100
        m["Gold_Scrap_Share_WGC"] = m["Gold_Recycling_t"] / m["Gold_WGC_Total_Supply_t"] * 100
    for c in ("Gold_Price", "Silver_Price", "Silver_Demand"):
        if c in m.columns:
            m[f"{c}_YoY"] = m[c].pct_change() * 100
    if "Silver_Price" in m.columns:
        m = add_price_index(m, "Silver_Price", base_row=m["Silver_Price"].first_valid_index())
    return m


def rbi_to_quarterly(rbi):
    """Take the LAST observation of each quarter (stock variable), so it aligns with quarterly demand."""
    q = rbi.set_index("Date").resample("QE").last().dropna(how="all").reset_index()
    q["Year"], q["Quarter"] = q["Date"].dt.year, q["Date"].dt.quarter
    return q
