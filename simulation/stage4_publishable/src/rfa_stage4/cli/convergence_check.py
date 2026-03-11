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
sys.path.insert(0, str(ROOT / 'src'))
from rfa_stage4.geometry import build_geometry
from rfa_stage4.io_utils import load_yaml
from rfa_stage4.metrics import compute_all_metrics
from rfa_stage4.solver_fd import run_case

METRICS = ['equivalent_lesion_diameter_mm', 'TCR', 'MDI', 'VUA_deg']

def _case_rows(cfg_base, case):
    cfg = deepcopy(cfg_base)
    cfg['geometry']['disable_vessel'] = bool(case['disable_vessel'])
    if not case['disable_vessel']:
        cfg['geometry']['vessel_gap_mm'] = float(case['gap_mm'])
        cfg['geometry']['vessel_radius_mm'] = float(case['vessel_diameter_mm']) / 2.0
    return cfg

def _plot_group(rows, case_label, varying, metric, out_path):
    sub = [r for r in rows if r['case_label']==case_label]
    order = sorted(set(r[varying] for r in sub))
    y = [next(r for r in sub if r[varying]==x)[metric] for x in order]
    fig, ax = plt.subplots(figsize=(5.2, 4.0))
    ax.plot(order, y, marker='o')
    ax.set_xlabel(varying)
    ax.set_ylabel(metric)
    ax.set_title(f'{case_label}: {metric} vs {varying}')
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/base.yaml')
    parser.add_argument('--conv-config', default='configs/convergence.yaml')
    args = parser.parse_args()
    cfg = load_yaml(ROOT / args.config)
    ccfg = load_yaml(ROOT / args.conv_config)
    rows = []
    # grid convergence
    for case in ccfg['cases']:
        for grid_n in ccfg['grid_shapes']:
            cfg_i = _case_rows(cfg, case)
            cfg_i['geometry']['grid_shape'] = [int(grid_n), int(grid_n)]
            cfg_i['protocol']['time_step_s'] = float(ccfg['fixed_dt_s'])
            geom = build_geometry(cfg_i)
            fields = run_case(geom, cfg_i)
            m = compute_all_metrics(
                lesion_mask=fields['lesion_mask'], tumor_mask=geom.tumor_mask,
                tumor_center_mm=geom.tumor_center_mm, vessel_center_mm=geom.vessel_center_mm,
                xx_mm=geom.xx_mm, yy_mm=geom.yy_mm,
                safety_margin_mm=float(cfg_i['metrics']['safety_margin_mm']),
                dx_mm=geom.grid.dx_mm, dy_mm=geom.grid.dy_mm,
                angular_bins=int(cfg_i['metrics'].get('angular_bins', 360)), has_vessel=not bool(case['disable_vessel']),
            )
            rows.append({'group':'grid', 'case_label':case['label'], 'grid_n':int(grid_n), 'dt_s':float(ccfg['fixed_dt_s']), **m})
        for dt_s in ccfg['time_steps_s']:
            cfg_i = _case_rows(cfg, case)
            cfg_i['geometry']['grid_shape'] = [int(ccfg['fixed_grid_n']), int(ccfg['fixed_grid_n'])]
            cfg_i['protocol']['time_step_s'] = float(dt_s)
            geom = build_geometry(cfg_i)
            fields = run_case(geom, cfg_i)
            m = compute_all_metrics(
                lesion_mask=fields['lesion_mask'], tumor_mask=geom.tumor_mask,
                tumor_center_mm=geom.tumor_center_mm, vessel_center_mm=geom.vessel_center_mm,
                xx_mm=geom.xx_mm, yy_mm=geom.yy_mm,
                safety_margin_mm=float(cfg_i['metrics']['safety_margin_mm']),
                dx_mm=geom.grid.dx_mm, dy_mm=geom.grid.dy_mm,
                angular_bins=int(cfg_i['metrics'].get('angular_bins', 360)), has_vessel=not bool(case['disable_vessel']),
            )
            rows.append({'group':'dt', 'case_label':case['label'], 'grid_n':int(ccfg['fixed_grid_n']), 'dt_s':float(dt_s), **m})

    out_csv = ROOT / 'outputs' / 'tables' / 'stage4_convergence_summary.csv'
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)

    for case in ccfg['cases']:
        for metric in METRICS:
            _plot_group([r for r in rows if r['group']=='grid'], case['label'], 'grid_n', metric, ROOT / 'outputs' / 'figures' / f"stage4_conv_grid_{case['label']}_{metric}.png")
            _plot_group([r for r in rows if r['group']=='dt'], case['label'], 'dt_s', metric, ROOT / 'outputs' / 'figures' / f"stage4_conv_dt_{case['label']}_{metric}.png")
    print(f'Saved convergence summary to {out_csv}')

if __name__ == '__main__':
    main()
