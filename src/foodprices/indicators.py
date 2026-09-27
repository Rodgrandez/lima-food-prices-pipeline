import numpy as np
import pandas as pd

from foodprices import config


def wide(clean: pd.DataFrame) -> pd.DataFrame:
    w = clean.pivot(index="date", columns="variety", values="price").sort_index()
    return w.reindex(pd.date_range(w.index.min(), w.index.max(), freq="D", name="date"))


def smooth(w: pd.DataFrame) -> pd.DataFrame:
    return w.rolling(config.SMOOTH_DAYS, min_periods=3).mean()


def change(sm: pd.DataFrame, days: int) -> pd.DataFrame:
    return 100 * np.log(sm / sm.shift(days))


def volatility(w: pd.DataFrame) -> pd.DataFrame:
    return (100 * np.log(w).diff()).rolling(config.CHANGE_DAYS, min_periods=10).std()


def pressure(chg: pd.DataFrame) -> pd.DataFrame:
    n = chg.notna().sum(axis=1)
    up = (chg > config.DIFFUSION_THRESHOLD).sum(axis=1)
    down = (chg < -config.DIFFUSION_THRESHOLD).sum(axis=1)
    out = pd.DataFrame({"median": chg.median(axis=1), "diffusion": 100 * (up - down) / n.where(n > 0), "n": n})
    return out[out["n"] > 0]


def shocks(sm: pd.DataFrame, weeks: int) -> pd.DataFrame:
    weekly = np.log(sm.resample("W").last()).diff()
    z = (weekly / weekly.std()).clip(-4, 4)
    return z.iloc[-weeks:].T


def summary(clean, sm, chg28, yoy, vol) -> pd.DataFrame:
    end = clean["date"].max()
    last = clean.sort_values("date").groupby("variety").last()
    active = last[last["date"] > end - pd.Timedelta(days=config.DISCONTINUED_DAYS)]
    rows = []
    for v, r in active.iterrows():
        rows.append({"variety": v, "category": r["category"], "last_date": f"{r['date']:%Y-%m-%d}",
                     "price": float(r["price"]), "chg28": float(chg28[v].dropna().iloc[-1]) if chg28[v].notna().any()
                     else np.nan, "yoy": float(yoy[v].dropna().iloc[-1]) if yoy[v].notna().any() else np.nan,
                     "vol": float(vol[v].dropna().iloc[-1]) if vol[v].notna().any() else np.nan})
    return pd.DataFrame(rows).sort_values(["category", "variety"]).reset_index(drop=True)
