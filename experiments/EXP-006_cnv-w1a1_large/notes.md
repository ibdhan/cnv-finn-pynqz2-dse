# EXP-006 — CNV W1A1, folding large (build.py, minimize skip XNOR)

- **Tujuan:** W1A1 large via build.py: bandingkan langsung dgn EXP-001 (notebook, FIFO manual).
- **Perintah:** `build.py --exp EXP-006 --wbits 1 --abits 1 --folding large --mode full` (clk 10 ns, FIFO otomatis, `step_minimize_bit_width_skip_xnor`).
- **Latar:** EXP-002 turun 1,60 pp karena MinimizeAccumulatorWidth FINN v0.10.1 salah rentang untuk layer XNOR (38 threshold berubah perilaku). Lihat logbook 2026-11-21.

## Hasil build (2026-11-21, `run_w1a1_rebuild.sh`)
- Durasi 48,2 menit. Pasca-placement: LUT 26.284 (49,41%), FF 33.663 (31,64%), BRAM 108,5 tile (77,50%), Slice 12.016 (90,35%), DSP 0. Timing 100 MHz met, WNS +0,518 ns.

## Hasil board (2026-11-21 14:02 WIB)
- Akurasi **84.19%** (identik EXP-001/005).
- Throughput bs1000 **3038.57 img/s** = 99,6% estimasi 3.051,8 (EXP-001 notebook FIFO manual: 1.995 = 65%); latency bs1 **1.663 ms** (EXP-001: 1,646 ms).
- **Hipotesis FIFO terbukti langsung:** desain & folding sama dengan EXP-001, beda utama FIFO otomatis (rtlsim) vs manual → throughput +52% dengan biaya BRAM +9 tile (99,5 → 108,5), LUT +3%, FF +7%.

## Catatan / anomali
- 
