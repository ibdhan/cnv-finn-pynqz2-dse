# Notes on FINN v0.10.1: two issues (with workarounds in build.py) and one estimate caveat

Both were found while building the CNV network for the PYNQ-Z2. They were **not** checked against FINN releases newer
than v0.10.1.

## 1. Accumulator minimisation is too narrow for XNOR (W1A1) layers — silent accuracy loss

**Symptom.** EXP-002 (CNV W1A1, `small` folding, default `step_minimize_bit_width`) built and ran without any error,
but on-board accuracy was 82.62 % instead of 84.19 % (EXP-001, same streamlined model; reference model: 84.22 %).
W1A2 and W2A2 were unaffected.

**Diagnosis.** The streamlined model was identical to the one produced by the end-to-end notebook (EXP-001, 84.19 %).
The difference appears after `step_minimize_bit_width`, which the notebook does not run.
In `MatrixVectorActivation.minimize_accumulator_width()` (FINN v0.10.1), a layer in XNOR mode is handled as follows:
the binary weights are mapped to bipolar values (`2*w - 1`), the accumulator range is computed with
`calculate_matvec_accumulator_range()` for BINARY {0, 1} inputs, and the thresholds are then clipped to that range
with `np.clip`. But an XNOR–popcount layer accumulates a **popcount** of MW bits, whose range is 0…MW.

- Example, MVAU_hls_1 (MW = 576): the derived range is **[−329, 327]**, i.e. bounded by the largest number of −1 / +1
  weights in any single neuron, whereas the popcount can reach 576. Thresholds 348, 570 and 343 are clipped to 327.
- All clipped thresholds per layer change the neuron's behaviour (they now fire for popcounts they previously did not):

  | Layer | MW | Derived range | Thresholds clipped (all change behaviour) | Example |
  |---|---|---|---|---|
  | MVAU_hls_1 | 576 | [−329, 327] | 8 | 348, 570 → 327 |
  | MVAU_hls_3 | 1152 | [−636, 662] | 12 | 673, 1016 → 662 |
  | MVAU_hls_4 | 1152 | upper 669 | 1 | 765 → 669 |
  | MVAU_hls_5 | 2304 | upper 1286 | 1 | 3737 → 1286 |
  | MVAU_hls_6 | 256 | upper 159 | 1 | 160 → 159 |
  | MVAU_hls_7 | 512 | upper 291 | 15 | 300, 303 → 291 |
  | **total** | | | **38** | |

  The first layer (MVAU_hls_0, not in XNOR mode) is also clipped (5743 → 3448), but that threshold lies outside the
  reachable range, so it is harmless. The output of the final score layer (MVAU_hls_8) is narrowed from UINT32 to
  INT10 although its popcount can reach 512, a further overflow risk.
- The 38 changed thresholds explain the loss of 1.57 pp relative to EXP-001.
- For W1A2/W2A2 (no XNOR mode) every clipped threshold lies outside the reachable range, so 0 thresholds change
  behaviour and EXP-003/004 are valid.
- `04_code/analysis/stage_accuracy.py` executes models in software before/after the step to locate such losses.

**Workaround.** `step_minimize_bit_width_skip_xnor` in `04_code/build/build.py` applies the same minimisation to all
layers except MVAU nodes with `binaryXnorMode=1`. Result: EXP-005 (same configuration as EXP-002) reaches 84.19 %,
bit-exact with EXP-001 (8,419 correct images, identical per batch). Cost: about +8 % LUT (24,503 vs 22,642).

**Why it matters.** The error is silent: synthesis, timing and the driver all succeed, and the loss is only visible
when accuracy is measured on the board. Narrow-accumulator risks are discussed in the literature on
accumulator-aware quantisation (e.g. A2Q, Colbert et al., ICCV 2023).

## 2. Automatic folding violates the HLS constraint SIMD ≥ MW/1024 at low throughput targets

**Symptom.** EXP-007 (W1A1, `--target-fps 250`) failed in `step_hw_codegen`:
`HLS synthesis of MatrixVectorActivation requires: SIMD >= MW / 1024 ... SIMD=2 and MW=2304 for node: MVAU_hls_5`.

**Cause.** `SetFolding` (used by `target_fps`) lowers SIMD to save resources but does not check the limit of the HLS
template (at most 1024 accumulation steps per PE).

**Workaround.** `step_enforce_hls_simd_min` (runs right after `step_target_fps_parallelization`) raises SIMD to the
smallest divisor of MW that satisfies the constraint (here SIMD 2 → 3). The affected layer becomes slightly more
parallel than needed but is not the bottleneck; measured throughput still matched FINN's estimate (99.7 %).

## 3. The latency estimate is a pessimistic upper bound (not a bug)

**Observation.** For all ten measured designs, single-image latency on the board (batch 1) was 52–67 % of FINN's
estimated latency (`estimate_network_performance.json`, `critical_path_cycles`), and always above 1/estimated
throughput (the cycles of the slowest layer only).

**Cause.** `finn/analysis/fpgadataflow/dataflow_performance.py` sums the `cycles_estimate` of every node along the
critical path. Its docstring states that the estimate is very pessimistic because it assumes no overlap between
executions. For an MVAU, `cycles_estimate` is (MH/PE)·(MW/SIMD)·numInputVectors, i.e. the time to process a whole
frame, while in the streaming dataflow architecture each layer starts as soon as its first outputs arrive.

**How to use it.** Treat FINN's latency estimate as an upper bound and 1/estimated throughput as a lower bound;
measure latency on the board.

