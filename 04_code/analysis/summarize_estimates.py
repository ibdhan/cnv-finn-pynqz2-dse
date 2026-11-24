#!/usr/bin/env python3
"""summarize_estimates.py -- collect FINN (build_dataflow) estimate reports into one table.

Usage: python summarize_estimates.py <folder_with_one_subfolder_per_configuration>
Reads per subfolder: estimate_layer_resources.json (total), estimate_network_performance.json.
Writes summary.csv in that folder and prints a table with xc7z020 utilisation percentages.
"""
import csv
import json
import os
import sys

CAP = {"LUT": 53200, "BRAM_18K": 280, "DSP": 220}  # xc7z020; BRAM in 18K units (140 36K tiles)

root = sys.argv[1]
rows = []
for name in sorted(os.listdir(root)):
    d = os.path.join(root, name)
    res_f = os.path.join(d, "estimate_layer_resources.json")
    perf_f = os.path.join(d, "estimate_network_performance.json")
    if not os.path.isfile(res_f):
        continue
    res = json.load(open(res_f)).get("total", {})
    perf = json.load(open(perf_f)) if os.path.isfile(perf_f) else {}
    row = {
        "config": name,
        "LUT": round(res.get("LUT", 0)),
        "BRAM_18K": round(res.get("BRAM_18K", 0)),
        "URAM": round(res.get("URAM", 0)),
        "DSP": round(res.get("DSP", 0)),
        "est_fps": round(perf.get("estimated_throughput_fps", 0), 1),
        "est_latency_ms": round(perf.get("estimated_latency_ns", 0) / 1e6, 3),
        "critical_path_cycles": perf.get("critical_path_cycles"),
        "max_cycles": perf.get("max_cycles"),
        "max_cycles_node": perf.get("max_cycles_node_name"),
    }
    for k, cap in CAP.items():
        row[k + "_pct"] = round(100.0 * row[k] / cap, 1)
    rows.append(row)

if not rows:
    sys.exit("no estimate reports found in " + root)
out = os.path.join(root, "summary.csv")
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
hdr = f"{'config':34s} {'LUT':>7s} {'LUT%':>6s} {'BRAM18':>7s} {'BRAM%':>6s} {'DSP':>4s} {'est_fps':>9s} {'lat_ms':>7s}"
print(hdr)
for r in rows:
    print(f"{r['config']:34s} {r['LUT']:7d} {r['LUT_pct']:6.1f} {r['BRAM_18K']:7d} {r['BRAM_18K_pct']:6.1f} "
          f"{r['DSP']:4d} {r['est_fps']:9.1f} {r['est_latency_ms']:7.3f}")
print("summary ->", out)
