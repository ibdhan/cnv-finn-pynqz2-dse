# EXP-003 — CNV W1A2, folding small (G2)

- **Tujuan:** build penuh & ukur di board CNV W1A2 pretrained dengan folding `fold_cnv_small` (preset resmi FINN) → bandingkan 3 presisi pada folding yang sama (EXP-002/003/004).
- **Perintah:** `build.py --exp EXP-003 --wbits 1 --abits 2 --folding small --mode full` (clk 10 ns, auto FIFO rtlsim, swg_exception = abits==2).
- **Estimasi (EST-G2):** lihat `05_experiments/EST-G2_precheck/notes.md`.
- **Hasil build:** `reports/` (post_synth_resources, post_place_utilization.rpt, post_route_timing.rpt, build_meta.json, time_per_step.json).
- **Board:** `board/` — akurasi (validate_npz), throughput bs1000 & bs1.

## Hasil build (2026-11-21, `run_g2_builds.sh`)
- Durasi build: **53,9 menit** (set_fifo_depths 8,9 menit, synthesize_bitfile 34,8 menit). Estimasi FPS: 868,1 (bottleneck `MVAU_hls_3`, 115.200 cycle).
- Pasca-placement (`reports/post_place_utilization.rpt`, xc7z020): LUT 31.823 (59,82%), FF 39.091 (36,74%), BRAM tile 122 (87,14%), Slice 12.753 (95,89%), DSP 0.
- Timing 100 MHz: WNS +0,211 ns, "All user specified timing constraints are met" (`reports/post_route_timing.rpt`).
- Deploy: `board/deploy/{bitfile/finn-accel.bit, driver/}`.

## Hasil board (2026-11-21 11:27–11:31 WIB, `measure_on_board.sh`)
- Akurasi top-1 CIFAR-10 (10.000): **87.76%** (referensi Brevitas 87.80% → selisih -0.04 pp) — `board/accuracy.json`.
- Throughput batch 1000: **865.61 img/s** (estimasi FINN 868,1 → 99.7%); latency batch 1: **4.327 ms** — `board/nw_metrics_bs*.txt`.

## Catatan / anomali
- 
