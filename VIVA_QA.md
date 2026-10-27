# Viva questions and answers (student-friendly)
1. **Why this topic?** India is among the biggest gold consumers but mines very little; price swings affect households, jewellers and reserves.
2. **Why gold and silver?** Both are precious metals with jewellery and investment demand; silver also has industrial use, so comparing them shows different price sensitivity.
3. **Resources vs reserves?** Resources are identified deposits; reserves are the part that is economically mineable. Reserves <= resources.
4. **What is RBI gold reserve?** Gold held by the central bank as part of foreign-exchange reserves. It is not the gold under India's ground.
5. **Why WGC?** It is the standard source of quarterly gold demand and price data, built with Metals Focus.
6. **Why IBM?** Official government source for mineral resources, reserves and production.
7. **What preprocessing did you do?** Type conversion, duplicates, state-name standardisation, unit conversion, derived Investment = bar&coin + ETF, flagged outliers (see cleaning_log.md).
8. **How did you handle missing values?** We did not invent values; missing cells stay empty, and variables lacking reliable data were excluded and listed as limitations.
9. **What is correlation?** A number from -1 to +1 showing how two variables move together.
10. **Pearson correlation?** Measures linear association; sensitive to outliers.
11. **Spearman correlation?** Rank-based; captures monotonic relationships and is robust to outliers.
12. **What is regression?** A fitted line y = a + bx; b says how much y changes per unit of x on average.
13. **Price elasticity?** % change in demand / % change in price. We estimate it from a log-log slope; it is an association here, not a causal estimate.
14. **Why does correlation not imply causation?** A third factor (income, festivals, global prices) can drive both; the data cannot separate that.
15. **Why Linear Regression?** Simple, interpretable baseline that works with few observations.
16. **Why Random Forest?** Captures non-linear patterns and gives feature importance; we limit depth because data is small.
17. **What is R2?** The share of variation in the target explained by the model; it can be negative on test data if the model is worse than predicting the mean.
18. **What is RMSE?** Square root of average squared error, in tonnes; punishes large errors.
19. **What is MAE?** Average absolute error, in tonnes; easy to explain.
20. **How did you avoid data leakage?** Same-quarter jewellery and investment demand add up to total demand, so they were excluded; only lags and known-at-the-time variables were used; the split is chronological.
21. **Why a chronological split?** The future must not be used to predict the past; shuffling would give unrealistically good scores.
22. **Why a naive baseline?** If a model cannot beat 'same as last quarter', it adds no value.
23. **Why test YoY changes as well as levels?** Both series trend upward over time, which can create a misleading correlation; changes remove that shared trend.
24. **Limitations?** Small samples, mixed frequencies, snapshot resource data, gross vs net definitions, revisions, no causal design.
25. **Future improvements?** Monthly data, macro variables, exchange rates, import duties, SARIMA.

## Questions specific to the results (numbers as of the supplied data, Q2 2026)
26. **Main finding?** Jewellery volume falls when gold prices rise: YoY elasticity -1.06 (95% CI -1.70 to -0.42), still -0.56 to -0.90 in sub-samples. Bar & coin shows no significant association (+0.10, p = 0.76).
27. **Is H1 (price vs total demand) really supported?** Weakly. Significant on the full sample (-0.70) but -0.36 (p = 0.078) without the COVID window and -0.16 (p = 0.14) after 2022. Say it depends on COVID.
28. **Why did you add Newey-West (HAC) errors?** YoY changes of quarterly data overlap, so neighbouring observations are correlated and ordinary p-values are too small. HAC corrects the standard errors.
29. **Why did the template's linear model predict negative demand?** It used price levels. Prices in the test years (Rs 125,000-150,000) were far above the training range (Rs 17,000-100,000), so the line was extrapolated. Modelling YoY changes fixes the scale problem.
30. **Did machine learning beat the baseline?** No. The seasonal-naive forecast (same quarter last year) had RMSE 24.4 t against 32.0 t (Ridge), 32.4 t (Random Forest) and 36.6 t (price-adjusted). Price adds no predictive value beyond seasonality on this data. That is a legitimate finding.
31. **Why is 'same as last quarter' a poor baseline?** Demand is seasonal (average Q4 245 t vs Q1 169 t), so last quarter is a systematically wrong guide.
32. **Why walk-forward instead of one train/test split?** One 12-quarter split gives one noisy verdict; refitting and predicting one quarter at a time over 16 quarters uses the data more fairly.
33. **Why is demand = jewellery + bar & coin and not WGC's total?** WGC's total also includes ETFs and industrial demand; no India ETF series was supplied and the India Focus report gives only six quarters, so including it would break the series. The difference is 3-15% where checkable.
34. **Why is there no silver analysis?** The Silver Institute price/demand data were not in the supplied files and we do not estimate data. Silver resources (Rajasthan 98%) and production/imports are covered; H4 is future work.
35. **What does the resource analysis show?** India's identified gold resource is 658.8 t of metal (reserves 81.9 t); Karnataka and Rajasthan hold 79%. That total is smaller than one recent year of consumer demand (721 t in 2025), which is why India depends on imports (net bullion imports 77-92% of supply, 2012-2025).
36. **Resources vs RBI gold?** Resources are geological estimates in the ground (IBM). RBI gold (about 880 t per the India Focus report) is monetary reserves, bought abroad. They are not comparable.
37. **How did you validate the data?** Compared our extraction with the India Focus Q2 2026 table (differences <= 0.05 t), compared Q1 and Q2 workbooks, and checked that state sums equal IBM's all-India totals exactly.
38. **Does the elasticity mean price causes the fall in demand?** No. It is an association; income, festivals, import duty (raised in mid-May 2026), exchange rate and sentiment also move demand.
