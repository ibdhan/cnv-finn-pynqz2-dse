# EXP-010 — CNV W1A1, target_fps 2000 (sweep)

- **Tujuan:** titik sweep folding otomatis FINN (SetFolding) untuk target 2000 img/s → kurva Pareto.
- **Perintah:** `build.py --exp EXP-010 --wbits 1 --abits 1 --target-fps 2000 --mode full` (clk 10 ns, FIFO otomatis, minimize skip XNOR).
- **Estimasi:** `experiments/EST-SWEEP_precheck/reports/EST-SWEEP_cnv_w1a1_est-fps2000/` (tanpa --ram-from).

## Hasil build (2026-11-21, sweep paralel)
- 66,1 menit | LUT 24.786 (46,59%), FF 32.309, BRAM 91 (65,00%), DSP 54, Slice 84,62% | WNS +0,266 | est FPS 2.034,5, est LUT 22.660, est BRAM18 148
- Catatan: jalur target_fps memakai `resType=auto` (bawaan FINN) → MAC non-XNOR boleh ke DSP48 (preset large/small memaksa `resType=lut`, DSP 0).

## Hasil board (2026-11-21 19:47–19:54 WIB, `measure_on_board.sh`, sudo tanpa password)
- Akurasi **84.19%** (bit-exact dengan EXP-001/005/006).
- Throughput bs1000 **2026.89 img/s** = 99.6% estimasi (2034.5); latency bs1 **2.223 ms**.

## Catatan / anomali
- 
