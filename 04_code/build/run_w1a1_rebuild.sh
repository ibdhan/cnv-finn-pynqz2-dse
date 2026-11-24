#!/bin/bash
# run_w1a1_rebuild.sh -- quick estimate check of the XNOR fix, then full builds of
# EXP-005 (W1A1 small) and EXP-006 (W1A1 large).
#   source <repo>/04_code/configs/finn_env.sh
#   cd $FINN_ROOT && ./run-docker.sh bash <repo>/04_code/build/run_w1a1_rebuild.sh
R=${LIGHTCNN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
B=$R/04_code/build/build.py
echo "=================== estimate check W1A1 small (XNOR fix) ==================="
python $B --exp EST-G2 --wbits 1 --abits 1 --folding small --mode estimate --tag est-small-fixxnor || echo "!!! FAILED check"
for e in "EXP-005 small" "EXP-006 large"; do
  set -- $e
  echo "=================== $1 W1A1 $2 (full) start $(date '+%F %T') ==================="
  python $B --exp $1 --wbits 1 --abits 1 --folding $2 --mode full || echo "!!! FAILED: $1"
  echo "=================== $1 done $(date '+%F %T') ==================="
done
