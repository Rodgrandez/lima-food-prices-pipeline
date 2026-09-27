# src/foodprices/sisap.py
"""Client and parsers for the MIDAGRI-SISAP wholesale market portal (public, HTML responses in ISO-8859-1)."""
import html
import re
import time
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd

from foodprices import config

MISSING = {"", "...", "-"}
DATE_RE = re.compile(r"\d{2}/\d{2}/\d{4}")


def _text(cell: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", cell)).strip()


def _rows(page: str) -> list[list[str]]:
    return [[_text(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.DOTALL)]
            for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.DOTALL)]


def _number(value: str) -> float:
    return np.nan if value in MISSING else float(value)


def parse_products(page: str) -> dict[str, str]:
    pairs = re.findall(r'value=["\']?(\d{4})["\']?[^>]*>\s*(?:<[^>]*>\s*)*([^<]+)', page)
    return {code: html.unescape(name).strip() for code, name in pairs}


def parse_interval(page: str) -> pd.DataFrame:
    if "Demasiados criterios" in page:
        raise ValueError("SISAP rejected the query: too many criteria (shorten the date range)")
    rows = _rows(page)
    if not rows:
        return pd.DataFrame({"date": pd.Series(dtype="datetime64[ns]"), "variety": pd.Series(dtype=str),
                             "price": pd.Series(dtype=float)})
    header = rows[0][1:]
    records = []
    for row in rows[1:]:
        if not row or not DATE_RE.fullmatch(row[0]):
            continue
        date = pd.to_datetime(row[0], format="%d/%m/%Y")
        records += [(date, name, _number(value)) for name, value in zip(header, row[1:])]
    df = pd.DataFrame(records, columns=["date", "variety", "price"])
    # a variety name repeated in the header: keep its first published column (even when that cell is empty)
    df = df.drop_duplicates(["date", "variety"], keep="first").dropna(subset=["price"])
    return df.sort_values(["date", "variety"]).reset_index(drop=True)


def parse_day(page: str) -> pd.DataFrame:
    out, product = [], None
    for row in _rows(page)[1:]:
        if len(row) == 3:
            product, variety, value = row
        elif len(row) == 2 and product is not None:
            variety, value = row
        else:
            continue
        out.append({"product": product, "variety": variety, "price": _number(value)})
    return pd.DataFrame(out, columns=["product", "variety", "price"])


def chunks(start: pd.Timestamp, end: pd.Timestamp, months: int) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    out, a = [], start
    while a <= end:
        b = min(a + pd.DateOffset(months=months) - pd.Timedelta(days=1), end)
        out.append((a, b))
        a = b + pd.Timedelta(days=1)
    return out


class Client:
    def __init__(self, base: str = config.BASE, market: str = config.MARKET, sleep: float = config.SLEEP):
        self.base, self.market, self.sleep = base, market, sleep

    def _post(self, path: str, fields: dict) -> str:
        data = urllib.parse.urlencode(fields, doseq=True).encode()
        request = urllib.request.Request(self.base + path, data=data, headers={
            "User-Agent": "lima-food-prices-pipeline (github.com/Rodgrandez)", "X-Requested-With": "XMLHttpRequest"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(request, timeout=300) as response:
                    page = response.read().decode("iso-8859-1")
                time.sleep(self.sleep)
                return page
            except OSError:
                if attempt == 2:
                    raise
                time.sleep(10 * (attempt + 1))
        raise RuntimeError("unreachable")

    def products(self) -> dict[str, str]:
        return parse_products(self._post("generos/filtrarPorMercado", {"mercado": self.market}))

    def _query(self, codes: list[str], **fields) -> str:
        return self._post("resumenes/filtrar", {"__ajax_carga_final": "consulta", "mercado": self.market,
                                                "productos[]": codes, "variables[]": ["precio_prom"], **fields})

    def interval(self, start, end, codes: list[str]) -> pd.DataFrame:
        return parse_interval(self._query(codes, periodicidad="intervalo", desde=f"{start:%d/%m/%Y}",
                                          hasta=f"{end:%d/%m/%Y}"))

    def day(self, date, codes: list[str]) -> pd.DataFrame:
        return parse_day(self._query(codes, periodicidad="dia", fecha=f"{date:%d/%m/%Y}"))
