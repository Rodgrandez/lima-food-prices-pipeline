import pandas as pd
from test_panel import FakeClient

from foodprices import config, panel, pipeline


def _setup(tmp_path, monkeypatch):
    for name, value in {"DATA_RAW": tmp_path / "raw", "SITE": tmp_path / "site", "FIGURES": tmp_path / "fig",
                        "ROOT": tmp_path, "START": "2025-01-01"}.items():
        monkeypatch.setattr(config, name, value)
    monkeypatch.setattr(pipeline, "today", lambda: pd.Timestamp("2025-12-31"))
    (tmp_path / "README.md").write_text("<!-- STATUS:START -->\n<!-- STATUS:END -->\n", encoding="utf-8")


def test_update_falls_back_to_full_download(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    c = FakeClient()
    pipeline.stage_update(client=c, fetch_published=lambda: None)
    prices, _ = panel.load(config.DATA_RAW)
    assert prices["date"].min() == pd.Timestamp("2025-01-01") and len(c.calls) == 2


def test_update_keeps_history(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    old = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-01"), "variety": "Ajo Morado", "price": 9.0})
    c = FakeClient()
    pipeline.stage_update(client=c, fetch_published=lambda: old)
    prices, _ = panel.load(config.DATA_RAW)
    assert prices["date"].min() == pd.Timestamp("2024-01-01")
    assert prices.set_index("date").loc["2025-12-31", "price"] == 10.0     # re-downloaded window wins
    assert len(c.calls) == 1 and c.calls[0][0] == pd.Timestamp("2025-11-01")


def test_build_end_to_end(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    pipeline.stage_update(client=FakeClient(), fetch_published=lambda: None)
    pipeline.stage_build()
    assert (config.SITE / "data" / "status.json").exists() and (config.FIGURES / "preview.png").exists()
    assert "Data through 2025-12-31" in (tmp_path / "README.md").read_text(encoding="utf-8")
