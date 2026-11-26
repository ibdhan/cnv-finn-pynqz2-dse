# EST-SWEEP — pre-check sweep target_fps (estimasi, tanpa Vivado)

- **Tanggal:** 2026-11-21 15:30 WIB. `code/build/run_sweep_estimates.sh`, 17 konfigurasi, semua ok. Ringkasan: `reports/summary.csv`.
- Koreksi kalibrasi (EXP-001..006): BRAM ×1,43, LUT ×1,10. Batas aman: BRAM ≤95%, LUT ≤90%.

| presisi | target_fps | est FPS | LUT est (%) | BRAM18 est (%) | BRAM terkoreksi (tile, %) | muat? |
|---|---|---|---|---|---|---|
| W1A1 | 250 | 301,4 | 7.215 (13,6) | 99 (35,4) | 71 (51%) | ya |
| W1A1 | 500 | 508,6 | 9.221 (17,3) | 112 (40,0) | 80 (57%) | ya |
| W1A1 | 1000 | 1.017,3 | 13.846 (26,0) | 121 (43,2) | 87 (62%) | ya |
| W1A1 | 2000 | 2.034,5 | 22.660 (42,6) | 148 (52,9) | 106 (76%) | ya |
| W1A1 | 3000 | 3.051,8 | 25.190 (47,3) | 140 (50,0) | 100 (71%) | ya |
| W1A1 | 4000 | 4.069,0 | 40.255 (75,7) | 207 (73,9) | 148 (106%) | tidak |
| W1A1 | 6000 | 6.103,5 | 45.311 (85,2) | 207 (73,9) | 148 (106%) | tidak |
| W2A2 | 250 | 301,4 | 9.534 (17,9) | 190 (67,9) | 136 (97%) | sangat tipis |
| W2A2 | 500 | 508,6 | 13.106 (24,6) | 222 (79,3) | 159 (113%) | tidak |
| W2A2 | 1000 | 1.017,3 | 21.335 (40,1) | 235 (83,9) | 168 (120%) | tidak |
| W2A2 | 1500 | 1.525,9 | 23.831 (44,8) | 211 (75,4) | 151 (108%) | tidak |
| W2A2 | 2000 | 2.034,5 | 36.247 (68,1) | 291 (103,9) | 208 (149%) | tidak |
| W1A2 | 250–2000 | idem W2A2 | ≈ W2A2 | 196–292 | ≈ W2A2 | ≈ W2A2 |

## Temuan
1. **W1A1:** ruang trade-off lebar (301 → 3.052 est FPS) dengan BRAM 51–76%; batas atas antara 3.000 dan 4.000 fps (BRAM).
2. **2-bit: BRAM ≈ tidak turun walau target fps turun.** BRAM didominasi penyimpanan bobot (CNV ±1,54 juta bobot → 2 bit ≈ 3,1 Mbit ≈ 86 tile BRAM36 minimum = 61% chip; W1A1 ≈ 43 tile) — folding hanya mengubah jumlah unit compute (LUT). (logika, dari ukuran layer CNV)
3. **target_fps memakai ram_style=auto** → semua memori bobot ke BRAM (mis. W2A2 fps500 layer 1–3 = 40 BRAM18 vs 0 di preset small yang memakai LUTRAM). → opsi baru `build.py --ram-from small` (EXP-012).
4. Est FPS W1A1 fps3000 = 3.051,8 = sama dengan preset large (EST-G2) → SetFolding memilih titik setara.
5. W1A2 ≈ W2A2 (konsisten EST-G2).
