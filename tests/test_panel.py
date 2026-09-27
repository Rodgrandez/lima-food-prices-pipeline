import pandas as pd

from foodprices import panel


class FakeClient:
    def __init__(self):
        self.calls = []

    def products(self):
        return {"0204": "Ajo", "0202": "Aji fresco", "0628": "Piña"}

    def interval(self, start, end, codes):
        self.calls.append((start, end))
        days = pd.date_range(start, end)
        return pd.DataFrame({"date": days, "variety": "Ajo Morado", "price": 10.0})

    def day(self, date, codes):
        rows = [{"product": "Ajo", "variety": "Ajo Morado", "price": 10.0},
                {"product": "Aji Fresco", "variety": "Aji Escabeche", "price": 4.0},
                {"product": "Otros Raros", "variety": "Misterio", "price": 1.0}]
        if date >= pd.Timestamp("2025-06-01"):
            rows.append({"product": "Piña", "variety": "Piña Golden", "price": 3.0})
        return pd.DataFrame(rows)


def test_download_uses_six_month_chunks():
    c = FakeClient()
    df = panel.download(c, pd.Timestamp("2024-01-01"), pd.Timestamp("2025-03-31"))
    assert len(c.calls) == 3 and df["date"].min() == pd.Timestamp("2024-01-01")
    assert df["date"].max() == pd.Timestamp("2025-03-31")


def test_merge_new_wins_and_keeps_history():
    old = pd.DataFrame({"date": pd.to_datetime(["2025-01-01", "2025-01-02"]), "variety": "A", "price": [1.0, 2.0]})
    new = pd.DataFrame({"date": pd.to_datetime(["2025-01-02", "2025-01-03"]), "variety": "A", "price": [2.5, 3.0]})
    m = panel.merge(old, new).set_index("date")["price"]
    assert m.to_dict() == {pd.Timestamp("2025-01-01"): 1.0, pd.Timestamp("2025-01-02"): 2.5,
                           pd.Timestamp("2025-01-03"): 3.0}


def test_catalogue_dates_quarterly_plus_end():
    d = panel.catalogue_dates(pd.Timestamp("2024-01-01"), pd.Timestamp("2024-12-20"))
    assert d == [pd.Timestamp(x) for x in ["2024-01-15", "2024-04-15", "2024-07-15", "2024-10-15", "2024-12-20"]]


def test_catalogue_unknown_product_is_other():
    cat = panel.build_catalogue(FakeClient(), [pd.Timestamp("2025-01-15"), pd.Timestamp("2025-07-15")])
    c = cat.set_index("variety")
    assert c.loc["Ajo Morado", "code"] == "0204" and c.loc["Ajo Morado", "category"] == "Vegetables"
    assert c.loc["Aji Escabeche", "code"] == "0202"                # case-insensitive product match
    assert c.loc["Piña Golden", "category"] == "Fruits"
    assert c.loc["Misterio", "category"] == "Other" and pd.isna(c.loc["Misterio", "code"])


def test_save_load_roundtrip(tmp_path):
    prices = pd.DataFrame({"date": pd.to_datetime(["2025-01-01"]), "variety": ["Aji Montaña"], "price": [3.1]})
    cat = pd.DataFrame({"variety": ["Aji Montaña"], "product": ["Aji Fresco"], "code": ["0202"],
                        "category": ["Vegetables"]})
    panel.save(prices, cat, tmp_path)
    p, c = panel.load(tmp_path)
    assert p.equals(prices) and c.equals(cat)
