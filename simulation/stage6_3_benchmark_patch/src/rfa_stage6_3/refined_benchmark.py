from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .io_utils import ensure_dir, load_yaml
from .style import apply_style


class Stage4Bindings:
    def __init__(self, source_stage_root: Path):
        src_root = source_stage_root / 'src'
        if str(src_root) not in sys.path:
            sys.path.insert(0, str(src_root))
        from rfa_stage4.geometry import build_geometry
        from rfa_stage4.solver_fd import run_case
        self.build_geometry = build_geometry
        self.run_case = run_case


def _resolve_paths(root: Path, cfg: dict) -> dict:
    src = cfg['source']
    figs = cfg['figures']
    return {
        'final_stage_root': (root / src['final_stage_root']).resolve(),
        'final_summary_csv': (root / src['final_stage_root'] / src['final_summary_csv']).resolve(),
        'base_config': (root / src['final_stage_root'] / src['base_config']).resolve(),
        'output_supp_dir': ensure_dir((root / figs['output_supp_dir']).resolve()),
    }


def _save(fig, stem: str, out_dir: Path, export_pdf: bool, export_png: bool, png_dpi: int) -> None:
    ensure_dir(out_dir)
    if export_pdf:
        fig.savefig(out_dir / f'{stem}.pdf', bbox_inches='tight', pad_inches=0.02)
    if export_png:
        fig.savefig(out_dir / f'{stem}.png', dpi=png_dpi, bbox_inches='tight', pad_inches=0.02)
    plt.close(fig)


def _data_axis(ax, style_cfg: dict) -> None:
    ax.set_facecolor('white')
    ax.spines['left'].set_color(style_cfg['axis_color'])
    ax.spines['bottom'].set_color(style_cfg['axis_color'])
    ax.spines['left'].set_linewidth(0.8)
    ax.spines['bottom'].set_linewidth(0.8)


def _equivalent_diameter_mm(mask: np.ndarray, dx_mm: float, dy_mm: float) -> float:
    area_mm2 = float(mask.sum()) * float(dx_mm) * float(dy_mm)
    return 2.0 * np.sqrt(area_mm2 / np.pi)


def _run_calibration_sweep(bind: Stage4Bindings, base_cfg: dict, calib_cfg: dict) -> pd.DataFrame:
    scales = np.linspace(float(calib_cfg['source_scale_min']), float(calib_cfg['source_scale_max']), int(calib_cfg['num_points']))
    rows = []
    for scale in scales:
        cfg = deepcopy(base_cfg)
        cfg['geometry']['disable_vessel'] = True
        cfg['protocol']['nominal_power_W'] = float(calib_cfg['protocol_power_W'])
        cfg['protocol']['ablation_time_s'] = float(calib_cfg['protocol_time_s'])
        cfg['protocol']['source_scale_per_W'] = float(scale)
        geom = bind.build_geometry(cfg)
        fields = bind.run_case(geom, cfg)
        eq = _equivalent_diameter_mm(fields['lesion_mask'], geom.grid.dx_mm, geom.grid.dy_mm)
        rows.append({'source_scale_per_W': float(scale), 'equivalent_lesion_diameter_mm': eq})
    df = pd.DataFrame(rows)
    target = float(calib_cfg['target_diameter_mm'])
    idx = (df['equivalent_lesion_diameter_mm'] - target).abs().idxmin()
    df['is_selected'] = False
    df.loc[idx, 'is_selected'] = True
    return df


