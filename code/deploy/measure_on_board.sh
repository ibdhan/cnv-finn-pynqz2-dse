#!/bin/bash
# measure_on_board.sh -- measure one or more build.py experiments on the PYNQ-Z2 (run on the HOST).
#   bash <repo>/code/deploy/measure_on_board.sh EXP-005 EXP-006
# Per experiment: copy deploy/{bitfile,driver} + validate_npz.py + pynq_run.sh to the board ~/<EXP>/,
# measure accuracy (10,000 CIFAR-10 test images, batch 1000), throughput (batch 1000) and latency (batch 1),
# then fetch the results into experiments/<EXP>_*/board/.
# Prerequisites: SSH key to the board, direct link up, test set as .npz (code/analysis/make_cifar10_npz.py).
# Environment overrides: PYNQ_IP, PYNQ_USERNAME, CIFAR_NPZ, LIGHTCNN_ROOT.
set -e
R=${LIGHTCNN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
B=${PYNQ_USERNAME:-xilinx}@${PYNQ_IP:-192.168.2.99}
NPZ=${CIFAR_NPZ:-$HOME/finn_build/cifar10_test.npz}
[ $# -ge 1 ] || { echo "usage: $0 EXP-005 [EXP-006 ...]"; exit 1; }
ssh -o BatchMode=yes $B true || { echo "SSH to the board failed (key? link up?)"; exit 1; }
# passwordless sudo on the board? (one-time setup: docs/setup_board_pynq_z2.md)
if ssh -o BatchMode=yes $B "sudo -n true" 2>/dev/null; then
  NOPW=1; echo ">> passwordless sudo on board: ACTIVE"
else
  NOPW=0; echo ">> NOTE: board sudo still asks for a password. Type it when '>>> TYPE PASSWORD' appears."
fi
pw_hint() { [ $NOPW = 1 ] || echo ">>> TYPE PASSWORD for sudo on the board, then Enter:"; }
echo ">> set board clock (UTC) from host (the board has no RTC/internet)"
pw_hint
ssh -t $B "sudo date -u -s '$(date -u '+%F %T')' >/dev/null && date"
ssh $B "test -f ~/cifar10_test.npz" || { echo ">> copy test set"; scp -q $NPZ $B:~/cifar10_test.npz; }
for EXP in "$@"; do
  E=$(ls -d $R/experiments/${EXP}_* | head -1); D=$E/board/deploy
  [ -f $D/bitfile/finn-accel.bit ] || { echo "!!! $EXP: $D/bitfile/finn-accel.bit not found"; continue; }
  echo "=================== $EXP ($(basename $E)) $(date '+%T') ==================="
  ssh $B "rm -rf ~/$EXP && mkdir -p ~/$EXP"
  scp -q -r $D/bitfile $D/driver $B:~/$EXP/
  scp -q $R/code/deploy/validate_npz.py $R/code/deploy/pynq_run.sh $B:~/$EXP/driver/
  pw_hint
  ssh -t $B "cd ~/$EXP/driver && chmod +x pynq_run.sh && \
    sudo ./pynq_run.sh python3 validate_npz.py --npz \$HOME/cifar10_test.npz --batchsize 1000 --bitfile ../bitfile/finn-accel.bit 2>&1 | tee validate_log.txt && \
    sudo ./pynq_run.sh python3 driver.py --exec_mode=throughput_test --batchsize 1000 --bitfile ../bitfile/finn-accel.bit && cp nw_metrics.txt nw_metrics_bs1000.txt && \
    sudo ./pynq_run.sh python3 driver.py --exec_mode=throughput_test --batchsize 1 --bitfile ../bitfile/finn-accel.bit && cp nw_metrics.txt nw_metrics_bs1.txt"
  scp -q $B:~/$EXP/driver/{accuracy.json,validate_log.txt,nw_metrics_bs1000.txt,nw_metrics_bs1.txt} $E/board/
  echo ">> $EXP: $(grep -o '"top1_acc_pct": [0-9.]*' $E/board/accuracy.json) | bs1000: $(grep -o "'throughput\[images/s\]': [0-9.]*" $E/board/nw_metrics_bs1000.txt) | bs1: $(grep -o "'runtime\[ms\]': [0-9.]*" $E/board/nw_metrics_bs1.txt)"
done
echo ">> done $(date '+%T')"
