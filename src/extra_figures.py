"""Extra figures that directly support the research question (YoY elasticity, seasonality, indexed trends)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from . import config as C
from .visualization import _save
from .robustness import COVID_START, COVID_END


def yoy_scatter(g, y="Jewellery_Demand_LogChg", name="scatter_yoy_jewellery"):
    d = g[["Date", "Gold_Price_LogChg", y]].dropna()
    covid = (d["Date"] >= COVID_START) & (d["Date"] <= COVID_END)
    fig, ax = plt.subplots(figsize=(6.5, 5))
    ax.scatter(d.loc[~covid, "Gold_Price_LogChg"], d.loc[~covid, y], alpha=.75, label="Other quarters")
    ax.scatter(d.loc[covid, "Gold_Price_LogChg"], d.loc[covid, y], color="crimson", alpha=.85, label="COVID window (2020Q1-2022Q2)")
    b, a = np.polyfit(d["Gold_Price_LogChg"], d[y], 1)
    xs = np.linspace(d["Gold_Price_LogChg"].min(), d["Gold_Price_LogChg"].max(), 50)
    ax.plot(xs, a + b * xs, "k-", lw=1.5, label=f"OLS slope (elasticity) = {b:.2f}")
    ax.axhline(0, color="grey", lw=.6); ax.axvline(0, color="grey", lw=.6)
    ax.set(xlabel="YoY log change in gold price (INR/10 g)", ylabel="YoY log change in demand",
           title=y.replace("_LogChg", "").replace("_", " ") + ": YoY change vs price YoY change\\n(association, not causation)".replace("\\n", "\n"))
    ax.legend(fontsize=8)
    return _save(fig, name)


def seasonality_box(g):
    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.boxplot(data=g, x="Quarter", y="Gold_Demand", ax=ax, color="#9ecae1")
    sns.stripplot(data=g, x="Quarter", y="Gold_Demand", ax=ax, color="k", size=3, alpha=.6)
    ax.set(title="India gold demand (jewellery + bar & coin) by quarter, 2010-2026", ylabel="tonnes")
    return _save(fig, "seasonality_demand_box")


def indexed_trends(g):
    d = g.copy()
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for c, lbl in (("Gold_Price", "Gold price (INR/10 g)"), ("Jewellery_Demand", "Jewellery demand (t)"), ("Bar_Coin_Demand", "Bar & coin demand (t)")):
        s = d[c].rolling(4).mean()  # 4-quarter moving average removes seasonality
        ax.plot(d["Date"], s / s.dropna().iloc[0] * 100, label=lbl)
    ax.set(title="Indexed trends, 4-quarter moving averages (first available point = 100)", ylabel="index")
    ax.legend()
    return _save(fig, "indexed_price_vs_demand")


def run(g):
    yoy_scatter(g); yoy_scatter(g, "Investment_Demand_LogChg", "scatter_yoy_investment"); yoy_scatter(g, "Gold_Demand_LogChg", "scatter_yoy_total")
    seasonality_box(g); indexed_trends(g)
