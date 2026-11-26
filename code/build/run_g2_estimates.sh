#!/bin/bash
# run_g2_estimates.sh -- pre-check (EST-G2): FINN analytical estimates (no Vivado) for
# CNV W1A1/W1A2/W2A2 x folding presets large/small. Run INSIDE the FINN container:
#   source <repo>/code/configs/finn_env.sh
#   cd $FINN_ROOT && ./run-docker.sh bash <repo>/code/build/run_g2_estimates.sh
# Output: experiments/EST-G2_precheck/reports/<name>/ ; summary: .../summary.csv
R=${LIGHTCNN_ROOT:-$(cd "$(dirname "$0")/../.." && pwd)}
B=$R/code/build/build.py
for wa in "1 1" "1 2" "2 2"; do
  set -- $wa
  for fold in large small; do
    echo "=================== W$1A$2 folding=$fold ==================="
    python $B --exp EST-G2 --wbits $1 --abits $2 --folding $fold --mode estimate --tag est-$fold \
      || echo "!!! FAILED: W$1A$2 $fold"
  done
done
python $R/code/analysis/summarize_estimates.py $R/experiments/EST-G2_precheck/reports
