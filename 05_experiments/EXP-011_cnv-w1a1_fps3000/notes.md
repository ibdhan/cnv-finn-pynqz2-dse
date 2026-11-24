# EXP-011 — CNV W1A1, target_fps 3000 (sweep)

- **Tujuan:** titik sweep folding otomatis FINN (SetFolding) untuk target 3000 img/s → kurva Pareto.
- **Perintah:** `build.py --exp EXP-011 --wbits 1 --abits 1 --target-fps 3000 --mode full` (clk 10 ns, FIFO otomatis, minimize skip XNOR).
- **Estimasi:** `05_experiments/EST-SWEEP_precheck/reports/EST-SWEEP_cnv_w1a1_est-fps3000/` (tanpa --ram-from).

## Hasil build (2026-11-21, sweep paralel)
- 65,9 menit | LUT 25.720 (48,35%), FF 33.792, BRAM 87,5 (62,50%), DSP 54, Slice 89,24% | WNS +0,378 | est FPS 3.051,8, est LUT 25.190, est BRAM18 140
- Catatan: jalur target_fps memakai `resType=auto` (bawaan FINN) → MAC non-XNOR boleh ke DSP48 (preset large/small memaksa `resType=lut`, DSP 0).

## Hasil board (2026-11-21 19:47–19:54 WIB, `measure_on_board.sh`, sudo tanpa password)
- Akurasi **84.19%** (bit-exact dengan EXP-001/005/006).
- Throughput bs1000 **3037.33 img/s** = 99.5% estimasi (3051.8); latency bs1 **1.836 ms**.

## Catatan / anomali
- 
