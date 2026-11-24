#!/bin/bash
# pynq_run.sh -- run a command on a PYNQ v3.x board as root WITH the PYNQ and XRT environments.
# Without xrt_setup.sh, PYNQ 3.x cannot see the FPGA: "RuntimeError: No Devices Found".
# Usage (on the board):  sudo ./pynq_run.sh python3 validate_npz.py --npz cifar10_test.npz --batchsize 1000
set -e
source /etc/profile.d/pynq_venv.sh
source /etc/profile.d/xrt_setup.sh
exec "$@"
