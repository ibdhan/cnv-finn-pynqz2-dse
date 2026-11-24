# cnv-finn-pynqz2-dse

Design-space exploration of a lightweight quantized CNN (the CNV topology on CIFAR-10) on a low-cost
**PYNQ-Z2 (Zynq-7020)** board with **FINN v0.10.1** and **Vivado 2022.2**: weight/activation precision
(W1A1, W1A2, W2A2) × folding (FINN presets and automatic folding for throughput targets of 250–3000 img/s).
Every configuration was built to a bitstream and measured **on the board**: accuracy on the 10,000 CIFAR-10 test
images, throughput, latency, and post-placement resources.

This repository contains the build/measurement code, the raw reports of every experiment, the frozen result
tables and figures, and setup notes. It accompanies a manuscript submitted for publication (the citation will be added here once it is available).

## Main results (frozen data v01, 100 MHz)

| EXP | Precision | Folding | Top-1 acc. (%) | Throughput (img/s, bs 1000) | Latency (ms, bs 1) | LUT | BRAM (36K tiles) | DSP |
|---|---|---|---|---|---|---|---|---|
| EXP-001 | W1A1 | FINN notebook (manual FIFO) | 84.19 | 1,995.4 | 1.646 | 25,465 (47.9 %) | 99.5 (71.1 %) | 0 |
| EXP-006 | W1A1 | preset large | 84.19 | 3,038.6 | 1.663 | 26,284 (49.4 %) | 108.5 (77.5 %) | 0 |
| EXP-005 | W1A1 | preset small | 84.19 | 865.6 | 4.354 | 24,503 (46.1 %) | 92 (65.7 %) | 0 |
| EXP-007 | W1A1 | target_fps 250 | 84.19 | 300.6 | 12.638 | 21,136 (39.7 %) | 93 (66.4 %) | 10 |
| EXP-008 | W1A1 | target_fps 500 | 84.19 | 507.0 | 8.070 | 22,097 (41.5 %) | 86.5 (61.8 %) | 10 |
| EXP-009 | W1A1 | target_fps 1000 | 84.19 | 1,013.8 | 4.171 | 21,253 (40.0 %) | 82.5 (58.9 %) | 27 |
| EXP-010 | W1A1 | target_fps 2000 | 84.19 | 2,026.9 | 2.223 | 24,786 (46.6 %) | 91 (65.0 %) | 54 |
| EXP-011 | W1A1 | target_fps 3000 | 84.19 | 3,037.3 | 1.836 | 25,720 (48.4 %) | 87.5 (62.5 %) | 54 |
| EXP-003 | W1A2 | preset small | 87.76 | 865.6 | 4.327 | 31,823 (59.8 %) | 122 (87.1 %) | 0 |
| EXP-004 | W2A2 | preset small | 88.63 | 865.6 | 4.347 | 35,406 (66.5 %) | 122 (87.1 %) | 0 |
| EXP-012 | W2A2 | target_fps 250 + small RAM styles | 88.63 | 300.6 | 12.153 | 32,505 (61.1 %) | 127 (90.7 %) | 220 |

Source: [`06_results/tables/results_v01.csv`](06_results/tables/results_v01.csv) (complete table) — figures in
[`06_results/figures/`](06_results/figures/) (`*_en` = English labels). The two data figures of the manuscript are `fig_resource_floor_en` and `fig_estimate_latency_en`
(`04_code/analysis/make_figures_v07.py`). Device capacity: 53,200 LUT, 140 BRAM tiles, 220 DSP.

Highlights:
- Accuracy is bit-exact across all folding settings of the same precision (W1A1 84.19 %, W2A2 88.63 %).
- With automatically sized FIFOs, measured throughput is 99.5–99.7 % of FINN's estimate over a 10× range;
  the notebook flow with manual FIFO depths reaches only ~65 % (EXP-001 vs EXP-006).
- W1A1 resources stay almost flat (21–26 k LUT) from 300 to 3,000 img/s; a fixed part of the design (FIFOs, data
  movers, interconnect, shell) dominates at low folding.
- 2-bit designs are limited by on-chip weight memory: lowering the throughput target does not lower BRAM.
- Two FINN v0.10.1 issues were found and worked around, and FINN's latency estimate was found to be a pessimistic upper bound (measured 52–67 %) — see [`docs/findings.md`](docs/findings.md).

## Repository layout

| Path | Contents |
|---|---|
| [`04_code/`](04_code/) | build, deployment and analysis scripts ([overview](04_code/README.md)) |
| [`05_experiments/`](05_experiments/) | one folder per experiment: FINN/Vivado reports, board measurements, bitstream + driver (`board/deploy/`), `notes.md`; index in `registry.csv` |
| [`06_results/`](06_results/) | frozen tables and figures (v01) with source checksums (`FREEZE_v01.md`) |
| [`docs/`](docs/) | host, FINN and board setup; FINN issues found |

`EXP-002` is kept as evidence of the accumulator issue and is excluded from the results (superseded by `EXP-005`).
`EST-*` folders hold analytical estimates only (no hardware). Experiment `notes.md` files and some raw logs are lab notes
written in Indonesian; all numbers in them are also in the machine-readable reports.
In the raw logs and reports, the build host's user name was replaced by `user` (`/home/user/...`, host `finn_dev_user`);
no other content of the raw files was changed.

## Reproducing

1. Set up the host, FINN and the board: [`docs/setup_host_ubuntu2404_vivado2022.2.md`](docs/setup_host_ubuntu2404_vivado2022.2.md),
   [`docs/setup_finn_docker_v0.10.1.md`](docs/setup_finn_docker_v0.10.1.md), [`docs/setup_board_pynq_z2.md`](docs/setup_board_pynq_z2.md).
2. Edit and load the environment, then build (inside the FINN container):
   ```bash
   source 04_code/configs/finn_env.sh
   cd $FINN_ROOT && ./run-docker.sh python $LIGHTCNN_ROOT/04_code/build/build.py \
       --exp EXP-100 --wbits 2 --abits 2 --folding small --mode estimate     # seconds, no Vivado
   # --mode full : bitstream + driver (~45-65 min);  --target-fps N instead of --folding for automatic folding
   ```
   Use a new experiment ID (and add it to `05_experiments/registry.csv`) to avoid mixing with the published data.
3. Create the offline test set once: `./run-docker.sh python $LIGHTCNN_ROOT/04_code/analysis/make_cifar10_npz.py --out $FINN_BUILD_DIR/cifar10_test.npz`
4. Measure on the board from the host: `bash 04_code/deploy/measure_on_board.sh EXP-100`
5. To check the published bitstreams directly, run step 4 with an existing ID (e.g. `EXP-006`); the bitstream and driver
   are in `05_experiments/<EXP>/board/deploy/`.

## Tool versions
FINN v0.10.1 (`9d299689f`), Docker image `xilinx/finn:v0.10.1.xrt_202220.2.14.354_22.04-amd64-xrt`, Brevitas 0.10.0,
qonnx 0.3.0.post1.dev100+gfd61cfe, PyTorch 1.13.1, ONNX 1.13.0, ONNX Runtime 1.16.1, Vivado/Vitis HLS 2022.2,
PYNQ image v3.1 (pynq 3.1.1). Pretrained CNV models are downloaded by FINN (`get_test_model_trained`); no weights are
redistributed here.

## AI assistance
Parts of the build/analysis code and of this documentation were drafted with the help of a generative AI assistant
(Claude, Anthropic) under the authors' direction. All code was run and all results were measured on hardware and
checked by the authors.

## License
BSD 3-Clause (see [`LICENSE`](LICENSE)), the same license as FINN.
