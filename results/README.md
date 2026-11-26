# results -- frozen data

Tables and figures here are generated only from the raw files in `experiments/` and are never edited by hand.
A frozen version is never overwritten; additional data goes into a new version (`v02`, ...).

## v01 (2026-11-21)
- Tables: `tables/results_v01.csv` (complete), `tables/results_v01.md` (short). 11 experiments: EXP-001, 003–012.
  EXP-002 is excluded (superseded, XNOR accumulator issue; see `docs/findings.md`).
- Figures (`figures/*_v01.png` 300 dpi + `.pdf`; `*_v01_en.*` = English labels):
  - `fig1_resource_vs_throughput` — LUT %, BRAM %, DSP vs measured throughput (three panels)
  - `fig2_accuracy_vs_throughput` — top-1 accuracy vs throughput
  - `fig3_latency_vs_throughput` — batch-1 latency vs throughput (log-log) with a 1/throughput line
  - `fig4_estimate_vs_measured` — FINN-estimated vs measured throughput (y = x line)
- Colour = precision (W1A1 blue, W1A2 orange, W2A2 aqua); marker = folding method (filled circle = target_fps,
  hollow square = preset large/small, hollow triangle = notebook with manual FIFOs).
- Provenance: `FREEZE_v01.md` (commit of the private lab repository and sha256 of every source file).
- Regenerate: `python3 code/analysis/freeze_results.py --version vNN` then `python3 code/analysis/make_figures.py --version vNN [--lang id]`.

## Notes for interpretation
- Column `resType`: presets force `lut` (0 DSP); `target_fps` keeps FINN's default `auto`, so non-XNOR MACs may map to
  DSP48 slices. Compare LUT between the two groups with care.
- `fps_vs_est_pct` is 99.5–99.7 % for every design with automatic FIFO sizing; EXP-001 (manual FIFOs) has no build.py
  estimate (≈65 % of the corresponding FINN estimate).
- `latency_ms_bs1` includes DMA/driver overhead (`throughput_test` with batch 1).
- Some labels are in Indonesian to keep the frozen files byte-identical: `auto_fifo` "ya"/"tidak" = yes/no.
