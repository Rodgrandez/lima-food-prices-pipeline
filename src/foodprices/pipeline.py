import io
import json
import sys
import urllib.request

import pandas as pd

from foodprices import config, panel, plots, publish, quality, report, site
from foodprices import indicators as ind
from foodprices.sisap import Client


def today() -> pd.Timestamp:
    return pd.Timestamp.now(tz="America/Lima").normalize().tz_localize(None)


def _published():
    try:
        with urllib.request.urlopen(config.PAGES_URL + "data/prices.csv.gz", timeout=60) as r:
            return pd.read_csv(io.BytesIO(r.read()), compression="gzip", parse_dates=["date"])
    except OSError:
        return None


def stage_fetch(client=None):
    client = client or Client()
    end = today()
    prices = panel.download(client, pd.Timestamp(config.START), end)
    cat = panel.build_catalogue(client, panel.catalogue_dates(pd.Timestamp(config.START), end))
    panel.save(prices, cat, config.DATA_RAW)


def stage_update(client=None, fetch_published=_published):
    client = client or Client()
    if (config.DATA_RAW / "prices.csv.gz").exists():
        old, cat = panel.load(config.DATA_RAW)
    else:
        old, cat = fetch_published(), None
    if old is None or old.empty:
        return stage_fetch(client)
    end = today()
    new = panel.download(client, end - pd.Timedelta(days=config.UPDATE_DAYS), end)
    prices = panel.merge(old, new)
    fresh = panel.build_catalogue(client, [end])
    cat = fresh if cat is None else pd.concat([cat, fresh]).drop_duplicates("variety", keep="last")
    panel.save(prices, cat.sort_values("variety").reset_index(drop=True), config.DATA_RAW)


def stage_build():
    prices, cat = panel.load(config.DATA_RAW)
    clean, q = quality.check(prices, cat)
    status = site.build(clean, q, config.SITE)
    w = ind.wide(clean)
    sm = ind.smooth(w)
    chg28 = ind.change(sm, config.CHANGE_DAYS)
    plots.preview(ind.pressure(chg28).dropna(subset=["median"]), ind.shocks(sm, config.SHOCK_WEEKS),
                  config.FIGURES / "preview.png")
    summ = ind.summary(clean, sm, chg28, ind.change(sm, 365), ind.volatility(w))
    report.update_readme(config.ROOT / "README.md", status, q, summ)
    print(f"built site: data through {status['last_date']}, {status['varieties']} varieties", flush=True)


def stage_publish():
    status = json.loads((config.SITE / "data" / "status.json").read_text(encoding="utf-8"))
    publish.push_site(config.SITE, publish.remote_url(), message=f"Data through {status['last_date']}")
    print(f"published site: data through {status['last_date']}", flush=True)


STAGES = {"fetch": [stage_fetch], "update": [stage_update], "build": [stage_build], "publish": [stage_publish],
          "all": [stage_fetch, stage_build], "daily": [stage_update, stage_build, stage_publish]}

if __name__ == "__main__":
    for fn in STAGES[sys.argv[1] if len(sys.argv) > 1 else "all"]:
        print(f"== {fn.__name__}", flush=True)
        fn()
