import numpy as np
import pandas as pd
import pytest

from foodprices import indicators as ind


def _clean():
    days = pd.date_range("2024-01-01", periods=500)
    rows = []
    for v, growth in [("Up", 0.002), ("Flat", 0.0), ("Down", -0.002)]:
        for i, d in enumerate(days):
            if v == "Flat" and d.dayofweek == 6:
                continue                                    # a variety without Sundays
            rows.append({"date": d, "variety": v, "price": 10 * np.exp(growth * i), "category": "Vegetables",
                         "product": v, "stale": False})
    return pd.DataFrame(rows)


def test_wide_has_full_calendar_with_gaps():
    w = ind.wide(_clean())
    assert len(w) == 500 and w["Flat"].isna().sum() == 71 and set(w.columns) == {"Up", "Flat", "Down"}


def test_change_is_log_difference_in_percent():
    sm = ind.smooth(ind.wide(_clean()))
    c = ind.change(sm, 28)
    assert c["Up"].iloc[-1] == pytest.approx(100 * 0.002 * 28, rel=1e-6)
    assert c["Flat"].iloc[-1] == pytest.approx(0.0)


def test_pressure_median_and_diffusion():
    chg = pd.DataFrame({"a": [20.0, 1.0], "b": [15.0, np.nan], "c": [-12.0, -1.0], "d": [0.0, 0.0]},
                       index=pd.to_datetime(["2025-01-01", "2025-01-02"]))
    p = ind.pressure(chg)
    assert p.loc["2025-01-01", "median"] == pytest.approx(7.5)
    assert p.loc["2025-01-01", "diffusion"] == pytest.approx(100 * (2 / 4 - 1 / 4))
    assert p.loc["2025-01-02", "n"] == 3 and p.loc["2025-01-02", "diffusion"] == 0.0


def test_shocks_shape_and_clip():
    sm = ind.smooth(ind.wide(_clean()))
    sm.loc[sm.index[-3:], "Up"] *= 5                        # a big recent jump in 'Up'
    z = ind.shocks(sm, 26)
    assert z.shape == (3, 26) and z.max().max() <= 4 and z.loc["Up"].iloc[-1] == 4


def test_volatility_zero_for_constant_growth():
    v = ind.volatility(ind.wide(_clean()))
    assert v["Up"].iloc[-1] == pytest.approx(0.0, abs=1e-8)


def test_summary_one_row_per_active_variety():
    clean = _clean()
    w = ind.wide(clean)
    sm = ind.smooth(w)
    s = ind.summary(clean, sm, ind.change(sm, 28), ind.change(sm, 365), ind.volatility(w))
    assert set(s["variety"]) == {"Up", "Flat", "Down"}
    assert s.set_index("variety").loc["Up", "chg28"] == pytest.approx(5.6, rel=1e-3)


def test_shocks_leave_out_varieties_without_recent_data():
    clean = _clean()
    old = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=100), "variety": "Gone", "price": 5.0,
                        "category": "Fruits", "product": "Gone", "stale": False})
    sm = ind.smooth(ind.wide(pd.concat([clean, old])))
    assert "Gone" not in ind.shocks(sm, 26).index
