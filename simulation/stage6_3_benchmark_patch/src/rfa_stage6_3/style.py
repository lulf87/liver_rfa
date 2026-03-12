from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt


def apply_style(style_cfg: dict) -> None:
    mpl.rcParams.update({
        'font.family': style_cfg.get('font_family', 'DejaVu Sans'),
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',
        'savefig.facecolor': 'white',
        'savefig.edgecolor': 'white',
        'axes.edgecolor': style_cfg.get('axis_color', '#4A4A4A'),
        'axes.labelcolor': style_cfg.get('text_color', '#333333'),
        'xtick.color': style_cfg.get('text_color', '#333333'),
        'ytick.color': style_cfg.get('text_color', '#333333'),
        'text.color': style_cfg.get('text_color', '#333333'),
        'axes.titlesize': 10.0,
        'axes.labelsize': 9.0,
        'xtick.labelsize': 8.0,
        'ytick.labelsize': 8.0,
        'legend.fontsize': 8.0,
        'figure.dpi': 160,
        'savefig.dpi': 600,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.linewidth': 0.8,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })
    plt.rcParams['svg.fonttype'] = 'none'
