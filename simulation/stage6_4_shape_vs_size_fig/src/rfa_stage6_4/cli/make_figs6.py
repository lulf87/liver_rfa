from __future__ import annotations

import argparse
from pathlib import Path
import yaml
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def load_cfg(path: str | Path) -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def _autotext_color(value: float, vmin: float, vmax: float) -> str:
    if vmax <= vmin:
        return 'black'
    frac = (value - vmin) / (vmax - vmin)
    return 'white' if frac > 0.65 or frac < 0.18 else '#222222'


def _pick_examples(df: pd.DataFrame) -> pd.DataFrame:
    """Pick 3 matched-size examples as in current manuscript figure.

    We compare gap=0 vs gap=5 within the same protocol / vessel size and keep
    examples with small lesion-size difference but non-trivial MDI difference.
    """
    cands = []
    for protocol in ['balanced', 'aggressive']:
        for vd in [3.0, 5.0, 8.0]:
            d0 = df[(df.protocol_label == protocol) & (df.vessel_diameter_mm == vd) & (df.gap_mm == 0)]
            d5 = df[(df.protocol_label == protocol) & (df.vessel_diameter_mm == vd) & (df.gap_mm == 5)]
            if d0.empty or d5.empty:
                continue
            r0 = d0.iloc[0]
            r5 = d5.iloc[0]
            delta_d = abs(float(r5.equivalent_lesion_diameter_mm) - float(r0.equivalent_lesion_diameter_mm))
            delta_mdi = abs(float(r5.MDI) - float(r0.MDI))
            score = delta_mdi - 0.05 * delta_d  # favor large MDI separation, small size difference
            cands.append({
                'protocol_label': protocol,
                'vessel_diameter_mm': vd,
                'gap0_diam': float(r0.equivalent_lesion_diameter_mm),
                'gap5_diam': float(r5.equivalent_lesion_diameter_mm),
                'gap0_mdi': float(r0.MDI),
                'gap5_mdi': float(r5.MDI),
                'delta_d': delta_d,
                'delta_mdi': delta_mdi,
                'score': score,
            })
    ex = pd.DataFrame(cands).sort_values('score', ascending=False)
    if ex.empty:
        raise RuntimeError('No matched-size examples could be selected.')
    # prefer a diverse set similar to the current manuscript figure
    chosen = []
    preferred = [('balanced', 3.0), ('balanced', 5.0), ('aggressive', 5.0)]
    for p, vd in preferred:
        row = ex[(ex.protocol_label == p) & (ex.vessel_diameter_mm == vd)]
        if not row.empty:
            chosen.append(row.iloc[0].to_dict())
    if len(chosen) < 3:
        used = {(c['protocol_label'], c['vessel_diameter_mm']) for c in chosen}
        for _, row in ex.iterrows():
            key = (row['protocol_label'], row['vessel_diameter_mm'])
            if key not in used:
                chosen.append(row.to_dict())
                used.add(key)
            if len(chosen) == 3:
                break
    out = pd.DataFrame(chosen)
    out['example_label'] = [f'E{i+1}' for i in range(len(out))]
    return out


