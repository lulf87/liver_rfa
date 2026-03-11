
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
from rfa_stage2.geometry import build_geometry
from rfa_stage2.io_utils import load_yaml, save_json
from rfa_stage2.metrics import compute_all_metrics
from rfa_stage2.solver_fd import run_case


def _lineplot(x, ys, labels, ylabel, title, out_path: Path):
    fig, ax = plt.subplots(figsize=(6,4.5))
    for y, label in zip(ys, labels):
        ax.plot(x, y, marker='o', label=label)
    ax.set_xlabel('Vessel gap (mm)')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if len(labels) > 1:
        ax.legend(frameon=False)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def _contour_panel(geom_fields, out_path: Path):
    n = len(geom_fields)
    fig, axes = plt.subplots(1, n, figsize=(4*n, 4), squeeze=False)
    for ax, item in zip(axes[0], geom_fields):
        geom = item['geom']; fields = item['fields']; title = item['title']
        ax.contour(geom.xx_mm, geom.yy_mm, geom.tumor_mask.astype(float), levels=[0.5], linewidths=2)
        ax.contour(geom.xx_mm, geom.yy_mm, fields['lesion_mask'].astype(float), levels=[0.5], linewidths=2)
        if geom.vessel_mask.any():
            ax.contour(geom.xx_mm, geom.yy_mm, geom.vessel_mask.astype(float), levels=[0.5], linewidths=2)
        ax.contourf(geom.xx_mm, geom.yy_mm, geom.electrode_mask.astype(float), levels=[0.5,1.5], alpha=0.4)
        ax.set_aspect('equal')
        ax.set_title(title)
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/base.yaml')
    parser.add_argument('--gap-config', default='configs/gap_sweep.yaml')
    args = parser.parse_args()
    cfg = load_yaml(ROOT / args.config)
    gap_cfg = load_yaml(ROOT / args.gap_config)
    gaps = [float(v) for v in gap_cfg['grid']['gaps_mm']]
    selected_for_panel = [float(v) for v in gap_cfg.get('panel', {}).get('gaps_mm', gaps)]

    results = []
    geom_fields = []

    # no-vessel baseline companion case at same protocol
    cfg0 = deepcopy(cfg)
    cfg0['project']['case_id'] = 'stage2_novessel_reference'
    cfg0['geometry']['disable_vessel'] = True
    geom0 = build_geometry(cfg0)
    fields0 = run_case(geom0, cfg0)
    m0 = compute_all_metrics(
        lesion_mask=fields0['lesion_mask'],
        tumor_mask=geom0.tumor_mask,
        tumor_center_mm=geom0.tumor_center_mm,
        vessel_center_mm=geom0.vessel_center_mm,
        xx_mm=geom0.xx_mm,
        yy_mm=geom0.yy_mm,
        safety_margin_mm=float(cfg0['metrics']['safety_margin_mm']),
        dx_mm=geom0.grid.dx_mm,
        dy_mm=geom0.grid.dy_mm,
        angular_bins=int(cfg0['metrics'].get('angular_bins', 360)),
        has_vessel=False,
    )
    rec0 = {'case_id': cfg0['project']['case_id'], 'gap_mm': np.nan, 'has_vessel': 0, **m0}
    results.append(rec0)
    save_json(ROOT / 'outputs' / 'metrics' / f"{rec0['case_id']}.json", rec0)
    geom_fields.append({'geom': geom0, 'fields': fields0, 'title': 'no vessel'})

    for gap in gaps:
        cfg_i = deepcopy(cfg)
        cfg_i['project']['case_id'] = f"stage2_gap{str(gap).replace('.', 'p')}"
        cfg_i['geometry']['disable_vessel'] = False
        cfg_i['geometry']['vessel_gap_mm'] = gap
        geom = build_geometry(cfg_i)
        fields = run_case(geom, cfg_i)
        m = compute_all_metrics(
            lesion_mask=fields['lesion_mask'],
            tumor_mask=geom.tumor_mask,
            tumor_center_mm=geom.tumor_center_mm,
            vessel_center_mm=geom.vessel_center_mm,
            xx_mm=geom.xx_mm,
            yy_mm=geom.yy_mm,
            safety_margin_mm=float(cfg_i['metrics']['safety_margin_mm']),
            dx_mm=geom.grid.dx_mm,
            dy_mm=geom.grid.dy_mm,
            angular_bins=int(cfg_i['metrics'].get('angular_bins', 360)),
            has_vessel=True,
        )
        rec = {'case_id': cfg_i['project']['case_id'], 'gap_mm': gap, 'has_vessel': 1, **m}
        results.append(rec)
        save_json(ROOT / 'outputs' / 'metrics' / f"{rec['case_id']}.json", rec)
        if gap in selected_for_panel:
            geom_fields.append({'geom': geom, 'fields': fields, 'title': f'gap={gap:g} mm'})
        print(rec)

    out_csv = ROOT / 'outputs' / 'tables' / 'stage2_gap_sweep_summary.csv'
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader(); writer.writerows(results)

    # line plots for vessel cases only
    vessel_results = [r for r in results if r['has_vessel'] == 1]
    xs = [r['gap_mm'] for r in vessel_results]
    _lineplot(xs, [[r['TCR'] for r in vessel_results]], ['TCR'], 'TCR', 'Tumor coverage vs vessel gap', ROOT / 'outputs' / 'figures' / 'stage2_TCR_vs_gap.png')
    _lineplot(xs, [[r['MDI'] for r in vessel_results]], ['MDI'], 'MDI', 'Margin deficit vs vessel gap', ROOT / 'outputs' / 'figures' / 'stage2_MDI_vs_gap.png')
    _lineplot(xs, [[r['VUA_deg'] for r in vessel_results]], ['VUA'], 'VUA (deg)', 'Vessel-side undercoverage vs vessel gap', ROOT / 'outputs' / 'figures' / 'stage2_VUA_vs_gap.png')
    _contour_panel(geom_fields, ROOT / 'outputs' / 'figures' / 'stage2_lesion_contour_panel.png')
    print(f'Saved summary to {out_csv}')

if __name__ == '__main__':
    main()
