import json

import pandas as pd
from test_indicators import _clean

from foodprices import plots, quality, report, site


def _report():
    return {"rows_raw": 10, "rows_clean": 9, "varieties": 3, "start": "2024-01-01", "end": "2025-05-14",
            "duplicates": 1, "non_positive": 0, "outliers": 2, "outliers_by_variety": [["Up", 2]],
            "stale_now": [], "discontinued": ["Old"], "uncategorised": [], "coverage_median": 0.97}


def test_site_build_writes_all_files(tmp_path):
    status = site.build(_clean(), _report(), tmp_path)
    for f in ["series", "pressure", "shocks", "summary", "quality", "status"]:
        assert (tmp_path / "data" / f"{f}.json").stat().st_size > 0
    assert (tmp_path / "data" / "prices.csv.gz").exists() and (tmp_path / "index.html").exists()
    s = json.loads((tmp_path / "data" / "status.json").read_text(encoding="utf-8"))
    assert s == status and s["last_date"] == "2025-05-14" and s["varieties"] == 3


def test_site_json_keeps_accents(tmp_path):
    clean = _clean().replace({"variety": {"Up": "Aji Montaña"}})
    site.build(clean, _report(), tmp_path)
    assert "Aji Montaña" in (tmp_path / "data" / "series.json").read_text(encoding="utf-8")


def test_prices_csv_roundtrips_into_quality(tmp_path):
    site.build(_clean(), _report(), tmp_path)
    p = pd.read_csv(tmp_path / "data" / "prices.csv.gz", parse_dates=["date"])
    assert list(p.columns) == ["date", "variety", "price"] and len(p) == len(_clean())
    quality.check(p, pd.DataFrame(columns=["variety", "product", "code", "category"]))


def test_update_readme_from_status(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("# T\n<!-- STATUS:START -->\nold\n<!-- STATUS:END -->\nend\n", encoding="utf-8")
    status = {"last_date": "2025-05-14", "updated_utc": "2025-05-15T14:30Z", "varieties": 3,
              "median_chg28": 1.234, "diffusion": -12.5}
    summ = pd.DataFrame({"variety": ["A", "B", "C"], "category": "V", "last_date": "2025-05-14",
                         "price": [1.0, 2.0, 3.0], "chg28": [30.0, -20.0, 1.0], "yoy": 0.0, "vol": 1.0})
    report.update_readme(readme, status, _report(), summ)
    t = readme.read_text(encoding="utf-8")
    assert "old" not in t and "2025-05-14" in t and "+1.2%" in t and "-12.5" in t
    assert "A (+30.0%)" in t and "B (-20.0%)" in t and "2 outliers" in t and t.endswith("end\n")


def test_preview_png(tmp_path):
    p = pd.DataFrame({"median": [1.0, 2.0], "diffusion": [5.0, -5.0], "n": 3},
                     index=pd.to_datetime(["2025-01-01", "2025-01-02"]))
    z = pd.DataFrame([[0.5, -1.0], [2.0, 4.0]], index=["A", "B"], columns=pd.to_datetime(["2025-01-05", "2025-01-12"]))
    assert plots.preview(p, z, tmp_path / "p.png").stat().st_size > 0