def make_fig(df: pd.DataFrame, cfg: dict) -> plt.Figure:
    colors = cfg['style']['colors']
    color_map = {'balanced': colors['balanced'], 'aggressive': colors['aggressive']}
    marker_map = {3.0: 'o', 5.0: 's', 8.0: '^'}

    # keep only vessel cases
    plot_df = df[df['has_vessel'] == 1].copy()

    fig = plt.figure(figsize=cfg['style'].get('figsize', [10.6, 4.8]), facecolor=cfg['style'].get('facecolor', 'white'))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.55, 0.72, 0.72], wspace=0.48)

    ax1 = fig.add_subplot(gs[0, 0])
    ax2a = fig.add_subplot(gs[0, 1])
    ax2b = fig.add_subplot(gs[0, 2])

    # Panel A: scatter
    for _, row in plot_df.iterrows():
        protocol = row['protocol_label']
        vd = float(row['vessel_diameter_mm'])
        ax1.scatter(
            row['equivalent_lesion_diameter_mm'], row['MDI'],
            s=78,
            marker=marker_map.get(vd, 'o'),
            color=color_map[protocol],
            edgecolor='#222222',
            linewidth=0.8,
            alpha=0.95,
            zorder=3,
        )

    examples = _pick_examples(plot_df)
    # highlight selected examples on scatter
    for _, ex in examples.iterrows():
        protocol = ex['protocol_label']
        vd = float(ex['vessel_diameter_mm'])
        for x, y in [(ex['gap0_diam'], ex['gap0_mdi']), (ex['gap5_diam'], ex['gap5_mdi'])]:
            ax1.scatter(x, y, s=180, marker=marker_map.get(vd, 'o'), facecolors='none', edgecolors='#666666', linewidth=1.1, zorder=2)
        xm = 0.5 * (ex['gap0_diam'] + ex['gap5_diam'])
        ym = 0.5 * (ex['gap0_mdi'] + ex['gap5_mdi'])
        ax1.text(xm + 0.02, ym - 0.01, ex['example_label'], fontsize=9, weight='bold', color='#111111')

    ax1.set_title('(A) Lesion size does not uniquely determine margin deficit', fontsize=12, weight='bold', pad=10)
    ax1.set_xlabel('Equivalent lesion diameter (mm)')
    ax1.set_ylabel('Margin deficit index (MDI)')
    ax1.grid(alpha=0.2)

    protocol_handles = [
        Line2D([0], [0], marker='o', linestyle='None', markerfacecolor=color_map['balanced'], markeredgecolor='#111111', markersize=8, label='Balanced'),
        Line2D([0], [0], marker='o', linestyle='None', markerfacecolor=color_map['aggressive'], markeredgecolor='#111111', markersize=8, label='Aggressive'),
    ]
    vessel_handles = [
        Line2D([0], [0], marker='o', linestyle='None', markerfacecolor='white', markeredgecolor='#111111', markersize=8, label='3 mm vessel'),
        Line2D([0], [0], marker='s', linestyle='None', markerfacecolor='white', markeredgecolor='#111111', markersize=8, label='5 mm vessel'),
        Line2D([0], [0], marker='^', linestyle='None', markerfacecolor='white', markeredgecolor='#111111', markersize=8, label='8 mm vessel'),
    ]
    leg1 = ax1.legend(handles=protocol_handles, title='Protocol', loc='upper right', frameon=False)
    ax1.add_artist(leg1)
    ax1.legend(handles=vessel_handles, title='Marker', loc='lower left', frameon=False)

    # Panel B: matched-size examples (left = lesion size, right = MDI)
    y_positions = np.arange(len(examples))[::-1]
    ax2a.set_title('(B) Matched-size examples show larger separation in MDI than in lesion size', fontsize=12, weight='bold', pad=10)
    for idx, (_, ex) in enumerate(examples.iterrows()):
        y = y_positions[idx]
        col = color_map[ex['protocol_label']]
        ax2a.plot([ex['gap0_diam'], ex['gap5_diam']], [y, y], color=col, lw=2.0, alpha=0.85)
        ax2a.scatter([ex['gap0_diam'], ex['gap5_diam']], [y, y], color=col, edgecolor='#111111', s=85, zorder=3)
        ax2a.text(ex['gap0_diam'], y - 0.18, 'g=0', ha='center', va='top', fontsize=8)
        ax2a.text(ex['gap5_diam'], y - 0.18, 'g=5', ha='center', va='top', fontsize=8)
        ax2a.text(ex['gap5_diam'] + 0.06, y, f'ΔD={ex["delta_d"]:.2f} mm', va='center', fontsize=8.5)
        ax2a.text(ax2a.get_xlim()[0] if idx else 28.55, y + 0.18, ex['example_label'], fontsize=10, weight='bold')

    ax2a.set_yticks([])
    ax2a.set_xlabel('Equivalent lesion diameter (mm)')
    ax2a.set_xlim(plot_df['equivalent_lesion_diameter_mm'].min() - 0.4, plot_df['equivalent_lesion_diameter_mm'].max() + 0.6)
    ax2a.grid(axis='x', alpha=0.18)
    for spine in ['top', 'right', 'left']:
        ax2a.spines[spine].set_visible(False)

    for idx, (_, ex) in enumerate(examples.iterrows()):
        y = y_positions[idx]
        col = color_map[ex['protocol_label']]
        ax2b.plot([ex['gap5_mdi'], ex['gap0_mdi']], [y, y], color=col, lw=2.0, alpha=0.85)
        ax2b.scatter([ex['gap5_mdi'], ex['gap0_mdi']], [y, y], color=col, edgecolor='#111111', s=85, zorder=3)
        ax2b.text(ex['gap0_mdi'] + 0.01, y, f'ΔMDI={ex["delta_mdi"]:.3f}', va='center', fontsize=8.5)
        label = f"{ex['protocol_label'].capitalize()}, {int(ex['vessel_diameter_mm'])} mm vessel"
        ax2b.text(ax2b.get_xlim()[0] if idx else 0.235, y + 0.18, label, fontsize=8.8, color='#444444')

    ax2b.set_yticks([])
    ax2b.set_xlabel('Margin deficit index (MDI)')
    ax2b.grid(axis='x', alpha=0.18)
    for spine in ['top', 'right', 'left']:
        ax2b.spines[spine].set_visible(False)

    fig.text(0.5, 0.02, 'Examples E1–E3 illustrate cases with similar lesion size (ΔD≈1 mm) but materially different margin deficit.', ha='center', fontsize=9, color='#444444')
    fig.tight_layout(rect=[0, 0.05, 1, 1])
    return fig


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', required=True)
    args = ap.parse_args()

    cfg = load_cfg(args.config)
    summary_csv = Path(cfg['source']['final_summary_csv'])
    outdir = Path(cfg['output']['outdir'])
    basename = cfg['output']['basename']
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(summary_csv)
    fig = make_fig(df, cfg)
    if cfg['style'].get('pdf', True):
        fig.savefig(outdir / f'{basename}.pdf', bbox_inches='tight')
    if cfg['style'].get('png', True):
        fig.savefig(outdir / f'{basename}.png', dpi=cfg['style'].get('save_dpi', 300), bbox_inches='tight')
    plt.close(fig)
    print(f'Saved {outdir / (basename + ".pdf")} and/or PNG')


if __name__ == '__main__':
    main()
