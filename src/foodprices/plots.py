from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def preview(pressure, shocks, path) -> Path:
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 8), gridspec_kw={"height_ratios": [1, 1.6]})
    recent = pressure[pressure.index >= pressure.index.max() - pd.Timedelta(days=3 * 365)]
    a1.plot(recent.index, recent["median"], c="#1f4e79", lw=1.4, label="Median 4-week change (%)")
    a1.axhline(0, c="grey", lw=0.8)
    b = a1.twinx()
    b.plot(recent.index, recent["diffusion"], c="#c55a11", lw=1, alpha=0.8, label="Diffusion (rising − falling, pp)")
    a1.set_title("Lima wholesale food price pressure (last 3 years)")
    a1.legend(loc="upper left", frameon=False, fontsize=8)
    b.legend(loc="upper right", frameon=False, fontsize=8)
    im = a2.imshow(shocks.to_numpy(dtype=float), aspect="auto", cmap="RdBu_r", vmin=-4, vmax=4)
    a2.set_yticks(range(len(shocks.index)), shocks.index, fontsize=6)
    step = max(1, len(shocks.columns) // 6)
    a2.set_xticks(range(0, len(shocks.columns), step),
                  [f"{d:%d %b %y}" for d in shocks.columns[::step]], fontsize=7)
    a2.set_title("Weekly price shocks (z-score vs own history), last 26 weeks")
    fig.colorbar(im, ax=a2, fraction=0.025)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path
