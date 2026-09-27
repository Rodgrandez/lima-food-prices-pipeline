# Lima wholesale food prices: daily pipeline, quality checks and dashboard

[![CI](https://github.com/Rodgrandez/lima-food-prices-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/Rodgrandez/lima-food-prices-pipeline/actions/workflows/ci.yml)
[![Data through](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Frodgrandez.github.io%2Flima-food-prices-pipeline%2Fdata%2Fstatus.json&query=%24.last_date&label=data%20through)](https://rodgrandez.github.io/lima-food-prices-pipeline/)

**Live dashboard: https://rodgrandez.github.io/lima-food-prices-pipeline/**

A daily, automated pipeline for wholesale food prices at Lima's main wholesale market (Gran Mercado Mayorista de
Lima), published by MIDAGRI-SISAP. It downloads and normalises the data, runs explicit data-quality checks, computes
price-change, volatility and price-pressure indicators, and republishes a static Plotly.js dashboard every day.

![Dashboard preview](reports/figures/preview.png)

<!-- STATUS:START -->
<!-- STATUS:END -->

## Pipeline
1. **Download**: the SISAP portal is queried in six-month chunks (it rejects longer ranges); daily updates
   re-download the last 60 days to capture revisions and merge them into the existing panel.
2. **Normalise**: one row per date and variety; each variety is mapped to its product and category using the
   portal's daily tables.
3. **Quality checks**: duplicates, non-positive prices, isolated glitches (more than 0.7 log points from the median
   of the previous 15 observations, so only past data are used), stale prices (unchanged for 30+ observations,
   flagged but kept), discontinued and uncategorised varieties. The report is rebuilt from the full raw history
   and published with every update.
4. **Indicators**: 7-day average price; 4-week and 12-month log changes; 28-day volatility of daily log changes;
   weekly shocks as z-scores against each variety's own history; and a price-pressure indicator (median 4-week
   change across varieties and a diffusion index: share rising more than 10% minus share falling more than 10%).
   Units differ across varieties (kg, litre or unit) and the source does not say which, so all indicators use
   changes, never levels across varieties.
5. **Publish**: the static site (HTML, JS and JSON) is pushed to the `gh-pages` branch and served by GitHub Pages.

## Automation
The SISAP portal does not answer requests from outside Peru: a GitHub-hosted runner times out. The daily update
therefore runs on a machine in Lima (Windows Task Scheduler, `scripts/update.ps1`), which rebuilds the site and
pushes it to `gh-pages`. The "data through" badge always shows the date of the latest data actually published.
CI (lint and tests) runs on GitHub Actions and needs no network access.

## Reproduce
```bash
conda env create -f environment.yml && conda activate food-prices
make all      # full download since 2010 and build of site/
```

Data: MIDAGRI – SISAP (public). License: MIT.
