
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
from typing import Dict, List, Tuple

import matplotlib.pyplot as plt
from matplotlib import colors, cm
from matplotlib.patches import Rectangle
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
        'stage1_root': (root / src['stage1_root']).resolve(),
        'stage1_summary_csv': (root / src['stage1_root'] / src['stage1_summary_csv']).resolve(),
        'output_supp_dir': ensure_dir((root / figs['output_supp_dir']).resolve()),
    }


def _save(fig: plt.Figure, stem: str, out_dir: Path, export_pdf: bool, export_png: bool, png_dpi: int) -> None:
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


def _text_color_for_value(value: float, cmap_name: str, vmin: float, vmax: float) -> str:
    if vmax <= vmin:
        return '#222222'
    cmap = cm.get_cmap(cmap_name)
    norm = colors.Normalize(vmin=vmin, vmax=vmax)
    r, g, b, _ = cmap(norm(value))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return 'white' if luminance < 0.42 else '#2F2F2F'


def _annotate_heatmap(ax, data: np.ndarray, cmap_name: str, vmin: float, vmax: float, fmt: str = '.3f') -> None:
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = float(data[i, j])
            if fmt == 'int':
                s = f'{int(round(val))}'
            else:
                s = f'{val:{fmt}}'.rstrip('0').rstrip('.')
            ax.text(j, i, s, ha='center', va='center', fontsize=8.1,
                    color=_text_color_for_value(val, cmap_name, vmin, vmax))


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


def make_figS4(cfg: dict, paths: dict) -> None:
    style_cfg = cfg['style']
    apply_style(style_cfg)
    summary = pd.read_csv(paths['final_summary_csv'])
    base_cfg = load_yaml(paths['base_config'])
    bind = Stage4Bindings(paths['final_stage_root'])
    calib_df = _run_calibration_sweep(bind, base_cfg, cfg['calibration'])
    target = float(cfg['calibration']['target_diameter_mm'])
    sel = calib_df[calib_df['is_selected']].iloc[0]

    ref_d = float(cfg['benchmark']['reference_vessel_diameter_mm'])
    dia_penalty_rows = []
    for label in ['balanced', 'aggressive']:
        no_vessel = float(summary[(summary['protocol_label'] == label) & (summary['has_vessel'] == 0)]['equivalent_lesion_diameter_mm'].iloc[0])
        sub = summary[(summary['protocol_label'] == label) & (summary['has_vessel'] == 1) & (np.isclose(summary['vessel_diameter_mm'], ref_d))].sort_values('gap_mm')
        for _, row in sub.iterrows():
            dia_penalty_rows.append({
                'protocol_label': label,
                'gap_mm': float(row['gap_mm']),
                'diameter_penalty_mm': no_vessel - float(row['equivalent_lesion_diameter_mm']),
                'equivalent_lesion_diameter_mm': float(row['equivalent_lesion_diameter_mm']),
            })
    penalty = pd.DataFrame(dia_penalty_rows)

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.6))
    for ax in axes:
        _data_axis(ax, style_cfg)

    ax = axes[0]
    ax.plot(calib_df['source_scale_per_W'], calib_df['equivalent_lesion_diameter_mm'], color=style_cfg['balanced_color'], lw=2.1)
    ax.axhline(target, color=style_cfg['aggressive_color'], linestyle='--', lw=1.4)
    ax.axvline(float(sel['source_scale_per_W']), color='#999999', linestyle=':', lw=1.2)
    ax.scatter([float(sel['source_scale_per_W'])], [float(sel['equivalent_lesion_diameter_mm'])], color=style_cfg['aggressive_color'], s=28, zorder=4)
    ax.set_xlabel('source_scale_per_W')
    ax.set_ylabel('Equivalent lesion diameter (mm)')
    ax.text(0.02, 1.03, '(A) Baseline calibration', transform=ax.transAxes, fontweight='bold')
    ax.text(float(sel['source_scale_per_W']) + 0.03,
            float(sel['equivalent_lesion_diameter_mm']) + 0.15,
            f'selected = {float(sel["source_scale_per_W"]):.2f}', fontsize=7.6)
    ax.text(ax.get_xlim()[0] + 0.02*(ax.get_xlim()[1]-ax.get_xlim()[0]), target + 0.1,
            f'target = {target:.0f} mm', fontsize=7.6, color=style_cfg['aggressive_color'])

    ax = axes[1]
    for label, color in [('balanced', style_cfg['balanced_color']), ('aggressive', style_cfg['aggressive_color'])]:
        sub = penalty[penalty['protocol_label'] == label].sort_values('gap_mm')
        ax.plot(sub['gap_mm'], sub['diameter_penalty_mm'], marker='o', color=color, lw=2.1, ms=5.5, label=label.capitalize())
    ax.axhline(0.0, color='#BBBBBB', lw=1.0, linestyle='--')
    ax.set_xlabel('Vessel gap (mm)')
    ax.set_ylabel('Lesion diameter penalty (mm)')
    ax.set_xticks([0, 2, 5])
    ax.text(0.02, 1.03, '(B) Internal heat-sink benchmark', transform=ax.transAxes, fontweight='bold')
    ax.legend(frameon=False, loc='upper right')

    fig.subplots_adjust(wspace=0.28)
    _save(fig, 'FigS4_calibration_benchmark', paths['output_supp_dir'],
          cfg['figures']['export_pdf'], cfg['figures']['export_png'], int(cfg['figures']['png_dpi']))


