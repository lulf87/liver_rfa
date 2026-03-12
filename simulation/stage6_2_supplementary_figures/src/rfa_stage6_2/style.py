
from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt


def apply_style(style_cfg: dict) -> None:
    font = style_cfg.get('font_family', 'DejaVu Sans')
    mpl.rcParams.update({
        'font.family': font,
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
        'savefig.dpi': style_cfg.get('png_dpi', 600),
        'axes.spines.top': False,
        'axes.spines.right': False,
        'axes.linewidth': 0.8,
        'grid.linewidth': 0.5,
        'pdf.fonttype': 42,
        'ps.fonttype': 42,
    })
    plt.rcParams['svg.fonttype'] = 'none'
