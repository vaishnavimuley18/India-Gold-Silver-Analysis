"""Embed the pipeline's CSV results into template.html -> dashboard.html.
The dashboard is a single self-contained file (Chart.js is inlined from dashboard/vendor/, so it works offline).
Run AFTER run_pipeline.py:   python dashboard/build_dashboard.py"""
import json
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
P, T = ROOT / "data" / "processed", ROOT / "outputs" / "tables"


def n(v, d=4):
    return None if pd.isna(v) else round(float(v), d)


def recs(df, d=4):
    out = []
    for r in df.to_dict("records"):
        out.append({k: (None if (isinstance(v, float) and pd.isna(v)) else (round(v, d) if isinstance(v, float) else v)) for k, v in r.items()})
    return out


# ---- quarterly gold (price, demand, YoY log changes) ----
g = pd.read_csv(P / "gold_quarterly_features.csv", parse_dates=["Date"])
q = [dict(d=r.Date.strftime("%Y-%m-%d"), y=int(r.Year), qn=int(r.Quarter), p=f"{int(r.Year)} Q{int(r.Quarter)}",
          price=n(r.Gold_Price), usd=n(r.Gold_Price_USD_oz), jew=n(r.Jewellery_Demand), bar=n(r.Bar_Coin_Demand),
          dem=n(r.Gold_Demand), py=n(r.Gold_Price_LogChg), jy=n(r.Jewellery_Demand_LogChg),
          ty=n(r.Gold_Demand_LogChg), by=n(r.Investment_Demand_LogChg)) for r in g.itertuples()]

# ---- resources by state ----
rs = pd.read_csv(P / "resources_clean.csv")
res = [dict(s=r.State, m=r.Mineral, res=n(r.Resources), rsv=n(r.Reserves), rem=n(r.Remaining_Resources), sh=n(r.Resource_Share, 2)) for r in rs.itertuples()]

# ---- annual supply / production / silver ----
am = pd.read_csv(P / "annual_master.csv")
a = [dict(y=int(r.Year), gp=n(r.Gold_Production_t), gi=n(r.Gold_Imports_t), ni=n(r.Gold_Net_Imports_t), sc=n(r.Gold_Recycling_t),
          dom=n(r.Gold_Domestic_Other_t), ts=n(r.Gold_WGC_Total_Supply_t), nis=n(r.Gold_Net_Import_Share_WGC), scs=n(r.Gold_Scrap_Share_WGC),
          sp=n(r.Silver_Production_t), si=n(r.Silver_Imports_t), se=n(r.Silver_Exports_t)) for r in am.itertuples()]

# ---- result tables ----
rob = recs(pd.read_csv(T / "robustness_elasticity.csv"))
mp = pd.read_csv(T / "model_predictions_v2.csv")
mpl = [dict(d=str(r["Date"])[:7], a=n(r["Actual"]), sn=n(r["Seasonal naive (same quarter last year)"]), nl=n(r["Naive (last quarter)"]),
            rg=n(r["Ridge (YoY features)"]), rf=n(r["Random Forest (YoY features)"]), pa=n(r["Price-adjusted seasonal (YoY elasticity)"])) for _, r in mp.iterrows()]
mc = recs(pd.read_csv(T / "model_comparison_v2.csv"), 3)
rel = recs(pd.read_csv(T / "relationships.csv"), 5)
el = recs(pd.read_csv(T / "elasticity_gold.csv"), 5)
hyp = recs(pd.read_csv(T / "hypothesis_tests.csv"), 5) + recs(pd.read_csv(T / "hypothesis_tests_yoy.csv"), 5)
fi = recs(pd.read_csv(T / "feature_importance.csv").rename(columns={"Unnamed: 0": "feature"}), 4)
scen = recs(pd.read_csv(T / "scenario_next_quarter.csv"), 3)
cross = recs(pd.read_csv(T / "crosscheck_india_focus.csv"), 2)

data = dict(q=q, res=res, a=a, rob=rob, mp=mpl, mc=mc, rel=rel, el=el, hyp=hyp, fi=fi, scen=scen, cross=cross)
payload = json.dumps(data, separators=(",", ":"), allow_nan=False)

tpl = (HERE / "template.html").read_text(encoding="utf-8")
vendor = HERE / "vendor" / "chart.umd.js"
chart_tag = f"<script>{vendor.read_text(encoding='utf-8')}</script>" if vendor.exists() else \
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>'
html = tpl.replace("<!--CHARTJS-->", chart_tag).replace("/*DATA*/null", payload)
(HERE / "dashboard.html").write_text(html, encoding="utf-8")
print("dashboard.html written,", len(html) // 1024, "KB", "(Chart.js inlined)" if vendor.exists() else "(Chart.js from CDN)")
