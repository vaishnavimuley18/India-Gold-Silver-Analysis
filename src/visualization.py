"""STEP 4 - Plot helpers. Each function saves a PNG into outputs/figures and returns its path."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from . import config as C

sns.set_theme(style="whitegrid", context="notebook")


def _save(fig, name):
    p = C.FIG / f"{name}.png"
    fig.tight_layout()
    fig.savefig(p, dpi=150)
    plt.close(fig)
    return p


def line_plot(df, x, ys, title, ylabel, name):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for y in ys:
        ax.plot(df[x], df[y], marker="o", ms=3, label=y)
    ax.set(title=title, ylabel=ylabel, xlabel=x)
    if len(ys) > 1:
        ax.legend()
    return _save(fig, name)


def hist_plot(df, col, title, name):
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.histplot(df[col].dropna(), kde=True, ax=ax)
    ax.set_title(title)
    return _save(fig, name)


def box_by_quarter(df, col, title, name):
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.boxplot(data=df, x="Quarter", y=col, ax=ax)
    ax.set_title(title)
    return _save(fig, name)


def scatter_regression(df, x, y, title, name):
    d = df[[x, y]].dropna()
    fig, ax = plt.subplots(figsize=(6, 4.5))
    sns.regplot(data=d, x=x, y=y, ax=ax, scatter_kws=dict(alpha=.7))
    ax.set_title(title + "\n(association, not causation)")
    return _save(fig, name)


def stacked_bar(df, x, cols, title, ylabel, name):
    fig, ax = plt.subplots(figsize=(10, 4.5))
    d = df.set_index(x)[cols]
    d.plot(kind="bar", stacked=True, ax=ax)
    ax.set(title=title, ylabel=ylabel)
    return _save(fig, name)


def corr_heatmap(corr, title, name):
    fig, ax = plt.subplots(figsize=(8, 6.5))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", vmin=-1, vmax=1, ax=ax)
    ax.set_title(title + "\n|r|<0.3 weak, 0.3-0.6 moderate, >0.6 strong")
    return _save(fig, name)


def hbar(df, label, value, title, xlabel, name, top=10):
    d = df.sort_values(value, ascending=False).head(top).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(d[label], d[value])
    ax.set(title=title, xlabel=xlabel)
    return _save(fig, name)


def actual_vs_pred(dates, actual, preds: dict, title, name):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(dates, actual, "k-o", label="Actual", ms=3)
    for k, v in preds.items():
        ax.plot(dates, v, "--", label=f"Predicted - {k}")
    ax.set(title=title + " (predictions are model estimates, not official forecasts)", ylabel="tonnes")
    ax.legend()
    return _save(fig, name)


def importance_plot(imp, title, name):
    fig, ax = plt.subplots(figsize=(7, 4))
    imp.sort_values().plot(kind="barh", ax=ax)
    ax.set_title(title + "\n(predictive importance, not causal)")
    return _save(fig, name)
