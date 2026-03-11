from __future__ import annotations

from typing import Dict, Tuple

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve, splu

from .geometry import Geometry


def build_diffusion_matrix(k_map: np.ndarray, dx_m: float, dy_m: float, dirichlet_mask: np.ndarray) -> sparse.csr_matrix:
    ny, nx = k_map.shape
    rows = []
    cols = []
    data = []

    def idx(i: int, j: int) -> int:
        return i * nx + j

    for i in range(ny):
        for j in range(nx):
            p = idx(i, j)
            if dirichlet_mask[i, j]:
                rows.append(p)
                cols.append(p)
                data.append(1.0)
                continue

            diag = 0.0

            if j > 0:
                c = 0.5 * (k_map[i, j] + k_map[i, j - 1]) / dx_m ** 2
                rows.append(p)
                cols.append(idx(i, j - 1))
                data.append(-c)
                diag += c
            if j < nx - 1:
                c = 0.5 * (k_map[i, j] + k_map[i, j + 1]) / dx_m ** 2
                rows.append(p)
                cols.append(idx(i, j + 1))
                data.append(-c)
                diag += c
            if i > 0:
                c = 0.5 * (k_map[i, j] + k_map[i - 1, j]) / dy_m ** 2
                rows.append(p)
                cols.append(idx(i - 1, j))
                data.append(-c)
                diag += c
            if i < ny - 1:
                c = 0.5 * (k_map[i, j] + k_map[i + 1, j]) / dy_m ** 2
                rows.append(p)
                cols.append(idx(i + 1, j))
                data.append(-c)
                diag += c

            rows.append(p)
            cols.append(p)
            data.append(diag)

    N = ny * nx
    return sparse.csr_matrix((data, (rows, cols)), shape=(N, N))


def solve_potential(geom: Geometry, cfg: dict) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mat = cfg["materials"]
    sigma_map = np.full(geom.tumor_mask.shape, float(mat["sigma_liver_S_m"]), dtype=float)
    sigma_map[geom.tumor_mask] = float(mat["sigma_tumor_S_m"])
    sigma_map[geom.vessel_mask] = float(mat["sigma_blood_S_m"])

    dirichlet = geom.outer_boundary_mask | geom.electrode_mask
    values = np.zeros_like(sigma_map, dtype=float)
    values[geom.electrode_mask] = 1.0

    A = build_diffusion_matrix(sigma_map, geom.grid.dx_mm / 1000.0, geom.grid.dy_mm / 1000.0, dirichlet)
    phi = spsolve(A, values.ravel()).reshape(sigma_map.shape)

    grad_y, grad_x = np.gradient(phi, geom.grid.dy_mm / 1000.0, geom.grid.dx_mm / 1000.0)
    q_unit = sigma_map * (grad_x ** 2 + grad_y ** 2)
    q_unit[geom.electrode_mask] = 0.0
    return phi, q_unit, sigma_map


def solve_heat_and_damage(geom: Geometry, cfg: dict, q_unit: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    mat = cfg["materials"]
    dmg = cfg["damage"]
    protocol = cfg["protocol"]

    ny, nx = q_unit.shape
    dx_m = geom.grid.dx_mm / 1000.0
    dy_m = geom.grid.dy_mm / 1000.0

    k_map = np.full((ny, nx), float(mat["k_liver_W_m_K"]), dtype=float)
    k_map[geom.tumor_mask] = float(mat["k_tumor_W_m_K"])

    perf_map = np.full((ny, nx), float(mat["perfusion_sink_liver_W_m3_K"]), dtype=float)
    perf_map[geom.tumor_mask] = float(mat["perfusion_sink_tumor_W_m3_K"])
    perf_map[geom.vessel_mask] = 0.0

    dirichlet = geom.outer_boundary_mask | geom.vessel_mask
    T_init_C = float(mat["T_init_C"])
    T_blood_C = float(mat["T_blood_C"])
    nominal_power_W = float(protocol["nominal_power_W"])
    source_scale_per_W = float(protocol["source_scale_per_W"])
    dt_s = float(protocol["time_step_s"])
    t_end_s = float(protocol["ablation_time_s"])

    # Reduced-order 2D power mapping: a single calibration constant is fitted on a no-vessel reference case.
    q_source = q_unit * nominal_power_W * source_scale_per_W

    A_diff = build_diffusion_matrix(k_map, dx_m, dy_m, dirichlet)
    rho_c = float(mat["rho_kg_m3"]) * float(mat["c_J_kg_K"])
    N = ny * nx
    M = (rho_c / dt_s) * sparse.eye(N, format="csr") + A_diff + sparse.diags(perf_map.ravel(), format="csr")
    M = M.tolil()
    dmask = dirichlet.ravel()
    for p in np.where(dmask)[0]:
        M.rows[p] = [p]
        M.data[p] = [1.0]
    lu = splu(M.tocsc())

    T = np.full((ny, nx), T_init_C, dtype=float)
    T[geom.vessel_mask] = T_blood_C
    omega = np.zeros_like(T)

    A_freq = float(dmg["A_freq_1_s"])
    Ea = float(dmg["Ea_J_mol"])
    R = 8.314

    n_steps = int(np.ceil(t_end_s / dt_s))
    for _ in range(n_steps):
        rhs = (rho_c / dt_s) * T.ravel() + q_source.ravel() + perf_map.ravel() * T_blood_C
        rhs[dmask] = T_blood_C
        T = lu.solve(rhs).reshape((ny, nx))
        T[geom.vessel_mask] = T_blood_C

        T_kelvin = T + 273.15
        omega += A_freq * np.exp(-Ea / (R * T_kelvin)) * dt_s

    threshold = float(dmg.get("threshold_omega", 1.0))
    lesion_mask = omega >= threshold
    return T, omega, lesion_mask


def run_case(geom: Geometry, cfg: dict) -> Dict[str, np.ndarray]:
    phi, q_unit, sigma_map = solve_potential(geom, cfg)
    T, omega, lesion_mask = solve_heat_and_damage(geom, cfg, q_unit)
    return {
        "phi": phi,
        "q_unit": q_unit,
        "sigma_map": sigma_map,
        "temperature_C": T,
        "omega": omega,
        "lesion_mask": lesion_mask,
    }
