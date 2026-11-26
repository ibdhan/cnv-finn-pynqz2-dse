#!/usr/bin/env python3
"""make_figures_v07.py — figures of the paper (Figs. 2 and 3), built from the frozen table results/tables/results_<v>.csv.

Usage: python3 code/analysis/make_figures_v07.py --version v01
Outputs (results/figures/, png 300 dpi + pdf, English labels, print-safe palette):
  fig_resource_floor_en      = Fig. 1 of make_figures.py (LUT, BRAM, DSP vs throughput) + two dashed lines in the
                               BRAM panel: storage that all weights need at 1 and 2 bits.
  fig_estimate_latency_en    = two panels side by side: (a) measured vs FINN-estimated throughput (old fig4),
                               (b) single-image latency vs measured throughput (old fig3).
Reuses scatter()/legend() of make_figures.py so markers and colours stay identical. Only writes the two files above.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_figures as mf
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

ROOT = mf.ROOT
OUT = os.path.join(ROOT, "results", "figures")
N_WEIGHTS = 1_542_848          # CNV weights (all nine MVAUs)
TILE_BITS = 36 * 1024          # one BRAM36 tile
CAP_TILES = 140                # xc7z020


def plain_log(axis, ticks):
    """log axis with plain tick labels (300, 1,000, ...) and no minor labels -> no overlapping 3x10^2 labels"""
    axis.set_major_locator(FixedLocator(ticks))
    axis.set_major_formatter(FixedFormatter([(f"{t // 1000}k" if t >= 1000 else f"{t:g}") for t in ticks]))
    axis.set_minor_locator(NullLocator())


TX = [300, 500, 1000, 2000, 3000]


def save(fig, name):
    os.makedirs(OUT, exist_ok=True)
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=300, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True)
    v = ap.parse_args().version
    mf.LANG = "en"; mf.COL.update(mf.COL_PRINT)
    plt.rcParams.update({"font.size": 8})
    mf.EN.update({"Throughput terukur (img/s, batch 1000)": "Measured throughput (img/s)",
                  "Throughput terukur di board (img/s)": "Measured throughput (img/s)"})
    tr = mf.tr
    rows = mf.load(v)

    # --- resource vs throughput, with weight-storage floors in the BRAM panel
    ids = ("EXP-003", "EXP-004", "EXP-006", "EXP-012")
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.9))
    for ax, k, t, yl in zip(axs, ["LUT_pct", "BRAM_pct", "DSP"],
                            [tr("LUT (% dari 53.200)"), tr("BRAM (% dari 140 tile)"), tr("DSP48 (dari 220)")],
                            [(0, 100), (0, 100), (-35, 235)]):
        ax.set_ylim(*yl)
        if k == "BRAM_pct":
            for bits in (1, 2):
                tiles = N_WEIGHTS * bits / TILE_BITS
                pct = 100 * tiles / CAP_TILES
                ax.axhline(pct, ls="--", color=mf.INK2, linewidth=0.9, zorder=1)
                ax.text(0.98, pct - 3.0, f"{bits}-bit weights: {tiles:.0f} tiles", transform=ax.get_yaxis_transform(),
                        fontsize=6.5, color=mf.INK2, va="top", ha="right")
        mf.scatter(ax, rows, "throughput_fps_bs1000", k, ("EXP-012",) if k == "BRAM_pct" else ids)
        ax.set_xscale("log"); plain_log(ax.xaxis, TX); ax.set_xlabel(tr("Throughput terukur (img/s, batch 1000)"))
        ax.set_title(t, fontsize=9, color=mf.INK, loc="left")
    mf.legend(fig); fig.tight_layout(rect=(0, 0.09, 1, 1)); save(fig, "fig_resource_floor_en")

    # --- (a) estimate vs measured throughput, (b) latency vs throughput
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.0, 2.6))
    pts = [r for r in rows if r["est_fps"]]
    mf.scatter(a, pts, "est_fps", "throughput_fps_bs1000", ("EXP-003", "EXP-004", "EXP-005", "EXP-012", "EXP-007"), logy=True)
    a.plot([200, 4000], [200, 4000], ls="--", color=mf.INK2, linewidth=1, zorder=1)
    a.text(230, 330, "y = x", fontsize=7.5, color=mf.INK2)
    a.set_xscale("log"); a.set_yscale("log"); plain_log(a.xaxis, TX); plain_log(a.yaxis, TX)
    a.set_xlabel(tr("Throughput estimasi FINN (img/s)")); a.set_ylabel(tr("Throughput terukur di board (img/s)"))
    a.set_title("(a) Throughput: measured vs estimated", fontsize=9, color=mf.INK, loc="left")
    mf.scatter(b, rows, "throughput_fps_bs1000", "latency_ms_bs1", ("EXP-006", "EXP-011", "EXP-012", "EXP-007", "EXP-005"), logy=True)
    xs = [200, 4000]; b.plot(xs, [1000 / x for x in xs], ls="--", color=mf.INK2, linewidth=1, zorder=1)
    b.text(260, 1000 / 260 * 0.62, "1/throughput", fontsize=7.5, color=mf.INK2, rotation=-27)
    b.set_xscale("log"); b.set_yscale("log"); plain_log(b.xaxis, TX); plain_log(b.yaxis, [0.5, 1, 2, 5, 10])
    b.set_xlabel(tr("Throughput terukur (img/s, batch 1000)")); b.set_ylabel(tr("Latency terukur (ms, batch 1)"))
    b.set_title("(b) Single-image latency", fontsize=9, color=mf.INK, loc="left")
    mf.legend(fig); fig.tight_layout(rect=(0, 0.09, 1, 1)); save(fig, "fig_estimate_latency_en")
    print("figures ->", OUT)


if __name__ == "__main__":
    main()
