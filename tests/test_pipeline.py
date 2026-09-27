import pandas as pd
import pytest
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
    pipeline.stage_update(client=c, fetch_published=lambda: (None, None))
    prices, _ = panel.load(config.DATA_RAW)
    assert prices["date"].min() == pd.Timestamp("2025-01-01") and len(c.calls) == 2


def test_update_keeps_history(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    old = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-01"), "variety": "Ajo Morado", "price": 9.0})
    c = FakeClient()
    pipeline.stage_update(client=c, fetch_published=lambda: (old, None))
    prices, _ = panel.load(config.DATA_RAW)
    assert prices["date"].min() == pd.Timestamp("2024-01-01")
    assert prices.set_index("date").loc["2025-12-31", "price"] == 10.0     # re-downloaded window wins
    assert len(c.calls) == 1 and c.calls[0][0] == pd.Timestamp("2025-11-01")


def test_build_end_to_end(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    pipeline.stage_update(client=FakeClient(), fetch_published=lambda: (None, None))
    pipeline.stage_build()
    assert (config.SITE / "data" / "status.json").exists() and (config.FIGURES / "preview.png").exists()
    assert "data through 2025-12-31" in (tmp_path / "README.md").read_text(encoding="utf-8")


class NoTodayClient(FakeClient):
    """SISAP has not posted today's table yet: the day query is empty and the interval stops yesterday."""

    def interval(self, start, end, codes):
        return super().interval(start, min(end, pd.Timestamp("2025-12-30")), codes)

    def day(self, date, codes):
        return pd.DataFrame(columns=["product", "variety", "price"]) if date > pd.Timestamp("2025-12-30") \
            else super().day(date, codes)


def test_update_survives_missing_day_table(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    old = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-01"), "variety": "Ajo Morado", "price": 9.0})
    pipeline.stage_update(client=NoTodayClient(), fetch_published=lambda: (old, None))
    prices, cat = panel.load(config.DATA_RAW)
    assert prices["date"].max() == pd.Timestamp("2025-12-30") and "Ajo Morado" in set(cat["variety"])


def test_update_fails_loudly_when_download_is_empty(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    old = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-01"), "variety": "Ajo Morado", "price": 9.0})

    class EmptyClient(FakeClient):
        def interval(self, start, end, codes):
            return pd.DataFrame(columns=["date", "variety", "price"])

    with pytest.raises(RuntimeError, match="no prices"):
        pipeline.stage_update(client=EmptyClient(), fetch_published=lambda: (old, None))


def test_build_publishes_raw_panel_and_catalogue(tmp_path, monkeypatch):
    # the published files are what a fresh machine bootstraps from, so they must be the raw panel, not the clean one
    _setup(tmp_path, monkeypatch)
    pipeline.stage_update(client=FakeClient(), fetch_published=lambda: (None, None))
    raw, cat = panel.load(config.DATA_RAW)
    raw.loc[len(raw)] = [pd.Timestamp("2025-06-15"), "Glitchy", -1.0]      # removed by quality, kept in raw
    panel.save(raw, cat, config.DATA_RAW)
    pipeline.stage_build()
    pub, pub_cat = panel.load(config.SITE / "data")
    assert len(pub) == len(raw) and pub_cat.equals(cat)


def test_update_bootstraps_catalogue_from_published(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    old = pd.DataFrame({"date": pd.date_range("2024-01-01", "2025-12-01"), "variety": "Mango Edward", "price": 3.0})
    cat = pd.DataFrame({"variety": ["Mango Edward"], "product": ["Mango"], "code": ["0615"], "category": ["Fruits"]})
    pipeline.stage_update(client=FakeClient(), fetch_published=lambda: (old, cat))
    _, saved = panel.load(config.DATA_RAW)
    assert saved.set_index("variety").loc["Mango Edward", "category"] == "Fruits"


def test_daily_build_leaves_readme_and_preview_alone(tmp_path, monkeypatch):
    # the scheduled run publishes the site only; README and preview are refreshed by hand at release time
    _setup(tmp_path, monkeypatch)
    pipeline.stage_update(client=FakeClient(), fetch_published=lambda: (None, None))
    before = (tmp_path / "README.md").read_text(encoding="utf-8")
    pipeline.stage_build(release=False)
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == before
    assert not (config.FIGURES / "preview.png").exists() and (config.SITE / "data" / "status.json").exists()


def test_site_ships_preview_image_for_link_previews(tmp_path, monkeypatch):
    # index.html points og:image at preview.png, so every build (daily too) must publish it next to the page
    _setup(tmp_path, monkeypatch)
    pipeline.stage_update(client=FakeClient(), fetch_published=lambda: (None, None))
    pipeline.stage_build()
    pipeline.stage_build(release=False)
    assert (config.SITE / "preview.png").read_bytes() == (config.FIGURES / "preview.png").read_bytes()
    html = (config.SITE / "index.html").read_text(encoding="utf-8")
    assert 'property="og:image" content="https://rodgrandez.github.io/lima-food-prices-pipeline/preview.png"' in html
