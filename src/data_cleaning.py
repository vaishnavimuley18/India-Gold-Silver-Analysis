"""STEP 1 - Load, clean and validate the raw CSV files.

WHAT: read the raw files you filled in, fix types/names/units, flag suspicious values.
WHY : analysis is only as trustworthy as the data. We FLAG problems instead of silently deleting.
"""
import pandas as pd
import numpy as np
from . import config as C

CLEANING_LOG = []   # every cleaning action is appended here and written to outputs/reports/cleaning_log.md


def log(msg):
    CLEANING_LOG.append(msg)


# ---------- loading ----------
def load_data(key):
    """Return the raw DataFrame, or None if the file is missing or has no rows yet."""
    path = C.RAW_FILES[key]
    if not path.exists():
        print(f"[skip] {path.name} not found")
        return None
    df = pd.read_csv(path)
    if df.empty:
        print(f"[skip] {path.name} has headers only - add real data first")
        return None
    return df


# ---------- helpers ----------
STATE_MAP = {  # inconsistent spellings -> one standard name
    "orissa": "Odisha", "odisha": "Odisha", "andhra pradesh": "Andhra Pradesh",
    "a.p.": "Andhra Pradesh", "karnataka": "Karnataka", "rajasthan": "Rajasthan",
    "jharkhand": "Jharkhand", "bihar": "Bihar", "madhya pradesh": "Madhya Pradesh",
    "west bengal": "West Bengal", "maharashtra": "Maharashtra", "kerala": "Kerala",
    "tamil nadu": "Tamil Nadu", "telangana": "Telangana", "chhattisgarh": "Chhattisgarh",
    "uttar pradesh": "Uttar Pradesh", "assam": "Assam", "gujarat": "Gujarat",
    "uttarakhand": "Uttarakhand", "himachal pradesh": "Himachal Pradesh",
    "meghalaya": "Meghalaya", "nagaland": "Nagaland",
}


def standardize_state(s):
    key = str(s).strip().lower()
    return STATE_MAP.get(key, str(s).strip().title())


def kg_to_tonnes(x):
    return x / 1000.0


def usd_oz_to_usd_10g(x):
    return x / C.OZ_TO_GRAMS * 10


def _numeric(df, cols):
    for c in cols:
        if c in df.columns:
            before = df[c].isna().sum()
            df[c] = pd.to_numeric(df[c], errors="coerce")
            if df[c].isna().sum() > before:
                log(f"{c}: non-numeric entries converted to NaN")
    return df


def _drop_dupes(df, subset, name):
    n = df.duplicated(subset=subset).sum()
    if n:
        log(f"{name}: removed {n} duplicate row(s) on {subset}")
        df = df.drop_duplicates(subset=subset, keep="last")
    return df


# ---------- cleaners ----------
def clean_gold_quarterly(df):
    df = df.copy()
    df.columns = [c.strip() for c in df.columns]
    df = _numeric(df, [c for c in df.columns if c != "Quarter"])
    df["Quarter"] = df["Quarter"].astype(str).str.upper().str.extract(r"(\d)")[0].astype(float)
    df = _drop_dupes(df, ["Year", "Quarter"], "gold_quarterly")
    df["Date"] = pd.PeriodIndex(df["Year"].astype(int).astype(str) + "Q" + df["Quarter"].astype(int).astype(str), freq="Q").to_timestamp(how="end").normalize()
    # WGC defines India investment = bar&coin + ETF. We derive it (documented, not invented).
    df["Investment_Demand"] = df[["Bar_Coin_Demand_t", "ETF_Demand_t"]].sum(axis=1, min_count=1)
    log("Investment_Demand derived as Bar_Coin_Demand_t + ETF_Demand_t (WGC definition)")
    if df["ETF_Demand"].isna().all() if "ETF_Demand" in df.columns else df["ETF_Demand_t"].isna().all():
        log("ETF_Demand_t is blank for ALL quarters (no India ETF series in the supplied data), so Investment_Demand = bar & coin only and Gold_Demand = jewellery + bar & coin. WGC's headline India total also includes ETF and industrial demand (3-15% higher in the six quarters that can be checked).")
    df = df.rename(columns={"Jewellery_Demand_t": "Jewellery_Demand", "Bar_Coin_Demand_t": "Bar_Coin_Demand",
                            "ETF_Demand_t": "ETF_Demand"})
    # Total demand: prefer WGC's own total if you supplied it; otherwise Jewellery + Investment.
    if "Total_Demand_t" in df.columns and df["Total_Demand_t"].notna().any():
        df["Gold_Demand"] = df["Total_Demand_t"]
        log("Gold_Demand taken from the WGC total column supplied by the user")
    else:
        df["Gold_Demand"] = df["Jewellery_Demand"] + df["Investment_Demand"]
        log("Gold_Demand = Jewellery_Demand + Investment_Demand (jewellery is gross incl. recycled gold; investment is net)")
    # Price: prefer INR; fall back to USD/oz converted at nothing (kept separate - no FX invented)
    df["Gold_Price"] = df["Gold_Price_INR_10g"] if df["Gold_Price_INR_10g"].notna().any() else df["Gold_Price_USD_oz"]
    df["Gold_Price_Unit"] = "INR per 10 g" if df["Gold_Price_INR_10g"].notna().any() else "USD per oz"
    log(f"Gold_Price uses: {df['Gold_Price_Unit'].iloc[0]}")
    df = df.sort_values("Date").reset_index(drop=True)
    return df.drop(columns=["Total_Demand_t"], errors="ignore")


