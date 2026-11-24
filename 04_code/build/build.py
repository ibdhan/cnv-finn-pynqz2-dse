#!/usr/bin/env python3
"""build.py -- build the pretrained CNV network (Brevitas, BNN-PYNQ) with FINN v0.10.1 for the PYNQ-Z2.

One command = one experiment (EXP-NNN). The flow follows FINN's official end-to-end test
`tests/end2end/test_end2end_bnn_pynq.py` (export -> pre/post-processing -> streamline ->
conversion to HW layers -> folding -> FIFO sizing -> stitched IP -> bitstream -> driver),
executed through `build_dataflow` so that estimate/resource/timing reports are uniform.

Folding:
  --folding large   = FINN's fold_cnv_large (same as the end-to-end notebook / EXP-001; used by FINN for W1A1)
  --folding small   = FINN's fold_cnv_small (used by FINN for W1A2/W2A2)
  --target-fps N    = FINN automatic folding (SetFolding) for a throughput target of N img/s
                      (sweep axis; mutually exclusive with --folding)

Mode:
  --mode estimate   = stop after FINN's analytical estimate reports (seconds, no Vivado)
  --mode full       = run until bitstream + driver + deployment package (~45-65 min per configuration)

Run INSIDE the FINN container (this repository must be mounted, see 04_code/configs/finn_env.sh):
  source <repo>/04_code/configs/finn_env.sh
  cd $FINN_ROOT && ./run-docker.sh python <repo>/04_code/build/build.py \
      --exp EXP-004 --wbits 2 --abits 2 --folding small --mode estimate

Build output : $FINN_BUILD_DIR/exp/<EXP>_cnv_w<W>a<A>_<tag>/   (large; keep outside the repository)
Copied back  : 05_experiments/<EXP>_*/reports/ (+ board/deploy/ in full mode)

Two fixes for FINN v0.10.1 are applied (see docs/findings.md):
  step_minimize_bit_width_skip_xnor  -- accumulator minimisation is skipped for XNOR (W1A1) layers
  step_enforce_hls_simd_min          -- SIMD raised to satisfy the HLS constraint SIMD >= MW/1024
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime

import torch
from brevitas.export import export_qonnx
from qonnx.core.datatype import DataType
from qonnx.core.modelwrapper import ModelWrapper
from qonnx.custom_op.registry import getCustomOp
from qonnx.transformation.fold_constants import FoldConstants
from qonnx.transformation.general import (
    GiveReadableTensorNames,
    GiveUniqueNodeNames,
    RemoveStaticGraphInputs,
)
from qonnx.transformation.infer_datatypes import InferDataTypes
from qonnx.transformation.infer_shapes import InferShapes
from qonnx.transformation.insert_topk import InsertTopK
from qonnx.transformation.merge_onnx_models import MergeONNXModels
from qonnx.util.cleanup import cleanup as qonnx_cleanup

import finn.builder.build_dataflow as build
import finn.builder.build_dataflow_config as build_cfg
from finn.builder.build_dataflow_config import DataflowOutputType as Out
import finn.transformation.streamline.absorb as absorb
from finn.transformation.qonnx.convert_qonnx_to_finn import ConvertQONNXtoFINN
from finn.transformation.streamline import Streamline
from finn.transformation.streamline.reorder import MakeMaxPoolNHWC, MoveScalarLinearPastInvariants
from qonnx.transformation.bipolar_to_xnor import ConvertBipolarMatMulToXnorPopcount
from qonnx.transformation.general import RemoveUnusedTensors
from qonnx.transformation.infer_data_layouts import InferDataLayouts
from qonnx.transformation.lower_convs_to_matmul import LowerConvsToMatMul
from finn.util.pytorch import ToTensor
from finn.util.test import get_test_model_trained

# repository root (two levels above this file) unless LIGHTCNN_ROOT is set
RESEARCH_ROOT_DEFAULT = os.environ.get(
    "LIGHTCNN_ROOT", os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
FINN_ROOT = os.environ.get("FINN_ROOT", os.path.expanduser("~/finn"))

# ---------------------------------------------------------------------------
# Folding presets: exact copy of tests/end2end/test_end2end_bnn_pynq.py (FINN v0.10.1)
# order = order of the 9 MVAU_hls layers in the CNV graph; rows are (PE, SIMD[, ram_style])
# ---------------------------------------------------------------------------
FOLD_LARGE = [(16, 3), (32, 32), (16, 32), (16, 32), (4, 32), (1, 32), (1, 4), (1, 8), (5, 1)]
FOLD_SMALL = [
    (8, 3, "distributed"), (16, 16, "distributed"), (8, 16, "auto"), (8, 16, "distributed"),
    (4, 8, "auto"), (1, 8, "auto"), (1, 2, "block"), (2, 2, "auto"), (5, 1, "distributed"),
]


def make_fold_step(preset):
    """Return a custom build_dataflow step that applies a folding preset by layer order."""

    def step_apply_cnv_preset_folding(model: ModelWrapper, cfg):
        mvaus = model.get_nodes_by_op_type("MVAU_hls")
        swgs = model.get_nodes_by_op_type("ConvolutionInputGenerator_rtl")
        assert len(mvaus) == 9, f"expected 9 MVAU_hls nodes, found {len(mvaus)}"
        table = FOLD_LARGE if preset == "large" else FOLD_SMALL
        for node, row in zip(mvaus, table):
            inst = getCustomOp(node)
            inst.set_nodeattr("PE", row[0])
            inst.set_nodeattr("SIMD", row[1])
            if preset == "small":
                inst.set_nodeattr("ram_style", row[2])
            inst.set_nodeattr("mem_mode", "internal_decoupled")
            inst.set_nodeattr("resType", "lut")
        for i, node in enumerate(swgs):
            inst = getCustomOp(node)
            inst.set_nodeattr("SIMD", table[i][1])
            inst.set_nodeattr("ram_style", "distributed")
        if preset == "small":
            thr = model.get_nodes_by_op_type("Thresholding_rtl")
            if thr:
                t = getCustomOp(thr[0])
                t.set_nodeattr("depth_trigger_uram", 32000)
                t.set_nodeattr("depth_trigger_bram", 32000)
        return model

    step_apply_cnv_preset_folding.__name__ = f"step_apply_cnv_folding_{preset}"
    return step_apply_cnv_preset_folding


def step_enforce_hls_simd_min(model: ModelWrapper, cfg):
    """Ensure every MVAU_hls satisfies the FINN HLS template constraint SIMD >= MW/1024 and MW % SIMD == 0.
    SetFolding (target_fps) in FINN v0.10.1 does not check this: at low fps it chose SIMD=2 for
    MW=2304 (MVAU_hls_5) -> AssertionError in step_hw_codegen (EXP-007).
    SIMD is raised to the smallest valid divisor of MW; that layer becomes slightly more parallel (not the bottleneck)."""
    import math
    for node in model.get_nodes_by_op_type("MVAU_hls"):
        inst = getCustomOp(node)
        mw, simd = inst.get_nodeattr("MW"), inst.get_nodeattr("SIMD")
        need = math.ceil(mw / 1024)
        if simd < need or mw % simd != 0:
            new = next(d for d in range(max(simd, need), mw + 1) if mw % d == 0)
            print(f"[build.py] {node.name}: SIMD {simd} -> {new} (MW={mw}, requires SIMD >= {mw / 1024:.2f})")
            inst.set_nodeattr("SIMD", new)
    return model


def make_ram_from_preset_step(preset):
    """After automatic folding (target_fps): copy the per-MVAU ram_style (+ distributed SWG) from a preset.
    Reason (EST-SWEEP): target_fps keeps ram_style=auto -> all weights go to BRAM, including small
    layers that the 'small' preset places in LUTRAM -> 2-bit designs do not fit."""

    def step_ram_style_from_preset(model: ModelWrapper, cfg):
        table = FOLD_SMALL if preset == "small" else None
        mvaus = model.get_nodes_by_op_type("MVAU_hls")
        for node, row in zip(mvaus, table):
            getCustomOp(node).set_nodeattr("ram_style", row[2])
        for node in model.get_nodes_by_op_type("ConvolutionInputGenerator_rtl"):
            getCustomOp(node).set_nodeattr("ram_style", "distributed")
        return model

    step_ram_style_from_preset.__name__ = f"step_ram_style_from_{preset}"
    return step_ram_style_from_preset


def step_cnv_pre_post(model: ModelWrapper, cfg):
    """Add pre-processing (uint8 / 255 as torchvision ToTensor) and post-processing (Top-1).
    Same as test_add_pre_and_postproc in FINN's official test."""
    ishape = model.get_tensor_shape(model.graph.input[0].name)
    pre_path = cfg.output_dir + "/intermediate_models/preproc_totensor.onnx"
    os.makedirs(os.path.dirname(pre_path), exist_ok=True)
    export_qonnx(ToTensor(), torch.randn(ishape), pre_path, opset_version=13)
    qonnx_cleanup(pre_path, out_file=pre_path)
    pre = ModelWrapper(pre_path).transform(ConvertQONNXtoFINN())
    pre = pre.transform(InferShapes()).transform(FoldConstants())
    model = model.transform(MergeONNXModels(pre))
    model.set_tensor_datatype(model.graph.input[0].name, DataType["UINT8"])
    model = model.transform(InsertTopK(k=1))
    for t in [InferShapes(), FoldConstants(), GiveUniqueNodeNames(), GiveReadableTensorNames(),
              InferDataTypes(), RemoveStaticGraphInputs()]:
        model = model.transform(t)
    return model


