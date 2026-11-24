# EXP-008 — CNV W1A1, target_fps 500 (sweep)

- **Tujuan:** titik sweep folding otomatis FINN (SetFolding) untuk target 500 img/s → kurva Pareto.
- **Perintah:** `build.py --exp EXP-008 --wbits 1 --abits 1 --target-fps 500 --mode full` (clk 10 ns, FIFO otomatis, minimize skip XNOR).
- **Estimasi:** `05_experiments/EST-SWEEP_precheck/reports/EST-SWEEP_cnv_w1a1_est-fps500/` (tanpa --ram-from).

## Hasil build (2026-11-21, sweep paralel)
- 60,9 menit | LUT 22.097 (41,54%), FF 24.522, BRAM 86,5 (61,79%), DSP 10, Slice 72,05% | WNS +0,597 | est FPS 508,6, est LUT 9.221, est BRAM18 112
- Catatan: jalur target_fps memakai `resType=auto` (bawaan FINN) → MAC non-XNOR boleh ke DSP48 (preset large/small memaksa `resType=lut`, DSP 0).

## Hasil board (2026-11-21 19:47–19:54 WIB, `measure_on_board.sh`, sudo tanpa password)
- Akurasi **84.19%** (bit-exact dengan EXP-001/005/006).
- Throughput bs1000 **507.04 img/s** = 99.7% estimasi (508.6); latency bs1 **8.07 ms**.

## Catatan / anomali
- 
