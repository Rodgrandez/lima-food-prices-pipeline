import itertools

import pandas as pd
import pytest
from conftest import DAY_HTML, INTERVAL_HTML, PRODUCTS_HTML

from foodprices import sisap


def test_parse_products():
    assert sisap.parse_products(PRODUCTS_HTML) == {"0204": "Ajo", "0202": "Aji fresco"}


def test_parse_interval_missing_and_accents():
    df = sisap.parse_interval(INTERVAL_HTML)
    assert list(df.columns) == ["date", "variety", "price"]
    assert set(df["variety"]) == {"Aji Montaña", "Ajo Morado"}
    assert len(df) == 3                                 # the '...' cell is dropped
    assert df["date"].is_monotonic_increasing


def test_parse_interval_duplicate_variety_keeps_first():
    df = sisap.parse_interval(INTERVAL_HTML).set_index(["date", "variety"])["price"]
    assert df.loc[(pd.Timestamp("2025-01-01"), "Ajo Morado")] == 10.50
    assert (pd.Timestamp("2025-01-02"), "Ajo Morado") not in df.index   # first column was '...'


def test_parse_interval_too_many_criteria_raises():
    with pytest.raises(ValueError, match="too many"):
        sisap.parse_interval("<p>Demasiados criterios para realizar la consulta.</p>")


def test_parse_day_carries_rowspan_product():
    df = sisap.parse_day(DAY_HTML)
    assert df.to_dict("records") == [
        {"product": "Aji Fresco", "variety": "Aji Escabeche", "price": 4.78},
        {"product": "Aji Fresco", "variety": "Aji Montaña", "price": 3.10},
        {"product": "Ajo", "variety": "Ajo Morado", "price": 6.33}]


def test_chunks_cover_range_without_overlap():
    c = sisap.chunks(pd.Timestamp("2025-01-15"), pd.Timestamp("2026-02-10"), 6)
    assert c[0][0] == pd.Timestamp("2025-01-15") and c[-1][1] == pd.Timestamp("2026-02-10")
    for (a, b), (a2, _) in itertools.pairwise(c):
        assert a <= b and a2 == b + pd.Timedelta(days=1)
    assert all((b - a).days < 184 for a, b in c)


def test_client_posts_expected_fields():
    sent = []

    class FakeClient(sisap.Client):
        def _post(self, path, fields):
            sent.append((path, fields))
            return INTERVAL_HTML

    df = FakeClient(sleep=0).interval(pd.Timestamp("2025-01-01"), pd.Timestamp("2025-01-02"), ["0204"])
    path, fields = sent[0]
    assert path == "resumenes/filtrar" and fields["periodicidad"] == "intervalo"
    assert fields["desde"] == "01/01/2025" and fields["hasta"] == "02/01/2025" and fields["productos[]"] == ["0204"]
    assert len(df) == 3


def test_decode_prefers_utf8_and_falls_back_to_latin1():
    # the price tables are UTF-8 although the server declares ISO-8859-1; the product list really is Latin-1
    assert sisap.decode("Aji Montaña".encode()) == "Aji Montaña"
    assert sisap.decode("Piña".encode("iso-8859-1")) == "Piña"
