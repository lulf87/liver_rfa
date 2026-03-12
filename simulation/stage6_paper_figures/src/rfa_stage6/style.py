from __future__ import annotations

from typing import Dict

import matplotlib as mpl


def apply_style(style_cfg: Dict) -> None:
    family = style_cfg.get("font_family", "DejaVu Sans")
    text_color = style_cfg.get("text_color", "#333333")
    mpl.rcParams.update({
        "font.family": family,
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "text.color": text_color,
        "axes.labelcolor": text_color,
        "axes.edgecolor": "#555555",
        "xtick.color": text_color,
        "ytick.color": text_color,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "savefig.bbox": "tight",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })
