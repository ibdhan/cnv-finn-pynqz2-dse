# EXP-005 — CNV W1A1, folding small (build.py, minimize skip XNOR)

- **Tujuan:** Pengganti EXP-002 (bug akumulator XNOR diperbaiki).
- **Perintah:** `build.py --exp EXP-005 --wbits 1 --abits 1 --folding small --mode full` (clk 10 ns, FIFO otomatis, `step_minimize_bit_width_skip_xnor`).
- **Latar:** EXP-002 turun 1,60 pp karena MinimizeAccumulatorWidth FINN v0.10.1 salah rentang untuk layer XNOR (38 threshold berubah perilaku). Lihat logbook 2026-11-21.

## Hasil build (2026-11-21, `run_w1a1_rebuild.sh`)
- Durasi 46,3 menit. Pasca-placement: LUT 24.503 (46,06%), FF 27.117 (25,49%), BRAM 92 tile (65,71%), Slice 10.128 (76,15%), DSP 0. Timing 100 MHz met, WNS +0,319 ns.
- Verifikasi fix: 0 threshold layer XNOR berubah; MVAU_hls_8 output UINT32 (bukan INT10).
- Biaya fix vs EXP-002: LUT +1.861 (+8,2%), FF +1.673, BRAM sama → harga kebenaran akumulator XNOR.

## Hasil board (2026-11-21 14:00 WIB)
- Akurasi **84.19%** — identik dengan EXP-001 (8.419 benar, hitungan per batch sama persis) → fix terbukti.
- Throughput bs1000 **865.61 img/s** (99,7% estimasi 868,1); latency bs1 **4.354 ms**.

## Catatan / anomali
- 
