"""STEP 3 - Statistics: descriptive stats, correlation, regression, elasticity, hypothesis tests.
Important: a correlation is an ASSOCIATION. We never claim that price 'causes' demand to change."""
import numpy as np
import pandas as pd
from scipy import stats
from . import config as C


def describe(df, cols):
    """Mean, median, min, max, std, variance, quartiles, IQR, skewness, missing count."""
    rows = {}
    for c in cols:
        s = df[c].dropna()
        if s.empty:
            continue
        q1, q3 = s.quantile([.25, .75])
        rows[c] = dict(count=len(s), mean=s.mean(), median=s.median(), min=s.min(), max=s.max(),
                       std=s.std(), variance=s.var(), Q1=q1, Q3=q3, IQR=q3 - q1,
                       skew=s.skew(), missing=int(df[c].isna().sum()))
    return pd.DataFrame(rows).T


def strength_label(r):
    a = abs(r)
    s = "weak" if a < 0.3 else "moderate" if a < 0.6 else "strong"
    return f"{s} {'positive' if r > 0 else 'negative'}"


def relationship(x, y):
    """Pearson + Spearman + simple linear regression (y = a + b x) for one pair of variables."""
    d = pd.concat([x, y], axis=1).dropna()
    n = len(d)
    if n < 4:
        return dict(n=n, note="too few observations")
    xv, yv = d.iloc[:, 0], d.iloc[:, 1]
    pr, pp = stats.pearsonr(xv, yv)
    sr, sp = stats.spearmanr(xv, yv)
    lr = stats.linregress(xv, yv)
    return dict(n=n, pearson_r=pr, pearson_p=pp, spearman_rho=sr, spearman_p=sp,
                slope=lr.slope, intercept=lr.intercept, r_squared=lr.rvalue ** 2, slope_p=lr.pvalue,
                strength=strength_label(pr))


def relationship_table(df, pairs, label):
    rows = []
    for name, (xc, yc) in pairs.items():
        if xc in df.columns and yc in df.columns:
            r = relationship(df[xc], df[yc])
            rows.append(dict(analysis=name, basis=label, x=xc, y=yc, **r))
    return pd.DataFrame(rows)


def elasticity(df, price, demand):
    """Log-log regression  ln(D) = a + e*ln(P) + error.  The slope e is the price elasticity estimate.
    We also fit it on 4-quarter log changes (removes the shared time trend). Interpret with caution."""
    d = df[[price, demand]].dropna()
    d = d[(d > 0).all(axis=1)]
    out = {}
    for tag, data in (("levels", np.log(d)), ("yoy_log_change", np.log(d).diff(4).dropna())):
        if len(data) < 6:
            continue
        lr = stats.linregress(data[price], data[demand])
        tcrit = stats.t.ppf(0.975, len(data) - 2)
        out[tag] = dict(n=len(data), elasticity=lr.slope, std_err=lr.stderr, p_value=lr.pvalue,
                        ci_low=lr.slope - tcrit * lr.stderr, ci_high=lr.slope + tcrit * lr.stderr,
                        r_squared=lr.rvalue ** 2, interpretation=interpret_elasticity(lr.slope, lr.pvalue))
    return out


def interpret_elasticity(e, p=None):
    if e < -1:
        txt = "elastic (|e|>1, negative)"
    elif e < 0:
        txt = "inelastic negative relationship"
    else:
        txt = "positive relationship (demand rises with price in this data)"
    if p is not None and p >= C.ALPHA:
        txt += "; NOT statistically significant, so treat as inconclusive"
    return txt


def hypothesis_tests(rel_df, hyps):
    """H0: no significant relationship. Test = Pearson correlation t-test. Reject H0 if p < alpha."""
    rows = []
    for name, key in hyps.items():
        r = rel_df[rel_df["analysis"] == key]
        if r.empty or "pearson_p" not in r or pd.isna(r.iloc[0].get("pearson_p")):
            continue
        r = r.iloc[0]
        n, rr = int(r["n"]), r["pearson_r"]
        t = rr * np.sqrt((n - 2) / (1 - rr ** 2)) if abs(rr) < 1 else np.inf
        reject = r["pearson_p"] < C.ALPHA
        rows.append(dict(hypothesis=name, test="Pearson correlation t-test", n=n, statistic_t=t, p_value=r["pearson_p"],
                         alpha=C.ALPHA, decision="Reject H0" if reject else "Fail to reject H0",
                         interpretation=("Significant " if reject else "No significant ") + r["strength"].split()[1] +
                         " association (not proof of causation)."))
    return pd.DataFrame(rows)


def correlation_matrix(df, cols, method="pearson"):
    cols = [c for c in cols if c in df.columns and df[c].notna().sum() > 3]
    return df[cols].corr(method=method)


def concentration(res, mineral, year=None, top_n=5):
    """Top-N states vs rest of India (share of total resource)."""
    d = res[res["Mineral"].str.lower() == mineral.lower()]
    if year is None:
        year = d["Year"].max()
    d = d[d["Year"] == year].sort_values("Resources", ascending=False)
    total = d["Resources"].sum()
    top = d.head(top_n)
    return pd.DataFrame({"group": [f"Top {top_n} states", "Rest of listed states"],
                         "resources": [top["Resources"].sum(), total - top["Resources"].sum()],
                         "share_pct": [top["Resources"].sum() / total * 100, 100 - top["Resources"].sum() / total * 100],
                         "year": year})


def seasonality_by_quarter(df, col):
    """Average of the metric per quarter number - only a hint of seasonality; need several years to trust it."""
    return df.groupby("Quarter")[col].agg(["mean", "std", "count"])