def make_figS5(cfg: dict, paths: dict) -> None:
    style_cfg = cfg['style']
    apply_style(style_cfg)
    df = pd.read_csv(paths['stage1_summary_csv'])

    # robust column names
    power_col = 'power_W'
    time_col = 'time_s'
    times_s = sorted(df[time_col].unique())
    powers_w = sorted(df[power_col].unique())
    times_min = [t / 60.0 for t in times_s]

    tcr = np.zeros((len(powers_w), len(times_s)), dtype=float)
    mdi = np.zeros((len(powers_w), len(times_s)), dtype=float)
    for i, p in enumerate(powers_w):
        for j, t in enumerate(times_s):
            row = df[(np.isclose(df[power_col], p)) & (np.isclose(df[time_col], t))].iloc[0]
            tcr[i, j] = float(row['TCR'])
            mdi[i, j] = float(row['MDI'])

    bal_p, bal_t = float(cfg['protocol_selection']['balanced_power_W']), float(cfg['protocol_selection']['balanced_time_s'])
    agg_p, agg_t = float(cfg['protocol_selection']['aggressive_power_W']), float(cfg['protocol_selection']['aggressive_time_s'])
    j_bal = times_s.index(bal_t); i_bal = powers_w.index(bal_p)
    j_agg = times_s.index(agg_t); i_agg = powers_w.index(agg_p)

    fig, axes = plt.subplots(1, 2, figsize=(8.8, 3.9))
    for ax in axes:
        _data_axis(ax, style_cfg)

    # TCR heatmap
    cmap1 = 'viridis'
    vmin1, vmax1 = float(tcr.min()), 1.0
    im1 = axes[0].imshow(tcr, origin='lower', aspect='auto', cmap=cmap1, vmin=vmin1, vmax=vmax1)
    axes[0].set_xticks(np.arange(len(times_s))); axes[0].set_xticklabels([f'{int(m)}' for m in times_min])
    axes[0].set_yticks(np.arange(len(powers_w))); axes[0].set_yticklabels([f'{int(p)}' for p in powers_w])
    axes[0].set_xlabel('Time (min)'); axes[0].set_ylabel('Power (W)')
    _annotate_heatmap(axes[0], tcr, cmap1, vmin1, vmax1, '.3f')
    axes[0].text(0.02, 1.03, '(A) No-vessel TCR map', transform=axes[0].transAxes, fontweight='bold')
    # highlight protocols
    for (i,j,color,label,dy) in [(i_bal,j_bal,style_cfg['balanced_color'],'Balanced',0.15),(i_agg,j_agg,style_cfg['aggressive_color'],'Aggressive',-0.28)]:
        axes[0].add_patch(Rectangle((j-0.5, i-0.5), 1, 1, fill=False, ec=color, lw=2.0))
        axes[0].text(j+0.55, i+dy, label, color=color, fontsize=7.4, fontweight='bold')

    # MDI heatmap
    cmap2 = 'viridis_r'
    vmin2, vmax2 = float(mdi.min()), float(mdi.max())
    im2 = axes[1].imshow(mdi, origin='lower', aspect='auto', cmap=cmap2, vmin=vmin2, vmax=vmax2)
    axes[1].set_xticks(np.arange(len(times_s))); axes[1].set_xticklabels([f'{int(m)}' for m in times_min])
    axes[1].set_yticks(np.arange(len(powers_w))); axes[1].set_yticklabels([f'{int(p)}' for p in powers_w])
    axes[1].set_xlabel('Time (min)'); axes[1].set_ylabel('')
    axes[1].set_yticklabels([])
    _annotate_heatmap(axes[1], mdi, cmap2, vmin2, vmax2, '.3f')
    axes[1].text(0.02, 1.03, '(B) No-vessel MDI map', transform=axes[1].transAxes, fontweight='bold')
    for (i,j,color,label,dy) in [(i_bal,j_bal,style_cfg['balanced_color'],'Balanced',0.15),(i_agg,j_agg,style_cfg['aggressive_color'],'Aggressive',-0.28)]:
        axes[1].add_patch(Rectangle((j-0.5, i-0.5), 1, 1, fill=False, ec=color, lw=2.0))
        axes[1].text(j+0.55, i+dy, label, color=color, fontsize=7.4, fontweight='bold')

    cbar1 = fig.colorbar(im1, ax=axes[0], fraction=0.046, pad=0.03)
    cbar1.set_label('TCR')
    cbar2 = fig.colorbar(im2, ax=axes[1], fraction=0.046, pad=0.03)
    cbar2.set_label('MDI')
    fig.subplots_adjust(wspace=0.18)
    _save(fig, 'FigS5_protocol_selection', paths['output_supp_dir'],
          cfg['figures']['export_pdf'], cfg['figures']['export_png'], int(cfg['figures']['png_dpi']))


def make_all(config_path: str | Path, root: Path) -> None:
    cfg = load_yaml(root / config_path)
    paths = _resolve_paths(root, cfg)
    make_figS4(cfg, paths)
    make_figS5(cfg, paths)
