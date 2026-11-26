# FINN v0.10.1 (Docker) setup

## Requirements
- Vivado + Vitis HLS 2022.2 in `/tools/Xilinx` ([host setup](setup_host_ubuntu2404_vivado2022.2.md)).
- Docker, user in the `docker` group; internet for the first image build (several GB).

## Steps
1. Clone FINN outside this repository and pin the release:
   ```bash
   cd ~ && git clone https://github.com/Xilinx/finn.git && cd finn
   git checkout v0.10.1 && git log --oneline -1      # 9d299689f (tag: v0.10.1)
   mkdir -p ~/finn_build
   ```
   v0.10.1 is the last FINN release paired with Vivado 2022.2 that still targets the Pynq-Z1/Z2 out of the box.
2. Load the environment of this repository (edit paths/IP inside first):
   ```bash
   source <repo>/code/configs/finn_env.sh
   ```
3. Quicktest (also builds the image the first time):
   ```bash
   cd $FINN_ROOT && ./run-docker.sh quicktest 2>&1 | tee ~/finn_build/quicktest.log | tail -30
   ```
   Our result: `977 passed, 16 skipped, 4 xfailed, 2 xpassed`, no failures.
   Image: `xilinx/finn:v0.10.1.xrt_202220.2.14.354_22.04-amd64-xrt`.

Package versions inside the container (used in the paper): Brevitas 0.10.0, qonnx 0.3.0.post1.dev100+gfd61cfe,
PyTorch 1.13.1, ONNX 1.13.0, ONNX Runtime 1.16.1, NumPy 1.26.4, pytest 6.2.5.

## Common problems
| Symptom | Cause | Fix |
|---|---|---|
| `No module named '_pytest.scope'` from `anyio/pytest_plugin.py` | unpinned `anyio` (recent versions need pytest ≥7; FINN pins 6.2.5) | `FINN_DOCKER_EXTRA="-e PYTEST_ADDOPTS=-pno:anyio"` (already in `finn_env.sh`) |
| `Unable to find /settings64.sh ... Vitis` | full Vitis platform not installed | ignore; the Zynq flow needs only Vivado + Vitis HLS |
| `Please set PLATFORM_REPO_PATHS` | Alveo only | ignore |
| a build stops at a `(Pdb)` prompt | `enable_build_pdb_debug=True` (FINN default) | `build.py` sets it to `False` |
| `./run-docker.sh bash -c "..."` prints pip help | quoted arguments are not forwarded intact | run commands from an interactive `./run-docker.sh` shell or pass a script file |
