"""Central configuration: folder paths, raw file names and thresholds.
Every other module imports from here so paths are defined in ONE place."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
OUT = ROOT / "outputs"
FIG, TAB, MOD, REP = OUT / "figures", OUT / "tables", OUT / "models", OUT / "reports"
DASH = ROOT / "dashboard"

# Raw files that YOU fill in with real, downloaded values (see DATA_DOWNLOAD_CHECKLIST.md)
RAW_FILES = {
    "gold_quarterly": RAW / "gold" / "gold_quarterly_raw.csv",
    "silver_annual": RAW / "silver" / "silver_annual_raw.csv",
    "resources": RAW / "resources" / "mineral_resources_raw.csv",
    "rbi_gold": RAW / "rbi" / "rbi_gold_raw.csv",
    "annual_supply": RAW / "imports_exports" / "annual_supply_raw.csv",
}

ALPHA = 0.05            # significance level for hypothesis tests
TEST_FRACTION = 0.20    # latest 20% of observations are the test set
RANDOM_STATE = 42
OZ_TO_GRAMS = 31.1034768  # troy ounce -> grams

for _d in (PROC, FIG, TAB, MOD, REP, DASH):
    _d.mkdir(parents=True, exist_ok=True)