def make_refined_figS4(config_path: str | Path, root: Path) -> None:
    cfg = load_yaml(root / config_path)
    paths = _resolve_paths(root, cfg)
    style_cfg = cfg['style']
    apply_style(style_cfg)

    summary = pd.read_csv(paths['final_summary_csv'])
    base_cfg = load_yaml(paths['base_config'])
    bind = Stage4Bindings(paths['final_stage_root'])
    calib_df = _run_calibration_sweep(bind, base_cfg, cfg['calibration'])

    target = float(cfg['calibration']['target_diameter_mm'])
    sel = calib_df[calib_df['is_selected']].iloc[0]
    ref_d = float(cfg['benchmark']['reference_vessel_diameter_mm'])

    norm_rows = []
    for label in ['balanced', 'aggressive']:
        no_vessel = float(summary[(summary['protocol_label'] == label) & (summary['has_vessel'] == 0)]['equivalent_lesion_diameter_mm'].iloc[0])
        sub = summary[(summary['protocol_label'] == label) & (summary['has_vessel'] == 1) & (np.isclose(summary['vessel_diameter_mm'], ref_d))].sort_values('gap_mm')
        for _, row in sub.iterrows():
            vessel_d = float(row['equivalent_lesion_diameter_mm'])
            reduction_pct = (no_vessel - vessel_d) / no_vessel * 100.0
            norm_rows.append({
                'protocol_label': label,
                'gap_mm': float(row['gap_mm']),
                'reduction_pct': reduction_pct,
            })
    norm_df = pd.DataFrame(norm_rows)

    fig, axes = plt.subplots(1, 2, figsize=(8.9, 3.7))
    for ax in axes:
        _data_axis(ax, style_cfg)

    ax = axes[0]
    ax.plot(calib_df['source_scale_per_W'], calib_df['equivalent_lesion_diameter_mm'], color=style_cfg['balanced_color'], lw=2.15)
    ax.axhline(target, color=style_cfg['aggressive_color'], linestyle='--', lw=1.5)
    ax.axvline(float(sel['source_scale_per_W']), color='#999999', linestyle=':', lw=1.2)
    ax.scatter([float(sel['source_scale_per_W'])], [float(sel['equivalent_lesion_diameter_mm'])], color=style_cfg['aggressive_color'], s=34, zorder=4)
    ax.set_xlabel('source_scale_per_W')
    ax.set_ylabel('Equivalent lesion diameter (mm)')
    ax.text(0.02, 1.03, '(A) Baseline calibration', transform=ax.transAxes, fontweight='bold')
    ax.text(float(sel['source_scale_per_W']) + 0.08,
        float(sel['equivalent_lesion_diameter_mm']) + 0.28,
        f'selected = {float(sel["source_scale_per_W"]):.2f}',
        fontsize=7.6,
        ha='left',
        va='bottom',
        bbox=dict(boxstyle='round,pad=0.12',
                  facecolor='white',
                  edgecolor='none',
                  alpha=0.85))
    ax.text(ax.get_xlim()[0] + 0.02*(ax.get_xlim()[1]-ax.get_xlim()[0]), target + 0.1,
            f'target = {target:.0f} mm', fontsize=7.6, color=style_cfg['aggressive_color'])

    ax = axes[1]
    for label, color in [('balanced', style_cfg['balanced_color']), ('aggressive', style_cfg['aggressive_color'])]:
        sub = norm_df[norm_df['protocol_label'] == label].sort_values('gap_mm')
        ax.plot(sub['gap_mm'], sub['reduction_pct'], marker='o', color=color, lw=2.15, ms=5.8, label=label.capitalize())
    ax.axhline(0.0, color='#BBBBBB', lw=1.0, linestyle='--')
    ax.set_xlabel('Vessel gap (mm)')
    ax.set_ylabel('Normalized lesion reduction (%)')
    ax.set_xticks([0, 2, 5])
    ax.text(0.02, 1.03, '(B) Normalized heat-sink benchmark', transform=ax.transAxes, fontweight='bold')
    ax.legend(frameon=False, loc='upper right')

    fig.subplots_adjust(wspace=0.28)
    _save(fig, 'FigS4_calibration_benchmark', paths['output_supp_dir'],
          cfg['figures']['export_pdf'], cfg['figures']['export_png'], int(cfg['figures']['png_dpi']))
