#!/usr/bin/env python3
"""freeze_results.py -- freeze experiment data into results/ (tables), version vNN.

Sources are ALWAYS the raw files of each experiment (never retyped numbers):
  board/accuracy.json, board/nw_metrics_bs1000.txt, board/nw_metrics_bs1.txt,
  reports/*utilization_placed*.rpt, reports/*timing*routed*.rpt,
  reports/estimate_network_performance.json, reports/build_meta.json (if present)
Metadata (precision, folding, status) comes from experiments/registry.csv.
Only status 'done' is included; everything else is listed as excluded.

Usage:  python3 code/analysis/freeze_results.py --version v02
Output: results/tables/results_<v>.csv/.md, results/FREEZE_<v>.md (commit, time, source checksums)
A frozen version is never overwritten. Output labels are kept in the original (Indonesian) wording so that
re-running reproduces v01 byte-for-byte: "Hasil beku" = frozen results, auto_fifo "ya"/"tidak" = yes/no.
"""
import argparse, ast, csv, glob, hashlib, json, os, re, subprocess
from datetime import datetime

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CAP = {"LUT": 53200, "FF": 106400, "BRAM": 140, "DSP": 220}

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

def util(rpt):
    out = {}
    for line in open(rpt):
        if not line.startswith("| "):
            continue
        c = [x.strip() for x in line.split("|")]
        name = c[1]
        key = {"Slice LUTs": "LUT", "Slice Registers": "FF", "Block RAM Tile": "BRAM", "DSPs": "DSP", "Slice": "Slice"}.get(name)
        if key and key not in out:
            out[key] = float(c[2]); out[key + "_pct"] = float(c[-2])
    return out

def timing(rpt):
    t = open(rpt).read()
    m = re.search(r"WNS\(ns\).*?\n.*?\n\s+(-?[\d.]+)", t)
    return float(m.group(1)), "All user specified timing constraints are met" in t

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--version", required=True); a = ap.parse_args()
    v = a.version
    reg = list(csv.DictReader(open(f"{ROOT}/experiments/registry.csv")))
    rows, excluded, sources = [], [], []
    for r in reg:
        eid = r["exp_id"]
        if not eid.startswith("EXP-"):
            continue
        if r["status"] != "done":
            excluded.append((eid, r["status"])); continue
        d = glob.glob(f"{ROOT}/experiments/{eid}_*")[0]
        b, rp = f"{d}/board", f"{d}/reports"
        f_acc, f_t, f_l = f"{b}/accuracy.json", f"{b}/nw_metrics_bs1000.txt", f"{b}/nw_metrics_bs1.txt"
        f_u = (glob.glob(f"{rp}/post_place_utilization.rpt") + glob.glob(f"{rp}/*utilization_placed.rpt"))[0]
        f_tm = (glob.glob(f"{rp}/post_route_timing.rpt") + glob.glob(f"{rp}/*timing_summary_routed.rpt"))[0]
        f_e, f_m = f"{rp}/estimate_network_performance.json", f"{rp}/build_meta.json"
        for f in [f_acc, f_t, f_l, f_u, f_tm] + [x for x in [f_e, f_m] if os.path.isfile(x)]:
            sources.append((os.path.relpath(f, ROOT), sha(f)))
        acc = json.load(open(f_acc))
        mt, ml = ast.literal_eval(open(f_t).read()), ast.literal_eval(open(f_l).read())
        u = util(f_u); wns, met = timing(f_tm)
        est = json.load(open(f_e)) if os.path.isfile(f_e) else {}
        meta = json.load(open(f_m)) if os.path.isfile(f_m) else {}
        if r["folding_cfg"] in ("large", "small"):
            method = f"preset-{r['folding_cfg']}"
        elif r["folding_cfg"] == "notebook-default":
            method = "notebook (FIFO manual)"
        else:
            method = "target_fps" + (" + ram_small" if "ram" in r["folding_cfg"] else "")
        fps = mt["throughput[images/s]"]
        rows.append({
            "exp_id": eid, "precision": f"W{r['w_bits']}A{r['a_bits']}", "folding_method": method,
            "target_fps": r["target_fps"] or "", "top1_acc_pct": acc["top1_acc_pct"], "n_test": acc["n_samples"],
            "throughput_fps_bs1000": round(fps, 1), "latency_ms_bs1": round(ml["runtime[ms]"], 3),
            "est_fps": round(est["estimated_throughput_fps"], 1) if est else "",
            "fps_vs_est_pct": round(100 * fps / est["estimated_throughput_fps"], 1) if est else "",
            "est_latency_ms": round(est["estimated_latency_ns"] / 1e6, 3) if est else "",
            "LUT": int(u["LUT"]), "LUT_pct": u["LUT_pct"], "FF": int(u["FF"]), "FF_pct": u["FF_pct"],
            "BRAM_tile": u["BRAM"], "BRAM_pct": u["BRAM_pct"], "DSP": int(u["DSP"]), "DSP_pct": u["DSP_pct"],
            "Slice_pct": u.get("Slice_pct", ""), "fclk_MHz": mt.get("fclk[mhz]", 100.0), "WNS_ns": wns,
            "timing_met": met, "auto_fifo": "tidak" if "notebook" in method else "ya",
            "resType": "lut" if method.startswith("preset") else ("default" if "notebook" in method else "auto"),
            "build_min": meta.get("duration_min", ""),
        })
    os.makedirs(f"{ROOT}/results/tables", exist_ok=True); os.makedirs(f"{ROOT}/results/figures", exist_ok=True)
    out_csv = f"{ROOT}/results/tables/results_{v}.csv"
    assert not os.path.exists(out_csv), f"{out_csv} already exists - a frozen version must not be overwritten; use a new version"
    with open(out_csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    cols = ["exp_id", "precision", "folding_method", "target_fps", "top1_acc_pct", "throughput_fps_bs1000",
            "latency_ms_bs1", "fps_vs_est_pct", "LUT", "LUT_pct", "BRAM_tile", "BRAM_pct", "DSP", "WNS_ns"]
    with open(f"{ROOT}/results/tables/results_{v}.md", "w") as f:
        f.write(f"# Hasil beku {v} (sumber: `results_{v}.csv`)\n\n| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
        for r in rows:
            f.write("| " + " | ".join(str(r[c]) for c in cols) + " |\n")
    commit = subprocess.run(["git", "--no-optional-locks", "-c", "safe.directory=*", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                            capture_output=True, text=True).stdout.strip() or "unknown"
    with open(f"{ROOT}/results/FREEZE_{v}.md", "w") as f:
        f.write(f"# FREEZE {v}\n\n- Waktu (UTC mesin build): {datetime.now().isoformat(timespec='seconds')}\n- Commit repo saat freeze: `{commit}`\n"
                f"- Skrip: `code/analysis/freeze_results.py --version {v}`\n- Eksperimen masuk ({len(rows)}): {', '.join(r['exp_id'] for r in rows)}\n"
                f"- Dikecualikan: {', '.join(f'{e} ({s})' for e, s in excluded)}\n\n## Checksum sumber (sha256, 16 karakter)\n")
        for p, h in sources:
            f.write(f"- `{p}` {h}\n")
    json.dump(rows, open(f"/tmp/rows_{v}.json", "w"))
    print(f"{len(rows)} eksperimen dibekukan -> {out_csv}")

if __name__ == "__main__":
    main()
