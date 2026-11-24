#!/bin/bash
# run_sweep_estimates.sh -- pre-check of the target_fps sweep (FINN analytical estimates, ~10 s per configuration, no Vivado).
#   source <repo>/04_code/configs/finn_env.sh
#   cd $FINN_ROOT && ./run-docker.sh bash <repo>/04_code/build/run_sweep_estimates.sh
# Output: 05_experiments/EST-SWEEP_precheck/reports/<name>/ + summary.csv
R=${LIGHTCNN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
B=$R/04_code/build/build.py
run() { python $B --exp EST-SWEEP --wbits $1 --abits $2 --target-fps $3 --mode estimate --tag est-fps$3 \
        > /tmp/est_w$1a$2_$3.log 2>&1 && echo "ok     W$1A$2 fps$3" || { echo "FAILED W$1A$2 fps$3"; tail -3 /tmp/est_w$1a$2_$3.log; }; }
for f in 250 500 1000 2000 3000 4000 6000; do run 1 1 $f; done
for f in 250 500 1000 1500 2000; do run 2 2 $f; done
for f in 250 500 1000 1500 2000; do run 1 2 $f; done
python $R/04_code/analysis/summarize_estimates.py $R/05_experiments/EST-SWEEP_precheck/reports
