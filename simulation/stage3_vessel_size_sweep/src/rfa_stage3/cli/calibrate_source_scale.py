#!/usr/bin/env python
from __future__ import annotations
import argparse
from copy import deepcopy
from pathlib import Path
import sys
import numpy as np
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'src'))
from rfa_stage3.geometry import build_geometry
from rfa_stage3.io_utils import load_yaml
from rfa_stage3.metrics import equivalent_diameter_mm
from rfa_stage3.solver_fd import run_case

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/base.yaml')
    parser.add_argument('--target-equivalent-diameter-mm', type=float, default=22.0)
    parser.add_argument('--search-min', type=float, default=1.0)
    parser.add_argument('--search-max', type=float, default=1e4)
    parser.add_argument('--num', type=int, default=20)
    args = parser.parse_args()
    cfg = load_yaml(ROOT / args.config)
    cfg0 = deepcopy(cfg)
    cfg0['geometry']['disable_vessel'] = True
    candidates = np.geomspace(args.search_min, args.search_max, args.num)
    best = None; best_err = float('inf')
    for c in candidates:
        cfg0['protocol']['source_scale_per_W'] = float(c)
        geom = build_geometry(cfg0)
        fields = run_case(geom, cfg0)
        eq_d = equivalent_diameter_mm(fields['lesion_mask'], geom.grid.dx_mm, geom.grid.dy_mm)
        err = abs(eq_d - args.target_equivalent_diameter_mm)
        if err < best_err:
            best_err = err; best = (c, eq_d)
    print('Suggested calibration constant:')
    print({
        'source_scale_per_W': float(best[0]),
        'simulated_equivalent_diameter_mm': float(best[1]),
        'target_equivalent_diameter_mm': float(args.target_equivalent_diameter_mm),
        'absolute_error_mm': float(best_err),
    })
if __name__ == '__main__':
    main()