def step_cnv_streamline(model: ModelWrapper, cfg):
    """Streamline EXACTLY as test_streamline in FINN's official test (order matters!).
    Note: an earlier version (MoveScalarLinearPastInvariants -> default step_streamline) applied
    AbsorbSignBiasIntoMultiThreshold AFTER Move..., so W1A2 failed in
    InferQuantizedMatrixVectorActivation ("Signed output requres actval < 0")."""
    model = model.transform(absorb.AbsorbSignBiasIntoMultiThreshold())
    model = model.transform(MoveScalarLinearPastInvariants())
    model = model.transform(Streamline())
    model = model.transform(LowerConvsToMatMul())
    model = model.transform(MakeMaxPoolNHWC())
    model = model.transform(absorb.AbsorbTransposeIntoMultiThreshold())
    model = model.transform(ConvertBipolarMatMulToXnorPopcount())
    model = model.transform(Streamline())
    model = model.transform(absorb.AbsorbScalarMulAddIntoTopK())
    model = model.transform(InferDataLayouts())
    model = model.transform(RemoveUnusedTensors())
    return model


def step_minimize_bit_width_skip_xnor(model: ModelWrapper, cfg):
    """Replacement for step_minimize_bit_width: identical, EXCEPT for MVAU layers in XNOR mode (binaryXnorMode=1).

    Finding (EXP-002): in FINN v0.10.1, MinimizeAccumulatorWidth computes the accumulator range of
    XNOR layers as for an ordinary bipolar product, which is too narrow (e.g. MW=576 -> INT10,
    thresholds 348/570 clipped to 327). 38 W1A1 thresholds changed behaviour -> on-board accuracy
    dropped by 1.60 pp without any error. Non-XNOR layers (W1A2/W2A2) are unaffected (0 thresholds
    change behaviour), so EXP-003/004 are identical with or without this step."""
    from finn.util.fpgadataflow import is_fpgadataflow_node
    from qonnx.transformation.infer_datatypes import InferDataTypes as _IDT
    from finn.transformation.fpgadataflow.minimize_weight_bit_width import MinimizeWeightBitWidth

    for node_id in range(len(model.graph.node)):
        node = model.graph.node[node_id]
        if not is_fpgadataflow_node(node):
            continue
        inst = getCustomOp(node)
        if node.op_type.startswith("MVAU") and inst.get_nodeattr("binaryXnorMode") == 1:
            continue
        if hasattr(inst, "minimize_accumulator_width"):
            inst.minimize_accumulator_width(model)
            model = model.transform(_IDT())
    model = model.transform(MinimizeWeightBitWidth())
    return model


