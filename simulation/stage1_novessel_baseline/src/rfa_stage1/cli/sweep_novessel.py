#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
from copy import deepcopy
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from rfa_stage1.geometry import build_geometry
from rfa_stage1.io_utils import load_yaml, save_json
from rfa_stage1.metrics import compute_all_metrics
from rfa_stage1.plotting import plot_case_overview
from rfa_stage1.solver_fd import run_case


def save_heatmap(data: np.ndarray, powers, times, title: str, path: Path, fmt: str = ".3f") -> None:
    fig, ax = plt.subplots(figsize=(6, 4.5))
    im = ax.imshow(data, origin="lower", aspect="auto")
    ax.set_xticks(np.arange(len(times)), [str(int(t/60)) for t in times])
    ax.set_yticks(np.arange(len(powers)), [str(int(p)) for p in powers])
    ax.set_xlabel("Time (min)")
    ax.set_ylabel("Power (W)")
    ax.set_title(title)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            ax.text(j, i, format(float(data[i, j]), fmt), ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-config", default="configs/base.yaml")
    parser.add_argument("--sweep-config", default="configs/sweep_novessel.yaml")
    args = parser.parse_args()

    base_cfg = load_yaml(ROOT / args.base_config)
    sweep_cfg = load_yaml(ROOT / args.sweep_config)

    powers = [float(x) for x in sweep_cfg["sweep"]["powers_W"]]
    times = [float(x) for x in sweep_cfg["sweep"]["times_s"]]
    case_prefix = sweep_cfg["sweep"].get("case_prefix", "novessel")
    make_overview = bool(sweep_cfg["sweep"].get("save_case_figures", False))

    out_metrics = ROOT / "outputs" / "metrics"
    out_figs = ROOT / "outputs" / "figures"
    out_cases = ROOT / "outputs" / "cases"
    out_tables = ROOT / "outputs" / "tables"
    out_metrics.mkdir(parents=True, exist_ok=True)
    out_figs.mkdir(parents=True, exist_ok=True)
    out_cases.mkdir(parents=True, exist_ok=True)
    out_tables.mkdir(parents=True, exist_ok=True)

    rows = []
    eq_map = np.zeros((len(powers), len(times)), dtype=float)
    tcr_map = np.zeros_like(eq_map)
    mdi_map = np.zeros_like(eq_map)

    for i, p in enumerate(powers):
        for j, t in enumerate(times):
            cfg = deepcopy(base_cfg)
            cfg["geometry"]["disable_vessel"] = True
            cfg["protocol"]["nominal_power_W"] = float(p)
            cfg["protocol"]["ablation_time_s"] = float(t)
            case_id = f"{case_prefix}_p{int(p)}_t{int(t/60)}"
            cfg["project"]["case_id"] = case_id

            geom = build_geometry(cfg)
            fields = run_case(geom, cfg)
            metrics = compute_all_metrics(
                lesion_mask=fields["lesion_mask"],
                tumor_mask=geom.tumor_mask,
                tumor_center_mm=geom.tumor_center_mm,
                vessel_center_mm=geom.vessel_center_mm,
                xx_mm=geom.xx_mm,
                yy_mm=geom.yy_mm,
                safety_margin_mm=float(cfg["metrics"]["safety_margin_mm"]),
                dx_mm=geom.grid.dx_mm,
                dy_mm=geom.grid.dy_mm,
                angular_bins=int(cfg["metrics"].get("angular_bins", 360)),
                has_vessel=False,
            )
            np.savez_compressed(
                out_cases / f"{case_id}.npz",
                phi=fields["phi"],
                q_unit=fields["q_unit"],
                sigma_map=fields["sigma_map"],
                temperature_C=fields["temperature_C"],
                omega=fields["omega"],
                lesion_mask=fields["lesion_mask"].astype(np.uint8),
                tumor_mask=geom.tumor_mask.astype(np.uint8),
                vessel_mask=geom.vessel_mask.astype(np.uint8),
                electrode_mask=geom.electrode_mask.astype(np.uint8),
            )
            save_json(out_metrics / f"{case_id}.json", metrics)
            if make_overview:
                plot_case_overview(geom, fields, out_figs / f"{case_id}_overview.png", float(cfg["metrics"]["safety_margin_mm"]))

            row = {"case_id": case_id, "power_W": p, "time_s": t, **metrics}
            rows.append(row)
            eq_map[i, j] = metrics["equivalent_lesion_diameter_mm"]
            tcr_map[i, j] = metrics["TCR"]
            mdi_map[i, j] = metrics["MDI"]
            print(row)

    with open(out_tables / "novessel_summary.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    save_heatmap(eq_map, powers, times, "Equivalent lesion diameter (mm)", out_figs / "heatmap_eq_diameter.png", fmt=".1f")
    save_heatmap(tcr_map, powers, times, "Tumor coverage ratio (TCR)", out_figs / "heatmap_TCR.png", fmt=".3f")
    save_heatmap(mdi_map, powers, times, "Margin deficit index (MDI)", out_figs / "heatmap_MDI.png", fmt=".3f")

    # simple recommendation: highest TCR, then lowest MDI, then smaller eq diameter
    best = sorted(rows, key=lambda r: (-r["TCR"], r["MDI"], r["equivalent_lesion_diameter_mm"]))[0]
    save_json(out_tables / "recommended_case.json", best)
    print("Recommended case:")
    print(best)


if __name__ == "__main__":
    main()