def clean_silver_annual(df):
    df = df.copy()
    df = _numeric(df, list(df.columns))
    df = _drop_dupes(df, ["Year"], "silver_annual")
    df = df.rename(columns={"Silver_Price_INR_kg": "Silver_Price", "Silver_Demand_t": "Silver_Demand"})
    return df.sort_values("Year").reset_index(drop=True)


def clean_resources(df):
    df = df.copy()
    df["State"] = df["State"].map(standardize_state)
    df["Mineral"] = df["Mineral"].astype(str).str.strip().str.title()
    df = _numeric(df, ["Year", "Resources_Metal_t", "Reserves_Metal_t", "Production_t"])
    df = _drop_dupes(df, ["State", "Mineral", "Year"], "resources")
    df["Remaining_Resources"] = df["Resources_Metal_t"] - df["Reserves_Metal_t"]
    # Resource_Share = state resource / India total (sum of states) x 100, per mineral-year
    tot = df.groupby(["Mineral", "Year"])["Resources_Metal_t"].transform("sum")
    df["Resource_Share"] = df["Resources_Metal_t"] / tot * 100
    log("Resource_Share = State Resource / sum of listed states x 100 (per mineral and year)")
    return df.rename(columns={"Resources_Metal_t": "Resources", "Reserves_Metal_t": "Reserves", "Production_t": "Production"})


def clean_rbi(df):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad = df["Date"].isna().sum()
    if bad:
        log(f"rbi_gold: {bad} invalid dates dropped")
    df = df.dropna(subset=["Date"])
    df = _numeric(df, ["RBI_Gold_Tonnes", "Gold_Value_USD_mn", "Total_FX_Reserves_USD_mn"])
    df = _drop_dupes(df, ["Date"], "rbi_gold")
    df["Gold_Share_FX_Reserves"] = df["Gold_Value_USD_mn"] / df["Total_FX_Reserves_USD_mn"] * 100
    df = df.rename(columns={"RBI_Gold_Tonnes": "RBI_Gold_Holdings"})
    return df.sort_values("Date").reset_index(drop=True)


def clean_annual_supply(df):
    df = df.copy()
    df = _numeric(df, list(df.columns))
    df = _drop_dupes(df, ["Year"], "annual_supply")
    return df.sort_values("Year").reset_index(drop=True)


# ---------- validation ----------
RULES = {  # column -> (check name, function that returns True for BAD rows)
    "Gold_Demand": ("negative demand", lambda s: s < 0),
    "Silver_Demand": ("negative demand", lambda s: s < 0),
    "Gold_Price": ("non-positive price", lambda s: s <= 0),
    "Silver_Price": ("non-positive price", lambda s: s <= 0),
    "Resources": ("negative resources", lambda s: s < 0),
    "Reserves": ("negative reserves", lambda s: s < 0),
    "Production": ("negative production", lambda s: s < 0),
}


def validate(df, name):
    """Create a validation report (saved as CSV). Returns the report DataFrame."""
    num = df.select_dtypes("number")
    rep = pd.DataFrame({
        "dtype": df.dtypes.astype(str), "missing": df.isna().sum(), "min": num.min(), "max": num.max(),
        "mean": num.mean(), "median": num.median(),
    })
    rep.loc["__rows__", "missing"] = len(df)
    rep.loc["__duplicate_rows__", "missing"] = df.duplicated().sum()
    flags = []
    for col, (msg, bad) in RULES.items():
        if col in df.columns:
            n = int(bad(df[col]).sum())
            if n:
                flags.append(f"{col}: {n} row(s) with {msg}")
    rep.loc["__flags__", "dtype"] = "; ".join(flags) if flags else "none"
    rep.to_csv(C.TAB / f"validation_{name}.csv")
    print(f"[validated] {name}: {len(df)} rows, flags: {rep.loc['__flags__', 'dtype']}")
    return rep


def flag_outliers_iqr(df, col):
    """Mark (do NOT delete) values outside 1.5*IQR. A human then decides if it is an error or a genuine market event."""
    q1, q3 = df[col].quantile([.25, .75])
    iqr = q3 - q1
    return (df[col] < q1 - 1.5 * iqr) | (df[col] > q3 + 1.5 * iqr)


def write_cleaning_log():
    text = "# Cleaning log\n\n" + "\n".join(f"- {m}" for m in dict.fromkeys(CLEANING_LOG)) + "\n"
    (C.REP / "cleaning_log.md").write_text(text)
