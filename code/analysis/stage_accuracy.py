#!/usr/bin/env python3
"""stage_accuracy.py -- top-1 accuracy of a FINN model IN SOFTWARE (Python execution, no FPGA), used to
locate the build step that reduces accuracy (this is how the XNOR accumulator issue was traced).

Use a model with GENERIC HW layers (before specialisation), e.g. intermediate_models/step_convert_to_hw.onnx;
*_hls/*_rtl layers can only be executed through cppsim/rtlsim.
Variants evaluated for each model:
  asis      : model as is
  minimize  : + MinimizeAccumulatorWidth + MinimizeWeightBitWidth (same as step_minimize_bit_width)

Run inside the FINN container (slow: several seconds per image):
  cd $FINN_ROOT && ./run-docker.sh python <repo>/code/analysis/stage_accuracy.py --n 500 <step_convert_to_hw.onnx> [...]
Data: $FINN_BUILD_DIR/cifar10_test.npz (x NHWC uint8, y). Results: stdout + --out (JSON).
"""
import argparse
import json
import os
import time

import numpy as np
from qonnx.core.modelwrapper import ModelWrapper

from finn.core.onnx_exec import execute_onnx
from finn.transformation.fpgadataflow.minimize_accumulator_width import MinimizeAccumulatorWidth
from finn.transformation.fpgadataflow.minimize_weight_bit_width import MinimizeWeightBitWidth

p = argparse.ArgumentParser()
p.add_argument("models", nargs="+")
p.add_argument("--n", type=int, default=500, help="number of test images (from the start of the test set)")
p.add_argument("--variants", default="asis,minimize")
p.add_argument("--npz", default=os.path.join(os.environ.get("FINN_BUILD_DIR", os.path.expanduser("~/finn_build")), "cifar10_test.npz"))
p.add_argument("--out", default=os.path.join(os.environ.get("FINN_BUILD_DIR", os.path.expanduser("~/finn_build")), "stage_accuracy.json"))
a = p.parse_args()

d = np.load(a.npz)
x_nhwc, y = d["x"][: a.n], d["y"][: a.n]
results = {}
for mp in a.models:
    base = ModelWrapper(mp)
    for var in a.variants.split(","):
        m = base
        if var == "minimize":
            m = m.transform(MinimizeAccumulatorWidth()).transform(MinimizeWeightBitWidth())
        iname, oname = m.graph.input[0].name, m.graph.output[0].name
        ishape = m.get_tensor_shape(iname)
        nchw = list(ishape[1:]) == [3, 32, 32]
        ok, t0 = 0, time.time()
        for i in range(a.n):
            xi = x_nhwc[i].transpose(2, 0, 1) if nchw else x_nhwc[i]
            out = execute_onnx(m, {iname: xi.reshape(ishape).astype(np.float32)})[oname]
            ok += int(int(np.asarray(out).flatten()[0]) == int(y[i]))
            if (i + 1) % 100 == 0:
                print(f"  [{var}] {i + 1}/{a.n} correct {ok}  ({time.time() - t0:.0f} s)", flush=True)
        key = f"{mp}::{var}"
        results[key] = {"n": a.n, "correct": ok, "acc_pct": 100.0 * ok / a.n}
        print(f"== {key}\n   software accuracy {100.0 * ok / a.n:.2f}% ({ok}/{a.n})", flush=True)
json.dump(results, open(a.out, "w"), indent=2)
print("->", a.out)
