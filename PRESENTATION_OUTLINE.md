# Presentation outline (15 slides) - filled with the project's real results
1. **Title** - India's Gold & Silver: Trends, Market Analysis and Resource Insights; team, guide.
2. **Problem** - how do gold prices relate to demand in India, given tiny domestic resources?
3. **Motivation** - India: 658.8 t of identified gold resource vs ~721 t of consumer demand in 2025 alone.
4. **Objectives** - describe, test price-demand association, estimate elasticity, predict, visualise.
5. **Data** - WGC (66 quarters), IBM NMI 2025 (state resources), IBM production/trade; what was NOT available (silver price/demand, RBI series).
6. **Preprocessing** - Jewellery + bar & coin definition; cross-check against India Focus (<= 0.05 t); quarterly vs annual kept separate.
7. **EDA** - price 16.6k to 150.7k Rs/10 g; demand seasonality (Q4 245 t vs Q1 169 t); jewellery vs bar & coin trends (`indexed_price_vs_demand`, `seasonality_demand_box`).
8. **Resources** - Karnataka 41.8% + Rajasthan 37.2% of gold; Rajasthan 97.7% of silver (`top_states_*`).
9. **Price vs demand** - YoY scatters, COVID points highlighted (`scatter_yoy_*`).
10. **Statistics** - jewellery elasticity -1.06 (robust); total weak ex-COVID; bar & coin none; H1/H2 vs H3 decisions; Newey-West.
11. **ML** - v1 failure (negative predictions) explained; v2 walk-forward; seasonal naive RMSE 24.4 t beats Ridge 32.0, RF 32.4.
12. **Dashboard** - `dashboard/dashboard.html` screenshots (and Power BI if built).
13. **Insights and implications** - volume adjusts to price; investment behaves differently; import dependence.
14. **Limitations and future scope** - silver and RBI data, ETF/industrial demand, monthly data, FX/duty/festival variables, SARIMA.
15. **Conclusion** - answer using only these results.
