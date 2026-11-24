#!/bin/bash
# run_g2_builds.sh -- full builds of CNV W1A1/W1A2/W2A2 with the 'small' folding preset (sequential).
# Note: EXP-002 (W1A1) was built before the XNOR fix and is kept only as evidence (superseded by EXP-005).
#   source <repo>/04_code/configs/finn_env.sh
#   cd $FINN_ROOT && ./run-docker.sh bash <repo>/04_code/build/run_g2_builds.sh
R=${LIGHTCNN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
B=$R/04_code/build/build.py
for e in "EXP-002 1 1" "EXP-003 1 2" "EXP-004 2 2"; do
  set -- $e
  echo "=================== $1 W$2A$3 small (full) start $(date '+%F %T') ==================="
  python $B --exp $1 --wbits $2 --abits $3 --folding small --mode full || echo "!!! FAILED: $1"
  echo "=================== $1 done $(date '+%F %T') ==================="
done
