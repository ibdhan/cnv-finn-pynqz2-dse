#!/bin/bash
# run_sweep_builds.sh -- full builds of the target_fps sweep (~50 min per configuration sequentially, ~60 min with 2 streams):
#   EXP-007..011 = W1A1 target_fps 250/500/1000/2000/3000
#   EXP-012      = W2A2 target_fps 250 --ram-from small, ONLY if the corrected BRAM estimate (x1.43) is <= 95%
#   source <repo>/code/configs/finn_env.sh
#   cd $FINN_ROOT && ./run-docker.sh bash <repo>/code/build/run_sweep_builds.sh [A|B|ALL]
# Two parallel streams (two terminals): A = EXP-007, 009, 011 ; B = gate + EXP-008, 010, 012. No argument = ALL (sequential).
# (In our run the gate said SKIP (96%); EXP-012 was then built manually and fitted at 90.7% BRAM.)
STREAM=${1:-ALL}
R=${LIGHTCNN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
B=$R/code/build/build.py
if [ "$STREAM" != A ]; then
echo "=================== gate EXP-012: estimate W2A2 fps250 --ram-from small ==================="
python $B --exp EST-SWEEP --wbits 2 --abits 2 --target-fps 250 --ram-from small --mode estimate --tag est-fps250-ramsmall \
  > /tmp/est_w2a2_250_ramsmall.log 2>&1 || echo "!!! FAILED gate estimate"
GATE=$(python - <<'PY'
import json, os
r=json.load(open(os.environ["FINN_BUILD_DIR"] + "/exp/EST-SWEEP_cnv_w2a2_est-fps250-ramsmall/report/estimate_layer_resources.json"))["total"]
bram_tile=r["BRAM_18K"]*1.43/2; lut=r["LUT"]*1.10
ok = bram_tile <= 0.95*140 and lut <= 0.90*53200
print(f"{'GO' if ok else 'SKIP'} (BRAM18 est {r['BRAM_18K']:.0f} -> corrected {bram_tile:.0f} tiles = {100*bram_tile/140:.0f}%; corrected LUT {100*lut/53200:.0f}%)")
PY
)
echo "gate EXP-012: $GATE"
fi
case $STREAM in
  A) LIST="EXP-007:250 EXP-009:1000 EXP-011:3000" ;;
  B) LIST="EXP-008:500 EXP-010:2000" ;;
  *) LIST="EXP-007:250 EXP-008:500 EXP-009:1000 EXP-010:2000 EXP-011:3000" ;;
esac
for e in $LIST; do
  IFS=: read X F <<< "$e"; set -- $X $F
  echo "=================== $1 W1A1 fps$2 (full) start $(date '+%F %T') ==================="
  python $B --exp $1 --wbits 1 --abits 1 --target-fps $2 --mode full || echo "!!! FAILED: $1"
  echo "=================== $1 done $(date '+%F %T') ==================="
done
if [ "$STREAM" = A ]; then :
elif [[ "$GATE" == GO* ]]; then
  echo "=================== EXP-012 W2A2 fps250 ram-small (full) start $(date '+%F %T') ==================="
  python $B --exp EXP-012 --wbits 2 --abits 2 --target-fps 250 --ram-from small --mode full || echo "!!! FAILED: EXP-012"
  echo "=================== EXP-012 done $(date '+%F %T') ==================="
else
  echo "=================== EXP-012 SKIPPED: $GATE ==================="
fi
echo "=================== SWEEP ($STREAM) DONE $(date '+%F %T') ==================="