def step_give_unique_names(model: ModelWrapper, cfg):
    """Give all nodes unique names after specialisation (the official test does this too).
    Without it, nodes named "" overwrite each other in per-layer estimates and IP generation may clash."""
    return model.transform(GiveUniqueNodeNames())


def step_collect_vivado_reports(model: ModelWrapper, cfg):
    """Copy Vivado post-placement utilisation report into report/ (timing is copied by the default steps)."""
    proj = model.get_metadata_prop("vivado_pynq_proj")
    if proj:
        rpt = f"{proj}/finn_zynq_link.runs/impl_1/top_wrapper_utilization_placed.rpt"
        if os.path.isfile(rpt):
            shutil.copy(rpt, cfg.output_dir + "/report/post_place_utilization.rpt")
    return model


def git_rev(path):
    try:
        h = subprocess.check_output(["git", "-C", path, "rev-parse", "--short", "HEAD"],
                                    stderr=subprocess.DEVNULL).decode().strip()
        dirty = subprocess.call(["git", "-C", path, "diff", "--quiet", "HEAD"],
                                stderr=subprocess.DEVNULL) != 0
        return h + ("-dirty" if dirty else "")
    except Exception:
        return "unknown"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--exp", required=True, help="experiment ID, e.g. EXP-004 (register it in 05_experiments/registry.csv first)")
    p.add_argument("--wbits", type=int, choices=[1, 2], required=True)
    p.add_argument("--abits", type=int, choices=[1, 2], required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--folding", choices=["large", "small"])
    g.add_argument("--target-fps", type=int)
    p.add_argument("--mode", choices=["estimate", "full"], default="estimate")
    p.add_argument("--clk-ns", type=float, default=10.0, help="synthesis clock period (default 10 ns = 100 MHz)")
    p.add_argument("--board", default="Pynq-Z2")
    p.add_argument("--auto-fifo", dest="auto_fifo", action="store_true", default=True,
                   help="size FIFOs automatically via rtlsim (default, as in the official test)")
    p.add_argument("--no-auto-fifo", dest="auto_fifo", action="store_false")
    p.add_argument("--swg-exception", choices=["auto", "on", "off"], default="auto",
                   help="auto = on when abits==2 (as in FINN's official test for xc7z020)")
    p.add_argument("--ram-from", choices=["small"], default=None,
                   help="(only with --target-fps) copy per-layer ram_style from the small preset")
    p.add_argument("--research-root", default=RESEARCH_ROOT_DEFAULT)
    p.add_argument("--tag", default=None, help="folder label (default: folding name or fps<N>)")
    a = p.parse_args()

    if (a.wbits, a.abits) == (2, 1):
        sys.exit("CNV W2A1 is not available as a pretrained model")

    tag = a.tag or (a.folding if a.folding else f"fps{a.target_fps}")
    name = f"{a.exp}_cnv_w{a.wbits}a{a.abits}_{tag}"
    out_dir = os.path.join(os.environ["FINN_BUILD_DIR"], "exp", name)
    if os.path.exists(out_dir):
        sys.exit(f"Output folder already exists: {out_dir}\nMove it away first, or use another --tag.")
    os.makedirs(out_dir)

    swg = {"on": True, "off": False}.get(a.swg_exception, a.abits == 2)
    t0 = time.time()
    print(f"[build.py] {name} | mode={a.mode} | clk={a.clk_ns} ns | auto_fifo={a.auto_fifo} | swg_exception={swg}")

    # 1) export the pretrained model to QONNX
    model_path = os.path.join(out_dir, f"cnv_w{a.wbits}a{a.abits}_qonnx.onnx")
    net = get_test_model_trained("CNV", a.wbits, a.abits)
    export_qonnx(net, torch.randn(1, 3, 32, 32), model_path)
    qonnx_cleanup(model_path, out_file=model_path)

    # 2) assemble the build steps
    steps = ["step_qonnx_to_finn", "step_tidy_up", step_cnv_pre_post, step_cnv_streamline,
             "step_convert_to_hw", "step_create_dataflow_partition", "step_specialize_layers",
             step_give_unique_names]
    if a.folding:
        steps.append(make_fold_step(a.folding))
    else:
        steps.append("step_target_fps_parallelization")
        steps.append(step_enforce_hls_simd_min)
        if a.ram_from:
            steps.append(make_ram_from_preset_step(a.ram_from))
    steps += [step_minimize_bit_width_skip_xnor, "step_generate_estimate_reports"]
    outputs = [Out.ESTIMATE_REPORTS]
    if a.mode == "full":
        steps += ["step_hw_codegen", "step_hw_ipgen", "step_set_fifo_depths", "step_create_stitched_ip",
                  "step_synthesize_bitfile", step_collect_vivado_reports,
                  "step_make_pynq_driver", "step_deployment_package"]
        outputs += [Out.STITCHED_IP, Out.BITFILE, Out.PYNQ_DRIVER, Out.DEPLOYMENT_PACKAGE]

    cfg = build_cfg.DataflowBuildConfig(
        output_dir=out_dir,
        synth_clk_period_ns=a.clk_ns,
        board=a.board,
        shell_flow_type=build_cfg.ShellFlowType.VIVADO_ZYNQ,
        generate_outputs=outputs,
        steps=steps,
        target_fps=a.target_fps,
        auto_fifo_depths=a.auto_fifo,
        default_swg_exception=swg,
        save_intermediate_models=True,
        enable_build_pdb_debug=False,  # if True, an error drops into a (Pdb) prompt and the process hangs
    )

    meta = {
        "exp": a.exp, "name": name, "model": "cnv", "wbits": a.wbits, "abits": a.abits,
        "folding": a.folding, "target_fps": a.target_fps, "ram_from": a.ram_from, "mode": a.mode, "clk_ns": a.clk_ns,
        "board": a.board, "auto_fifo_depths": a.auto_fifo, "swg_exception": swg,
        "out_dir": out_dir, "start": datetime.now().isoformat(timespec="seconds"),
        "research_commit": git_rev(a.research_root), "finn_commit": git_rev(FINN_ROOT),
        "steps": [s if isinstance(s, str) else s.__name__ for s in steps],
    }
    with open(os.path.join(out_dir, "build_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # 3) run
    ret = build.build_dataflow_cfg(model_path, cfg)
    meta["end"] = datetime.now().isoformat(timespec="seconds")
    meta["duration_min"] = round((time.time() - t0) / 60, 1)
    meta["return_code"] = ret
    with open(os.path.join(out_dir, "build_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # 4) copy results into the experiment folder of this repository
    matches = glob.glob(os.path.join(a.research_root, "05_experiments", f"{a.exp}_*"))
    exp_dir = matches[0] if matches else os.path.join(
        a.research_root, "05_experiments", f"{a.exp}_cnv-w{a.wbits}a{a.abits}_{tag}")
    # estimate mode: several configurations may share one folder (e.g. EST-G2) -> one subfolder per name
    rep_dst = os.path.join(exp_dir, "reports") if a.mode == "full" else os.path.join(exp_dir, "reports", name)
    os.makedirs(rep_dst, exist_ok=True)
    for fn in glob.glob(os.path.join(out_dir, "report", "*")):
        if os.path.isfile(fn):
            shutil.copy(fn, rep_dst)
    for fn in ["build_meta.json", "auto_folding_config.json", "final_hw_config.json",
               "build_dataflow.log", "time_per_step.json"]:
        src = os.path.join(out_dir, fn)
        if os.path.isfile(src):
            shutil.copy(src, rep_dst)
    if a.mode == "full" and os.path.isdir(os.path.join(out_dir, "deploy")):
        dst = os.path.join(exp_dir, "board", "deploy")
        if os.path.exists(dst):
            dst += "_" + datetime.now().strftime("%H%M%S")
        shutil.copytree(os.path.join(out_dir, "deploy"), dst)

    print(f"[build.py] done: return={ret}, {meta['duration_min']} min")
    print(f"[build.py] output build : {out_dir}")
    print(f"[build.py] results copied: {exp_dir}")
    est = os.path.join(out_dir, "report", "estimate_network_performance.json")
    if os.path.isfile(est):
        print("[build.py] performance estimate:", open(est).read())
    sys.exit(0 if ret == 0 else 1)


if __name__ == "__main__":
    main()
