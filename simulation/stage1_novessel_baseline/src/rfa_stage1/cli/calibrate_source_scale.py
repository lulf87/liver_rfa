#!/usr/bin/env python
from __future__ import annotations

import argparse
from copy import deepcopy
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from rfa_stage1.geometry import build_geometry
from rfa_stage1.io_utils import load_yaml
from rfa_stage1.metrics import equivalent_diameter_mm
from rfa_stage1.solver_fd import run_case


def simulate_eq_d(cfg: dict, scale: float) -> float:
    cfg1 = deepcopy(cfg)
    cfg1["protocol"]["source_scale_per_W"] = float(scale)
    cfg1["geometry"]["disable_vessel"] = True
    geom = build_geometry(cfg1)
    fields = run_case(geom, cfg1)
    return equivalent_diameter_mm(fields["lesion_mask"], geom.grid.dx_mm, geom.grid.dy_mm)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/base.yaml")
    parser.add_argument("--target-equivalent-diameter-mm", type=float, default=22.0)
    parser.add_argument("--search-min", type=float, default=1.0)
    parser.add_argument("--search-max", type=float, default=30.0)
    parser.add_argument("--num", type=int, default=20)
    args = parser.parse_args()

    cfg = load_yaml(ROOT / args.config)
    candidates = np.linspace(args.search_min, args.search_max, args.num)
    best_scale = None
    best_eq = None
    best_err = float("inf")
    for c in candidates:
        eq_d = simulate_eq_d(cfg, float(c))
        err = abs(eq_d - args.target_equivalent_diameter_mm)
        if err < best_err:
            best_err = err
            best_scale, best_eq = float(c), float(eq_d)

    # local refinement
    lo = max(args.search_min, best_scale - (args.search_max - args.search_min) / max(args.num - 1, 1))
    hi = min(args.search_max, best_scale + (args.search_max - args.search_min) / max(args.num - 1, 1))
    for c in np.linspace(lo, hi, 21):
        eq_d = simulate_eq_d(cfg, float(c))
        err = abs(eq_d - args.target_equivalent_diameter_mm)
        if err < best_err:
            best_err = err
            best_scale, best_eq = float(c), float(eq_d)

    print("Suggested calibration constant:")
    print({
        "source_scale_per_W": float(best_scale),
        "simulated_equivalent_diameter_mm": float(best_eq),
        "target_equivalent_diameter_mm": float(args.target_equivalent_diameter_mm),
        "absolute_error_mm": float(best_err),
    })


if __name__ == "__main__":
    main()
