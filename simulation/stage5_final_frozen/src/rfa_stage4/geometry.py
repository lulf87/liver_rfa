from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass
class Grid:
    x_mm: np.ndarray
    y_mm: np.ndarray
    dx_mm: float
    dy_mm: float

    @property
    def shape(self) -> Tuple[int, int]:
        return (self.y_mm.size, self.x_mm.size)


@dataclass
class Geometry:
    grid: Grid
    xx_mm: np.ndarray
    yy_mm: np.ndarray
    tumor_mask: np.ndarray
    vessel_mask: np.ndarray
    electrode_mask: np.ndarray
    outer_boundary_mask: np.ndarray
    tumor_center_mm: Tuple[float, float]
    vessel_center_mm: Tuple[float, float]


def make_grid(domain_mm: Tuple[float, float], grid_shape: Tuple[int, int]) -> Grid:
    lx_mm, ly_mm = domain_mm
    nx, ny = grid_shape
    x_mm = np.linspace(-lx_mm / 2.0, lx_mm / 2.0, nx)
    y_mm = np.linspace(-ly_mm / 2.0, ly_mm / 2.0, ny)
    return Grid(
        x_mm=x_mm,
        y_mm=y_mm,
        dx_mm=float(x_mm[1] - x_mm[0]),
        dy_mm=float(y_mm[1] - y_mm[0]),
    )


def ellipse_mask(xx_mm: np.ndarray, yy_mm: np.ndarray, center_mm: Tuple[float, float], radii_mm: Tuple[float, float]) -> np.ndarray:
    cx, cy = center_mm
    rx, ry = radii_mm
    return ((xx_mm - cx) / rx) ** 2 + ((yy_mm - cy) / ry) ** 2 <= 1.0


def circle_mask(xx_mm: np.ndarray, yy_mm: np.ndarray, center_mm: Tuple[float, float], radius_mm: float) -> np.ndarray:
    cx, cy = center_mm
    return (xx_mm - cx) ** 2 + (yy_mm - cy) ** 2 <= radius_mm ** 2


def rectangle_mask(
    xx_mm: np.ndarray,
    yy_mm: np.ndarray,
    center_mm: Tuple[float, float],
    width_mm: float,
    length_mm: float,
) -> np.ndarray:
    cx, cy = center_mm
    return (np.abs(xx_mm - cx) <= width_mm / 2.0) & (np.abs(yy_mm - cy) <= length_mm / 2.0)


def build_geometry(cfg: dict) -> Geometry:
    geom_cfg = cfg["geometry"]
    grid = make_grid(tuple(geom_cfg["domain_mm"]), tuple(geom_cfg["grid_shape"]))
    xx_mm, yy_mm = np.meshgrid(grid.x_mm, grid.y_mm, indexing="xy")

    tumor_center_mm = tuple(float(v) for v in geom_cfg["tumor_center_mm"])
    tumor_radii_mm = tuple(float(v) for v in geom_cfg["tumor_radius_mm"])
    gap_mm = float(geom_cfg["vessel_gap_mm"])
    vessel_radius_mm = float(geom_cfg["vessel_radius_mm"])
    electrode_width_mm = float(geom_cfg["electrode_width_mm"])
    electrode_length_mm = float(geom_cfg["electrode_length_mm"])
    disable_vessel = bool(geom_cfg.get("disable_vessel", False))

    tumor_mask = ellipse_mask(xx_mm, yy_mm, tumor_center_mm, tumor_radii_mm)
    vessel_center_mm = (
        tumor_center_mm[0] + tumor_radii_mm[0] + gap_mm + vessel_radius_mm,
        tumor_center_mm[1],
    )
    vessel_mask = np.zeros_like(tumor_mask, dtype=bool) if disable_vessel else circle_mask(xx_mm, yy_mm, vessel_center_mm, vessel_radius_mm)
    electrode_mask = rectangle_mask(xx_mm, yy_mm, tumor_center_mm, electrode_width_mm, electrode_length_mm)

    outer_boundary_mask = np.zeros_like(tumor_mask, dtype=bool)
    outer_boundary_mask[0, :] = True
    outer_boundary_mask[-1, :] = True
    outer_boundary_mask[:, 0] = True
    outer_boundary_mask[:, -1] = True

    return Geometry(
        grid=grid,
        xx_mm=xx_mm,
        yy_mm=yy_mm,
        tumor_mask=tumor_mask,
        vessel_mask=vessel_mask,
        electrode_mask=electrode_mask,
        outer_boundary_mask=outer_boundary_mask,
        tumor_center_mm=tumor_center_mm,
        vessel_center_mm=vessel_center_mm,
    )
