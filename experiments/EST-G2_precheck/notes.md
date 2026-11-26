# EST-G2 — pre-check estimasi G2 (tanpa Vivado)

- **Tanggal:** 2026-11-21 07:44 WIB. Alat: `code/build/run_g2_estimates.sh` (build.py `--mode estimate`), ±10 detik/konfigurasi.
- **Bukan titik data paper** (estimasi analitik FINN); dipakai untuk memutuskan folding G2.
- Percobaan pertama 07:04 tidak valid (bug build.py: urutan streamline & node tanpa nama) → `reports/_invalid_0704/`.

## Hasil (`reports/summary.csv`), clk 10 ns
| konfigurasi | LUT (est) | LUT% | BRAM18K (est) | BRAM% | DSP | est FPS | est latency |
|---|---|---|---|---|---|---|---|
| W1A1 large | 23.159 | 43,5 | 147 | 52,5 | 0 | 3.051,8 | 2,494 ms |
| W1A1 small | 13.777 | 25,9 | 86 | 30,7 | 0 | 868,1 | 7,202 ms |
| W1A2 large | 38.175 | 71,8 | 284 | **101,4** | 0 | 3.051,8 | 2,494 ms |
| W1A2 small | 20.980 | 39,4 | 171 | 61,1 | 0 | 868,1 | 7,202 ms |
| W2A2 large | 38.175 | 71,8 | 284 | **101,4** | 0 | 3.051,8 | 2,494 ms |
| W2A2 small | 20.980 | 39,4 | 171 | 61,1 | 0 | 868,1 | 7,202 ms |

## Temuan
1. **Kalibrasi vs Vivado (W1A1 large = EXP-001):** LUT est 23.159 vs nyata 25.465 (+10%); BRAM est 147×18K = 73,5 tile 36K vs nyata 99,5 tile (+35%) — selisih kemungkinan dari FIFO, DMA, interconnect & shell yang tidak masuk estimasi per-layer (asumsi).
2. **2-bit + folding large TIDAK MUAT:** BRAM est 101% sebelum koreksi → konsisten dengan pilihan FINN (fold_cnv_small untuk A2).
3. **2-bit + folding small diperkirakan muat:** 171 BRAM18 = 85,5 tile; ×1,35 ≈ 115 tile (±82%) — ketat; LUT ±23k (±43%).
4. **W1A2 ≡ W2A2 di hardware:** atribut MVAU setelah `step_minimize_bit_width` — W1A2 dan W2A2 sama-sama `weightDataType=INT2`, `inputDataType=INT2`, `binaryXnorMode=0` (layer 1–8). Bobot bipolar ±1 hanya hemat (1 bit, XNOR) bila aktivasi juga biner (W1A1: `BINARY`, `binaryXnorMode=1`); dengan aktivasi 2-bit, ±1 disimpan sebagai INT2. → biaya resource & throughput identik, akurasi W2A2 (89,03%) > W1A2 (87,80%) → **W1A2 terdominasi (Pareto)** pada alur FINN ini. Dikonfirmasi dengan build penuh EXP-003/004.
5. Layer pertama (`MVAU_hls_0`) di semua varian: bobot INT2, input INT8 (piksel).
