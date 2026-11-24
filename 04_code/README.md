# Code

| Folder | Contents |
|---|---|
| `configs/finn_env.sh` | environment for FINN v0.10.1 (source it before `run-docker.sh`) |
| `build/build.py` | one command = one experiment: export → streamline → HW layers → folding (preset or `--target-fps`) → estimates → [full] FIFO sizing, stitched IP, bitstream, driver |
| `build/run_*.sh` | the batch scripts exactly as used for the experiments in this repository |
| `deploy/measure_on_board.sh` | run on the host: accuracy (10,000 images), throughput (batch 1000) and latency (batch 1) on the board |
| `deploy/validate_npz.py`, `deploy/pynq_run.sh` | copied to the board by `measure_on_board.sh` |
| `analysis/make_cifar10_npz.py` | CIFAR-10 test set → `.npz` for the offline board |
| `analysis/summarize_estimates.py` | FINN estimate reports → `summary.csv` |
| `analysis/stage_accuracy.py` | software accuracy before/after a build step (debugging) |
| `analysis/freeze_results.py`, `analysis/make_figures.py`, `analysis/make_figures_v07.py` | raw experiment files → frozen tables and figures in `06_results/` (`make_figures_v07.py`: the two data figures of the manuscript) |
