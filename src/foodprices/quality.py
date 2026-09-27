import numpy as np
import pandas as pd

from foodprices import config


def _stale_flags(price: pd.Series) -> pd.Series:
    """True where the price has been identical for at least STALE_DAYS consecutive observations."""
    run_id = (price != price.shift()).cumsum()
    run_len = price.groupby(run_id).cumcount() + 1
    return run_len >= config.STALE_DAYS


def check(prices: pd.DataFrame, catalogue: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    rows_raw = len(prices)
    df = prices.sort_values(["variety", "date"], kind="stable")
    dup = df.duplicated(["date", "variety"], keep="last")
    df = df[~dup]
    non_pos = df["price"] <= 0
    df = df[~non_pos].copy()

    logp = np.log(df["price"])
    med = logp.groupby(df["variety"]).transform(
        lambda s: s.rolling(config.OUTLIER_WINDOW, min_periods=3).median().shift(1))
    out = (logp - med).abs() > config.OUTLIER_LOG_MAX
    by_var = df.loc[out, "variety"].value_counts()
    df = df[~out].copy()
    df["stale"] = df.groupby("variety")["price"].transform(_stale_flags).astype(bool)

    df = df.merge(catalogue[["variety", "product", "category"]], on="variety", how="left")
    df["category"] = df["category"].fillna("Other")
    df["product"] = df["product"].fillna(df["variety"])

    end = df["date"].max()
    g = df.groupby("variety")
    last = g["date"].max()
    span_days = (last - g["date"].min()).dt.days + 1
    coverage = g.size() / span_days
    stale_now = sorted(v for v, s in g["stale"].last().items() if s and last[v] > end - pd.Timedelta(
        days=config.DISCONTINUED_DAYS))
    report = {
        "rows_raw": int(rows_raw), "rows_clean": len(df), "varieties": int(df["variety"].nunique()),
        "start": f"{df['date'].min():%Y-%m-%d}", "end": f"{end:%Y-%m-%d}",
        "duplicates": int(dup.sum()), "non_positive": int(non_pos.sum()), "outliers": int(out.sum()),
        "outliers_by_variety": [[v, int(n)] for v, n in by_var.head(5).items()],
        "stale_now": stale_now,
        "discontinued": sorted(last[last < end - pd.Timedelta(days=config.DISCONTINUED_DAYS)].index),
        "uncategorised": sorted(set(df.loc[df["category"] == "Other", "variety"])),
        "coverage_median": float(coverage.median()),
    }
    cols = ["date", "variety", "price", "category", "product", "stale"]
    return df[cols].sort_values(["date", "variety"]).reset_index(drop=True), report
