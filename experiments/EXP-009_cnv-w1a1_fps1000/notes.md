# EXP-009 — CNV W1A1, target_fps 1000 (sweep)

- **Tujuan:** titik sweep folding otomatis FINN (SetFolding) untuk target 1000 img/s → kurva Pareto.
- **Perintah:** `build.py --exp EXP-009 --wbits 1 --abits 1 --target-fps 1000 --mode full` (clk 10 ns, FIFO otomatis, minimize skip XNOR).
- **Estimasi:** `experiments/EST-SWEEP_precheck/reports/EST-SWEEP_cnv_w1a1_est-fps1000/` (tanpa --ram-from).

## Hasil build (2026-11-21, sweep paralel)
- 63,1 menit | LUT 21.253 (39,95%), FF 27.513, BRAM 82,5 (58,93%), DSP 27, Slice 75,60% | WNS +0,363 | est FPS 1.017,3, est LUT 13.846, est BRAM18 121
- Catatan: jalur target_fps memakai `resType=auto` (bawaan FINN) → MAC non-XNOR boleh ke DSP48 (preset large/small memaksa `resType=lut`, DSP 0).

## Hasil board (2026-11-21 19:47–19:54 WIB, `measure_on_board.sh`, sudo tanpa password)
- Akurasi **84.19%** (bit-exact dengan EXP-001/005/006).
- Throughput bs1000 **1013.81 img/s** = 99.7% estimasi (1017.3); latency bs1 **4.171 ms**.

## Catatan / anomali
- 
