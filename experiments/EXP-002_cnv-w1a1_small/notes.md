# EXP-002 — CNV W1A1, folding small (G2)

- **Tujuan:** build penuh & ukur di board CNV W1A1 pretrained dengan folding `fold_cnv_small` (preset resmi FINN) → bandingkan 3 presisi pada folding yang sama (EXP-002/003/004).
- **Perintah:** `build.py --exp EXP-002 --wbits 1 --abits 1 --folding small --mode full` (clk 10 ns, auto FIFO rtlsim, swg_exception = abits==2).
- **Estimasi (EST-G2):** lihat `experiments/EST-G2_precheck/notes.md`.
- **Hasil build:** `reports/` (post_synth_resources, post_place_utilization.rpt, post_route_timing.rpt, build_meta.json, time_per_step.json).
- **Board:** `board/` — akurasi (validate_npz), throughput bs1000 & bs1.

## Hasil build (2026-11-21, `run_g2_builds.sh`)
- Durasi build: **51,1 menit** (set_fifo_depths 9,1 menit, synthesize_bitfile 31,3 menit). Estimasi FPS: 868,1 (bottleneck `MVAU_hls_3`, 115.200 cycle).
- Pasca-placement (`reports/post_place_utilization.rpt`, xc7z020): LUT 22.642 (42,56%), FF 25.444 (23,91%), BRAM tile 92 (65,71%), Slice 9.798 (73,67%), DSP 0.
- Timing 100 MHz: WNS +0,454 ns, "All user specified timing constraints are met" (`reports/post_route_timing.rpt`).
- Deploy: `board/deploy/{bitfile/finn-accel.bit, driver/}`.

## Hasil board (2026-11-21 11:27–11:31 WIB, `measure_on_board.sh`)
- Akurasi top-1 CIFAR-10 (10.000): **82.62%** (referensi Brevitas 84.22% → selisih -1.60 pp) — `board/accuracy.json`.
- Throughput batch 1000: **865.59 img/s** (estimasi FINN 868,1 → 99.7%); latency batch 1: **4.319 ms** — `board/nw_metrics_bs*.txt`.
- ⚠️ **ANOMALI:** akurasi turun 1,60 pp padahal model sama dengan EXP-001 (84,19%). Model streamline identik dengan notebook; yang beda: `step_minimize_bit_width` memotong threshold & mengecilkan akumulator (mis. MVAU_hls_1 acc INT10 padahal popcount XNOR 0..576). Diselidiki dengan `code/analysis/stage_accuracy.py`. **Angka akurasi EXP-002 jangan dipakai di paper.**
- ✅ **Penyebab terbukti (2026-11-21):** MinimizeAccumulatorWidth FINN v0.10.1 salah rentang untuk layer XNOR → 38 threshold berubah perilaku. Diganti **EXP-005** (fix `step_minimize_bit_width_skip_xnor`) → 84,19%. EXP-002 disimpan sebagai bukti anomali (status `superseded`).

## Catatan / anomali
- 
