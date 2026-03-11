#!/usr/bin/env python
from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from rfa_stage0.geometry import build_geometry
from rfa_stage0.io_utils import load_yaml, save_json
from rfa_stage0.metrics import compute_all_metrics
from rfa_stage0.plotting import plot_case_overview
from rfa_stage0.solver_fd import run_case


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    args = parser.parse_args()

    cfg = load_yaml(ROOT / args.config)
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
        has_vessel=bool(geom.vessel_mask.any()),
    )

    case_id = cfg["project"]["case_id"]
    npz_path = ROOT / "outputs" / "cases" / f"{case_id}.npz"
    json_path = ROOT / "outputs" / "metrics" / f"{case_id}.json"
    fig_path = ROOT / "outputs" / "figures" / f"{case_id}_overview.png"

    npz_path.parent.mkdir(parents=True, exist_ok=True)
    fig_path.parent.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        npz_path,
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
    save_json(json_path, metrics)
    plot_case_overview(geom, fields, fig_path, float(cfg["metrics"]["safety_margin_mm"]))

    print(f"Saved fields to {npz_path}")
    print(f"Saved metrics to {json_path}")
    print(f"Saved figure to {fig_path}")
    print(metrics)


if __name__ == "__main__":
    main()
