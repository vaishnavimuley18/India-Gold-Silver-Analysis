"""Independent validation of the extracted WGC numbers.
(1) Q2'26 workbook vs the India Focus Q2 2026 report, Table 1 (transcribed from the PDF).
(2) Q1'26 workbook vs Q2'26 workbook for all overlapping quarters (detects data revisions)."""
import pandas as pd
from . import config as C
from .build_raw_from_sources import wgc_quarterly, Q1_FILE, Q2_FILE

# India Focus Q2 2026, Table 1 (tonnes; prices LBMA US$/oz and MCX INR/10g)
TABLE1 = pd.DataFrame({
    "Period": ["2025Q1", "2025Q2", "2025Q3", "2025Q4", "2026Q1", "2026Q2"],
    "Jewellery": [81.6, 88.8, 125.0, 145.3, 66.1, 75.1],
    "BarCoin": [46.7, 46.1, 91.6, 96.0, 62.3, 50.3],
    "ETF": [6.7, 2.3, 10.7, 17.6, 19.9, 3.6],
    "Industrial": [2.5, 2.0, 2.5, 3.0, 2.3, 1.9],
    "WGC_Total": [137.4, 139.1, 229.8, 261.9, 150.6, 130.9],
    "LBMA_USD_oz": [2860, 3280, 3457, 4135, 4873, 4506],
    "MCX_INR_10g": [83376, 94877, 102289, 125744, 151108, 150733],
})


def run():
    g = wgc_quarterly(Q2_FILE)
    g["Period"] = g["Year"].astype(str) + g["Quarter"]
    m = TABLE1.merge(g, on="Period")
    out = pd.DataFrame({
        "Period": m["Period"],
        "Jewellery_diff_t": (m["Jewellery_Demand_t"] - m["Jewellery"]).round(2),
        "BarCoin_diff_t": (m["Bar_Coin_Demand_t"] - m["BarCoin"]).round(2),
        "Price_USD_diff": (m["Gold_Price_USD_oz"] - m["LBMA_USD_oz"]).round(1),
        "Price_INR_diff": (m["Gold_Price_INR_10g"] - m["MCX_INR_10g"]).round(0),
        "Our_Demand_t(Jew+Bar)": (m["Jewellery_Demand_t"] + m["Bar_Coin_Demand_t"]).round(1),
        "WGC_Headline_Total_t": m["WGC_Total"],
        "Gap_ETF_plus_Industrial_t": (m["WGC_Total"] - m["Jewellery_Demand_t"] - m["Bar_Coin_Demand_t"]).round(1),
        "Gap_pct_of_headline": ((m["WGC_Total"] - m["Jewellery_Demand_t"] - m["Bar_Coin_Demand_t"]) / m["WGC_Total"] * 100).round(1),
    })
    out.to_csv(C.TAB / "crosscheck_india_focus.csv", index=False)
    print(out.to_string(index=False))

    q1 = wgc_quarterly(Q1_FILE)
    j = q1.merge(g, on=["Year", "Quarter"], suffixes=("_q1", "_q2"))
    cols = ["Gold_Price_USD_oz", "Gold_Price_INR_10g", "Jewellery_Demand_t", "Bar_Coin_Demand_t"]
    rev = pd.DataFrame({"Year": j["Year"], "Quarter": j["Quarter"]})
    for c in cols:
        rev[c + "_rev"] = (j[c + "_q2"] - j[c + "_q1"]).abs()
    changed = rev[(rev[[c + "_rev" for c in cols]] > 1e-6).any(axis=1)]
    changed.to_csv(C.TAB / "crosscheck_q1_vs_q2_revisions.csv", index=False)
    print(f"\nOverlapping quarters compared: {len(j)}; quarters revised between Q1'26 and Q2'26 workbooks: {len(changed)}")
    if len(changed):
        print(changed.round(3).to_string(index=False))


if __name__ == "__main__":
    run()
