#!/usr/bin/env python3
"""make_figures.py -- paper figures from the frozen table 06_results/tables/results_<v>.csv (never from raw data).

Usage:  python3 04_code/analysis/make_figures.py --version v01 [--lang en|id]
Output: 06_results/figures/fig{1..4}_*_<v>[_en].png (300 dpi) + .pdf
  --lang en (default here) -> English labels, files *_en ; --lang id -> Indonesian labels (report/lecture slides)
Colour = precision (W1A1 blue, W1A2 orange, W2A2 aqua); marker = folding method
(circle target_fps, square preset, triangle notebook), so identity does not rely on colour alone.
"""
import argparse, csv, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COL = {"W1A1": "#2a78d6", "W1A2": "#eb6834", "W2A2": "#1baf7a"}
# print-safe palette (JET requires figures readable in greyscale): distinct lightness dark / light / mid
COL_PRINT = {"W1A1": "#1f3f8f", "W1A2": "#f0a04b", "W2A2": "#1f8f6f"}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
# --- label language: en (paper, files *_en) | id (Indonesian; report and lecture slides) ---
LANG = "en"
EN = {'(berimpit)': '(same)', 'target_fps (FINN otomatis)': 'auto folding (target_fps)', 'preset large/small (berongga)': 'preset large/small', 'notebook, FIFO manual (berongga)': 'notebook (manual FIFO)', 'LUT (% dari 53.200)': 'LUT (% of 53,200)', 'BRAM (% dari 140 tile)': 'BRAM (% of 140 tiles)', 'DSP48 (dari 220)': 'DSP48 (of 220)', 'Throughput terukur (img/s, batch 1000)': 'Measured throughput (img/s, batch 1000)', 'Akurasi top-1 CIFAR-10 (%)': 'CIFAR-10 top-1 accuracy (%)', 'Latency terukur (ms, batch 1)': 'Measured latency (ms, batch 1)', 'Throughput estimasi FINN (img/s)': 'FINN-estimated throughput (img/s)', 'Throughput terukur di board (img/s)': 'Measured on-board throughput (img/s)'}
def tr(s):
    return EN.get(s, s) if LANG == "en" else s

def marker(m):
    return "o" if m.startswith("target_fps") else ("s" if m.startswith("preset") else "^")

plt.rcParams.update({"font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
                     "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "legend.frameon": False,
                     "font.family": "DejaVu Sans"})

def load(v):
    rows = list(csv.DictReader(open(f"{ROOT}/06_results/tables/results_{v}.csv")))
    for r in rows:
        for k in ["throughput_fps_bs1000", "latency_ms_bs1", "LUT_pct", "BRAM_pct", "top1_acc_pct", "DSP", "est_fps", "est_latency_ms"]:
            r[k] = float(r[k]) if r[k] not in ("", None) else None
    return rows

def scatter(ax, rows, x, y, label_ids=(), logx=True, logy=False):
    """target_fps = filled markers; preset/notebook = hollow and larger, drawn on top
    -> coincident points stay visible. Labels of nearby points are merged."""
    sweep = sorted([r for r in rows if r["precision"] == "W1A1" and r["folding_method"] == "target_fps"], key=lambda r: r[x])
    ax.plot([r[x] for r in sweep], [r[y] for r in sweep], color=COL["W1A1"], linewidth=1.2, alpha=0.5, zorder=2)
    for r in rows:
        if r["folding_method"].startswith("target_fps"):
            ax.scatter(r[x], r[y], s=38, marker="o", color=COL[r["precision"]], edgecolor="white", linewidth=1.0, zorder=3)
    for r in rows:
        if not r["folding_method"].startswith("target_fps"):
            ax.scatter(r[x], r[y], s=78, marker=marker(r["folding_method"]), facecolor="white",
                       edgecolor=COL[r["precision"]], linewidth=1.8, zorder=4)
    # merge labels of nearby points (positions in log/linear scale)
    import math
    def key(r):
        fx = math.log10(r[x]) if logx else r[x]; fy = math.log10(r[y]) if logy else r[y]
        return fx, fy
    lab = [r for r in rows if r["exp_id"] in label_ids]
    groups = []
    for r in lab:
        kx, ky = key(r)
        for g in groups:
            gx, gy = key(g[0])
            if abs(kx - gx) < 0.04 and abs(ky - gy) < (0.06 if logy else 0.02 * (ax.get_ylim()[1] - ax.get_ylim()[0] or 1)):
                g.append(r); break
        else:
            groups.append([r])
    for g in groups:
        txt = ", ".join(r["exp_id"].replace("EXP-", "E") for r in g)
        same = len(g) > 1 and all(abs(r[x] - g[0][x]) <= 0.01 * abs(g[0][x]) and abs(r[y] - g[0][y]) <= 0.01 * abs(g[0][y]) for r in g)
        if same:
            txt += " " + tr("(berimpit)")
        off = (7, -12) if len(g) > 1 else (7, 5)
        ax.annotate(txt, (g[0][x], g[0][y]), xytext=off, textcoords="offset points", fontsize=7.5, color=INK2, zorder=5)

def legend(fig):
    from matplotlib.lines import Line2D
    h = [Line2D([], [], marker="o", ls="", color=COL[p], label=p) for p in COL]
    h += [Line2D([], [], marker=m, ls="", color=INK2, markerfacecolor="white", label=l)
          for m, l in [("o", tr("target_fps (FINN otomatis)")), ("s", tr("preset large/small (berongga)")), ("^", tr("notebook, FIFO manual (berongga)"))]]
    narrow = fig.get_figwidth() < 6  # column-width paper figures: legend in two rows
    fig.legend(handles=h, loc="lower center", ncol=3 if narrow else 6, fontsize=6.5 if narrow else 7.5,
               bbox_to_anchor=(0.5, -0.02), columnspacing=1.0, handletextpad=0.3)

