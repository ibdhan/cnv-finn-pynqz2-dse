# EXP-007 — CNV W1A1, target_fps 250 (sweep)

- **Tujuan:** titik sweep folding otomatis FINN (SetFolding) untuk target 250 img/s → kurva Pareto.
- **Perintah:** `build.py --exp EXP-007 --wbits 1 --abits 1 --target-fps 250 --mode full` (clk 10 ns, FIFO otomatis, minimize skip XNOR).
- **Estimasi:** `05_experiments/EST-SWEEP_precheck/reports/EST-SWEEP_cnv_w1a1_est-fps250/` (tanpa --ram-from).

## Hasil build (2026-11-21, sweep paralel)
- 58,5 menit | LUT 21.136 (39,73%), FF 23.417, BRAM 93 tile (66,43%), DSP 10, Slice 71,04% | WNS +0,381 | est FPS 301,4, est LUT 7.222, est BRAM18 111 | SIMD MVAU_hls_5 2→3
- Catatan: jalur target_fps memakai `resType=auto` (bawaan FINN) → MAC non-XNOR boleh ke DSP48 (preset large/small memaksa `resType=lut`, DSP 0).

## Hasil board (2026-11-21 19:47–19:54 WIB, `measure_on_board.sh`, sudo tanpa password)
- Akurasi **84.19%** (bit-exact dengan EXP-001/005/006).
- Throughput bs1000 **300.55 img/s** = 99.7% estimasi (301.4); latency bs1 **12.638 ms**.

## Catatan / anomali
- 
