# EXP-001 — CNV W1A1, notebook end-to-end FINN (gate G1)

- **Tanggal:** 2026-11-20 (mulai ±18:10 WIB)
- **Tujuan / hipotesis:** membuktikan alur penuh FINN v0.10.1 + Vivado 2022.2 → bitstream → jalan di PYNQ-Z2 (image PYNQ v3.1). Lulus G1 bila akurasi di board ≈ akurasi referensi model pretrained dan throughput terukur.
- **Basis:** model CNV W1A1 pretrained Brevitas (bawaan FINN), notebook `cnv_end2end_example.ipynb` dengan satu perubahan: `pynq_board = "Pynq-Z2"`. Commit repo riset: `f216704` (+ commit sesi 2026-11-20 sore).
- **Konfigurasi:** lihat `config.yaml` (W1A1, folding manual bawaan notebook, clk 10 ns).
- **Versi tool:** FINN v0.10.1 (`9d299689f`), Vivado/Vitis HLS 2022.2, Brevitas 0.10.0, image Docker `xilinx/finn:v0.10.1.xrt_202220.2.14.354_22.04-amd64-xrt`, image PYNQ v3.1 (pynq 3.1.1).
- **Lokasi build di laptop (tidak disalin):** `~/finn_build/` (file `end2end_cnv_w1a1_*.onnx`, folder vivado/zynq_proj_*). Perubahan notebook disimpan sebagai patch: `reports/notebook.diff`.

## Hasil
### Build (2026-11-20)
- Durasi `ZynqBuild`: **32 menit** (`_folded.onnx` 18:18:58 → `_synth.onnx` 18:51:06). Tahap: HLS per layer ±4 menit (s.d. 18:23), stitch IP s.d. 18:28, proyek Vivado Zynq (synth+P&R+bitstream) ±22 menit (s.d. 18:50:52).
- Laporan pasca-placement (`reports/top_wrapper_utilization_placed.rpt`, device xc7z020clg400-1):

| Resource | Terpakai | Tersedia | Util |
|---|---|---|---|
| LUT | 25.465 | 53.200 | 47,87% |
| — LUT as Memory | 2.035 | 17.400 | 11,70% |
| FF | 31.599 | 106.400 | 29,70% |
| BRAM (tile 36K) | 99,5 (93 RAMB36 + 13 RAMB18) | 140 | 71,07% |
| DSP48 | 0 | 220 | 0% |
| Slice | 11.689 | 13.300 | 87,89% |

- Timing (`reports/top_wrapper_timing_summary_routed.rpt`): clk_fpga_0 = 10 ns (100 MHz), **WNS +0,318 ns**, TNS 0, WHS +0,018 ns → "All user specified timing constraints are met".
- Folder deploy (bitstream `resizer.bit` 4,0 MB, `resizer.hwh`, driver, `validate.py`) → `board/deploy/`.
- Build dir laptop: `~/finn_build/vivado_zynq_proj_7e1n9kvr/`, `~/finn_build/pynq_deployment_69pzx7fl/`, `~/finn_build/pynq_driver_314xkw31/`.

### Board (2026-11-20 ±19:35 WIB; jam board salah → timestamp di file = 2025-05-03) — **G1 LULUS**
- Image PYNQ v3.1 (pynq 3.1.1); dijalankan sebagai root dengan `pynq_venv.sh` **+ `xrt_setup.sh`**.
- **Akurasi top-1 CIFAR-10 (10.000 gambar uji): 84,19%** (8.419 benar) — `board/accuracy.json`, `board/validate_log.txt`. Referensi Brevitas CNV_1W1A: 84,22% → selisih 0,03 pp (3 gambar).
- Throughput test (`driver.py --exec_mode=throughput_test`, fclk 100 MHz):

| batch | runtime [ms] | throughput [img/s] | DRAM in [MB/s] | copy_input [ms] | unpack_output [ms] |
|---|---|---|---|---|---|
| 1000 | 501,16 | **1.995,37** | 6,13 | 19,55 | 0,99 |
| 1 | **1,646** | 607,52 | 1,87 | 0,38 | 0,84 |

  File: `board/nw_metrics_bs1000.txt`, `board/nw_metrics_bs1.txt`.
- Validasi penuh lewat Python host (batch 1000): 10.000 gambar dalam 5,20 s → 1.924 img/s (overhead host ±4% vs throughput murni).
- Interpretasi: latency 1 gambar 1,65 ms (termasuk overhead DMA), sedangkan throughput saat pipeline penuh 1.995 img/s ≈ 0,50 ms/gambar → efek pipeline dataflow.

## Catatan / anomali
- Sel `showInNetron(...)` kedua gagal `OSError: [Errno 98] Address already in use` (server Netron sebelumnya masih memakai port 8081) → hanya visualisasi, dilewati.
- DSP = 0: W1A1 → perkalian ±1 jadi XNOR + popcount di LUT.
- BRAM 71% & slice 88% → resource paling kritis bila folding diperbesar; slack timing tipis (+0,318 ns).
- PYNQ 3.x: `sudo bash -c 'source pynq_venv.sh && ...'` → `RuntimeError: No Devices Found`; perlu juga `source /etc/profile.d/xrt_setup.sh` (sekarang via `04_code/deploy/pynq_run.sh`).
- Jam board tidak sinkron (tanpa internet) → set dari laptop sebelum mengukur.
- `validate.py` bawaan butuh `dataset_loading` + unduh CIFAR-10 di board (board tanpa internet) → diganti `validate_npz.py` + data uji `.npz` dari laptop.