def save(fig, name, v):
    for ext in ("png", "pdf"):
        fig.savefig(f"{ROOT}/06_results/figures/{name}_{v}{'_en' if LANG == 'en' else ''}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

def main():
    global LANG
    ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True)
    ap.add_argument("--lang", choices=["id", "en"], default="en")
    a = ap.parse_args(); v = a.version; LANG = a.lang
    if LANG == "en":  # paper figures: greyscale-safe colours (Indonesian v01 figures keep the original palette)
        COL.update(COL_PRINT)
    rows = load(v)
    PAPER = LANG == "en"  # paper layout: Fig.1 page-wide (7 in), Fig.2-4 column-wide (3.4 in, JET column = 8 cm)
    if PAPER:
        plt.rcParams.update({"font.size": 8})
    SZ1, SZN, BOT = ((7.0, 2.9), (3.4, 3.1), 0.15) if PAPER else ((10, 3.3), None, None)
    if PAPER:  # shorter axis labels so they fit 8 cm columns / three panels
        EN.update({"Throughput terukur (img/s, batch 1000)": "Measured throughput (img/s)",
                   "Throughput terukur di board (img/s)": "Measured throughput (img/s)"})
    ids = ("EXP-001", "EXP-003", "EXP-004", "EXP-006", "EXP-012")
    if PAPER:  # EXP-001 is the only triangle; its label collided with others in Fig. 1
        ids = ("EXP-003", "EXP-004", "EXP-006", "EXP-012")
    # Fig 1: resource vs throughput (three panels, one axis each)
    fig, axs = plt.subplots(1, 3, figsize=SZ1)
    for ax, k, t, yl in zip(axs, ["LUT_pct", "BRAM_pct", "DSP"], [tr("LUT (% dari 53.200)"), tr("BRAM (% dari 140 tile)"), tr("DSP48 (dari 220)")], [(0, 100), (0, 100), (-35, 235) if PAPER else (-5, 230)]):
        ax.set_ylim(*yl)
        scatter(ax, rows, "throughput_fps_bs1000", k, ids)
        ax.set_xscale("log"); ax.set_xlabel(tr("Throughput terukur (img/s, batch 1000)")); ax.set_title(t, fontsize=9, color=INK, loc="left")
    legend(fig); fig.tight_layout(rect=(0, 0.09 if PAPER else 0.06, 1, 1)); save(fig, "fig1_resource_vs_throughput", v)
    # Fig 2: accuracy vs throughput
    fig, ax = plt.subplots(figsize=SZN or (5.2, 3.4))
    ax.set_ylim(83, 90)
    scatter(ax, rows, "throughput_fps_bs1000", "top1_acc_pct", ("EXP-003", "EXP-004", "EXP-012", "EXP-001", "EXP-005"))
    ax.set_xscale("log"); ax.set_xlabel(tr("Throughput terukur (img/s, batch 1000)")); ax.set_ylabel(tr("Akurasi top-1 CIFAR-10 (%)"))
    ax.set_ylim(83, 90); legend(fig); fig.tight_layout(rect=(0, BOT or 0.1, 1, 1)); save(fig, "fig2_accuracy_vs_throughput", v)
    # Fig 3: latency vs throughput (log-log) + 1/throughput line
    fig, ax = plt.subplots(figsize=SZN or (5.2, 3.4))
    scatter(ax, rows, "throughput_fps_bs1000", "latency_ms_bs1", ("EXP-006", "EXP-011", "EXP-012", "EXP-007", "EXP-001", "EXP-005"), logy=True)
    xs = [200, 4000]; ax.plot(xs, [1000 / x for x in xs], ls="--", color=INK2, linewidth=1, zorder=1)
    ax.text(260, 1000 / 260 * 0.62, "1/throughput", fontsize=7.5, color=INK2, rotation=-27)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel(tr("Throughput terukur (img/s, batch 1000)"))
    ax.set_ylabel(tr("Latency terukur (ms, batch 1)")); legend(fig); fig.tight_layout(rect=(0, BOT or 0.1, 1, 1)); save(fig, "fig3_latency_vs_throughput", v)
    # Fig 4: estimated vs measured
    fig, ax = plt.subplots(figsize=SZN or (4.2, 3.6))
    pts = [r for r in rows if r["est_fps"]]
    scatter(ax, pts, "est_fps", "throughput_fps_bs1000", ("EXP-003", "EXP-004", "EXP-005", "EXP-012", "EXP-007"), logy=True)
    ax.plot([200, 4000], [200, 4000], ls="--", color=INK2, linewidth=1, zorder=1)
    ax.text(230, 330, "y = x", fontsize=7.5, color=INK2)
    e1 = [r for r in rows if r["exp_id"] == "EXP-001"]
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlabel(tr("Throughput estimasi FINN (img/s)")); ax.set_ylabel(tr("Throughput terukur di board (img/s)"))
    legend(fig); fig.tight_layout(rect=(0, BOT or 0.12, 1, 1)); save(fig, "fig4_estimate_vs_measured", v)
    print("figures ->", f"{ROOT}/06_results/figures/")

if __name__ == "__main__":
    main()
