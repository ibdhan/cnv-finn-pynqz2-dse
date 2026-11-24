# finn_env.sh -- environment for FINN v0.10.1 + Vivado 2022.2 targeting the PYNQ-Z2.
# Usage:  source <repo>/04_code/configs/finn_env.sh && cd $FINN_ROOT && ./run-docker.sh <command>
# Edit the values below for your machine.

# --- this repository (mounted into the FINN container at the same path) ---
_here="${BASH_SOURCE[0]:-$0}"
export LIGHTCNN_ROOT=${LIGHTCNN_ROOT:-$(cd "$(dirname "$_here")/../.." && pwd)}

# --- FINN checkout (git clone https://github.com/Xilinx/finn && git checkout v0.10.1) ---
export FINN_ROOT=${FINN_ROOT:-$HOME/finn}

# --- AMD tools on the host (mounted into the container) ---
export FINN_XILINX_PATH=/tools/Xilinx
export FINN_XILINX_VERSION=2022.2

# --- build folder: keep it OUTSIDE the repository (thousands of files, several GB per build) ---
export FINN_HOST_BUILD_DIR=$HOME/finn_build

# --- parallelism: our host had 16 threads and 14 GiB RAM ---
export NUM_DEFAULT_WORKERS=4

# --- target board (direct Ethernet link, see docs/setup_board_pynq_z2.md) ---
export PYNQ_BOARD=Pynq-Z2
export PYNQ_IP=192.168.2.99
export PYNQ_USERNAME=xilinx
export PYNQ_PASSWORD=xilinx          # factory default of the PYNQ image; SSH keys recommended
export PYNQ_TARGET_DIR=/home/xilinx/finn_dev

# --- pytest workaround ---
# A FINN v0.10.1 image built today pulls the latest anyio, whose pytest plugin needs _pytest.scope
# (absent in the pinned pytest 6.2.5) -> quicktest fails before running. Disable the anyio plugin.
# The repository is mounted so build.py can be read and results are copied straight into 05_experiments/.
export FINN_DOCKER_EXTRA="-e PYTEST_ADDOPTS=-pno:anyio -v $LIGHTCNN_ROOT:$LIGHTCNN_ROOT -e LIGHTCNN_ROOT=$LIGHTCNN_ROOT"

# --- Jupyter inside the container ---
export JUPYTER_PORT=8888

echo "[finn_env] repo $LIGHTCNN_ROOT | FINN $FINN_ROOT | Vivado $FINN_XILINX_VERSION @ $FINN_XILINX_PATH | build -> $FINN_HOST_BUILD_DIR | workers=$NUM_DEFAULT_WORKERS | board=$PYNQ_BOARD@$PYNQ_IP"
