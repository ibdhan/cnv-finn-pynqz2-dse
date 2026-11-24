# EXP-012 — CNV W2A2, target_fps 250 (sweep)

- **Tujuan:** titik sweep folding otomatis FINN (SetFolding) untuk target 250 img/s → kurva Pareto.
- **Perintah:** `build.py --exp EXP-012 --wbits 2 --abits 2 --target-fps 250 --ram-from small --mode full` (clk 10 ns, FIFO otomatis, minimize skip XNOR).
- **Estimasi:** `05_experiments/EST-SWEEP_precheck/reports/EST-SWEEP_cnv_w2a2_est-fps250/` (tanpa --ram-from).

## Hasil build (2026-11-21, sweep paralel)
- 66,7 menit | LUT 32.505 (61,10%), FF 36.323, BRAM 127 tile (90,71%), **DSP 220 (100%)**, Slice 94,74% | WNS **+0,047** (sangat tipis) | est FPS 301,4, est LUT 15.521, est BRAM18 188 | SIMD MVAU_hls_5 2→3
- Catatan: jalur target_fps memakai `resType=auto` (bawaan FINN) → MAC non-XNOR boleh ke DSP48 (preset large/small memaksa `resType=lut`, DSP 0).

## Hasil board (2026-11-21 19:47–19:54 WIB, `measure_on_board.sh`, sudo tanpa password)
- Akurasi **88.63%** (bit-exact dengan EXP-004).
- Throughput bs1000 **300.6 img/s** = 99.7% estimasi (301.4); latency bs1 **12.153 ms**.

## Catatan / anomali
- Gerbang estimasi otomatis: LEWATI (BRAM18 188 → terkoreksi 134 tile = 96% > 95%). **Keputusan Bos 2026-11-21 16:07:** tetap di-build manual setelah aliran B — titik W2A2 kedua (pembanding EXP-004) untuk menguji "BRAM 2-bit tidak turun walau throughput turun"; gagal placement pun dapat diterima.
- 
