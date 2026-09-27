from pathlib import Path

import pandas as pd

from foodprices import config
from foodprices.sisap import chunks

COLUMNS = ["date", "variety", "price"]


def download(client, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    codes = list(client.products())
    parts = [client.interval(a, b, codes) for a, b in chunks(start, end, config.CHUNK_MONTHS)]
    parts = [p for p in parts if len(p)]
    return pd.concat(parts, ignore_index=True)[COLUMNS] if parts else pd.DataFrame(columns=COLUMNS)


def merge(old: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    both = pd.concat([old[COLUMNS], new[COLUMNS]], ignore_index=True)
    both = both.drop_duplicates(["date", "variety"], keep="last")
    return both.sort_values(["date", "variety"]).reset_index(drop=True)


def catalogue_dates(start: pd.Timestamp, end: pd.Timestamp) -> list[pd.Timestamp]:
    month_starts = pd.date_range(pd.Timestamp(start.year, start.month, 1), end, freq="3MS")
    dates = [d for d in month_starts + pd.Timedelta(days=14) if start <= d <= end]
    return dates + [end]


def build_catalogue(client, dates: list[pd.Timestamp]) -> pd.DataFrame:
    products = client.products()
    by_name = {name.lower(): code for code, name in products.items()}
    codes = list(products)
    frames = [client.day(d, codes).assign(seen=d) for d in dates]
    frames = [f for f in frames if len(f)]
    if not frames:
        return pd.DataFrame(columns=["variety", "product", "code", "category"])
    days = pd.concat(frames, ignore_index=True)
    days = days.sort_values("seen").drop_duplicates("variety", keep="last")
    days["code"] = days["product"].str.lower().map(by_name)
    days["category"] = days["code"].str[:2].map(config.CATEGORIES).fillna("Other")
    return days[["variety", "product", "code", "category"]].sort_values("variety").reset_index(drop=True)


def save(prices: pd.DataFrame, catalogue: pd.DataFrame, dest: Path = config.DATA_RAW) -> None:
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    prices.to_csv(dest / "prices.csv.gz", index=False, date_format="%Y-%m-%d")
    catalogue.to_csv(dest / "catalogue.csv", index=False)


def load(dest: Path = config.DATA_RAW) -> tuple[pd.DataFrame, pd.DataFrame]:
    dest = Path(dest)
    prices = pd.read_csv(dest / "prices.csv.gz", parse_dates=["date"])
    catalogue = pd.read_csv(dest / "catalogue.csv", dtype={"code": str})
    return prices, catalogue
