"""Connectivity check: can this machine (e.g. a GitHub runner) reach SISAP and parse a week of prices?"""
import pandas as pd

from foodprices.sisap import Client


def main() -> None:
    client = Client(sleep=0)
    codes = list(client.products())
    end = pd.Timestamp.now(tz="America/Lima").normalize().tz_localize(None) - pd.Timedelta(days=1)
    df = client.interval(end - pd.Timedelta(days=6), end, codes)
    print(f"products={len(codes)} rows={len(df)} varieties={df['variety'].nunique() if len(df) else 0}")
    if df.empty:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
