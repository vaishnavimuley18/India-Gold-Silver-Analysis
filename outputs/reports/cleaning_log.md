# Cleaning log

- Investment_Demand derived as Bar_Coin_Demand_t + ETF_Demand_t (WGC definition)
- ETF_Demand_t is blank for ALL quarters (no India ETF series in the supplied data), so Investment_Demand = bar & coin only and Gold_Demand = jewellery + bar & coin. WGC's headline India total also includes ETF and industrial demand (3-15% higher in the six quarters that can be checked).
- Gold_Demand = Jewellery_Demand + Investment_Demand (jewellery is gross incl. recycled gold; investment is net)
- Gold_Price uses: INR per 10 g
- Resource_Share = State Resource / sum of listed states x 100 (per mineral and year)
