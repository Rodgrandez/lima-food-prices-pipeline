import numpy as np
import pandas as pd

from foodprices import quality


def _prices():
    days = pd.date_range("2025-01-01", periods=120)
    a = pd.DataFrame({"date": days, "variety": "A", "price": 10 + np.sin(np.arange(120) / 5)})
    a.loc[60, "price"] = 0.46                               # isolated glitch
    b = pd.DataFrame({"date": days[:50], "variety": "B", "price": 5.0})    # stops early: discontinued
    c = pd.DataFrame({"date": days, "variety": "C", "price": np.r_[np.linspace(3, 4, 80), np.full(40, 4.0)]})
    d = pd.DataFrame({"date": days[:3], "variety": "D", "price": [-1.0, 2.0, 2.0]})
    dup = a.iloc[[5]]                                       # overlapping chunk boundary
    return pd.concat([a, b, c, d, dup], ignore_index=True)


CAT = pd.DataFrame({"variety": ["A", "B", "C"], "product": ["P", "P", "Q"], "code": ["0204", "0204", "0628"],
                    "category": ["Vegetables", "Vegetables", "Fruits"]})


def test_counts_duplicates_and_non_positive():
    clean, rep = quality.check(_prices(), CAT)
    assert rep["duplicates"] == 1 and rep["non_positive"] == 1
    assert not clean.duplicated(["date", "variety"]).any() and (clean["price"] > 0).all()


def test_outlier_rule_is_past_only():
    clean, rep = quality.check(_prices(), CAT)
    assert rep["outliers"] == 1 and rep["outliers_by_variety"] == [["A", 1]]
    assert pd.Timestamp("2025-03-02") not in set(clean.loc[clean.variety == "A", "date"])
    # past-only: the value right after the glitch is kept (its trailing median ignores the glitch's future)
    assert pd.Timestamp("2025-03-03") in set(clean.loc[clean.variety == "A", "date"])


def test_stale_run_flagged_not_dropped():
    clean, rep = quality.check(_prices(), CAT)
    c = clean[clean.variety == "C"]
    assert len(c) == 120 and c["stale"].iloc[-1] and not c["stale"].iloc[0]
    assert rep["stale_now"] == ["C"]


def test_quality_lists_uncategorised_and_discontinued():
    clean, rep = quality.check(_prices(), CAT)
    assert rep["discontinued"] == ["B", "D"]
    assert rep["uncategorised"] == ["D"]
    assert clean.loc[clean.variety == "D", "category"].eq("Other").all()
    assert 0 < rep["coverage_median"] <= 1 and rep["end"] == "2025-04-30"
