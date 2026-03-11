from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .geometry import Geometry
from .metrics import target_mask_from_tumor


def plot_geometry(geom: Geometry, output_path: str | Path, safety_margin_mm: float = 5.0) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    target = target_mask_from_tumor(geom.tumor_mask, safety_margin_mm, geom.grid.dx_mm, geom.grid.dy_mm)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.contour(geom.xx_mm, geom.yy_mm, geom.tumor_mask.astype(float), levels=[0.5], linewidths=2)
    ax.contour(geom.xx_mm, geom.yy_mm, target.astype(float), levels=[0.5], linewidths=1.5, linestyles="--")
    if geom.vessel_mask.any():
        ax.contour(geom.xx_mm, geom.yy_mm, geom.vessel_mask.astype(float), levels=[0.5], linewidths=2)
    ax.contourf(geom.xx_mm, geom.yy_mm, geom.electrode_mask.astype(float), levels=[0.5, 1.5], alpha=0.4)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_aspect("equal")
    ax.set_title("A-version geometry preview")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)


def plot_case_overview(geom: Geometry, fields: dict, output_path: str | Path, safety_margin_mm: float = 5.0) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lesion = fields["lesion_mask"]
    target = target_mask_from_tumor(geom.tumor_mask, safety_margin_mm, geom.grid.dx_mm, geom.grid.dy_mm)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(
        fields["temperature_C"],
        origin="lower",
        extent=[geom.grid.x_mm.min(), geom.grid.x_mm.max(), geom.grid.y_mm.min(), geom.grid.y_mm.max()],
        aspect="equal",
    )
    fig.colorbar(im, ax=ax, label="Temperature (°C)")
    ax.contour(geom.xx_mm, geom.yy_mm, geom.tumor_mask.astype(float), levels=[0.5], linewidths=2)
    ax.contour(geom.xx_mm, geom.yy_mm, target.astype(float), levels=[0.5], linewidths=1.5, linestyles="--")
    ax.contour(geom.xx_mm, geom.yy_mm, lesion.astype(float), levels=[0.5], linewidths=2)
    if geom.vessel_mask.any():
        ax.contour(geom.xx_mm, geom.yy_mm, geom.vessel_mask.astype(float), levels=[0.5], linewidths=2)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    ax.set_title("Temperature field and lesion contour")
    fig.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
