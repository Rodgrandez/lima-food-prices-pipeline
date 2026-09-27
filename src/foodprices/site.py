import json
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

from foodprices import config
from foodprices import indicators as ind


def _num(x):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), 4)


def _dump(obj, path: Path) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def build(clean: pd.DataFrame, quality_report: dict, out_dir: Path) -> dict:
    out_dir, data = Path(out_dir), Path(out_dir) / "data"
    data.mkdir(parents=True, exist_ok=True)
    w = ind.wide(clean)
    sm = ind.smooth(w)
    chg28, yoy, vol = ind.change(sm, config.CHANGE_DAYS), ind.change(sm, 365), ind.volatility(w)
    press = ind.pressure(chg28).dropna(subset=["median"])
    z = ind.shocks(sm, config.SHOCK_WEEKS)
    cats = clean.drop_duplicates("variety", keep="last").set_index("variety")["category"]
    weekly = w.resample("W").mean()
    _dump({v: {"category": cats[v], "dates": [f"{d:%Y-%m-%d}" for d in weekly.index[weekly[v].notna()]],
               "price": [_num(x) for x in weekly[v].dropna()]} for v in weekly.columns}, data / "series.json")
    _dump({"dates": [f"{d:%Y-%m-%d}" for d in press.index], "median": [_num(x) for x in press["median"]],
           "diffusion": [_num(x) for x in press["diffusion"]], "n": [int(x) for x in press["n"]]},
          data / "pressure.json")
    order = sorted(z.index, key=lambda v: (cats.get(v, "Other"), v))
    _dump({"weeks": [f"{d:%Y-%m-%d}" for d in z.columns], "varieties": order,
           "z": [[_num(x) for x in z.loc[v]] for v in order]}, data / "shocks.json")
    summ = ind.summary(clean, sm, chg28, yoy, vol)
    _dump([{k: (_num(v) if isinstance(v, float) else v) for k, v in r.items()} for r in summ.to_dict("records")],
          data / "summary.json")
    _dump(quality_report, data / "quality.json")
    status = {"last_date": f"{clean['date'].max():%Y-%m-%d}",
              "updated_utc": pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%dT%H:%MZ"),
              "varieties": len(summ),
              "median_chg28": _num(press["median"].iloc[-1]), "diffusion": _num(press["diffusion"].iloc[-1])}
    _dump(status, data / "status.json")
    for f in config.WEB.iterdir():
        shutil.copy(f, out_dir / f.name)
    return status
