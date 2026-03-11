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
from rfa_stage4.io_utils import load_yaml, save_json
from rfa_stage4.metrics import compute_all_metrics
from rfa_stage4.solver_fd import run_case


def _heatmap(values: np.ndarray, x_labels, y_labels, title: str, cbar_label: str, out_path: Path):
    fig, ax = plt.subplots(figsize=(6.2, 4.8))
    im = ax.imshow(values, origin='lower', aspect='auto')
    ax.set_xticks(np.arange(len(x_labels)))
    ax.set_xticklabels([str(v) for v in x_labels])
    ax.set_yticks(np.arange(len(y_labels)))
    ax.set_yticklabels([str(v) for v in y_labels])
    ax.set_xlabel('Vessel gap (mm)')
    ax.set_ylabel('Vessel diameter (mm)')
    ax.set_title(title)
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label(cbar_label)
    for i in range(values.shape[0]):
        for j in range(values.shape[1]):
            ax.text(j, i, f"{values[i, j]:.3g}", ha='center', va='center', fontsize=8)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def _contour_panel(items, out_path: Path):
    fig, axes = plt.subplots(1, len(items), figsize=(4.2*len(items), 4.2), squeeze=False)
    for ax, item in zip(axes[0], items):
        geom = item['geom']; fields = item['fields']; title = item['title']
        ax.contour(geom.xx_mm, geom.yy_mm, geom.tumor_mask.astype(float), levels=[0.5], linewidths=2)
        ax.contour(geom.xx_mm, geom.yy_mm, fields['lesion_mask'].astype(float), levels=[0.5], linewidths=2)
        if geom.vessel_mask.any():
            ax.contour(geom.xx_mm, geom.yy_mm, geom.vessel_mask.astype(float), levels=[0.5], linewidths=2)
        ax.contourf(geom.xx_mm, geom.yy_mm, geom.electrode_mask.astype(float), levels=[0.5, 1.5], alpha=0.35)
        ax.set_aspect('equal')
        ax.set_title(title)
        ax.set_xlabel('x (mm)')
        ax.set_ylabel('y (mm)')
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='configs/base.yaml')
    parser.add_argument('--sweep-config', default='configs/gap_diameter_sweep.yaml')
    args = parser.parse_args()
    cfg = load_yaml(ROOT / args.config)
    scfg = load_yaml(ROOT / args.sweep_config)
    gaps = [float(v) for v in scfg['grid']['gaps_mm']]
    diameters = [float(v) for v in scfg['grid']['vessel_diameters_mm']]
    panel_gap = float(scfg.get('panel', {}).get('gap_mm', gaps[0]))
    panel_diams = [float(v) for v in scfg.get('panel', {}).get('vessel_diameters_mm', diameters)]

    results = []
    panel_items = []

    cfg0 = deepcopy(cfg)
    cfg0['project']['case_id'] = 'stage4_novessel_reference'
    cfg0['geometry']['disable_vessel'] = True
    geom0 = build_geometry(cfg0)
    fields0 = run_case(geom0, cfg0)
    m0 = compute_all_metrics(
        lesion_mask=fields0['lesion_mask'], tumor_mask=geom0.tumor_mask,
        tumor_center_mm=geom0.tumor_center_mm, vessel_center_mm=geom0.vessel_center_mm,
        xx_mm=geom0.xx_mm, yy_mm=geom0.yy_mm,
        safety_margin_mm=float(cfg0['metrics']['safety_margin_mm']),
        dx_mm=geom0.grid.dx_mm, dy_mm=geom0.grid.dy_mm,
        angular_bins=int(cfg0['metrics'].get('angular_bins', 360)), has_vessel=False,
    )
    rec0 = {'case_id': cfg0['project']['case_id'], 'gap_mm': np.nan, 'vessel_diameter_mm': np.nan, 'has_vessel': 0, **m0}
    results.append(rec0)
    save_json(ROOT / 'outputs' / 'metrics' / f"{rec0['case_id']}.json", rec0)
    panel_items.append({'geom': geom0, 'fields': fields0, 'title': 'no vessel'})

    for d in diameters:
        for g in gaps:
            cfg_i = deepcopy(cfg)
            cfg_i['project']['case_id'] = f"stage4_d{str(d).replace('.', 'p')}_g{str(g).replace('.', 'p')}"
            cfg_i['geometry']['disable_vessel'] = False
            cfg_i['geometry']['vessel_gap_mm'] = g
            cfg_i['geometry']['vessel_radius_mm'] = d / 2.0
            geom = build_geometry(cfg_i)
            fields = run_case(geom, cfg_i)
            m = compute_all_metrics(
                lesion_mask=fields['lesion_mask'], tumor_mask=geom.tumor_mask,
                tumor_center_mm=geom.tumor_center_mm, vessel_center_mm=geom.vessel_center_mm,
                xx_mm=geom.xx_mm, yy_mm=geom.yy_mm,
                safety_margin_mm=float(cfg_i['metrics']['safety_margin_mm']),
                dx_mm=geom.grid.dx_mm, dy_mm=geom.grid.dy_mm,
                angular_bins=int(cfg_i['metrics'].get('angular_bins', 360)), has_vessel=True,
            )
            rec = {'case_id': cfg_i['project']['case_id'], 'gap_mm': g, 'vessel_diameter_mm': d, 'has_vessel': 1, **m}
            results.append(rec)
            save_json(ROOT / 'outputs' / 'metrics' / f"{rec['case_id']}.json", rec)
            print(rec)
            if (g == panel_gap) and (d in panel_diams):
                panel_items.append({'geom': geom, 'fields': fields, 'title': f'd={d:g} mm, gap={g:g} mm'})

    out_csv = ROOT / 'outputs' / 'tables' / 'stage4_gap_diameter_summary.csv'
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader(); writer.writerows(results)

    vessel_results = [r for r in results if r['has_vessel'] == 1]
    def mat(metric):
        arr = np.zeros((len(diameters), len(gaps)), dtype=float)
        for i, d in enumerate(diameters):
            for j, g in enumerate(gaps):
                rec = next(r for r in vessel_results if r['vessel_diameter_mm']==d and r['gap_mm']==g)
                arr[i,j] = rec[metric]
        return arr

    _heatmap(mat('TCR'), gaps, diameters, 'Tumor coverage across gap and vessel size', 'TCR', ROOT / 'outputs' / 'figures' / 'stage4_TCR_heatmap.png')
    _heatmap(mat('MDI'), gaps, diameters, 'Margin deficit across gap and vessel size', 'MDI', ROOT / 'outputs' / 'figures' / 'stage4_MDI_heatmap.png')
    _heatmap(mat('VUA_deg'), gaps, diameters, 'Vessel-side undercoverage across gap and vessel size', 'VUA (deg)', ROOT / 'outputs' / 'figures' / 'stage4_VUA_heatmap.png')
    _heatmap(mat('equivalent_lesion_diameter_mm'), gaps, diameters, 'Equivalent lesion diameter across gap and vessel size', 'Diameter (mm)', ROOT / 'outputs' / 'figures' / 'stage4_eqdiam_heatmap.png')
    _contour_panel(panel_items, ROOT / 'outputs' / 'figures' / 'stage4_contour_panel_gap0.png')
    print(f'Saved summary to {out_csv}')

if __name__ == '__main__':
    main()
