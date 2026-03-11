from __future__ import annotations

from typing import Dict

import numpy as np
from scipy import ndimage


def equivalent_diameter_mm(mask: np.ndarray, dx_mm: float, dy_mm: float) -> float:
    area_mm2 = float(mask.sum()) * dx_mm * dy_mm
    return float(np.sqrt(4.0 * area_mm2 / np.pi)) if area_mm2 > 0 else 0.0


def target_mask_from_tumor(tumor_mask: np.ndarray, safety_margin_mm: float, dx_mm: float, dy_mm: float) -> np.ndarray:
    radius_px_x = max(1, int(np.ceil(safety_margin_mm / dx_mm)))
    radius_px_y = max(1, int(np.ceil(safety_margin_mm / dy_mm)))
    y, x = np.ogrid[-radius_px_y: radius_px_y + 1, -radius_px_x: radius_px_x + 1]
    structure = (x * dx_mm) ** 2 + (y * dy_mm) ** 2 <= safety_margin_mm ** 2
    return ndimage.binary_dilation(tumor_mask, structure=structure)


def tumor_coverage_ratio(lesion_mask: np.ndarray, tumor_mask: np.ndarray) -> float:
    denom = float(tumor_mask.sum())
    return float((lesion_mask & tumor_mask).sum() / denom) if denom > 0 else 0.0


def dice_score(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(a.sum() + b.sum())
    return float(2.0 * (a & b).sum() / denom) if denom > 0 else 0.0


def ppv(pred: np.ndarray, target: np.ndarray) -> float:
    denom = float(pred.sum())
    return float((pred & target).sum() / denom) if denom > 0 else 0.0


def tumor_boundary_mask(tumor_mask: np.ndarray) -> np.ndarray:
    eroded = ndimage.binary_erosion(tumor_mask)
    return tumor_mask & (~eroded)


def local_margin_map_mm(lesion_mask: np.ndarray, dx_mm: float, dy_mm: float) -> np.ndarray:
    return ndimage.distance_transform_edt(lesion_mask, sampling=(dy_mm, dx_mm))


def margin_deficit_index(lesion_mask: np.ndarray, tumor_mask: np.ndarray, safety_margin_mm: float, dx_mm: float, dy_mm: float) -> float:
    boundary = tumor_boundary_mask(tumor_mask)
    if boundary.sum() == 0:
        return 0.0
    margin_map = local_margin_map_mm(lesion_mask, dx_mm, dy_mm)
    deficits = margin_map[boundary] < safety_margin_mm
    return float(deficits.mean())


def vessel_side_undercoverage_angle_deg(
    lesion_mask: np.ndarray,
    tumor_mask: np.ndarray,
    tumor_center_mm: tuple[float, float],
    vessel_center_mm: tuple[float, float],
    xx_mm: np.ndarray,
    yy_mm: np.ndarray,
    safety_margin_mm: float,
    dx_mm: float,
    dy_mm: float,
    angular_bins: int = 360,
) -> float:
    boundary = tumor_boundary_mask(tumor_mask)
    if boundary.sum() == 0:
        return 0.0
    margin_map = local_margin_map_mm(lesion_mask, dx_mm, dy_mm)

    bx = xx_mm[boundary]
    by = yy_mm[boundary]
    tx, ty = tumor_center_mm
    vx, vy = vessel_center_mm

    vessel_vec = np.array([vx - tx, vy - ty], dtype=float)
    if np.linalg.norm(vessel_vec) == 0:
        return 0.0
    vessel_vec = vessel_vec / np.linalg.norm(vessel_vec)

    rel = np.stack([bx - tx, by - ty], axis=1)
    norms = np.linalg.norm(rel, axis=1)
    valid = norms > 0
    rel = rel[valid]
    margins = margin_map[boundary][valid]
    rel_unit = rel / norms[valid][:, None]

    facing = (rel_unit @ vessel_vec) >= 0.0
    if not np.any(facing):
        return 0.0

    rel_facing = rel[facing]
    margins_facing = margins[facing]
    angles = (np.degrees(np.arctan2(rel_facing[:, 1], rel_facing[:, 0])) + 360.0) % 360.0
    under = margins_facing < safety_margin_mm
    if not np.any(under):
        return 0.0

    bin_ids = np.floor(angles[under] / 360.0 * angular_bins).astype(int)
    bin_ids = np.clip(bin_ids, 0, angular_bins - 1)
    flags = np.zeros(angular_bins, dtype=bool)
    flags[bin_ids] = True
    return float(flags.sum() * (360.0 / angular_bins))


def compute_all_metrics(
    lesion_mask: np.ndarray,
    tumor_mask: np.ndarray,
    tumor_center_mm: tuple[float, float],
    vessel_center_mm: tuple[float, float],
    xx_mm: np.ndarray,
    yy_mm: np.ndarray,
    safety_margin_mm: float,
    dx_mm: float,
    dy_mm: float,
    angular_bins: int = 360,
    has_vessel: bool = True,
) -> Dict[str, float]:
    target_mask = target_mask_from_tumor(tumor_mask, safety_margin_mm, dx_mm, dy_mm)
    metrics = {
        "equivalent_lesion_diameter_mm": equivalent_diameter_mm(lesion_mask, dx_mm, dy_mm),
        "TCR": tumor_coverage_ratio(lesion_mask, tumor_mask),
        "MDI": margin_deficit_index(lesion_mask, tumor_mask, safety_margin_mm, dx_mm, dy_mm),
        "VUA_deg": 0.0 if not has_vessel else vessel_side_undercoverage_angle_deg(
            lesion_mask=lesion_mask,
            tumor_mask=tumor_mask,
            tumor_center_mm=tumor_center_mm,
            vessel_center_mm=vessel_center_mm,
            xx_mm=xx_mm,
            yy_mm=yy_mm,
            safety_margin_mm=safety_margin_mm,
            dx_mm=dx_mm,
            dy_mm=dy_mm,
            angular_bins=angular_bins,
        ),
        "DSC_target": dice_score(lesion_mask, target_mask),
        "PPV_target": ppv(lesion_mask, target_mask),
        "target_area_px": int(target_mask.sum()),
        "lesion_area_px": int(lesion_mask.sum()),
        "tumor_area_px": int(tumor_mask.sum()),
    }
    return metrics
